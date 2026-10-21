import csv
import tempfile
from pathlib import Path
import unittest

from trafficpulse.decisions import FIELDS, MODELS, allocation, evaluate, fingerprint, load_predictions


class DecisionTests(unittest.TestCase):
    def test_exact_rounding_and_zero(self):
        self.assertEqual([allocation(x, 500) for x in [0, 499, 500, 501]], [0, 1, 1, 2])

    def test_asymmetric_cost_arithmetic_and_shortfall_denominator(self):
        result = evaluate([0, 450, 1200], [0, 400, 900], 500, 3)
        self.assertEqual(result['n'], 3)
        self.assertEqual(result['total_loss'], 650)
        self.assertEqual(result['mean_loss'], 650/3)
        self.assertEqual(result['shortfall_hours'], 1)
        self.assertEqual(result['shortfall_rate'], 1/3)
        self.assertEqual(result['mean_shortfall'], 200/3)
        self.assertEqual(result['mean_unused_capacity'], 50/3)
        self.assertEqual(result['mean_blocks'], 1)

    def test_actions_do_not_depend_on_outcome_or_cost(self):
        a=evaluate([0, 1, 2], [0, 600, 900], 500, 1)
        b=evaluate([10000, 9999, 9998], [0, 600, 900], 500, 10)
        self.assertEqual(a['mean_blocks'], b['mean_blocks'])
        self.assertNotEqual(a['mean_loss'], b['mean_loss'])

    def test_conservatism_reduces_shortfall_but_can_increase_loss(self):
        point=evaluate([500, 500], [500, 500], 500, 10)
        upper=evaluate([500, 500], [600, 600], 500, 10)
        self.assertGreater(upper['mean_loss'], point['mean_loss'])
        a=evaluate([750, 1100], [500, 800], 500, 3)
        b=evaluate([750, 1100], [900, 1200], 500, 3)
        self.assertLessEqual(b['mean_shortfall'], a['mean_shortfall'])
        self.assertGreaterEqual(b['mean_unused_capacity'], a['mean_unused_capacity'])

    def test_invalid_parameters_and_populations_fail(self):
        for args in [([], [], 500, 1), ([1], [], 500, 1), ([-1], [1], 500, 1),
                     ([float('nan')], [1], 500, 1), ([1], [-1], 500, 1),
                     ([1], [float('inf')], 500, 1), ([1], [1], 0, 1),
                     ([1], [1], float('nan'), 1), ([1], [1], 500, 0),
                     ([1], [1], 500, float('inf'))]:
            with self.subTest(args=args), self.assertRaises(ValueError): evaluate(*args)

    def sample(self, stamp='2017-07-01 00:00:00'):
        return [stamp, 0, 10, 0, 20, 20, 0, 40]

    def load(self, rows, fields=FIELDS, expected_n=None, bad_hash=False):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'predictions.csv'
            with path.open('w', newline='', encoding='utf-8') as handle:
                writer=csv.writer(handle)
                writer.writerow(fields)
                writer.writerows(rows)
            return load_predictions(path, 'wrong' if bad_hash else fingerprint(path),
                                    len(rows) if expected_n is None else expected_n)

    def test_same_hours_for_all_policies_zero_preserved(self):
        actual, predictions=self.load([self.sample(), self.sample('2017-07-01 02:00:00')])
        self.assertEqual(actual, [0, 0])
        self.assertEqual(len(predictions), 4)
        self.assertTrue(all(len(p)==len(actual) for p in predictions.values()))

    def test_holdout_calibration_nonhour_timezone_and_duplicates_rejected(self):
        for stamp in ['2018-01-01 00:00:00', '2017-06-30 23:00:00',
                      '2017-07-01 00:01:00', '2017-07-01 00:00:00+00:00']:
            with self.subTest(stamp=stamp), self.assertRaises(ValueError): self.load([self.sample(stamp)])
        for rows in [[self.sample(), self.sample()],
                     [self.sample('2017-07-02 00:00:00'), self.sample()]]:
            with self.assertRaises(ValueError): self.load(rows)

    def test_fingerprint_schema_count_and_interval_failures(self):
        for kwargs in [dict(bad_hash=True), dict(fields=FIELDS[:-1]), dict(expected_n=2)]:
            with self.assertRaises(ValueError): self.load([self.sample()], **kwargs)
        for index, value in [(1, ''), (1, -1), (2, 'nan'), (4, 5), (7, 'inf')]:
            row=self.sample(); row[index]=value
            with self.subTest(index=index, value=value), self.assertRaises(ValueError): self.load([row])
        with self.assertRaises(ValueError): self.load([])


if __name__ == '__main__':
    unittest.main()
