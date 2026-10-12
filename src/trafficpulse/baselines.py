"""Training-only descriptive statistics and validation baselines."""
from collections import defaultdict
import csv
from datetime import datetime, timedelta
import json
import math
from pathlib import Path
import statistics

from .data import ROOT

ISSUE_DELAY = timedelta(hours=2)
SEASONAL_LAG = timedelta(hours=168)
TRAINING_END = datetime(2017, 1, 1)
VALIDATION_END = datetime(2018, 1, 1)


def read_hourly(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        rows = []
        for row in csv.DictReader(handle):
            rows.append({
                "date_time": datetime.fromisoformat(row["date_time"]),
                "traffic_volume": int(row["traffic_volume"]) if row["traffic_volume"] else None,
                "split": row["split"],
            })
    return rows


def _distribution(values):
    ordered = sorted(values)
    if not ordered:
        raise ValueError("No observed training targets")

    def percentile(fraction):
        position = (len(ordered) - 1) * fraction
        lower = math.floor(position)
        upper = math.ceil(position)
        if lower == upper:
            return ordered[lower]
        return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)

    return {
        "count": len(ordered),
        "mean": statistics.fmean(ordered),
        "median": statistics.median(ordered),
        "standard_deviation": statistics.pstdev(ordered),
        "p10": percentile(0.10),
        "p90": percentile(0.90),
        "min": ordered[0],
        "max": ordered[-1],
    }


def _metrics(actual, predicted):
    errors = [prediction - observed for observed, prediction in zip(actual, predicted)]
    return {
        "n": len(errors),
        "mae_vehicles_per_hour": statistics.fmean(abs(error) for error in errors),
        "rmse_vehicles_per_hour": math.sqrt(statistics.fmean(error * error for error in errors)),
        "mean_error_vehicles_per_hour": statistics.fmean(errors),
    }


