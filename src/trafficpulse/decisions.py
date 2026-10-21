"""Hypothetical capacity tradeoffs using frozen development forecasts only."""
import csv
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import statistics

from .data import ROOT

MODELS = ('hist_leaves_31', 'weekday_hour_mean')
BLOCK_SIZES = (250, 500, 1000)
SHORTFALL_PENALTIES = (1, 3, 10)
FIELDS = ['date_time', 'actual', *(f'{m}__{f}' for m in MODELS for f in ('point', 'lower', 'upper'))]


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def allocation(forecast, block_size):
    if not math.isfinite(forecast) or forecast < 0:
        raise ValueError('Forecast must be finite and nonnegative')
    if not math.isfinite(block_size) or block_size <= 0:
        raise ValueError('Block size must be finite and positive')
    return math.ceil(forecast / block_size)


def evaluate(actual, forecasts, block_size, shortfall_penalty):
    if not actual or len(actual) != len(forecasts):
        raise ValueError('Need the same nonempty population for outcomes and forecasts')
    if not math.isfinite(shortfall_penalty) or shortfall_penalty <= 0:
        raise ValueError('Shortfall penalty must be finite and positive')
    if any(not math.isfinite(y) or y < 0 for y in actual):
        raise ValueError('Outcomes must be finite and nonnegative')
    blocks = [allocation(p, block_size) for p in forecasts]
    shortfalls = [max(y-b*block_size, 0) for y, b in zip(actual, blocks)]
    unused = [max(b*block_size-y, 0) for y, b in zip(actual, blocks)]
    total = math.fsum(shortfall_penalty*s+u for s, u in zip(shortfalls, unused))
    hours = sum(s > 0 for s in shortfalls)
    return dict(n=len(actual), mean_loss=total/len(actual), total_loss=total,
                shortfall_hours=hours, shortfall_rate=hours/len(actual),
                mean_shortfall=statistics.fmean(shortfalls),
                mean_unused_capacity=statistics.fmean(unused), mean_blocks=statistics.fmean(blocks))


def load_predictions(path, expected_sha256, expected_n):
    if fingerprint(path) != expected_sha256:
        raise ValueError('Part 7 prediction fingerprint mismatch; reproduce Part 7 first')
    with path.open(newline='', encoding='utf-8') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            raise ValueError('Unexpected Part 7 prediction schema')
        records = list(reader)
    if len(records) != expected_n or not records:
        raise ValueError('Part 7 population mismatch')
    previous = None
    actual, forecasts = [], {f'{m}__{rule}': [] for m in MODELS for rule in ('point', 'upper')}
    for row in records:
        stamp = datetime.fromisoformat(row['date_time'])
        if (stamp.tzinfo is not None or stamp.minute or stamp.second or stamp.microsecond
                or not datetime(2017, 7, 1) <= stamp < datetime(2018, 1, 1)
                or (previous is not None and stamp <= previous)):
            raise ValueError('Need unique sorted hourly development timestamps; holdout prohibited')
        previous = stamp
        values = {key: float(row[key]) for key in FIELDS[1:]}
        if any(not math.isfinite(v) or v < 0 for v in values.values()):
            raise ValueError('Invalid prediction or target')
        actual.append(values['actual'])
        for model in MODELS:
            if not values[f'{model}__lower'] <= values[f'{model}__point'] <= values[f'{model}__upper']:
                raise ValueError('Point must lie inside its interval')
            for rule in ('point', 'upper'):
                forecasts[f'{model}__{rule}'].append(values[f'{model}__{rule}'])
    return actual, forecasts


def run(root=ROOT):
    root = Path(root)
    prior_path = root/'reports/part07_intervals.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    if (prior['protocol']['final_holdout_read'] is not False
            or prior['protocol']['evaluation_start'] != '2017-07-01 00:00:00'
            or prior['protocol']['evaluation_end_exclusive'] != '2018-01-01 00:00:00'):
        raise ValueError('Part 7 evaluation contract changed; review required')
    path = root/'data/processed/part07_interval_predictions.csv'
    actual, forecasts = load_predictions(path, prior['prediction_csv_sha256'], prior['evaluation']['n'])
    result = dict(protocol=dict(hypothetical=True, currency=False, final_holdout_read=False,
                               validation_previously_inspected=True, policy_optimized=False,
                               models_refitted=False, unused_penalty=1,
                               evaluation_start='2017-07-01 00:00:00',
                               evaluation_end_exclusive='2018-01-01 00:00:00'),
                  n=len(actual), missing_targets=prior['evaluation_missing_targets'],
                  prediction_csv_sha256=fingerprint(path), part07_report_sha256=fingerprint(prior_path),
                  decision_plan_sha256=fingerprint(root/'docs/DECISION_PLAN.md'),
                  scenarios=[dict(block_size=b, shortfall_penalty=r,
                                  policies={name: evaluate(actual, p, b, r) for name, p in forecasts.items()})
                             for b in BLOCK_SIZES for r in SHORTFALL_PENALTIES])
    (root/'reports/part08_decisions.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    result = run()
    print(json.dumps(dict(n=result['n'], scenarios=result['scenarios']), indent=2))
