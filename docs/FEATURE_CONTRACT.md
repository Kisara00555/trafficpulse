# Feature contract - Part 4

Version 1.0, completed 14 October 2026. This feature set is specified before fitting the Part 5 models. No model scores or final holdout outcomes were used to choose it.

## What is available at forecast time?

We predict the count for hour t at the start of t. Under the project's reporting assumption, an observed count must have a source timestamp no later than t-2 hours. These are naive source-clock timestamps; timezone and daylight-saving ambiguity remain unresolved.

| Inputs | Definition | Why available |
|---|---|---|
| hour, weekday, month, is_weekend | Target-hour calendar; Monday=0, Sunday=6 | Known in advance |
| hour_sin, hour_cos | sin/cos of 2*pi*hour/24 | Fixed calendar formula; midnight is adjacent to 23:00 |
| weekday_sin, weekday_cos | sin/cos of 2*pi*weekday/7 | Fixed calendar formula; Sunday is adjacent to Monday |
| lag_2h, lag_3h | Counts exactly 2 and 3 hours before t | Short-term history satisfying the delay |
| lag_24h, lag_48h, lag_168h | Counts exactly 1 day, 2 days and 1 week before t | Daily/weekly history |
| rolling_mean_24h | Mean of all 24 hourly counts from t-25 through t-2 inclusive | Entire window precedes the cutoff |
| rolling_count_24h | Number of observed counts in that window, 0 to 24 | Describes historical input coverage only |

The five lags, eight calendar values and two rolling values form the explicit 15-column allowlist `FEATURE_COLUMNS`. `traffic_volume` is the label, not a predictor. `date_time` and `split` are metadata. Current-hour quality flags, source-row counts, actual weather and raw holiday labels are excluded. The rolling count is allowed because it describes only past observations, unlike a current-target availability flag.

## Missing hours and evaluation

Look up actual timestamps, never row positions. Keep missing lags blank. A measured zero remains zero. The rolling mean is blank unless all 24 source hours are observed; its count remains available. There is no interpolation, backward fill, imputation, scaling or learned encoding in this part. Do not silently discard difficult validation hours or compare models on different populations.

Part 5 must specify a missing-input strategy and fallback using training data and validation only. Any learned preprocessing must fit within each training fold with the same label-availability cutoff as the model. Use only `FEATURE_COLUMNS` as predictors. Feature CSVs intentionally retain rows with missing labels; those are never supervised training examples or scored targets.

The model-fit helper `training_rows_available(rows, issue_time)` selects only observed training labels at or before issue_time-2. At the first validation issue time (2017-01-01 00:00), 25,328 training labels are available, of which 13,328 have every feature. The full training partition has 25,329 observed targets, of which 13,329 have all features. Validation has 8,713 observed targets and 8,148 complete-feature targets (93.5%). These are coverage counts, not accuracy results. The strict rolling requirement reduces coverage substantially in older training data; model handling must make that tradeoff visible.

Earlier validation observations may be used as lag inputs once they reach the reporting cutoff, as a rolling forecast would do. They are never used by the training-label selection helper. At each forecast, changing t-1, t or future counts must not change its feature vector.

## Reproduce and verify

After Parts 1 and 2, set `PYTHONPATH=src` and run:

```sh
python -m trafficpulse.features
python -m unittest discover -s tests -v
```

The loader verifies the fixed training and validation CSVs against Part 2 SHA-256 fingerprints before use. It does not load `test.csv` or `hourly.csv`; the final holdout stays sealed. Outputs are ignored local `data/processed/train_features.csv` and `validation_features.csv`; the committed [report](../reports/part04_features.json) records input/output fingerprints, missingness, coverage and the fit cutoff. Synthetic tests cover future-value changes, exact lags across gaps, real zero counts, window endpoints, partition boundaries, label delay, duplicate timestamps and changed input fingerprints.

Source: Hogue (2019), Metro Interstate Traffic Volume, UCI Machine Learning Repository, [DOI 10.24432/C5X60B](https://doi.org/10.24432/C5X60B), CC BY 4.0. See [the data card](DATA_CARD.md) and [forecasting contract](PROJECT_BRIEF.md). This is one historical station and no live operational benefit is established.
