"""Frozen residual intervals with chronological calibration; final holdout sealed."""
import csv
from datetime import datetime
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import platform
import statistics

import numpy as np
import scipy
import sklearn

from .baselines import ISSUE_DELAY, TRAINING_END, VALIDATION_END
from .data import ROOT
from .features import FEATURE_COLUMNS, build_features, load_verified_inputs, validate_rows
from .models import baseline_predictions, fit_model, predict, scores_for

EVALUATION_START = datetime(2017, 7, 1)
COVERAGE = Fraction(9, 10)
TREE = 'hist_leaves_31'
BASELINE = 'weekday_hour_mean'


def residual_quantile(residuals):
    values = sorted(residuals)
    if not values or any(not math.isfinite(x) or x < 0 for x in values):
        raise ValueError('Need finite nonnegative calibration residuals')
    rank = math.ceil((len(values)+1)*COVERAGE)
    if rank > len(values):
        raise ValueError('Too few calibration observations for a finite 90% radius')
    return dict(n=len(values), rank=rank, radius=values[rank-1])


def bounds(predictions, radius):
    if not math.isfinite(radius) or radius < 0:
        raise ValueError('Invalid radius')
    if any(not math.isfinite(x) or x < 0 for x in predictions):
        raise ValueError('Invalid point forecast')
    return [(max(0.0, x-radius), x+radius) for x in predictions]


def interval_metrics(actual, intervals):
    if len(actual) != len(intervals):
        raise ValueError('Interval and outcome populations differ')
    if not actual:
        return None
    widths, scores = [], []
    below = above = 0
    for y, (lo, hi) in zip(actual, intervals):
        if not all(math.isfinite(x) for x in (y, lo, hi)) or y < 0 or lo < 0 or lo > hi:
            raise ValueError('Invalid outcome or interval')
        below += y < lo
        above += y > hi
        widths.append(hi-lo)
        scores.append(hi-lo + 20*max(lo-y, 0) + 20*max(y-hi, 0))
    return dict(n=len(actual), covered=len(actual)-below-above,
                coverage=(len(actual)-below-above)/len(actual),
                below_lower=below, above_upper=above,
                mean_width=statistics.fmean(widths), mean_interval_score=statistics.fmean(scores))


def calibrate(rows, predictions):
    validate_rows(rows)
    if len(rows) != len(predictions):
        raise ValueError('Calibration predictions do not match rows')
    chosen = [i for i, r in enumerate(rows) if r['split'] == 'validation'
              and TRAINING_END <= r['date_time'] <= EVALUATION_START-ISSUE_DELAY
              and r['traffic_volume'] is not None]
    return residual_quantile([abs(rows[i]['traffic_volume']-predictions[i]) for i in chosen])


def summarize(rows, predictions, intervals):
    if any(len(v) != len(rows) for v in [*predictions.values(), *intervals.values()]):
        raise ValueError('All methods must score the same hours')
    return dict(n=len(rows),
                point_scores=scores_for(rows, predictions),
                intervals={name: interval_metrics([r['traffic_volume'] for r in rows], values)
                           for name, values in intervals.items()})


def diagnostics(rows, predictions, intervals):
    specs = {
        'month': (range(7, 13), lambda r: str(r['date_time'].month)),
        'season': (('JJA_partial', 'SON', 'DJF_partial'), lambda r:
                   'JJA_partial' if r['date_time'].month <= 8 else
                   'SON' if r['date_time'].month <= 11 else 'DJF_partial'),
        'hour': (range(24), lambda r: str(r['date_time'].hour)),
        'day_type': (('weekday', 'weekend'), lambda r:
                     'weekend' if r['date_time'].weekday() >= 5 else 'weekday'),
        'inputs': (('complete', 'incomplete'), lambda r:
                   'incomplete' if any(r[c] is None for c in FEATURE_COLUMNS) else 'complete'),
    }
    result = {}
    for dim, (keys, classify) in specs.items():
        result[dim] = {}
        for key in keys:
            indices = [i for i, r in enumerate(rows) if classify(r) == str(key)]
            result[dim][str(key)] = summarize(
                [rows[i] for i in indices],
                {name: [v[i] for i in indices] for name, v in predictions.items()},
                {name: [v[i] for i in indices] for name, v in intervals.items()})
    misses = []
    for r, p, (lo, hi) in zip(rows, predictions[TREE], intervals[TREE]):
        distance = max(lo-r['traffic_volume'], r['traffic_volume']-hi, 0)
        if distance:
            misses.append(dict(date_time=str(r['date_time']), actual=r['traffic_volume'],
                               prediction=p, lower=lo, upper=hi, distance_beyond_bound=distance))
    result['largest_tree_misses'] = sorted(misses, key=lambda x:
                                          (-x['distance_beyond_bound'], x['date_time']))[:5]
    return result


