# Part 6 - Performance across time

Completed 17 October 2026. The tree beat all three baselines and Ridge in each of four 2017 quarters under both tested fitting policies. This supports its provisional status, but does not establish final-test or operational performance. The 2018+ holdout remains sealed.

## What was fixed before this comparison

The [backtest plan](BACKTEST_PLAN.md) fixes the Part 5 settings and four quarterly origins. Each expanding fit uses only labels through two hours before that origin, including eligible observations from earlier validation periods. Features still use exact timestamps and the same reporting delay. Models stay fixed within each quarter. The comparison also reproduces the original model fitted once on 1 January 2017.

2017 validation outcomes had already been inspected. These are development backtests, not four independent untouched tests. No parameters or features were selected from these results, and no refitting policy is adopted here.

## Fold coverage and availability

| Quarter | Fit labels | Latest fit label (source clock) | Scored hours | Missing targets | Incomplete inputs | Weekly fallback |
|---|---:|---|---:|---:|---:|---:|
| Q1 | 25,328 | 2016-12-31 22:00:00 | 2,141 | 19 | 181 | 19 |
| Q2 | 27,469 | 2017-03-31 22:00:00 | 2,175 | 9 | 83 | 9 |
| Q3 | 29,644 | 2017-06-30 22:00:00 | 2,197 | 11 | 144 | 10 |
| Q4 | 31,841 | 2017-09-30 22:00:00 | 2,200 | 8 | 157 | 8 |

The four half-open windows cover 1 January 2017 through 1 January 2018. All methods predict the same 8,713 observed targets; 47 missing targets are unscored. There are 565 incomplete-input targets and 46 weekly-lag fallbacks. No difficult observed targets are dropped.

## Error by quarter

MAE is in vehicles/hour; lower is better. Baselines below are refitted at the same quarterly origins as the tree.

| Quarter | Weekday/hour baseline | Weekly + fallback | Ridge | Quarterly tree | Fixed-origin tree |
|---|---:|---:|---:|---:|---:|
| Q1 | 281.1 | 307.4 | 381.5 | 206.4 | 206.4 |
| Q2 | 241.7 | 256.7 | 359.4 | 175.3 | 174.6 |
| Q3 | 263.9 | 287.2 | 361.6 | 177.5 | 179.9 |
| Q4 | 309.9 | 356.4 | 389.2 | 200.9 | 199.9 |

## Pooled comparison

Metrics pool individual hourly errors, rather than giving differently sized quarters equal weight. Signed error is prediction minus actual; negative means underprediction on average.

| Policy | Method | Hours | MAE | RMSE | Signed error |
|---|---|---:|---:|---:|---:|
| Fit once | Global mean | 8,713 | 1744.5 | 1986.3 | -124.0 |
| Fit once | Weekday/hour mean | 8,713 | 278.7 | 461.0 | -105.8 |
| Fit once | Same hour last week + fallback | 8,713 | 302.0 | 563.1 | 2.8 |
| Fit once | Ridge (alpha 1) | 8,713 | 381.1 | 556.8 | -13.8 |
| Fit once | Tree (31 leaves) | 8,713 | 190.2 | 298.8 | -24.6 |
| Quarterly refit | Global mean | 8,713 | 1743.5 | 1985.6 | -110.4 |
| Quarterly refit | Weekday/hour mean | 8,713 | 274.2 | 457.6 | -94.4 |
| Quarterly refit | Same hour last week + fallback | 8,713 | 302.0 | 563.1 | 2.8 |
| Quarterly refit | Ridge (alpha 1) | 8,713 | 372.9 | 549.8 | -12.0 |
| Quarterly refit | Tree (31 leaves) | 8,713 | 190.0 | 297.9 | -19.8 |

Quarterly refitting changes tree MAE from 190.16 to 189.98, only 0.18 vehicles/hour overall, and is slightly worse in Q2 and Q4. This is not evidence of a reliable advantage. The simpler fixed-origin tree remains the provisional reference; a final specification still needs to be frozen in Part 9.

## Where errors concentrate

The following diagnostics use quarterly-refit predictions. Each table partitions the same observed hours; different tables overlap and must not be added together. Winter means January, February and December within 2017, not one contiguous winter. These associations do not establish causes. Raw absolute errors can also differ with traffic scale.

### Calendar month

