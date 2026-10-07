"""Build a target-only hourly grid and frozen chronological partitions."""
from collections import defaultdict
import csv
from datetime import datetime, timedelta
import hashlib
import json
from .data import ROOT, read_rows

TRAIN_END = datetime(2017, 1, 1)
VALID_END = datetime(2018, 1, 1)
FIELDS = ['date_time', 'traffic_volume', 'observed', 'source_row_count', 'zero_volume_flag', 'split']


def partition(stamp):
    return 'train' if stamp < TRAIN_END else 'validation' if stamp < VALID_END else 'test'


def build_hourly(rows):
    groups = defaultdict(list)
    for row in rows:
        stamp = datetime.strptime(row['date_time'], '%Y-%m-%d %H:%M:%S')
        if stamp.minute or stamp.second:
            raise ValueError('Non-hourly timestamp')
        value = int(row['traffic_volume'])
        if value < 0:
            raise ValueError('Negative traffic count')
        groups[stamp].append(value)
    if not groups:
        raise ValueError('Empty source')
    for stamp, values in groups.items():
        if len(set(values)) != 1:
            raise ValueError(f'Conflicting traffic counts at {stamp}')
    current, end = min(groups), max(groups)
    result = []
    while current <= end:
        values = groups.get(current, [])
        target = values[0] if values else None
        result.append(dict(date_time=str(current), traffic_volume=target,
                           observed=int(bool(values)), source_row_count=len(values),
                           zero_volume_flag=int(target == 0), split=partition(current)))
        current += timedelta(hours=1)
    return result


def summarize(hourly):
    summary = {}
    for split in ('train', 'validation', 'test'):
        subset = [r for r in hourly if r['split'] == split]
        observed = sum(r['observed'] for r in subset)
        summary[split] = dict(first=subset[0]['date_time'] if subset else None,
                              last=subset[-1]['date_time'] if subset else None,
                              hourly_slots=len(subset), observed_hours=observed,
                              missing_hours=len(subset)-observed,
                              coverage=observed/len(subset) if subset else None)
    return summary


def run():
    archive = ROOT / 'data/raw/source.zip'
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != (ROOT / 'data/source.sha256').read_text().strip():
        raise ValueError('Source fingerprint mismatch')
    rows = read_rows(archive)
    hourly = build_hourly(rows)
    folder = ROOT / 'data/processed'
    folder.mkdir(parents=True, exist_ok=True)
    outputs = {}
    for name in ('hourly', 'train', 'validation', 'test'):
        selected = hourly if name == 'hourly' else [r for r in hourly if r['split'] == name]
        path = folder / f'{name}.csv'
        with path.open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator='\n')
            writer.writeheader()
            writer.writerows(selected)
        outputs[name] = dict(path=f'data/processed/{name}.csv',
                             sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    manifest = dict(source_sha256=digest, source_rows=len(rows),
                    hourly_slots=len(hourly), observed_hours=sum(r['observed'] for r in hourly),
                    missing_hours=sum(not r['observed'] for r in hourly),
                    train_end_exclusive=str(TRAIN_END), validation_end_exclusive=str(VALID_END),
                    timezone='Naive source clock, labeled local CST by UCI; DST unresolved',
                    target_missing_encoding='Empty CSV cell; never zero-filled or interpolated',
                    available_features='None yet: quality flags and source row counts are audit metadata, not model inputs',
                    partitions=summarize(hourly), outputs=outputs)
    (ROOT / 'reports/part02_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    return manifest


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