def experiment(rows):
    rows = sorted(rows, key=lambda r: r['date_time'])
    validate_rows(rows)
    validation = [r for r in rows if r['split'] == 'validation' and r['traffic_volume'] is not None]
    if not validation:
        raise ValueError('No validation observations')
    model, fit = fit_model(rows, TRAINING_END, 'hist', 31)
    points = {TREE: predict(model, validation),
              BASELINE: baseline_predictions(fit, validation)[BASELINE]}
    calibration = {name: calibrate(validation, p) for name, p in points.items()}
    chosen = [i for i, r in enumerate(validation) if r['date_time'] >= EVALUATION_START]
    evaluation = [validation[i] for i in chosen]
    if not evaluation:
        raise ValueError('No evaluation observations')
    predictions = {name: [p[i] for i in chosen] for name, p in points.items()}
    intervals = {name: bounds(p, calibration[name]['radius']) for name, p in predictions.items()}
    result = dict(protocol=dict(nominal_coverage=float(COVERAGE), final_holdout_read=False,
                                validation_previously_inspected=True, formal_coverage_guarantee=False,
                                fit_cutoff=str(TRAINING_END-ISSUE_DELAY),
                                calibration_start=str(TRAINING_END),
                                calibration_end_inclusive=str(EVALUATION_START-ISSUE_DELAY),
                                evaluation_start=str(EVALUATION_START),
                                evaluation_end_exclusive=str(VALIDATION_END),
                                refitting=False, evaluation_recalibration=False),
                  fit_n=len(fit), calibration=calibration,
                  evaluation_missing_targets=int((VALIDATION_END-EVALUATION_START).total_seconds()/3600)-len(evaluation),
                  evaluation=summarize(evaluation, predictions, intervals),
                  diagnostics=diagnostics(evaluation, predictions, intervals),
                  fixed_origin_reference=scores_for(validation, points))
    return result, evaluation, predictions, intervals


def run(root=ROOT):
    root = Path(root)
    prior_path = root/'reports/part05_models.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    if prior['selected_by_family']['hist'] != TREE:
        raise ValueError('Part 5 selection changed; review interval specification')
    raw, fingerprints = load_verified_inputs(root)
    result, rows, points, intervals = experiment(build_features(raw))
    for name, score in result['fixed_origin_reference'].items():
        for metric, value in score.items():
            if not math.isclose(value, prior['validation']['all_observed'][name][metric], rel_tol=1e-10, abs_tol=1e-10):
                raise ValueError('Fixed forecasts no longer reproduce Part 5')
    path = root/'data/processed/part07_interval_predictions.csv'
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(['date_time', 'actual', *(f'{n}__{field}' for n in points for field in ('point','lower','upper'))])
        for i, row in enumerate(rows):
            writer.writerow([row['date_time'], row['traffic_volume'],
                             *(x for name in points for x in (points[name][i], *intervals[name][i]))])
    result.update(input_sha256=fingerprints,
                  part05_report_sha256=hashlib.sha256(prior_path.read_bytes()).hexdigest(),
                  interval_plan_sha256=hashlib.sha256((root/'docs/INTERVAL_PLAN.md').read_bytes()).hexdigest(),
                  prediction_csv_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  versions=dict(python=platform.python_version(), numpy=np.__version__,
                                scipy=scipy.__version__, sklearn=sklearn.__version__))
    (root/'reports/part07_intervals.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    result = run()
    print(json.dumps({k: result[k] for k in ('calibration','evaluation','evaluation_missing_targets')}, indent=2))
