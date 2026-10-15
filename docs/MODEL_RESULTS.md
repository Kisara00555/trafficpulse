# Part 5 - First learned models

Completed 15 October 2026. The provisional champion is histogram gradient boosting with 31 leaves, selected on 2016 tuning MAE before inspecting 2017 outcomes. On all 8,713 observed 2017 targets it scored MAE 190.2 vehicles/hour versus 278.7 for the weekday/hour baseline. Ridge scored 381.1 and did not beat that simple baseline. This supports further temporal testing, not a deployment or final-holdout performance claim.

## Fixed experiment

The [plan](MODELING_PLAN.md) was saved before comparisons. The inner fit uses 20,966 available labels through 2016-06-30 22:00; tuning uses 4,361 observed targets from 2016-07-01 through 2016-12-31 22:00. Final fitting uses 25,328 labels through 2016-12-31 22:00. Imputation and scaling are fitted only within the relevant training window. No random split or automatic early stopping is used. The [feature contract](FEATURE_CONTRACT.md) is unchanged.

All five declared model configurations were evaluated once on the tuning window; no candidates were added after seeing the scores. The 15- and 31-leaf trees were close in tuning MAE (253.5 versus 253.3); the small difference is not evidence of statistically reliable superiority. The declared lowest-MAE rule selected 31 leaves. Part 6 will test stability across time.

## Tuning evidence (2016 only)

| Method | Hours | MAE (vehicles/hour) | RMSE (vehicles/hour) | Mean error (prediction - actual) |
|---|---:|---:|---:|---:|
| Global training mean | 4,361 | 1,637.9 | 1,873.3 | 206.2 |
| Weekday/hour training mean | 4,361 | 355.4 | 606.4 | 219.5 |
| Same hour last week + fallback | 4,361 | 380.5 | 706.4 | 19.8 |
| Ridge (alpha 1) | 4,361 | 431.5 | 620.5 | 26.3 |
| ridge_alpha_10 | 4,361 | 431.6 | 620.6 | 26.3 |
| ridge_alpha_100 | 4,361 | 431.8 | 620.9 | 26.3 |
| hist_leaves_15 | 4,361 | 253.5 | 388.1 | 50.1 |
| Histogram boosting (31 leaves) | 4,361 | 253.3 | 387.3 | 49.4 |

## Primary validation comparison (2017)

Every method predicts the same 8,713 observed targets. The 47 hours with no observed target cannot be scored. Both learned models handle missing historical inputs; no observed target is dropped for incomplete features. The seasonal baseline uses its fitted weekday/hour mean on 46 targets without a weekly lag (global mean if that group is absent). Negative learned-model predictions are clipped to zero by the predeclared rule.

| Method | Hours | MAE (vehicles/hour) | RMSE (vehicles/hour) | Mean error (prediction - actual) |
|---|---:|---:|---:|---:|
| Global training mean | 8,713 | 1,744.5 | 1,986.3 | -124.0 |
| Weekday/hour training mean | 8,713 | 278.7 | 461.0 | -105.8 |
| Same hour last week + fallback | 8,713 | 302.0 | 563.1 | 2.8 |
| Ridge (alpha 1) | 8,713 | 381.1 | 556.8 | -13.8 |
| Histogram boosting (31 leaves) | 8,713 | 190.2 | 298.8 | -24.6 |

## Match the earlier baseline population

On the same 8,667 hours used in Part 3, all three baseline metrics exactly reproduce that part. These subset scores must not be mixed with the primary all-target scores.

| Method | Hours | MAE (vehicles/hour) | RMSE (vehicles/hour) | Mean error (prediction - actual) |
|---|---:|---:|---:|---:|
| Global training mean | 8,667 | 1,742.8 | 1,985.1 | -124.4 |
| Weekday/hour training mean | 8,667 | 279.1 | 461.7 | -106.1 |
| Same hour last week + fallback | 8,667 | 302.6 | 564.2 | 3.1 |
| Ridge (alpha 1) | 8,667 | 378.1 | 552.8 | -14.5 |
| Histogram boosting (31 leaves) | 8,667 | 190.3 | 299.0 | -24.8 |

## Missing-input diagnostic

The following 565 targets have at least one missing predictor. The tree model's MAE is 211.3 here, compared with 190.2 overall. This subgroup is reported to expose a limitation, not to tune the selected model.

| Method | Hours | MAE (vehicles/hour) | RMSE (vehicles/hour) | Mean error (prediction - actual) |
|---|---:|---:|---:|---:|
| Global training mean | 565 | 1,829.3 | 2,066.2 | -165.7 |
| Weekday/hour training mean | 565 | 271.3 | 499.4 | -62.3 |
| Same hour last week + fallback | 565 | 364.6 | 727.8 | 19.5 |
| Ridge (alpha 1) | 565 | 454.7 | 655.2 | 24.4 |
| Histogram boosting (31 leaves) | 565 | 211.3 | 341.3 | -9.2 |

## Reproduce and checks

Use Python 3.12. From the repository root, after data preparation:

```sh
python -m pip install -e ".[model]"
python -m trafficpulse.models
python -m unittest discover -s tests -v
```

The model extra pins scikit-learn 1.7.2, NumPy 2.2.6, SciPy 1.15.3, joblib 1.5.2 and threadpoolctl 3.6.0. The source/feature steps still use the standard library. Without the extra, model unit tests explicitly skip; CI installs it so they must run. The [JSON evidence](../reports/part05_models.json) records input hashes, protocol hash, version information, selection and results. The ignored local prediction CSV supports independent recalculation; no serialized model binary or raw downloads are committed.

All 36 tests passed with no skips. A repeated full experiment produced identical report and prediction fingerprints in the recorded environment. Separate arithmetic on the saved predictions reproduced every primary MAE/RMSE result, and the shared-cohort baselines exactly matched Part 3. Tests check unavailable training labels, preprocessing isolation, missing inputs, feature allowlists and that changed validation labels cannot choose a different model. Cross-platform floating-point results may differ slightly; exact hashes describe the recorded environment.

## Interpretation and limits

Ready within the reviewed Part 5 scope, with caveats: a single inner tuning window and one historical station do not establish stability or real-world impact. Ridge uses the numeric calendar representation declared in Part 4; this is a bounded comparison, not a search over every possible linear encoding. The reporting delay is assumed and source-clock/DST ambiguity remains. No uncertainty intervals or operational savings are claimed. Validation has been inspected in this and earlier parts; it is not a pristine test set. The final 2018+ holdout remains sealed. Tomorrow's work is temporal backtesting and error analysis.

Source: Hogue (2019), [Metro Interstate Traffic Volume](https://doi.org/10.24432/C5X60B), UCI, CC BY 4.0. See the [data card](DATA_CARD.md). Library-method references are linked in the predeclared modeling plan.
