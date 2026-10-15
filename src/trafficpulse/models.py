"""Bounded chronological model selection with a sealed final holdout."""
from collections import defaultdict
import csv
from datetime import datetime
import hashlib
import json
import platform
import statistics

import numpy as np
import scipy
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from .baselines import ISSUE_DELAY, TRAINING_END, _metrics
from .data import ROOT
from .features import FEATURE_COLUMNS, build_features, load_verified_inputs, training_rows_available

TUNE_START = datetime(2016, 7, 1)
CANDIDATES = (
    ('ridge_alpha_1', 'ridge', 1), ('ridge_alpha_10', 'ridge', 10),
    ('ridge_alpha_100', 'ridge', 100),
    ('hist_leaves_15', 'hist', 15), ('hist_leaves_31', 'hist', 31),
)
BASELINE_NAMES = ('global_mean', 'weekday_hour_mean', 'weekly_with_fallback')


def matrix(rows):
    return np.asarray([[np.nan if row[c] is None else row[c] for c in FEATURE_COLUMNS]
                       for row in rows], dtype=float)


def make_model(family, setting):
    if family == 'ridge':
        return make_pipeline(SimpleImputer(strategy='median', add_indicator=True,
                                           keep_empty_features=True),
                             StandardScaler(), Ridge(alpha=setting, solver='svd'))
    if family == 'hist':
        return HistGradientBoostingRegressor(
            max_leaf_nodes=setting, learning_rate=0.05, max_iter=200,
            min_samples_leaf=20, l2_regularization=1, early_stopping=False,
            random_state=42, loss='squared_error')
    raise ValueError('Unknown model family')


def fit_model(rows, issue_time, family, setting):
    eligible = training_rows_available(rows, issue_time)
    if not eligible:
        raise ValueError('No available training labels')
    model = make_model(family, setting)
    with threadpool_limits(limits=1):
        model.fit(matrix(eligible), [row['traffic_volume'] for row in eligible])
    return model, eligible


def predict(model, rows):
    with threadpool_limits(limits=1):
        result = np.maximum(model.predict(matrix(rows)), 0)
    if not np.isfinite(result).all():
        raise ValueError('Nonfinite forecast; refuse to hide prediction failure')
    return result.tolist()


def baseline_predictions(fit_rows, score_rows):
    mean = statistics.fmean(row['traffic_volume'] for row in fit_rows)
    groups = defaultdict(list)
    for row in fit_rows:
        t = row['date_time']
        groups[(t.weekday(), t.hour)].append(row['traffic_volume'])
    means = {key: statistics.fmean(values) for key, values in groups.items()}
    weekday = [means.get((r['date_time'].weekday(), r['date_time'].hour), mean)
               for r in score_rows]
    return dict(global_mean=[mean] * len(score_rows), weekday_hour_mean=weekday,
                weekly_with_fallback=[r['lag_168h'] if r['lag_168h'] is not None else p
                                      for r, p in zip(score_rows, weekday)])


def select_candidate(scores, names):
    # min preserves the declared order for exact ties.
    return min(names, key=lambda name: scores[name]['mae_vehicles_per_hour'])


def tuning_rows(rows):
    return [row for row in rows if row['split'] == 'train'
            and TUNE_START <= row['date_time'] <= TRAINING_END - ISSUE_DELAY
            and row['traffic_volume'] is not None]


def scores_for(rows, predictions, mask=None):
    chosen = list(range(len(rows))) if mask is None else [i for i, keep in enumerate(mask) if keep]
    if not chosen:
        return {name: None for name in predictions}
    return {name: _metrics([rows[i]['traffic_volume'] for i in chosen], [values[i] for i in chosen])
            for name, values in predictions.items()}


def experiment(rows):
    tuning = tuning_rows(rows)
    if not tuning:
        raise ValueError('No tuning targets')
    inner_fit = training_rows_available(rows, TUNE_START)
    tuning_predictions = baseline_predictions(inner_fit, tuning)
    for name, family, setting in CANDIDATES:
        model, _ = fit_model(rows, TUNE_START, family, setting)
        tuning_predictions[name] = predict(model, tuning)
    tuning_scores = scores_for(tuning, tuning_predictions)
    selected = {family: select_candidate(tuning_scores, [n for n, f, _ in CANDIDATES if f == family])
                for family in ('ridge', 'hist')}
    champion = select_candidate(tuning_scores, [*BASELINE_NAMES, *selected.values()])
    # All selection decisions above precede inspection of validation outcomes.
    validation = [r for r in rows if r['split'] == 'validation' and r['traffic_volume'] is not None]
    if not validation:
        raise ValueError('No validation targets')
    final_fit = training_rows_available(rows, TRAINING_END)
    predictions = baseline_predictions(final_fit, validation)
    for name, family, setting in CANDIDATES:
        if name == selected[family]:
            model, _ = fit_model(rows, TRAINING_END, family, setting)
            predictions[name] = predict(model, validation)
    weekly_mask = [r['lag_168h'] is not None for r in validation]
    incomplete = [any(r[c] is None for c in FEATURE_COLUMNS) for r in validation]
    result = dict(
        protocol=dict(tune_start=str(TUNE_START), tune_end_inclusive=str(TRAINING_END-ISSUE_DELAY),
                      inner_fit_label_cutoff=str(TUNE_START-ISSUE_DELAY),
                      final_fit_label_cutoff=str(TRAINING_END-ISSUE_DELAY),
                      selection_metric='2016 tuning MAE; fixed order for exact ties',
                      validation_used_for_selection=False, final_holdout_read=False,
                      negative_prediction_policy='Clip learned forecasts to zero',
                      validation_refitting=False),
        inner_fit_n=len(inner_fit), tuning_n=len(tuning), final_fit_n=len(final_fit),
        tuning_scores=tuning_scores, selected_by_family=selected, provisional_champion=champion,
        validation=dict(observed_targets=len(validation), predicted_targets=len(validation),
                        weekly_fallback_count=sum(not x for x in weekly_mask),
                        incomplete_feature_targets=sum(incomplete),
                        all_observed=scores_for(validation, predictions),
                        shared_weekly_cohort=scores_for(validation, predictions, weekly_mask),
                        incomplete_features=scores_for(validation, predictions, incomplete)),
    )
    return result, validation, predictions


def run(root=ROOT):
    raw, fingerprints = load_verified_inputs(root)
    rows = build_features(raw)
    result, validation, predictions = experiment(rows)
    path = root / 'data/processed/part05_validation_predictions.csv'
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(['date_time', 'actual', *predictions])
        for i, row in enumerate(validation):
            writer.writerow([row['date_time'], row['traffic_volume'],
                             *(values[i] for values in predictions.values())])
    result.update(input_sha256=fingerprints, feature_columns=list(FEATURE_COLUMNS),
                  modeling_plan_sha256=hashlib.sha256((root/'docs/MODELING_PLAN.md').read_bytes()).hexdigest(),
                  prediction_csv_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  versions=dict(python=platform.python_version(), numpy=np.__version__,
                                scipy=scipy.__version__, sklearn=sklearn.__version__))
    (root/'reports/part05_models.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
