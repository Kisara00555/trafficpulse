# Part 7 - Prediction ranges and their limits

Completed 18 October 2026. The fixed tree model's nominal 90% prediction ranges covered **90.3%** of 4,397 observed July-December 2017 targets, with mean width **843.1 vehicles/hour**. The weekday/hour baseline covered 88.3% with wider ranges (1,180.8). Overall coverage hides important weaknesses: tree coverage was only **76.6% at 22:00** and **86.2% in December**. These are development results, not a formal guarantee or final-test result.

## Separate fitting, calibration and evaluation

The [specification](INTERVAL_PLAN.md) was saved before interval comparisons. Both point models remain fitted on the 25,328 training labels available through 2016-12-31 22:00; no calibration outcome refits the model. Their full-year point scores reproduce Part 5.

| Stage | Source-clock targets or labels | Observed count | Exclusions |
|---|---|---:|---|
| Model fitting | Training through 2016-12-31 22:00 | 25,328 | Later or missing labels |
| Radius calibration | 2017-01-01 00:00 through 2017-06-30 22:00 | 4,315 | 28 missing targets; 23:00 on 30 June excluded by reporting delay |
| Interval evaluation | 2017-07-01 00:00 through 2017-12-31 23:00 | 4,397 | 19 missing targets |

The last excluded June target may later enter lag features once it is genuinely available; it never sets the frozen calibration radius. All observed evaluation targets are scored, including 301 with incomplete inputs. The 2018+ holdout is never loaded.

2017 outcomes were previously inspected in other parts. This chronological separation prevents direct evaluation-label calibration, but does not turn reused development data into a pristine test. Time dependence and possible distribution changes also prevent claiming the usual exchangeability-based conformal guarantee.

## How the range is built

Each method gets its own radius from absolute calibration errors. With n=4,315, the one-based rank is ceil((n+1)*0.9)=3,885, without interpolation. The tree radius is 425.2333 vehicles/hour; the baseline radius is 604.5208. Every later range is [max(0, prediction-radius), prediction+radius]. Boundaries count as covered. Near zero, clipping makes the actual width smaller than twice the radius.

These are ranges for individual traffic counts, not confidence intervals for the model's mean accuracy. The same radius is used at every hour; it cannot adapt to changing conditions. No radius, window, model setting or subgroup adjustment was changed after observing evaluation coverage.

