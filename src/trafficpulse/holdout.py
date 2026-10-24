"""Single frozen holdout assessment, with explicit read-only reproducibility verification."""
import argparse
import csv
from datetime import datetime, timedelta
import hashlib
import io
import json
from pathlib import Path
import platform
import subprocess

import numpy as np
import scipy
import sklearn

from .baselines import ISSUE_DELAY, TRAINING_END, read_hourly
from .data import ROOT
from .features import FEATURE_COLUMNS, _validate_stamp, build_features, features_at, load_verified_inputs, validate_rows
from .intervals import BASELINE, TREE, bounds, summarize
from .models import baseline_predictions, fit_model, predict

FREEZE_COMMIT = 'd6101a1b824ec91d223d750a01fe3df65d90b782'
REPORT = 'reports/part09_holdout.json'
PREDICTIONS = 'data/processed/part09_holdout_predictions.csv'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def text_bytes(path):
    return Path(path).read_bytes().replace(b'\r\n', b'\n')


def load_freeze(root):
    root = Path(root).resolve()
    path = 'reports/part09_freeze.json'
    committed = subprocess.check_output(['git', '-c', f'safe.directory={root.as_posix()}',
                                         '-C', str(root), 'show', f'{FREEZE_COMMIT}:{path}'])
    if text_bytes(root/path) != committed:
        raise ValueError('Freeze record differs from the pre-holdout commit')
    freeze = json.loads(committed)
    for name, expected in freeze['text_sha256'].items():
        if sha(text_bytes(root/name)) != expected:
            raise ValueError(f'Frozen implementation/specification changed: {name}')
    if list(FEATURE_COLUMNS) != freeze['feature_columns']:
        raise ValueError('Feature allowlist changed')
    if not platform.python_version().startswith(freeze['versions']['python']+'.'):
        raise ValueError('Use the frozen Python minor version')
    for lib in (np, scipy, sklearn):
        if lib.__version__ != freeze['versions'][lib.__name__]:
            raise ValueError(f'Frozen dependency mismatch: {lib.__name__}')
    return freeze


def validate_holdout(rows, freeze):
    start, end = (datetime.fromisoformat(freeze[k]) for k in ('start', 'end_exclusive'))
    if not rows or len(rows) != freeze['slots']:
        raise ValueError('Holdout grid size mismatch')
    for i, row in enumerate(rows):
        stamp = row['date_time']
        _validate_stamp(stamp)
        if row['split'] != 'test' or stamp != start+timedelta(hours=i) or stamp >= end:
            raise ValueError('Need the complete ordered frozen test grid')
        value = row['traffic_volume']
        if value is not None and (type(value) is not int or value < 0):
            raise ValueError('Invalid holdout count')
    if rows[-1]['date_time']+timedelta(hours=1) != end:
        raise ValueError('Holdout endpoint mismatch')
    if sum(r['traffic_volume'] is not None for r in rows) != freeze['observed']:
        raise ValueError('Holdout observed-target count mismatch')


def holdout_features(development, test, freeze):
    validate_rows(development)
    validate_holdout(test, freeze)
    history = {r['date_time']: r['traffic_volume'] for r in [*development, *test]}
    return [dict(r, **features_at(r['date_time'], history)) for r in test]


def assess(rows, points, intervals):
    if any(len(v) != len(rows) for v in [*points.values(), *intervals.values()]):
        raise ValueError('Mismatched forecast population')
    ids = [i for i, r in enumerate(rows) if r['traffic_volume'] is not None]
    selected = [rows[i] for i in ids]
    result = summarize(selected, {n: [p[i] for i in ids] for n, p in points.items()},
                       {n: [p[i] for i in ids] for n, p in intervals.items()})
    result.update(hourly_slots=len(rows), missing_targets=len(rows)-len(ids),
                  predicted_slots=len(rows),
                  incomplete_feature_targets=sum(any(r[c] is None for c in FEATURE_COLUMNS) for r in selected),
                  weekly_fallback_count=sum(r['lag_168h'] is None for r in selected))
    return result


