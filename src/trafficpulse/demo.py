"""Build a dependency-free historical replay from verified saved holdout predictions."""
import csv
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path

from .data import ROOT


def payload(root):
    root = Path(root)
    report = json.loads((root/'reports/part09_holdout.json').read_text(encoding='utf-8'))
    freeze = json.loads((root/'reports/part09_freeze.json').read_text(encoding='utf-8'))
    path = root/'data/processed/part09_holdout_predictions.csv'
    if hashlib.sha256(path.read_bytes()).hexdigest() != report['prediction_csv_sha256']:
        raise ValueError('Demo prediction fingerprint mismatch')
    with path.open(newline='', encoding='utf-8') as handle:
        source = list(csv.DictReader(handle))
    chosen = source[:freeze['demo_hours']]
    if len(chosen) != freeze['demo_hours']:
        raise ValueError('Missing predeclared demo window')
    rows = []
    for i, row in enumerate(chosen):
        stamp = datetime.fromisoformat(row['date_time'])
        if stamp != datetime.fromisoformat(freeze['start'])+timedelta(hours=i):
            raise ValueError('Demo must use the first contiguous 48 hours, not selected successes')
        rows.append(dict(time=row['date_time'], cutoff=row['available_through'],
                         missing=int(row['missing_feature_count']),
                         actual=None if row['actual']=='' else int(row['actual']),
                         tree=float(row['hist_leaves_31']), baseline=float(row['weekday_hour_mean']),
                         lower=float(row['hist_leaves_31__lower']), upper=float(row['hist_leaves_31__upper'])))
    return dict(rows=rows, evaluation=report['evaluation'], freeze_commit=report['freeze_commit'],
                prediction_sha256=report['prediction_csv_sha256'])


def run(root=ROOT):
    root = Path(root)
    data = payload(root)
    template = (root/'demo/template.html').read_text(encoding='utf-8')
    if template.count('__TRAFFICPULSE_DATA__') != 1:
        raise ValueError('Expected exactly one data insertion marker')
    serialized = json.dumps(data, allow_nan=False, separators=(',', ':')).replace('<', '\\u003c')
    html = template.replace('__TRAFFICPULSE_DATA__', serialized)
    (root/'demo/index.html').write_text(html, encoding='utf-8', newline='\n')
    return len(data['rows'])


if __name__ == '__main__':
    print(f'Built historical replay with {run()} predeclared hourly forecasts: demo/index.html')
