"""Exact-clock forecasting inputs; no fitted transformations or final-test reads."""
import csv
from datetime import datetime, timedelta
import hashlib
import json
import math
from pathlib import Path
import statistics

from .baselines import ISSUE_DELAY, TRAINING_END, VALIDATION_END, read_hourly
from .data import ROOT

LAGS = (2, 3, 24, 48, 168)
ROLLING_OFFSETS = tuple(range(2, 26))
CALENDAR_COLUMNS = (
    'hour', 'weekday', 'month', 'is_weekend',
    'hour_sin', 'hour_cos', 'weekday_sin', 'weekday_cos',
)
FEATURE_COLUMNS = (*CALENDAR_COLUMNS, *(f'lag_{lag}h' for lag in LAGS),
                   'rolling_mean_24h', 'rolling_count_24h')
OUTPUT_COLUMNS = ('date_time', 'split', 'traffic_volume', *FEATURE_COLUMNS)


def _validate_stamp(stamp):
    if not isinstance(stamp, datetime) or stamp.tzinfo is not None:
        raise ValueError('Expected a naive source-clock datetime')
    if stamp.minute or stamp.second or stamp.microsecond:
        raise ValueError('Expected an exact hourly timestamp')


def validate_rows(rows):
    seen = set()
    for row in rows:
        stamp = row['date_time']
        _validate_stamp(stamp)
        if stamp in seen:
            raise ValueError('Duplicate timestamp')
        seen.add(stamp)
        split = row['split']
        if split not in {'train', 'validation'}:
            raise ValueError('Final test is excluded from Part 4')
        expected = 'train' if stamp < TRAINING_END else 'validation'
        if split != expected or stamp >= VALIDATION_END:
            raise ValueError('Row crosses frozen split boundary')
        value = row['traffic_volume']
        if value is not None and (type(value) is not int or value < 0):
            raise ValueError('Target must be a nonnegative integer or missing')


def features_at(stamp, history):
    """Use known calendar and exact history at t-2 or older; never inspect t."""
    _validate_stamp(stamp)
    hour_angle = 2 * math.pi * stamp.hour / 24
    weekday_angle = 2 * math.pi * stamp.weekday() / 7
    result = dict(hour=stamp.hour, weekday=stamp.weekday(), month=stamp.month,
                  is_weekend=int(stamp.weekday() >= 5),
                  hour_sin=math.sin(hour_angle), hour_cos=math.cos(hour_angle),
                  weekday_sin=math.sin(weekday_angle), weekday_cos=math.cos(weekday_angle))
    for lag in LAGS:
        result[f'lag_{lag}h'] = history.get(stamp - timedelta(hours=lag))
    values = [history.get(stamp - timedelta(hours=lag)) for lag in ROLLING_OFFSETS]
    observed = [value for value in values if value is not None]
    result['rolling_mean_24h'] = statistics.fmean(observed) if len(observed) == 24 else None
    result['rolling_count_24h'] = len(observed)
    return result


def build_features(rows):
    rows = list(rows)
    validate_rows(rows)
    history = {row['date_time']: row['traffic_volume'] for row in rows}
    return [dict(date_time=row['date_time'], split=row['split'],
                 traffic_volume=row['traffic_volume'],
                 **features_at(row['date_time'], history))
            for row in sorted(rows, key=lambda row: row['date_time'])]


def training_rows_available(rows, issue_time):
    """Select labeled training examples available at a declared model-fit issue time."""
    _validate_stamp(issue_time)
    rows = list(rows)
    validate_rows(rows)
    cutoff = issue_time - ISSUE_DELAY
    return [row for row in rows if row['split'] == 'train'
            and row['date_time'] <= cutoff and row['traffic_volume'] is not None]


def load_verified_inputs(root):
    root = Path(root)
    manifest = json.loads((root / 'reports/part02_manifest.json').read_text(encoding='utf-8'))
    if (manifest['train_end_exclusive'] != str(TRAINING_END)
            or manifest['validation_end_exclusive'] != str(VALIDATION_END)):
        raise ValueError('Frozen split manifest mismatch')
    rows, fingerprints = [], {}
    for split in ('train', 'validation'):
        # Fixed paths prevent a modified manifest from redirecting this loader to test.csv.
        path = root / 'data/processed' / f'{split}.csv'
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != manifest['outputs'][split]['sha256']:
            raise ValueError(f'{split} fingerprint mismatch; rebuild or review Part 2')
        partition = read_hourly(path)
        if any(row['split'] != split for row in partition):
            raise ValueError('Partition file contains a different split')
        rows.extend(partition)
        fingerprints[split] = digest
    validate_rows(rows)
    return rows, fingerprints


def summarize(rows):
    report = {}
    for split in ('train', 'validation'):
        subset = [row for row in rows if row['split'] == split]
        labeled = [row for row in subset if row['traffic_volume'] is not None]
        report[split] = dict(
            hourly_slots=len(subset), observed_targets=len(labeled),
            complete_feature_rows_with_target=sum(
                all(row[column] is not None for column in FEATURE_COLUMNS) for row in labeled),
            missing_by_feature={column: sum(row[column] is None for row in subset)
                                for column in FEATURE_COLUMNS},
        )
    return report


def run(root=ROOT):
    root = Path(root)
    inputs, fingerprints = load_verified_inputs(root)
    rows = build_features(inputs)
    outputs = {}
    for split in ('train', 'validation'):
        path = root / 'data/processed' / f'{split}_features.csv'
        with path.open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS, lineterminator='\n')
            writer.writeheader()
            writer.writerows(row for row in rows if row['split'] == split)
        outputs[split] = dict(path=f'data/processed/{path.name}',
                              sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    available = training_rows_available(rows, TRAINING_END)
    report = dict(
        specification_version='1.0', final_holdout_read=False,
        input_sha256=fingerprints, feature_columns=list(FEATURE_COLUMNS),
        lag_hours=list(LAGS), rolling_window_offsets_hours=list(ROLLING_OFFSETS),
        rolling_mean_minimum_observations=24,
        fitted_transformations='None; no imputation or scaling in Part 4',
        missing_policy='Preserve missing values; rolling count uses past observations only',
        model_fit_issue_time=str(TRAINING_END),
        model_fit_label_cutoff_inclusive=str(TRAINING_END - ISSUE_DELAY),
        available_training_labels=len(available),
        available_training_labels_with_complete_features=sum(
            all(row[column] is not None for column in FEATURE_COLUMNS) for row in available),
        partitions=summarize(rows), outputs=outputs,
    )
    (root / 'reports/part04_features.json').write_text(
        json.dumps(report, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
