import unittest
from trafficpulse.data import audit


def row(stamp='2017-01-01 00:00:00', volume='100', **overrides):
    item = dict(holiday='None', temp='280', rain_1h='0', snow_1h='0',
                clouds_all='0', weather_main='Clear', weather_description='sky is clear',
                date_time=stamp, traffic_volume=volume)
    item.update(overrides)
    return item


class AuditTests(unittest.TestCase):
    def test_missing_hour_is_not_missing_cell(self):
        result = audit([row(), row('2017-01-01 02:00:00')])
        self.assertEqual(result['missing_hourly_slots'], 1)
        self.assertEqual(sum(result['blank_cells_by_column'].values()), 0)

    def test_weather_rows_are_not_additional_traffic(self):
        result = audit([row(), row(weather_main='Clouds')])
        self.assertEqual(result['unique_timestamps'], 1)
        self.assertEqual(result['extra_rows_beyond_one_per_timestamp'], 1)
        self.assertEqual(result['timestamps_with_conflicting_traffic'], 0)
        self.assertEqual(result['exact_duplicate_rows'], 0)

    def test_conflicting_targets_are_reported(self):
        self.assertEqual(audit([row(), row(volume='200')])['timestamps_with_conflicting_traffic'], 1)

    def test_exact_duplicates(self):
        self.assertEqual(audit([row(), row()])['exact_duplicate_rows'], 1)

    def test_holiday_none_is_a_category(self):
        self.assertEqual(audit([row()])['blank_cells_by_column']['holiday'], 0)

    def test_impossible_ranges(self):
        flags = audit([row(volume='-1', temp='0', clouds_all='101', rain_1h='-1')])['range_flags']
        self.assertEqual(flags['negative_traffic_rows'], 1)
        self.assertEqual(flags['nonpositive_kelvin_rows'], 1)
        self.assertEqual(flags['clouds_outside_0_100_rows'], 1)
        self.assertEqual(flags['negative_rain_rows'], 1)

    def test_empty_input_is_rejected(self):
        with self.assertRaises(ValueError):
            audit([])

    def test_non_hour_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            audit([row('2017-01-01 00:30:00')])


if __name__ == '__main__':
    unittest.main()
