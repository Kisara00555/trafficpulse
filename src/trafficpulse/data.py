"""Download the attributed source and audit its hourly observation grain.

Day 1 intentionally does not clean, impute, split, or model the observations.
Only Python's standard library is required.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timedelta, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path
from urllib.request import urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[2]
URL = 'https://archive.ics.uci.edu/static/public/492/metro%2Binterstate%2Btraffic%2Bvolume.zip'
MEMBER = 'Metro_Interstate_Traffic_Volume.csv.gz'
COLUMNS = ['holiday', 'temp', 'rain_1h', 'snow_1h', 'clouds_all',
           'weather_main', 'weather_description', 'date_time', 'traffic_volume']


def read_rows(archive):
    """Read only the expected member; never extract arbitrary ZIP paths."""
    with zipfile.ZipFile(archive) as zipped:
        payload = gzip.decompress(zipped.read(MEMBER)).decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(payload))
    if reader.fieldnames != COLUMNS:
        raise ValueError(f'Unexpected schema: {reader.fieldnames}')
    return list(reader)


def audit(rows):
    if not rows:
        raise ValueError('Dataset is empty')
    missing_columns = set(COLUMNS) - set(rows[0])
    if missing_columns:
        raise ValueError(f'Missing columns: {sorted(missing_columns)}')
    times = []
    volumes = defaultdict(set)
    blank_counts = Counter()
    invalid_values = Counter()
    for row in rows:
        for column in COLUMNS:
            if row.get(column) in ('', None):
                blank_counts[column] += 1
        stamp = datetime.strptime(row['date_time'], '%Y-%m-%d %H:%M:%S')
        if stamp.minute or stamp.second:
            raise ValueError('Expected timestamps on hourly boundaries')
        times.append(stamp)
        volume = int(row['traffic_volume'])
        volumes[stamp].add(volume)
        invalid_values['negative_traffic_rows'] += volume < 0
        invalid_values['nonpositive_kelvin_rows'] += float(row['temp']) <= 0
        invalid_values['negative_rain_rows'] += float(row['rain_1h']) < 0
        invalid_values['negative_snow_rows'] += float(row['snow_1h']) < 0
        invalid_values['clouds_outside_0_100_rows'] += not 0 <= float(row['clouds_all']) <= 100
    counts = Counter(times)
    ordered = sorted(counts)
    gaps = []
    for left, right in zip(ordered, ordered[1:]):
        missing = int((right-left).total_seconds() // 3600) - 1
        if missing:
            gaps.append({'first_missing': str(left+timedelta(hours=1)),
                         'last_missing': str(right-timedelta(hours=1)),
                         'missing_hours': missing})
    expected = int((ordered[-1]-ordered[0]).total_seconds() // 3600) + 1
    return {
        'rows': len(rows), 'columns': len(COLUMNS),
        'first_timestamp': str(ordered[0]), 'last_timestamp': str(ordered[-1]),
        'unique_timestamps': len(counts), 'expected_hourly_slots': expected,
        'missing_hourly_slots': expected-len(counts),
        'timestamps_with_multiple_rows': sum(n > 1 for n in counts.values()),
        'extra_rows_beyond_one_per_timestamp': len(rows)-len(counts),
        'exact_duplicate_rows': len(rows)-len({tuple(row[c] for c in COLUMNS) for row in rows}),
        'timestamps_with_conflicting_traffic': sum(len(v) > 1 for v in volumes.values()),
        'blank_cells_by_column': {c: blank_counts[c] for c in COLUMNS},
        'range_flags': dict(invalid_values),
        'largest_gaps': sorted(gaps, key=lambda g: (-g['missing_hours'], g['first_missing']))[:5],
        'time_assumption': 'Naive source clock; UCI labels it local CST. DST interpretation is unresolved.',
        'scope': 'Structural audit only; no cleaning, target-distribution exploration or modeling.',
    }


def run(download=False):
    archive = ROOT / 'data/raw/source.zip'
    archive.parent.mkdir(parents=True, exist_ok=True)
    if not archive.exists():
        if not download:
            raise FileNotFoundError('Run with --download to fetch the public UCI dataset.')
        with urlopen(URL, timeout=60) as response:
            payload = response.read(10_000_001)
        if len(payload) > 10_000_000:
            raise ValueError('Unexpected source download size')
        # Validate before persisting an unexpected response as source data.
        read_rows(io.BytesIO(payload))
        archive.write_bytes(payload)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    expected_path = ROOT / 'data/source.sha256'
    if expected_path.exists() and expected_path.read_text().strip() != digest:
        raise ValueError('Source checksum changed. Review the source before updating the recorded checksum.')
    result = audit(read_rows(archive))
    destination = ROOT / 'reports'
    destination.mkdir(exist_ok=True)
    (destination / 'day01_audit.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    manifest = {
        'source_url': URL, 'dataset_doi': 'https://doi.org/10.24432/C5X60B',
        'citation': 'Hogue, J. (2019). Metro Interstate Traffic Volume. UCI Machine Learning Repository.',
        'license': 'CC BY 4.0', 'archive_sha256': digest,
        'archive_bytes': archive.stat().st_size,
        'audit_run_at_utc': datetime.now(timezone.utc).isoformat(),
        'archive_member': MEMBER,
    }
    (destination / 'source_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download', action='store_true', help='Download only if the local source is absent')
    args = parser.parse_args()
    print(json.dumps(run(download=args.download), indent=2))


if __name__ == '__main__':
    main()