| Group | Hours | Tree MAE | Weekday/hour MAE |
|---|---:|---:|---:|
| 1 | 744 | 215.3 | 307.0 |
| 2 | 657 | 211.1 | 251.1 |
| 3 | 740 | 193.3 | 281.5 |
| 4 | 711 | 182.2 | 242.3 |
| 5 | 744 | 161.3 | 261.4 |
| 6 | 720 | 183.1 | 220.6 |
| 7 | 738 | 180.7 | 272.1 |
| 8 | 743 | 163.9 | 230.0 |
| 9 | 716 | 188.3 | 290.6 |
| 10 | 744 | 178.6 | 255.4 |
| 11 | 716 | 195.9 | 301.1 |
| 12 | 740 | 228.2 | 373.2 |

### Meteorological season

| Group | Hours | Tree MAE | Weekday/hour MAE |
|---|---:|---:|---:|
| DJF | 2,141 | 218.5 | 312.7 |
| MAM | 2,195 | 178.9 | 262.0 |
| JJA | 2,201 | 175.8 | 241.0 |
| SON | 2,176 | 187.5 | 282.0 |

### Day type

| Group | Hours | Tree MAE | Weekday/hour MAE |
|---|---:|---:|---:|
| weekday | 6,200 | 179.6 | 270.5 |
| weekend | 2,513 | 215.6 | 283.3 |

### Input completeness

| Group | Hours | Tree MAE | Weekday/hour MAE |
|---|---:|---:|---:|
| complete | 8,148 | 188.5 | 274.6 |
| incomplete | 565 | 211.1 | 268.5 |

Winter MAE was 218.5 versus 175.8 in summer. December was the highest-error month (228.2); May was the lowest (161.3). Weekend error was 215.6 versus 179.6 on weekdays. Incomplete-input hours had MAE 211.1 versus 188.5 for complete inputs. These differences describe this sample; they do not prove missingness or season caused the errors.

All 24 issue-hour bins are retained in the JSON evidence. The highest tree MAE was at 22:00 (347.7 over 364 hours), followed by 07:00 (302.3 over 362 hours); the lowest was 03:00 (45.6 over 363 hours). This variation is why an annual average alone is inadequate.

### Largest observed errors

The three largest absolute tree errors are shown below; the JSON retains ten. All times are the unresolved naive source clock. No incident, weather or holiday cause has been established.

| Target hour | Actual | Prediction | Signed error | Incomplete inputs |
|---|---:|---:|---:|---|
| 2017-12-05 07:00:00 | 2,334 | 6,126.8 | 3,792.8 | No |
| 2017-07-04 07:00:00 | 1,091 | 3,714.8 | 2,623.8 | Yes |
| 2017-03-01 07:00:00 | 3,683 | 6,089.6 | 2,406.6 | No |

The largest error is a 3,792.8-vehicle/hour overprediction despite complete inputs. Completeness therefore does not ensure a reliable forecast. The next milestone will evaluate uncertainty ranges, without claiming they will cover every extreme event.

## Reproduce and verification

After the existing data preparation and Part 5 run, using Python 3.12 with the pinned model extra:

```sh
python -m trafficpulse.backtest
python -m unittest discover -s tests -v
```

The [JSON evidence](../reports/part06_backtest.json) records all methods, folds, bins, input hashes, plan hash, prior-report hash and environment versions. The prediction CSV stays ignored at `data/processed/part06_backtest_predictions.csv`.

All 42 tests passed with no skips. The checks include raw future-value mutation at a later fitting origin, legitimate use of earlier validation labels, excluded holdout rows, unequal fold sizes, empty bins, zero targets and mismatched prediction arrays. Independent arithmetic from the saved predictions reproduced pooled MAE/RMSE/signed errors and quarterly MAE/RMSE for all ten policy/method combinations. A second full run reproduced the report and prediction hashes; the fixed-origin results reproduce Part 5. The first sandboxed test attempt hit temporary-directory permissions; the approved rerun completed successfully. A new test fixture was corrected to actually contain unequal fold sizes before the successful run.

Ready within the reviewed Part 6 scope, with caveats: one historical station, one validation year, previously inspected outcomes, unresolved source-clock/DST interpretation and assumed reporting delay. No statistical significance, current-traffic performance, interval coverage or real savings is claimed. Broader delay sensitivity and final acceptance checks remain to be reconciled before handoff.

Source: Hogue (2019), [Metro Interstate Traffic Volume](https://doi.org/10.24432/C5X60B), UCI, CC BY 4.0. See the [data card](DATA_CARD.md), [feature contract](FEATURE_CONTRACT.md) and [Part 5 model settings](MODELING_PLAN.md).
