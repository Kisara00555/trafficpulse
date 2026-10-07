import unittest
from datetime import datetime
from trafficpulse.prepare import build_hourly, partition, summarize


def row(stamp, value):
    return {'date_time': stamp, 'traffic_volume': str(value)}


class PreparationTests(unittest.TestCase):
    def test_repeated_hour_is_not_summed(self):
        data = build_hourly([row('2016-01-01 00:00:00', 20)] * 3)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['traffic_volume'], 20)
        self.assertEqual(data[0]['source_row_count'], 3)

    def test_missing_and_measured_zero_are_distinct(self):
        data = build_hourly([row('2016-01-01 00:00:00', 0), row('2016-01-01 02:00:00', 10)])
        self.assertEqual(data[0]['zero_volume_flag'], 1)
        self.assertEqual(data[0]['observed'], 1)
        self.assertIsNone(data[1]['traffic_volume'])
        self.assertEqual(data[1]['observed'], 0)
        self.assertEqual(data[1]['zero_volume_flag'], 0)

    def test_conflicts_fail_instead_of_averaging(self):
        with self.assertRaises(ValueError):
            build_hourly([row('2016-01-01 00:00:00', 10), row('2016-01-01 00:00:00', 30)])

    def test_split_boundaries(self):
        for stamp, expected in [('2016-12-31 23:00:00','train'), ('2017-01-01 00:00:00','validation'),
                                ('2017-12-31 23:00:00','validation'), ('2018-01-01 00:00:00','test')]:
            self.assertEqual(partition(datetime.fromisoformat(stamp)), expected)

    def test_reordered_input_is_deterministic(self):
        rows = [row('2016-01-01 02:00:00', 5), row('2016-01-01 00:00:00', 2)]
        self.assertEqual(build_hourly(rows), build_hourly(list(reversed(rows))))

    def test_leap_day_and_partition_reconciliation(self):
        data = build_hourly([row('2016-02-28 23:00:00', 10), row('2016-03-01 00:00:00', 20)])
        self.assertEqual(len(data), 26)
        counts = summarize(data)['train']
        self.assertEqual(counts['missing_hours'], 24)
        self.assertEqual(counts['observed_hours'], 2)

    def test_invalid_inputs(self):
        for rows in ([], [row('2016-01-01 00:01:00', 1)], [row('2016-01-01 00:00:00', -1)]):
            with self.assertRaises(ValueError):
                build_hourly(rows)


if __name__ == '__main__':
    unittest.main()
