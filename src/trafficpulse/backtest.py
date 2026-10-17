"""Quarterly expanding-origin diagnostics; no tuning or final holdout reads."""
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import platform

import numpy as np
import scipy
import sklearn
from threadpoolctl import threadpool_limits

from .baselines import ISSUE_DELAY, TRAINING_END, VALIDATION_END
from .data import ROOT
from .features import (FEATURE_COLUMNS, _validate_stamp, build_features,
                       load_verified_inputs, validate_rows)
from .models import baseline_predictions, make_model, matrix, predict, scores_for

ORIGINS = tuple(datetime(2017, month, 1) for month in (1, 4, 7, 10))
SELECTED = (('ridge_alpha_1', 'ridge', 1), ('hist_leaves_31', 'hist', 31))
TREE = 'hist_leaves_31'


def available_history(rows, origin):
    """Allow earlier validation labels only when available at a backtest origin."""
    _validate_stamp(origin)
    if not TRAINING_END <= origin < VALIDATION_END:
        raise ValueError('Origin must be within validation; final holdout is excluded')
    validate_rows(rows)
    return [r for r in rows if r['date_time'] <= origin - ISSUE_DELAY
            and r['traffic_volume'] is not None]


def forecast_at_origin(rows, origin, targets):
    fit = available_history(rows, origin)
    validate_rows(targets)
    if any(r['date_time'] < origin for r in targets):
        raise ValueError('Forecast target precedes its fitting origin')
    if not fit or not targets:
        raise ValueError('Need available fitting labels and forecast targets')
    predictions = baseline_predictions(fit, targets)
    for name, family, setting in SELECTED:
        model = make_model(family, setting)
        with threadpool_limits(limits=1):
            model.fit(matrix(fit), [r['traffic_volume'] for r in fit])
        predictions[name] = predict(model, targets)
    return predictions, fit


def complete(row):
    return all(row[c] is not None for c in FEATURE_COLUMNS)


def population(rows, predictions):
    if any(len(values) != len(rows) for values in predictions.values()):
        raise ValueError('Every model must predict the same cohort')
    if any(not np.isfinite(values).all() for values in predictions.values()):
        raise ValueError('Nonfinite forecast')
    return dict(n=len(rows), incomplete_inputs=sum(not complete(r) for r in rows),
                weekly_fallback_count=sum(r['lag_168h'] is None for r in rows),
                scores=scores_for(rows, predictions))


def seasonal_bin(row):
    month = row['date_time'].month
    return 'DJF' if month in (12, 1, 2) else 'MAM' if month <= 5 else 'JJA' if month <= 8 else 'SON'


def diagnostics(rows, predictions):
    specs = {
        'month': (range(1, 13), lambda r: r['date_time'].month),
        'season': (('DJF', 'MAM', 'JJA', 'SON'), seasonal_bin),
        'hour': (range(24), lambda r: r['date_time'].hour),
        'day_type': (('weekday', 'weekend'),
                     lambda r: 'weekend' if r['date_time'].weekday() >= 5 else 'weekday'),
        'input_completeness': (('complete', 'incomplete'),
                               lambda r: 'complete' if complete(r) else 'incomplete'),
    }
    result = {}
    for dimension, (keys, classify) in specs.items():
        result[dimension] = {}
        for key in keys:
            indices = [i for i, row in enumerate(rows) if classify(row) == key]
            result[dimension][str(key)] = population(
                [rows[i] for i in indices],
                {name: [values[i] for i in indices] for name, values in predictions.items()})
    errors = sorted(range(len(rows)), key=lambda i: (
        -abs(predictions[TREE][i] - rows[i]['traffic_volume']), rows[i]['date_time']))[:10]
    result['largest_tree_errors'] = [dict(
        date_time=str(rows[i]['date_time']), actual=rows[i]['traffic_volume'],
        prediction=predictions[TREE][i],
        error_vehicles_per_hour=predictions[TREE][i]-rows[i]['traffic_volume'],
        incomplete_inputs=not complete(rows[i])) for i in errors]
    return result


