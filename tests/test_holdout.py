from datetime import datetime, timedelta
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

try:
    from trafficpulse.holdout import (REPORT, assess, experiment, holdout_features,
                                     load_freeze, prediction_bytes, run, validate_holdout)
    from trafficpulse.features import FEATURE_COLUMNS, build_features
    from trafficpulse.intervals import TREE, BASELINE
    HAS_MODELS = True
except ModuleNotFoundError as exc:
    if exc.name not in {'numpy', 'scipy', 'sklearn', 'threadpoolctl'}: raise
    HAS_MODELS = False


@unittest.skipUnless(HAS_MODELS, 'Install model extra for holdout tests')
class HoldoutTests(unittest.TestCase):
    def fixture(self):
        development=[]
        for start, hours, split in [(datetime(2016,12,30),48,'train'),
                                     (datetime(2017,12,24),192,'validation')]:
            development.extend(dict(date_time=start+timedelta(hours=h),split=split,traffic_volume=100+h%24)
                               for h in range(hours))
        test=[dict(date_time=datetime(2018,1,1)+timedelta(hours=h),split='test',
                   traffic_volume=None if h==10 else 120+h) for h in range(24)]
        freeze=dict(start='2018-01-01 00:00:00',end_exclusive='2018-01-02 00:00:00',
                    slots=24,observed=23,fit_n=47,fit_label_cutoff='2016-12-31 22:00:00',
                    radii={TREE:10,BASELINE:20})
        return development,test,freeze

    def test_current_too_recent_and_future_targets_do_not_change_features(self):
        dev,test,f=self.fixture()
        before=holdout_features(dev,test,f)
        changed=[dict(r,traffic_volume=99999) if r['date_time']>=datetime(2018,1,1,5)
                 and r['traffic_volume'] is not None else r for r in test]
        after=holdout_features(dev,changed,f)
        for i in range(7):
            self.assertEqual([before[i][c] for c in FEATURE_COLUMNS], [after[i][c] for c in FEATURE_COLUMNS])
        self.assertNotEqual(before[7]['lag_2h'],after[7]['lag_2h'])
        self.assertEqual(before[0]['lag_2h'],122)
        self.assertEqual(before[12]['lag_2h'],None)
        self.assertEqual(before[13]['lag_2h'],131)

    def test_final_labels_never_reach_fitting_and_first_predictions_unchanged(self):
        dev,test,f=self.fixture()
        before,rows,points,intervals=experiment(dev,test,f)
        changed=[dict(r,traffic_volume=r['traffic_volume']+10000) if r['traffic_volume'] is not None else r for r in test]
        after,_,changed_points,_=experiment(dev,changed,f)
        self.assertEqual(points[TREE][:2],changed_points[TREE][:2])
        self.assertEqual(points[BASELINE],changed_points[BASELINE])
        self.assertEqual(before['fit_n'],47)
        self.assertEqual(before['interval_radii'],after['interval_radii'])
        self.assertNotEqual(before['evaluation']['point_scores'],after['evaluation']['point_scores'])
        with self.assertRaises(ValueError): experiment(dev+test,test,f)
        # Existing development APIs continue rejecting the final partition.
        with self.assertRaises(ValueError): build_features(dev+test)

    def test_missing_targets_zero_and_all_slice_populations_reconcile(self):
        dev,test,f=self.fixture(); test[0]['traffic_volume']=0
        result,rows,points,intervals=experiment(dev,test,f)
        self.assertEqual(result['evaluation']['n'],23)
        self.assertEqual(result['evaluation']['predicted_slots'],24)
        self.assertEqual(result['evaluation']['missing_targets'],1)
        self.assertTrue(all(v['n']==23 for v in result['evaluation']['point_scores'].values()))
        for slices in result['diagnostics'].values():
            self.assertEqual(sum(s['n'] for s in slices.values()),23)
            self.assertEqual(sum(s['hourly_slots'] for s in slices.values()),24)
        self.assertIsNone(result['diagnostics']['month']['2']['intervals'][TREE])
        csv=prediction_bytes(rows,points,intervals).decode()
        self.assertIn('2018-01-01 00:00:00,0,2017-12-31 22:00:00',csv)
        self.assertIn('2018-01-01 10:00:00,,2018-01-01 08:00:00',csv)

    def test_grid_boundaries_duplicates_order_and_bad_targets_rejected(self):
        dev,test,f=self.fixture()
        for bad in [test[:-1],test[1:]+[test[-1]],list(reversed(test)),
                    [dict(test[0],split='validation')]+test[1:],
                    [dict(test[0],traffic_volume=-1)]+test[1:],
                    [dict(test[0],date_time=datetime(2018,1,1,0,1))]+test[1:]]:
            with self.assertRaises(ValueError): validate_holdout(bad,f)
        with self.assertRaises(ValueError): validate_holdout(test,dict(f,observed=24))

    def test_mismatched_prediction_arrays_fail(self):
        dev,test,f=self.fixture()
        with self.assertRaises(ValueError): assess(test,{TREE:[1]}, {TREE:[]})

    def test_existing_evidence_refuses_to_open_inputs(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/REPORT).parent.mkdir(); (root/REPORT).write_text('original')
            with patch('trafficpulse.holdout.load_freeze') as loader:
                with self.assertRaises(FileExistsError): run(root)
                loader.assert_not_called()
            self.assertEqual((root/REPORT).read_text(),'original')
            with self.assertRaises(ValueError): run(root,verify=True)

    def test_altered_freeze_record_rejected_before_data_reads(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'reports').mkdir()
            (root/'reports/part09_freeze.json').write_text('{"changed":true}\n')
            with patch('trafficpulse.holdout.subprocess.check_output',return_value=b'{"changed":false}\n'):
                with self.assertRaisesRegex(ValueError,'pre-holdout commit'): load_freeze(root)


if __name__ == '__main__': unittest.main()
