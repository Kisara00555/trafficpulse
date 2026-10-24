# Part 9: final holdout results

**Evaluated 23 October; demo review and milestone completion 24 October 2026.** The specification was [published before opening holdout](https://github.com/Kisara00555/trafficpulse/commit/d6101a1b824ec91d223d750a01fe3df65d90b782). No model setting, feature, fitting boundary or interval radius was changed after inspecting the outcomes.

## Final comparison

All methods predicted all 6,552 hourly slots from January through September 2018. Scores use the same 6,533 observed targets; 19 missing targets are excluded, never zero-filled. The model also predicts the 322 observed targets with incomplete inputs. The weekly baseline used its fixed weekday/hour fallback for 19 scored targets.

| Method | MAE (vehicles/hour) | RMSE (vehicles/hour) | Mean error (prediction minus actual) |
|---|---:|---:|---:|
| Global mean | 1,730.3 | 1,975.7 | -71.3 |
| Weekday/hour mean | 272.9 | 473.1 | -45.7 |
| Same hour last week, with fallback | 337.4 | 645.9 | -19.5 |
| Frozen tree model | 185.6 | 291.2 | -6.9 |

The tree's MAE is 32.0% lower than the weekday/hour baseline on this identical population: (272.8956 - 185.6059) / 272.8956. This is a relative reduction in average absolute error, **not 32% accuracy**, a significance result or a guaranteed future improvement. The tree was selected before the final comparison; this evaluation does not select a replacement model.

## Uncertainty and failure cases

| Method | Covered / observed | Empirical coverage | Mean width (vehicles/hour) | Mean interval score |
|---|---:|---:|---:|---:|
| Frozen tree model | 5,922 / 6,533 | 90.65% | 842.5 | 1,390.5 |
| Weekday/hour mean | 5,904 / 6,533 | 90.37% | 1,180.8 | 2,179.4 |

Both ranges have a nominal 90% target and reuse January-June 2017 calibration without adjustment. The tree had 293 outcomes below its lower bound and 318 above its upper bound. Coverage was only **78.4% at 22:00 (273 targets)**, **80.2% at 16:00 (273)** and **83.3% in April (720)**. Overall coverage does not imply dependable ranges in every subgroup. Time dependence prevents a general coverage guarantee.

The largest tree error was at 2018-07-04 07:00: predicted 4,166.9 versus observed 1,128 vehicles/hour, an absolute error of 3,038.9. The date alone does not establish the cause. No holiday feature, wider interval or model retuning was added after seeing this failure. All monthly/hour/day-type/input slices and the five largest errors are saved in [the full report](../reports/part09_holdout.json).

## What this evaluation means

The fixed model was fitted on 25,328 available labels through 2016-12-31 22:00. It uses the existing 15-feature set and no refitting. Later observations, including earlier holdout readings, may become lag inputs once they are at least two hours older than a forecast target. They never become training or calibration labels. This is sequential one-hour forecasting, not forecasting the entire nine-month period without new observations.

The holdout was unseen during model development and is now consumed. It cannot be reused as a new model-selection set while retaining an untouched-test claim. The documented read-only replay is a reproducibility check of the same fixed assessment, not another tuning trial. Further work must not tune against these outcomes.

Limits: one historical station; January-September rather than a full year; unresolved source-clock/DST interpretation; assumed reporting delay; a model fitted on older data; missing-input and temporal differences; no evidence of current deployment, cross-station performance, congestion reduction or real savings. Lower missing-input subgroup error does not prove missing data helps: the groups contain different hours.

## Try the demo

Open [demo/index.html](../demo/index.html) locally in a browser after cloning/downloading the repository. GitHub displays HTML source rather than running this page. It is self-contained and needs no external scripts or network requests to work. Alternatively, from the repository root run `python -m http.server 8765 --bind 127.0.0.1 --directory demo` and open `http://127.0.0.1:8765` locally. Stop the server with Ctrl+C.

The demo replays the first 48 calendar hours, selected in the frozen specification before results were inspected. Use the hour selector or Previous/Next, compare point forecasts and the tree range, then reveal the actual count. The observation cutoff stays visible. Actual outcomes are bundled in the page; hiding them is a learning aid. This is historical replay, not live inference or a deployed traffic service.

## Reproduce without changing the assessment

Use a full Git clone, Python 3.12 and `python -m pip install -e ".[model]"`. The runner needs the separate freeze commit in Git history. From the repository root:

```sh
python -m trafficpulse.data --download
python -m trafficpulse.prepare
python -m trafficpulse.restore_predictions
python -m trafficpulse.demo
python -m unittest discover -s tests -v
```

The committed final report stays in place. `restore_predictions` reconstructs the ignored prediction CSV only if its bytes match the report's saved fingerprint, then verifies the complete frozen assessment without overwriting the report. It refuses to replace an existing prediction file. Once both files exist, use `python -m trafficpulse.holdout --verify` for read-only reproduction. The original first-assessment command `python -m trafficpulse.holdout` intentionally refuses to run over saved evidence. All paths check the frozen specification, package versions, source implementations and CSV fingerprints; no retuning is performed. The large prediction CSV stays ignored; the 48-hour derived replay is the small intentional demonstration artifact.

Before the first holdout read, 64 tests passed, including seven new synthetic tests for information availability, fitting separation, population consistency, missing/zero targets, grid boundaries, modified freeze records and preservation of existing evidence. Independent CSV arithmetic matched 1,140 point/interval metric fields overall and across all declared slices. The subsequent fixed replay matched report and prediction bytes without replacing them. Browser checks and final publication checks are recorded in the [daily note](daily/2026-10-24.md).

Source: Hogue, J. (2019), [UCI Metro Interstate Traffic Volume](https://doi.org/10.24432/C5X60B), CC BY 4.0. See [the frozen plan](HOLDOUT_PLAN.md) and [freeze record](../reports/part09_freeze.json).