def experiment(rows):
    rows = sorted(rows, key=lambda r: r['date_time'])
    validate_rows(rows)
    targets = [r for r in rows if r['split'] == 'validation' and r['traffic_volume'] is not None]
    fixed, _ = forecast_at_origin(rows, TRAINING_END, targets)
    expanding = {name: [] for name in fixed}
    folds = []
    seen = []
    for origin, end in zip(ORIGINS, (*ORIGINS[1:], VALIDATION_END)):
        indices = [i for i, r in enumerate(targets) if origin <= r['date_time'] < end]
        subset = [targets[i] for i in indices]
        fit = available_history(rows, origin)
        predictions = {name: [] for name in fixed}
        if subset:
            # Reuse the identical first-origin model rather than fit it twice.
            if origin == TRAINING_END:
                predictions = {name: [values[i] for i in indices] for name, values in fixed.items()}
            else:
                predictions, fit = forecast_at_origin(rows, origin, subset)
        expected_slots = int((end - origin).total_seconds() // 3600)
        fold = dict(origin=str(origin), end_exclusive=str(end),
                    fit_label_cutoff_inclusive=str(origin-ISSUE_DELAY),
                    fit_n=len(fit), fit_latest_label=str(max(r['date_time'] for r in fit)),
                    expected_slots=expected_slots, missing_targets=expected_slots-len(subset),
                    quarterly_refit=population(subset, predictions),
                    fixed_origin=population(subset, {name: [values[i] for i in indices]
                                                    for name, values in fixed.items()}))
        folds.append(fold)
        seen.extend(indices)
        for name in expanding:
            expanding[name].extend(predictions[name])
    if seen != list(range(len(targets))):
        raise ValueError('Folds must cover every observed target exactly once')
    result = dict(
        protocol=dict(final_holdout_read=False, model_retuning=False,
                      validation_previously_inspected=True,
                      quarterly_refit='Expanding history through origin minus two hours',
                      fixed_origin='2017-01-01 model, unchanged throughout validation',
                      policy_adoption='Diagnostic comparison only; fixed-origin reference retained'),
        fixed_models={family: name for name, family, _ in SELECTED},
        folds=folds, pooled=dict(quarterly_refit=population(targets, expanding),
                                 fixed_origin=population(targets, fixed)),
        quarterly_refit_diagnostics=diagnostics(targets, expanding))
    return result, targets, fixed, expanding


def run(root=ROOT):
    root = Path(root)
    prior_path = root / 'reports/part05_models.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    if prior['selected_by_family'] != {family: name for name, family, _ in SELECTED}:
        raise ValueError('Part 5 selections changed; review the frozen backtest plan')
    raw, fingerprints = load_verified_inputs(root)
    result, targets, fixed, expanding = experiment(build_features(raw))
    # A changed earlier implementation must not silently rewrite the reference.
    for name, metrics in result['pooled']['fixed_origin']['scores'].items():
        for metric, value in metrics.items():
            if not np.isclose(value, prior['validation']['all_observed'][name][metric],
                              rtol=1e-10, atol=1e-10):
                raise ValueError('Fixed-origin reference does not reproduce Part 5')
    path = root / 'data/processed/part06_backtest_predictions.csv'
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        columns = [(policy, name) for policy in ('fixed', 'quarterly') for name in fixed]
        writer.writerow(['date_time', 'actual', *(f'{p}__{n}' for p, n in columns)])
        for i, row in enumerate(targets):
            writer.writerow([row['date_time'], row['traffic_volume'],
                             *((fixed if p == 'fixed' else expanding)[n][i] for p, n in columns)])
    result.update(input_sha256=fingerprints,
                  part05_report_sha256=hashlib.sha256(prior_path.read_bytes()).hexdigest(),
                  backtest_plan_sha256=hashlib.sha256((root/'docs/BACKTEST_PLAN.md').read_bytes()).hexdigest(),
                  prediction_csv_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  versions=dict(python=platform.python_version(), numpy=np.__version__,
                                scipy=scipy.__version__, sklearn=sklearn.__version__))
    (root/'reports/part06_backtest.json').write_text(
        json.dumps(result, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    result = run()
    print(json.dumps({'pooled': result['pooled'], 'folds': result['folds']}, indent=2))