def analyze(hourly_rows):
    """Fit simple statistics on training only; compare on a shared 2017 cohort."""
    if any(row["split"] not in {"train", "validation"} for row in hourly_rows):
        raise ValueError("Part 3 accepts training and validation rows only; final test is excluded")
    train = [row for row in hourly_rows if row["split"] == "train"]
    validation = [row for row in hourly_rows if row["split"] == "validation"]
    if any(row["date_time"] >= TRAINING_END for row in train):
        raise ValueError("Training row crosses the frozen training boundary")
    if any(not TRAINING_END <= row["date_time"] < VALIDATION_END for row in validation):
        raise ValueError("Validation row crosses the frozen validation boundary")

    train_values = [row["traffic_volume"] for row in train if row["traffic_volume"] is not None]
    if not train_values:
        raise ValueError("Training partition has no observed targets")
    global_mean = statistics.fmean(train_values)
    hour_week_values = defaultdict(list)
    hour_day_values = defaultdict(list)
    for row in train:
        value = row["traffic_volume"]
        if value is not None:
            stamp = row["date_time"]
            hour_week_values[(stamp.weekday(), stamp.hour)].append(value)
            hour_day_values[stamp.hour].append(value)
    hour_week_means = {key: statistics.fmean(values) for key, values in hour_week_values.items()}

    # Fit once using only labels available at the first validation issue time.
    # The last training hour is t-1 there, so it is not yet available.
    fit_cutoff = TRAINING_END - ISSUE_DELAY
    fit_rows = [row for row in train
                if row["date_time"] <= fit_cutoff and row["traffic_volume"] is not None]
    if not fit_rows:
        raise ValueError("No training targets available at the first validation issue time")
    fit_mean = statistics.fmean(row["traffic_volume"] for row in fit_rows)
    fit_groups = defaultdict(list)
    for row in fit_rows:
        stamp = row["date_time"]
        fit_groups[(stamp.weekday(), stamp.hour)].append(row["traffic_volume"])
    fit_hour_week = {key: statistics.fmean(values) for key, values in fit_groups.items()}

    by_stamp = {row["date_time"]: row["traffic_volume"] for row in hourly_rows}
    eligible = []
    for row in validation:
        actual = row["traffic_volume"]
        if actual is None:
            continue
        stamp = row["date_time"]
        seasonal_stamp = stamp - SEASONAL_LAG
        # The forecast may use only records available by issue time (start of t).
        if seasonal_stamp > stamp - ISSUE_DELAY:
            raise ValueError("Seasonal feature violates the two-hour availability rule")
        seasonal_value = by_stamp.get(seasonal_stamp)
        if seasonal_value is not None:
            eligible.append((stamp, actual, seasonal_value))
    if not eligible:
        raise ValueError("No validation hours have an observed same-hour-last-week value")

    actual = [row[1] for row in eligible]
    global_predictions = [fit_mean] * len(eligible)
    hour_week_predictions = [
        fit_hour_week.get((stamp.weekday(), stamp.hour), fit_mean)
        for stamp, _, _ in eligible
    ]
    seasonal_predictions = [row[2] for row in eligible]

    all_validation_observed = sum(row["traffic_volume"] is not None for row in validation)
    hour_week_profile = [
        {"weekday": weekday, "hour": hour,
         "mean_vehicles_per_hour": hour_week_means.get((weekday, hour), global_mean),
         "training_observations": len(hour_week_values.get((weekday, hour), []))}
        for weekday in range(7) for hour in range(24)
    ]
    hourly_profile = [
        {"hour": hour, "mean_vehicles_per_hour": statistics.fmean(hour_day_values[hour]),
         "training_observations": len(hour_day_values[hour])}
        for hour in range(24)
    ]
    return {
        "methodology": {
            "training_end_exclusive": str(TRAINING_END),
            "validation_end_exclusive": str(VALIDATION_END),
            "forecast_issue_time": "start of target hour t",
            "latest_permitted_source_time": "t-2 hours",
            "fit_source_cutoff_inclusive": str(fit_cutoff),
            "fit_policy": "Fit once before validation; exclude labels unavailable at its first issue time. Descriptive training profiles use the whole training partition and are not forecast parameters.",
            "validation_only_for_scoring": True,
            "final_test_read": False,
            "comparison_population": "Observed 2017 validation targets whose exact t-168 hourly target is also observed; identical rows for every baseline.",
            "hour_week_fallback": "Training global mean if a weekday-hour group is absent.",
            "seasonal_fallback": "None; report shared-cohort eligibility explicitly.",
        },
        "training": {
            "hourly_slots": len(train),
            "observed_hours": len(train_values),
            "coverage": len(train_values) / len(train),
            "traffic_volume_distribution": _distribution(train_values),
            "global_mean_vehicles_per_hour": global_mean,
            "hour_of_week_groups": len(hour_week_means),
            "hourly_profile": hourly_profile,
            "hour_of_week_profile": hour_week_profile,
        },
        "fit": {
            "observed_hours": len(fit_rows),
            "latest_source_time": str(max(row["date_time"] for row in fit_rows)),
            "global_mean_vehicles_per_hour": fit_mean,
            "hour_of_week_groups": len(fit_hour_week),
        },
        "validation": {
            "hourly_slots": len(validation),
            "observed_targets": all_validation_observed,
            "seasonal_lag_eligible_targets": len(eligible),
            "seasonal_lag_coverage_of_observed_targets": len(eligible) / all_validation_observed,
            "shared_cohort_start": str(eligible[0][0]),
            "shared_cohort_end": str(eligible[-1][0]),
            "shared_cohort_n": len(eligible),
            "baselines": {
                "training_global_mean": _metrics(actual, global_predictions),
                "training_hour_of_week_mean": _metrics(actual, hour_week_predictions),
                "same_hour_last_week": _metrics(actual, seasonal_predictions),
            },
        },
    }


