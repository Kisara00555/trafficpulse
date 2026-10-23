# Part 9: frozen final evaluation specification

Frozen on 23 October 2026 before reading final holdout outcomes. Publish this plan and its machine-readable freeze record in a separate commit before the first holdout evaluation. Part 9 is one milestone including evaluation and a small historical replay demo; this freeze commit alone is not completion.

## Selected approach and information boundary

Retain the Part 5 histogram boosting model with 31 leaves, learning rate 0.05, 200 iterations, minimum leaf size 20, L2=1, squared-error loss, random state 42, early stopping disabled and one computation thread. Use the existing 15-feature allowlist and exact-timestamp feature builder. Fit only the 25,328 observed training labels through 2016-12-31 22:00 inclusive, exactly as Parts 5-8. Do not add the last unavailable 2016 label, refit using 2017, or refit during holdout. Part 6 found negligible annual benefit from quarterly refitting; keeping the tested fixed policy also preserves the existing interval calibration. This conservative choice tests a potentially stale model; it is not a claim that refitting never helps.

For every target hour t, issue the forecast at its start using calendar features for t and observed counts no later than t-2. Earlier holdout readings may enter later lag/rolling features only after that cutoff; holdout labels must never enter model fitting, calibration, selection or rule changes. No actual target-hour weather or sparse source holiday labels. Missing features remain missing for the tree's native handling; negative learned predictions clip to zero. Nonfinite predictions fail loudly rather than silently falling back.

## Comparators, population and metrics

Evaluate 2018-01-01 00:00 through 2018-09-30 23:00 in the source clock. Structural Part 2 evidence already records 6,552 hourly slots, 6,533 observed targets and 19 missing targets. Verify all input CSV fingerprints and boundaries before use. Predict every slot; score only observed targets, including those with incomplete inputs. Do not interpolate or zero-fill missing targets.

Compare the selected tree with three fixed baselines on the exact same observed timestamps: training global mean, training weekday/hour mean (global fallback for an unseen group), and exact same-hour-last-week count (weekday/hour then global fallback if unavailable). All fitted means use the same frozen training labels as the tree. Report MAE as primary, RMSE and signed mean error as secondary metrics, forecast/target coverage, incomplete-input count and weekly fallback count. Do not choose a new winner or tune against this final result even if a baseline wins.

Report monthly, hour-of-day, weekday/weekend, complete/incomplete-input slices with counts and the five largest absolute tree errors. These diagnostics are descriptive; they cannot be used to alter this final evaluation. No significance, causal-impact or cross-station claims. State that January-September does not cover a full year and that source-clock/DST interpretation remains unresolved.

## Uncertainty

Reuse the Part 7 radii unchanged: tree 425.23329949818344 and weekday/hour baseline 604.5208333333335 vehicles/hour. They were calibrated using 4,315 observed January-June 2017 targets through 2017-06-30 22:00, with nominal coverage 90% and order-statistic rank 3,885. Bounds remain [max(0, point-radius), point+radius]. No recalibration or widening after seeing holdout. Report empirical coverage, mean width, misses below/above and mean interval score overall and in the same slices. Time dependence and earlier development use mean there is no formal coverage guarantee.

## One final assessment, reproducible verification

Commit a freeze record containing this plan's normalized-LF hash, existing model/feature/interval implementation hashes, pinned package versions, feature columns, fitting boundary, radii, and the already-known input fingerprints. The evaluation runner checks that record against the separately committed freeze before it opens test.csv. Test the runner with synthetic data before the first real evaluation. Save the first real result and predictions without overwriting existing evidence. A later explicit verification run may recompute with identical frozen settings and compare results byte-for-byte; it must not overwrite, retune or constitute another selection trial. Any demonstrated implementation error must be disclosed and repaired with the original evidence preserved.

The small demo is an offline historical replay of the first 48 calendar hours of this fixed holdout window, chosen before results are inspected. Show target hour, available-data cutoff, point forecasts, uncertainty bounds and missing-input status. Hide actual outcomes until the viewer opts to reveal them; they are packaged locally, not secret from the viewer. This is a demonstration of saved forecasts, not live inference, a deployed service, or a system connected to current traffic. No staffing recommendations are added to the demo.

Source: Hogue, J. (2019), [Metro Interstate Traffic Volume, UCI](https://doi.org/10.24432/C5X60B), CC BY 4.0. See [the data card](DATA_CARD.md) and [interval limitations](INTERVAL_RESULTS.md).
