from datetime import datetime, timedelta
import unittest

try:
    import numpy as np
    from trafficpulse.models import (
        TUNE_START, baseline_predictions, experiment, fit_model, matrix,
        predict, select_candidate, tuning_rows,
    )
    from trafficpulse.features import build_features
    HAS_MODELS = True
except ModuleNotFoundError as exc:
    if exc.name not in {'numpy', 'scipy', 'sklearn', 'threadpoolctl'}:
        raise
    HAS_MODELS = False


@unittest.skipUnless(HAS_MODELS, 'Install the model extra to run model tests')
class ModelTests(unittest.TestCase):
    def rows(self):
        raw = []
        for start, hours, split in [(datetime(2016, 6, 20), 24*12, 'train'),
                                    (datetime(2016, 12, 31), 24, 'train'),
                                    (datetime(2017, 1, 1), 48, 'validation')]:
            for h in range(hours):
                t = start + timedelta(hours=h)
                raw.append(dict(date_time=t, split=split, traffic_volume=100+t.hour))
        return build_features(raw)

    def test_fit_preprocessing_excludes_unavailable_and_future_labels(self):
        rows = self.rows()
        model, used = fit_model(rows, TUNE_START, 'ridge', 10)
        self.assertLessEqual(max(r['date_time'] for r in used), datetime(2016,6,30,22))
        before = model.named_steps['simpleimputer'].statistics_.copy()
        altered = [dict(r) for r in rows]
        for row in altered:
            if row['date_time'] > datetime(2016,6,30,22):
                row['traffic_volume'] = 999999
                row['lag_2h'] = 999999
        changed, _ = fit_model(altered, TUNE_START, 'ridge', 10)
        np.testing.assert_array_equal(before, changed.named_steps['simpleimputer'].statistics_)
        np.testing.assert_allclose(model.named_steps['ridge'].coef_, changed.named_steps['ridge'].coef_)

    def test_tuning_excludes_last_unavailable_training_hour(self):
        chosen = tuning_rows(self.rows())
        self.assertEqual(max(r['date_time'] for r in chosen), datetime(2016,12,31,22))
        self.assertTrue(all(r['split']=='train' for r in chosen))

    def test_feature_allowlist_excludes_target_and_audit_metadata(self):
        rows = self.rows()[:3]
        altered = [dict(r, traffic_volume=999999, observed=999999) for r in rows]
        np.testing.assert_array_equal(matrix(rows), matrix(altered))
        self.assertEqual(matrix(rows).shape[1], 15)

    def test_both_models_predict_with_missing_history(self):
        rows = self.rows()
        target = [dict(rows[-1])]
        for name in ('lag_2h','lag_3h','lag_24h','lag_48h','lag_168h','rolling_mean_24h'):
            target[0][name] = None
        for family, setting in [('ridge', 10), ('hist',15)]:
            model, _ = fit_model(rows, datetime(2017,1,1), family, setting)
            value = predict(model, target)[0]
            self.assertTrue(np.isfinite(value))
            self.assertGreaterEqual(value, 0)
            if family=='hist': self.assertFalse(model.early_stopping)

    def test_weekly_fallback_is_fitted_weekday_or_global(self):
        rows = self.rows()
        fit = [rows[0]]
        targets = [dict(rows[-1], lag_168h=None), dict(rows[-1],lag_168h=0)]
        preds = baseline_predictions(fit, targets)
        self.assertEqual(preds['weekly_with_fallback'], [rows[0]['traffic_volume'],0])

    def test_validation_targets_cannot_select_model(self):
        rows = self.rows()
        before, validation, forecasts = experiment(rows)
        altered = [dict(r, traffic_volume=999999) if r['split']=='validation' else r for r in rows]
        after, _, forecasts_after = experiment(altered)
        self.assertEqual(before['selected_by_family'], after['selected_by_family'])
        self.assertEqual(before['provisional_champion'], after['provisional_champion'])
        self.assertEqual(forecasts, forecasts_after)
        self.assertTrue(all(len(v)==len(validation) for v in forecasts.values()))
        self.assertTrue(all(s['n']==len(validation) for s in before['validation']['all_observed'].values()))

    def test_selection_tie_uses_declared_order(self):
        scores = {n: {'mae_vehicles_per_hour':1} for n in ('first','second')}
        self.assertEqual(select_candidate(scores, ['first','second']), 'first')


if __name__ == '__main__':
    unittest.main()
