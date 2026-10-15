# Part 5 experiment specification

Recorded before running model comparisons on 15 October 2026.

- Features: Part 4's fixed 15-column allowlist; no weather or current-target audit metadata.
- Inner fitting issue time: 2016-07-01 00:00; training labels at or before 2016-06-30 22:00.
- Tuning targets: 2016-07-01 00:00 through 2016-12-31 22:00 inclusive. The final training hour is excluded because it is not yet available at the 2017-01-01 forecast issue time.
- Final fitting issue time: 2017-01-01 00:00; labels through 2016-12-31 22:00. Models are fixed throughout 2017; eligible earlier observations can enter lag features.
- Selection: lowest tuning MAE in vehicles/hour; deterministic declared candidate order breaks exact ties. Select one configuration per model family, then a provisional champion across those families and the baselines. Never select using 2017 scores.
- Ridge candidates: alpha 1, 10, 100. Median imputation with missing indicators and retained empty columns, then standard scaling, then Ridge; all fitted only on the eligible fitting rows. All 15 features are numeric as declared in Part 4; no learned calendar encoding. Clip negative predictions to zero for both learned model families.
- Tree candidates: histogram gradient boosting with 15 or 31 leaves, learning rate 0.05, 200 iterations, minimum leaf size 20, L2 penalty 1, random_state 42, squared-error loss. Native missing-value handling. Disable early stopping to avoid an implicit random validation split. Use one numerical-library thread for reproducibility and bounded resource use.
- Baselines: training global mean, training weekday/hour mean (global fallback for absent groups), same-hour-last-week (weekday/hour fallback when lag missing). Fit means on exactly the same eligible labels as each learned model.
- Primary 2017 population: every observed target, including incomplete feature rows. Secondary population: targets with an observed weekly lag, matching Part 3's shared cohort. Report missing-input subgroup scores, coverage, fallback counts, MAE, RMSE and mean signed error; do not tune from these diagnostics.
- No final test input. No operational impact claims. No prediction intervals yet. In later parts, freeze any interval calibration policy before checking its evaluation period; previously viewed validation scores must be disclosed and cannot be called a pristine holdout.
- This is one inner chronological tuning window. Part 6 will check stability across time before making a final deployment-style recommendation. The champion is provisional, not a final claim of generalization.

Reproduce with Python 3.12 and the pinned `model` extra in pyproject.toml. The report records versions and the SHA-256 of this specification. Local prediction CSVs are ignored; committed results contain aggregate evidence and file hashes.

Implementation references: [scikit-learn pipelines and leakage](https://scikit-learn.org/stable/common_pitfalls.html), [histogram boosting missing values and early stopping](https://scikit-learn.org/1.7/modules/generated/sklearn.ensemble.HistGradientBoostingRegressor.html).
