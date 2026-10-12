import unittest
from datetime import datetime, timedelta

from trafficpulse.baselines import analyze, score_chart_svg


class BaselineTests(unittest.TestCase):
    def test_training_statistics_and_scores_exclude_other_partitions(self):
        start = datetime(2016, 12, 25)
        rows = []
        for hour in range(24 * 15):
            stamp = start + timedelta(hours=hour)
            split = "train" if stamp < datetime(2017, 1, 1) else "validation"
            rows.append({"date_time": stamp, "traffic_volume": 100 + stamp.hour,
                         "split": split})
        result = analyze(rows)
        self.assertEqual(result["training"]["observed_hours"], 24 * 7)
        self.assertEqual(result["training"]["traffic_volume_distribution"]["min"], 100)
        self.assertEqual(result["training"]["traffic_volume_distribution"]["max"], 123)
        self.assertIs(result["methodology"]["final_test_read"], False)
        self.assertEqual(result["validation"]["shared_cohort_n"], 24 * 8)
        self.assertEqual(set(result["validation"]["baselines"]), {
            "training_global_mean", "training_hour_of_week_mean", "same_hour_last_week"
        })
        self.assertEqual(result["validation"]["baselines"]["same_hour_last_week"]["mae_vehicles_per_hour"], 0)

    def test_final_test_partition_is_rejected(self):
        train = [{"date_time": datetime(2016, 12, 31), "traffic_volume": 10, "split": "train"}]
        test = [{"date_time": datetime(2018, 1, 1), "traffic_volume": 999_999, "split": "test"}]
        with self.assertRaisesRegex(ValueError, "final test is excluded"):
            analyze(train + test)

    def test_unavailable_last_training_label_cannot_change_first_forecast(self):
        start = datetime(2016, 12, 25)
        rows = [dict(date_time=start + timedelta(hours=hour), traffic_volume=100,
                     split="train") for hour in range(168)]
        rows.append(dict(date_time=datetime(2017, 1, 1), traffic_volume=100,
                         split="validation"))
        before = analyze(rows)
        rows[-2]["traffic_volume"] = 999_999  # t-1: unavailable at first forecast
        after = analyze(rows)
        self.assertEqual(before["validation"]["baselines"], after["validation"]["baselines"])
        self.assertEqual(after["fit"]["observed_hours"], 167)
        self.assertEqual(after["fit"]["latest_source_time"], "2016-12-31 22:00:00")
        self.assertEqual(after["training"]["observed_hours"], 168)
        rows[-3]["traffic_volume"] = 200  # t-2: available, must be included
        at_cutoff = analyze(rows)
        self.assertGreater(at_cutoff["fit"]["global_mean_vehicles_per_hour"], 100)

    def test_missing_seasonal_history_is_not_filled(self):
        start = datetime(2016, 12, 25)
        rows = []
        for hour in range(24 * 15):
            stamp = start + timedelta(hours=hour)
            value = None if stamp == datetime(2016, 12, 26) else 100 + stamp.hour
            split = "train" if stamp < datetime(2017, 1, 1) else "validation"
            rows.append({"date_time": stamp, "traffic_volume": value, "split": split})
        result = analyze(rows)
        self.assertLess(result["validation"]["seasonal_lag_eligible_targets"],
                        result["validation"]["observed_targets"])
        self.assertEqual(result["validation"]["baselines"]["same_hour_last_week"]["n"],
                         result["validation"]["shared_cohort_n"])

    def test_forbidden_future_training_row_fails(self):
        rows = [{"date_time": datetime(2017, 1, 1), "traffic_volume": 10, "split": "train"}]
        with self.assertRaises(ValueError):
            analyze(rows)

    def test_chart_declares_common_cohort_and_units(self):
        result = {
            "validation": {
                "shared_cohort_n": 4,
                "baselines": {
                    "training_global_mean": {"mae_vehicles_per_hour": 200},
                    "training_hour_of_week_mean": {"mae_vehicles_per_hour": 150},
                    "same_hour_last_week": {"mae_vehicles_per_hour": 100},
                },
            },
        }
        svg = score_chart_svg(result)
        self.assertIn("same 4 eligible validation hours", svg)
        self.assertIn("MAE (vehicles/hour)", svg)


if __name__ == "__main__":
    unittest.main()