Method reference: Angelopoulos and Bates, [A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification](https://arxiv.org/abs/2107.07511). We use its residual order-statistic construction as a chronological diagnostic, with the limitations above.

## Overall comparison

All widths, point MAEs and interval scores use vehicles/hour. Coverage is the fraction of actual counts inside the range. Interval score adds range width to a 20-fold penalty for distance beyond a missed bound; lower is better. This discourages achieving coverage merely by making ranges very wide.

| Method | Hours | Covered | Coverage | Mean width | Point MAE | Interval score | Below / above range |
|---|---:|---:|---:|---:|---:|---:|---|
| Tree | 4,397 | 3,970 | 90.3% | 843.1 | 190.0 | 1,417.6 | 164 / 263 |
| Weekday/hour baseline | 4,397 | 3,881 | 88.3% | 1,180.8 | 294.5 | 2,319.5 | 162 / 354 |

The tree missed 427 observed targets. Achieving the nominal rate overall does not establish 90% coverage for a particular forecast, hour, season or missing-input condition. No significance claim is made for the comparison.

## Coverage breakdowns

The following tables use the same evaluation population. Different tables overlap; do not add their counts together. The complete evidence includes both models' widths, scores and point errors for every bin.

### Month

| Group | Hours | Tree coverage | Baseline coverage | Tree mean width |
|---|---:|---:|---:|---:|
| 7 | 738 | 91.7% | 91.7% | 845.6 |
| 8 | 743 | 93.7% | 91.7% | 843.9 |
| 9 | 716 | 90.4% | 86.0% | 842.8 |
| 10 | 744 | 89.9% | 88.6% | 842.3 |
| 11 | 716 | 89.8% | 89.2% | 842.2 |
| 12 | 740 | 86.2% | 82.3% | 841.9 |

### Season within July-December

| Group | Hours | Tree coverage | Baseline coverage | Tree mean width |
|---|---:|---:|---:|---:|
| JJA_partial | 1,481 | 92.7% | 91.7% | 844.8 |
| SON | 2,176 | 90.0% | 88.0% | 842.4 |
| DJF_partial | 740 | 86.2% | 82.3% | 841.9 |

### Day type

| Group | Hours | Tree coverage | Baseline coverage | Tree mean width |
|---|---:|---:|---:|---:|
| weekday | 3,107 | 90.8% | 88.8% | 841.7 |
| weekend | 1,290 | 89.1% | 86.9% | 846.7 |

### Input completeness

| Group | Hours | Tree coverage | Baseline coverage | Tree mean width |
|---|---:|---:|---:|---:|
| complete | 4,096 | 90.6% | 88.2% | 843.1 |
| incomplete | 301 | 86.7% | 89.7% | 843.2 |

### Issue hour

| Group | Hours | Tree coverage | Baseline coverage | Tree mean width |
|---|---:|---:|---:|---:|
| 0 | 184 | 94.6% | 96.7% | 850.5 |
| 1 | 184 | 100.0% | 100.0% | 830.0 |
| 2 | 179 | 100.0% | 100.0% | 774.1 |
| 3 | 184 | 100.0% | 100.0% | 784.6 |
| 4 | 183 | 98.9% | 100.0% | 835.8 |
| 5 | 183 | 92.9% | 96.2% | 850.5 |
| 6 | 183 | 86.3% | 85.8% | 850.5 |
| 7 | 183 | 80.3% | 77.6% | 850.5 |
| 8 | 183 | 87.4% | 70.5% | 850.5 |
| 9 | 184 | 88.6% | 75.0% | 850.5 |
| 10 | 182 | 90.7% | 85.7% | 850.5 |
| 11 | 183 | 92.9% | 88.5% | 850.5 |
| 12 | 183 | 92.3% | 88.5% | 850.5 |
| 13 | 184 | 95.7% | 89.7% | 850.5 |
| 14 | 184 | 92.9% | 89.7% | 850.5 |
| 15 | 182 | 92.3% | 88.5% | 850.5 |
| 16 | 183 | 82.5% | 77.0% | 850.5 |
| 17 | 183 | 83.1% | 78.7% | 850.5 |
| 18 | 184 | 88.0% | 87.0% | 850.5 |
| 19 | 184 | 92.4% | 90.2% | 850.5 |
| 20 | 184 | 94.0% | 93.5% | 850.5 |
| 21 | 184 | 84.8% | 87.0% | 850.5 |
| 22 | 184 | 76.6% | 86.4% | 850.5 |
| 23 | 183 | 79.8% | 86.3% | 850.5 |

JJA_partial means July-August only; DJF_partial is December only. SON is September-November. These are not comparisons of complete annual seasons.

At 22:00 the tree covered 76.6% of 184 targets; at 07:00 it covered 80.3% of 183. Incomplete-input hours achieved 86.7% (301 targets), versus 90.6% on complete inputs (4,096). The weakest month was December at 86.2%. These are observed associations, not explanations of the causes. The interval remains unchanged so these failures stay visible.

## Large misses still happen

| Target hour | Actual | Point forecast | Lower | Upper | Distance outside range |
|---|---:|---:|---:|---:|---:|
| 2017-12-05 07:00:00 | 2,334 | 6,055.9 | 5,630.6 | 6,481.1 | 3,296.6 |
| 2017-07-04 07:00:00 | 1,091 | 3,507.2 | 3,082.0 | 3,932.4 | 1,991.0 |
| 2017-07-03 06:00:00 | 3,353 | 5,552.0 | 5,126.8 | 5,977.2 | 1,773.8 |
| 2017-12-05 08:00:00 | 2,160 | 4,200.0 | 3,774.8 | 4,625.3 | 1,614.8 |
| 2017-07-26 23:00:00 | 3,420 | 1,439.8 | 1,014.5 | 1,865.0 | 1,555.0 |

These examples were selected by largest distance beyond a bound, not as a representative sample. No incident, holiday or weather cause is established. In particular, the 5 December morning forecast was far above the actual count even after allowing for the range. The fixed-origin forecasts here differ from Part 6's quarterly-refit examples by design.

## Reproduce and verification

Using the existing Python 3.12 environment with the pinned model extra, after data preparation and Part 5:

```sh
python -m trafficpulse.intervals
python -m unittest discover -s tests -v
```

The [JSON report](../reports/part07_intervals.json) contains the fixed specification, all subgroup metrics, calibration rank/radii, file hashes and library versions. The local prediction CSV is ignored at `data/processed/part07_interval_predictions.csv`.

All 49 tests passed with no skips. Tests cover rank arithmetic and ties, insufficient samples, unavailable calibration labels, changed evaluation labels, clipping, inclusive boundaries, independent interval-score arithmetic, empty bins, identical populations and final-holdout rejection. Independent arithmetic from the saved Part 5 forecasts reproduced both radii; separate calculations from Part 7 predictions matched coverage, widths and interval scores overall and for every month/hour. A repeated full experiment reproduced the same report and prediction hashes.

Ready within the reviewed Part 7 scope, with caveats: global ranges under-cover some subgroups; 2017 was previously inspected; source-clock/DST and reporting-latency assumptions remain; missing targets cannot be assessed. These results do not establish operational reliability or real savings. Before Part 9, freeze the final model/calibration policy without accessing final holdout outcomes. A refitted point model requires a compatible calibration protocol.

Next: the explicitly hypothetical decision-cost study in Part 8. Its assumptions must acknowledge weak subgroup coverage rather than treat a nominal 90% range as guaranteed protection.

Data: Hogue (2019), [Metro Interstate Traffic Volume](https://doi.org/10.24432/C5X60B), UCI, CC BY 4.0. See the [data card](DATA_CARD.md) and [feature contract](FEATURE_CONTRACT.md).
