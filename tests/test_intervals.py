from datetime import datetime, timedelta
import unittest

try:
    from trafficpulse.intervals import (BASELINE, TREE, bounds, calibrate, diagnostics,
                                       experiment, interval_metrics, residual_quantile, summarize)
    from trafficpulse.features import build_features
    HAS_MODELS = True
except ModuleNotFoundError as exc:
    if exc.name not in {'numpy', 'scipy', 'sklearn', 'threadpoolctl'}:
        raise
    HAS_MODELS = False


@unittest.skipUnless(HAS_MODELS, 'Install model extra for interval tests')
class IntervalTests(unittest.TestCase):
    def rows(self):
        raw = []
        for start, hours in [(datetime(2016,12,30),48), (datetime(2017,1,1),48),
                             (datetime(2017,6,30),48), (datetime(2017,12,31),24)]:
            for h in range(hours):
                t=start+timedelta(hours=h)
                raw.append(dict(date_time=t, split='train' if t.year==2016 else 'validation',
                                traffic_volume=None if h==10 else 100+t.hour))
        return build_features(raw)

    def test_rank_uses_finite_sample_order_statistic_and_ties(self):
        self.assertEqual(residual_quantile(list(range(1,20))), dict(n=19,rank=18,radius=18))
        self.assertEqual(residual_quantile([4]*9), dict(n=9,rank=9,radius=4))
        for bad in ([], [1]*8, [1]*9+[float('nan')], [1]*9+[-1], [float('inf')]*9):
            with self.assertRaises(ValueError): residual_quantile(bad)

    def test_calibration_excludes_unavailable_hour_and_future_labels(self):
        rows=self.rows()
        before=calibrate(rows, [0]*len(rows))
        changed=[dict(r,traffic_volume=999999) if r['date_time']>=datetime(2017,6,30,23)
                 else r for r in rows]
        self.assertEqual(before,calibrate(changed,[0]*len(rows)))
        eligible=[r for r in rows if r['split']=='validation'
                  and r['date_time']<=datetime(2017,6,30,22) and r['traffic_volume'] is not None]
        self.assertEqual(before['n'],len(eligible))
        with self.assertRaises(ValueError): calibrate(rows,[0])

    def test_evaluation_labels_cannot_change_radii_or_predictions(self):
        rows=self.rows()
        before,targets,points,intervals=experiment(rows)
        changed=[dict(r,traffic_volume=r['traffic_volume']+10000)
                 if r['date_time']>=datetime(2017,7,1) and r['traffic_volume'] is not None
                 else r for r in rows]
        after,_,points2,intervals2=experiment(changed)
        self.assertEqual(before['calibration'],after['calibration'])
        self.assertEqual(points,points2)
        self.assertEqual(intervals,intervals2)
        self.assertNotEqual(before['evaluation'],after['evaluation'])
        self.assertTrue(all(r['date_time']>=datetime(2017,7,1) for r in targets))
        self.assertEqual(before['evaluation']['intervals'][TREE]['n'],len(targets))
        self.assertEqual(before['evaluation']['intervals'][BASELINE]['n'],len(targets))

    def test_clipping_endpoints_and_interval_score_arithmetic(self):
        self.assertEqual(bounds([0,3,10],5),[(0,5),(0,8),(5,15)])
        result=interval_metrics([0,5,8,1],[(0,5),(0,5),(2,6),(2,6)])
        self.assertEqual(result['covered'],2)
        self.assertEqual(result['coverage'],.5)
        self.assertEqual((result['below_lower'],result['above_upper']),(1,1))
        self.assertEqual(result['mean_width'],4.5)
        self.assertEqual(result['mean_interval_score'],19.5)

    def test_empty_bins_and_invalid_inputs(self):
        self.assertIsNone(interval_metrics([],[]))
        for actual,intervals in [([1],[]),([1],[(2,1)]),([-1],[(0,1)]),([1],[(0,float('inf'))])]:
            with self.assertRaises(ValueError): interval_metrics(actual,intervals)
        for preds,radius in [([1],-1),([-1],1),([float('nan')],1)]:
            with self.assertRaises(ValueError): bounds(preds,radius)
        with self.assertRaises(ValueError): summarize(self.rows(),{TREE:[]},{TREE:[]})

    def test_all_diagnostic_bins_reconcile_without_dropping_missing_inputs(self):
        report,rows,points,intervals=experiment(self.rows())
        d=report['diagnostics']
        for dim in ('month','season','hour','day_type','inputs'):
            self.assertEqual(sum(x['n'] for x in d[dim].values()),len(rows))
        self.assertIsNone(d['month']['8']['intervals'][TREE])
        self.assertGreater(d['inputs']['incomplete']['n'],0)

    def test_final_holdout_and_duplicate_rows_are_rejected(self):
        rows=self.rows()
        for bad in (rows+[rows[0]], rows+[dict(rows[-1],split='test',date_time=datetime(2018,1,1))]):
            with self.assertRaises(ValueError): experiment(bad)


if __name__ == '__main__':
    unittest.main()