def experiment(development, test, freeze):
    # This fit path rejects test rows and never receives the test argument.
    dev_features = build_features(development)
    model, fit = fit_model(dev_features, TRAINING_END, 'hist', 31)
    if len(fit) != freeze['fit_n']:
        raise ValueError('Frozen fitting population changed')
    rows = holdout_features(development, test, freeze)
    points = baseline_predictions(fit, rows)
    points[TREE] = predict(model, rows)
    intervals = {name: bounds(points[name], radius) for name, radius in freeze['radii'].items()}
    specs = dict(month=(range(1, 10), lambda r: str(r['date_time'].month)),
                 hour=(range(24), lambda r: str(r['date_time'].hour)),
                 day_type=(('weekday', 'weekend'), lambda r: 'weekend' if r['date_time'].weekday() >= 5 else 'weekday'),
                 inputs=(('complete', 'incomplete'), lambda r: 'incomplete' if any(r[c] is None for c in FEATURE_COLUMNS) else 'complete'))
    slices = {}
    for dim, (keys, classify) in specs.items():
        slices[dim] = {}
        for key in keys:
            ids = [i for i, row in enumerate(rows) if classify(row) == str(key)]
            slices[dim][str(key)] = assess([rows[i] for i in ids],
                {n: [p[i] for i in ids] for n, p in points.items()},
                {n: [p[i] for i in ids] for n, p in intervals.items()})
    failures = [dict(date_time=str(r['date_time']), actual=r['traffic_volume'], prediction=points[TREE][i],
                     absolute_error=abs(r['traffic_volume']-points[TREE][i]))
                for i, r in enumerate(rows) if r['traffic_volume'] is not None]
    report = dict(freeze_commit=FREEZE_COMMIT, fit_n=len(fit),
                  fit_label_cutoff=freeze['fit_label_cutoff'], refitting=False,
                  holdout_used_for_selection=False, interval_radii=freeze['radii'],
                  evaluation=assess(rows, points, intervals), diagnostics=slices,
                  largest_tree_errors=sorted(failures, key=lambda r: (-r['absolute_error'], r['date_time']))[:5])
    return report, rows, points, intervals


def prediction_bytes(rows, points, intervals):
    output = io.StringIO(newline='')
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(['date_time', 'actual', 'available_through', 'missing_feature_count', *points,
                     *(f'{name}__{bound}' for name in intervals for bound in ('lower', 'upper'))])
    for i, row in enumerate(rows):
        writer.writerow([row['date_time'], row['traffic_volume'], row['date_time']-ISSUE_DELAY,
                         sum(row[c] is None for c in FEATURE_COLUMNS),
                         *(p[i] for p in points.values()), *(x for v in intervals.values() for x in v[i])])
    return output.getvalue().encode('utf-8')


def run(root=ROOT, verify=False):
    root = Path(root)
    report_path, csv_path = root/REPORT, root/PREDICTIONS
    if verify:
        if not report_path.exists() or not csv_path.exists():
            raise ValueError('Verification requires both existing evidence files')
    elif report_path.exists() or csv_path.exists():
        raise FileExistsError('Final evidence already exists; use --verify, never overwrite')
    freeze = load_freeze(root)
    development, fingerprints = load_verified_inputs(root)
    if any(fingerprints[s] != freeze['input_sha256'][s] for s in fingerprints):
        raise ValueError('Development inputs differ from the freeze')
    # First and only real-test loader, reached only after freeze checks above.
    path = root/'data/processed/test.csv'
    if sha(path.read_bytes()) != freeze['input_sha256']['test']:
        raise ValueError('Holdout fingerprint mismatch')
    test = read_hourly(path)
    result, rows, points, intervals = experiment(development, test, freeze)
    predictions = prediction_bytes(rows, points, intervals)
    result.update(input_sha256=freeze['input_sha256'],
                  freeze_sha256=sha(text_bytes(root/'reports/part09_freeze.json')),
                  runner_sha256=sha(text_bytes(root/'src/trafficpulse/holdout.py')),
                  prediction_csv_sha256=sha(predictions), versions=freeze['versions'])
    serialized = (json.dumps(result, indent=2, allow_nan=False)+'\n').encode('utf-8')
    if verify:
        if text_bytes(report_path) != serialized or csv_path.read_bytes() != predictions:
            raise ValueError('Frozen replay differs; original evidence preserved')
    else:
        # Exclusive creation prevents accidental replacement even in a concurrent run.
        with csv_path.open('xb') as handle: handle.write(predictions)
        with report_path.open('xb') as handle: handle.write(serialized)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true', help='Recompute unchanged settings and compare without overwriting')
    result = run(verify=parser.parse_args().verify)
    print(json.dumps(result['evaluation'], indent=2))