def score_chart_svg(result):
    """Return a portable, labeled SVG comparison for the notebook and report."""
    scores = result["validation"]["baselines"]
    labels = [
        ("Training global mean", scores["training_global_mean"]["mae_vehicles_per_hour"]),
        ("Training weekday + hour", scores["training_hour_of_week_mean"]["mae_vehicles_per_hour"]),
        ("Same hour last week", scores["same_hour_last_week"]["mae_vehicles_per_hour"]),
    ]
    maximum = max(value for _, value in labels) * 1.12
    width, height, left, right = 760, 300, 220, 28
    plot_width = width - left - right
    rows = []
    for index, (label, value) in enumerate(labels):
        y = 64 + index * 72
        bar_width = plot_width * value / maximum
        rows.append(
            f'<text x="{left - 12}" y="{y + 23}" text-anchor="end" class="label">{label}</text>'
            f'<rect x="{left}" y="{y}" width="{bar_width:.1f}" height="34" rx="3" fill="#245b86" />'
            f'<text x="{left + bar_width + 8:.1f}" y="{y + 23}" class="value">{value:,.0f}</text>'
        )
    axis_y = 64 + len(labels) * 72 - 16
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc" viewBox="0 0 {width} {height}">'
        '<title id="title">Validation MAE by baseline</title>'
        f'<desc id="desc">Mean absolute error in vehicles per hour for three baselines on the same {result["validation"]["shared_cohort_n"]:,} eligible validation hours.</desc>'
        '<style>text{font:15px Arial,sans-serif;fill:#182b3a}.label{font-size:14px}.value{font-size:15px;font-weight:700}.axis{stroke:#788997;stroke-width:1}.grid{stroke:#d9e1e7;stroke-width:1}</style>'
        '<text x="24" y="28" font-size="18" font-weight="700">2017 validation error (lower is better)</text>'
        + ''.join(rows)
        + f'<line x1="{left}" y1="{axis_y}" x2="{width-right}" y2="{axis_y}" class="axis"/>'
        + f'<text x="{left}" y="{axis_y+24}" text-anchor="middle" class="label">0</text>'
        + f'<text x="{width-right}" y="{axis_y+24}" text-anchor="end" class="label">{maximum:,.0f} MAE (vehicles/hour)</text>'
        + '</svg>'
    )


def hourly_profile_chart_svg(result):
    """Return a labeled training-only hourly traffic profile."""
    profile = result["training"]["hourly_profile"]
    values = [point["mean_vehicles_per_hour"] for point in profile]
    width, height = 760, 330
    left, right, top, bottom = 72, 28, 48, 56
    plot_width, plot_height = width-left-right, height-top-bottom
    maximum = max(values) * 1.12
    points = []
    for hour, value in enumerate(values):
        x = left + plot_width * hour / (len(values)-1)
        y = top + plot_height * (1-value/maximum)
        points.append((x, y))
    path = " ".join(("M" if i == 0 else "L") + f"{x:.1f},{y:.1f}" for i, (x,y) in enumerate(points))
    grid = []
    for fraction in (0, .25, .5, .75, 1):
        y = top + plot_height * fraction
        value = maximum * (1-fraction)
        grid.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" class="grid"/><text x="{left-9}" y="{y+5:.1f}" text-anchor="end" class="tick">{value:,.0f}</text>')
    ticks = []
    for hour in [*range(0,24,4), 23]:
        x = left + plot_width * hour / (len(values)-1)
        ticks.append(f'<text x="{x:.1f}" y="{height-24}" text-anchor="middle" class="tick">{hour:02d}:00</text>')
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.4" fill="#245b86"/>' for x,y in points)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc" viewBox="0 0 {width} {height}">'
        '<title id="title">Mean traffic volume by hour of day, training period only</title>'
        f'<desc id="desc">Average target count for the {result["training"]["observed_hours"]:,} observed training hours, grouped by source-clock hour.</desc>'
        '<style>text{font:14px Arial,sans-serif;fill:#182b3a}.tick{font-size:12px}.grid{stroke:#d9e1e7;stroke-width:1}.axis{stroke:#788997;stroke-width:1}</style>'
        '<text x="24" y="26" font-size="18" font-weight="700">Training traffic profile by hour of day</text>'
        + ''.join(grid)
        + f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" class="axis"/><line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" class="axis"/>'
        + f'<path d="{path}" fill="none" stroke="#245b86" stroke-width="2.5"/>{dots}'
        + ''.join(ticks)
        + f'<text transform="translate(18 {height/2}) rotate(-90)" text-anchor="middle">Mean traffic volume (vehicles/hour)</text>'
        + '</svg>'
    )


def run():
    # Deliberately load only these frozen partitions; never open test.csv here.
    rows = read_hourly(ROOT / "data/processed/train.csv")
    rows += read_hourly(ROOT / "data/processed/validation.csv")
    result = analyze(rows)
    (ROOT / "reports/part03_baselines.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    (ROOT / "reports/part03_baselines.svg").write_text(score_chart_svg(result) + "\n", encoding="utf-8")
    (ROOT / "reports/part03_training_hour_profile.svg").write_text(
        hourly_profile_chart_svg(result) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = run()
    print(json.dumps({"training": result["training"]["traffic_volume_distribution"],
                      "validation": result["validation"]}, indent=2))
