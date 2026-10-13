from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from trafficpulse.features import (
    FEATURE_COLUMNS, build_features, features_at, load_verified_inputs,
    training_rows_available,
)


class FeatureTests(unittest.TestCase):
    def test_future_and_unavailable_observations_cannot_change_features(self):
        t = datetime(2017, 1, 2, 12)
        history = {t - timedelta(hours=h): h for h in range(200)}
        expected = features_at(t, history)
        for offset in (-24, -1, 0, 1):
            history[t - timedelta(hours=offset)] = 999999
        self.assertEqual(features_at(t, history), expected)
        history[t - timedelta(hours=2)] = 500
        self.assertEqual(features_at(t, history)['lag_2h'], 500)
        self.assertNotEqual(features_at(t, history)['rolling_mean_24h'],
                            expected['rolling_mean_24h'])

    def test_missing_exact_lag_is_not_previous_row_and_zero_is_observed(self):
        t = datetime(2017, 1, 1)
        result = features_at(t, {t - timedelta(hours=3): 0})
        self.assertIsNone(result['lag_2h'])
        self.assertEqual(result['lag_3h'], 0)
        self.assertEqual(result['rolling_count_24h'], 1)
        self.assertIsNone(result['rolling_mean_24h'])

    def test_rolling_window_has_exact_endpoints_and_requires_full_coverage(self):
        t = datetime(2017, 1, 1)
        history = {t - timedelta(hours=h): h for h in range(2, 26)}
        history[t - timedelta(hours=26)] = 999999
        result = features_at(t, history)
        self.assertEqual(result['rolling_mean_24h'], 13.5)
        self.assertEqual(result['rolling_count_24h'], 24)
        history[t - timedelta(hours=25)] = None
        self.assertIsNone(features_at(t, history)['rolling_mean_24h'])

    def test_validation_can_use_available_training_history(self):
        rows = [dict(date_time=datetime(2016, 12, 31, 22), split='train', traffic_volume=42),
                dict(date_time=datetime(2017, 1, 1), split='validation', traffic_volume=None)]
        features = build_features(rows)
        self.assertEqual(features[-1]['lag_2h'], 42)
        self.assertIsNone(features[-1]['traffic_volume'])
        self.assertEqual(build_features(reversed(rows)), features)
        self.assertNotIn('traffic_volume', FEATURE_COLUMNS)
        self.assertNotIn('observed', FEATURE_COLUMNS)

    def test_fit_labels_obey_delay_and_never_include_validation(self):
        rows = [dict(date_time=datetime(2016, 12, 31, hour), split='train', traffic_volume=hour)
                for hour in (21, 22, 23)]
        rows.append(dict(date_time=datetime(2017, 1, 1), split='validation', traffic_volume=500))
        self.assertEqual([r['traffic_volume'] for r in training_rows_available(
            rows, datetime(2017, 1, 1))], [21, 22])
        self.assertEqual(len(training_rows_available(rows, datetime(2018, 1, 1))), 3)

    def test_duplicates_final_test_wrong_boundary_and_nonhourly_fail(self):
        row = dict(date_time=datetime(2016, 12, 31), split='train', traffic_volume=1)
        for bad in ([row, row], [dict(row, split='test')],
                    [dict(row, date_time=datetime(2017, 1, 1))],
                    [dict(row, date_time=datetime(2016, 12, 31, 0, 30))]):
            with self.subTest(rows=bad), self.assertRaises(ValueError):
                build_features(bad)

    def test_calendar_features_are_known_without_history(self):
        result = features_at(datetime(2017, 1, 1), {})
        self.assertEqual((result['hour'], result['weekday'], result['month'],
                          result['is_weekend']), (0, 6, 1, 1))
        self.assertEqual(result['hour_cos'], 1)
        self.assertEqual(result['hour_sin'], 0)
        self.assertEqual(set(result), set(FEATURE_COLUMNS))

    def test_loader_checks_fingerprints_and_needs_no_test_file(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'reports').mkdir()
            (root / 'data/processed').mkdir(parents=True)
            outputs = {}
            for split, date in [('train', '2016-12-31 22:00:00'),
                                ('validation', '2017-01-01 00:00:00')]:
                path = root / 'data/processed' / f'{split}.csv'
                path.write_text(f'date_time,traffic_volume,split\n{date},42,{split}\n', encoding='utf-8')
                outputs[split] = dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            manifest = dict(train_end_exclusive='2017-01-01 00:00:00',
                            validation_end_exclusive='2018-01-01 00:00:00', outputs=outputs)
            (root / 'reports/part02_manifest.json').write_text(json.dumps(manifest))
            self.assertEqual(len(load_verified_inputs(root)[0]), 2)
            path.write_text(path.read_text().replace(',42,', ',43,'))
            with self.assertRaisesRegex(ValueError, 'fingerprint mismatch'):
                load_verified_inputs(root)


if __name__ == '__main__':
    unittest.main()
