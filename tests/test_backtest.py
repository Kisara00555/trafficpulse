from datetime import datetime, timedelta
import math
import unittest

try:
    from trafficpulse.backtest import (
        ORIGINS, available_history, diagnostics, experiment, forecast_at_origin, population,
    )
    from trafficpulse.features import build_features
    HAS_MODELS = True
except ModuleNotFoundError as exc:
    if exc.name not in {'numpy', 'scipy', 'sklearn', 'threadpoolctl'}:
        raise
    HAS_MODELS = False


@unittest.skipUnless(HAS_MODELS, 'Install the model extra to run backtest tests')
class BacktestTests(unittest.TestCase):
    def raw(self):
        result = []
        for origin in ORIGINS:
            for h in range(-48, 48):
                t = origin + timedelta(hours=h)
                result.append(dict(date_time=t, split='train' if t.year == 2016 else 'validation',
                                   traffic_volume=None if h == 10 or (origin.month == 4 and h == 11)
                                   else 100+t.hour))
        return result

    def test_origin_uses_earlier_validation_but_not_last_unavailable_hour(self):
        origin = datetime(2017, 4, 1)
        fit = available_history(build_features(self.raw()), origin)
        self.assertEqual(max(r['date_time'] for r in fit), origin-timedelta(hours=2))
        self.assertTrue(any(r['split'] == 'validation' for r in fit))
        self.assertTrue(any(r['split'] == 'train' for r in fit))
        with self.assertRaises(ValueError):
            available_history(build_features(self.raw()), datetime(2018, 1, 1))

    def test_future_raw_values_cannot_change_origin_forecast(self):
        origin = datetime(2017, 4, 1)
        raw = self.raw()
        before = build_features(raw)
        altered = [dict(r, traffic_volume=999999) if r['date_time'] > origin-timedelta(hours=2)
                   else r for r in raw]
        after = build_features(altered)
        p1, _ = forecast_at_origin(before, origin, [r for r in before if r['date_time'] == origin])
        p2, _ = forecast_at_origin(after, origin, [r for r in after if r['date_time'] == origin])
        self.assertEqual(p1, p2)
        # Earlier validation observations are genuinely eligible at this later origin.
        revised = build_features([dict(r, traffic_volume=0) if r['split'] == 'validation'
                                  and r['date_time'] <= origin-timedelta(hours=2) else r for r in raw])
        p3, _ = forecast_at_origin(revised, origin, [r for r in revised if r['date_time'] == origin])
        self.assertNotEqual(p1['global_mean'], p3['global_mean'])

    def test_rejects_test_rows_duplicates_and_retrospective_targets(self):
        rows = build_features(self.raw())
        for invalid in (rows+[dict(rows[-1], split='test', date_time=datetime(2018, 1, 1))],
                        rows+[rows[0]]):
            with self.assertRaises(ValueError):
                experiment(invalid)
        with self.assertRaises(ValueError):
            forecast_at_origin(rows, datetime(2017, 4, 1), [rows[0]])

    def test_pooled_metrics_and_nonoverlapping_fold_coverage(self):
        result, rows, fixed, expanding = experiment(build_features(self.raw()))
        self.assertEqual(len(rows), len({r['date_time'] for r in rows}))
        self.assertEqual(sum(f['quarterly_refit']['n'] for f in result['folds']), len(rows))
        self.assertEqual(sum(f['expected_slots'] for f in result['folds']), 8760)
        self.assertNotEqual(result['folds'][0]['quarterly_refit']['n'],
                            result['folds'][1]['quarterly_refit']['n'])
        for policy, preds in [('fixed_origin', fixed), ('quarterly_refit', expanding)]:
            for name, values in preds.items():
                errors = [p-r['traffic_volume'] for p, r in zip(values, rows)]
                score = result['pooled'][policy]['scores'][name]
                self.assertEqual(score['n'], len(rows))
                self.assertAlmostEqual(score['mae_vehicles_per_hour'], sum(map(abs, errors))/len(rows))
                self.assertAlmostEqual(score['rmse_vehicles_per_hour'],
                                       math.sqrt(sum(e*e for e in errors)/len(rows)))
        for dimension in ('month', 'season', 'hour', 'day_type', 'input_completeness'):
            self.assertEqual(sum(x['n'] for x in result['quarterly_refit_diagnostics'][dimension].values()), len(rows))

    def test_empty_bins_and_zero_actual_are_not_hidden(self):
        row = dict(build_features(self.raw())[0], traffic_volume=0)
        preds = {'hist_leaves_31': [5.0]}
        report = diagnostics([row], preds)
        self.assertEqual(report['month']['12']['scores']['hist_leaves_31']['mae_vehicles_per_hour'], 5)
        self.assertIsNone(report['month']['2']['scores']['hist_leaves_31'])
        self.assertEqual(report['largest_tree_errors'][0]['actual'], 0)

    def test_mismatched_or_nonfinite_predictions_fail(self):
        row = build_features(self.raw())[0]
        for predictions in ({'model': []}, {'model': [float('nan')]}):
            with self.assertRaises(ValueError):
                population([row], predictions)


if __name__ == '__main__':
    unittest.main()
