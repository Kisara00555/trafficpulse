# Part 6 temporal backtest specification

Recorded on 17 October 2026 before running this part's comparisons. Part 5 already exposed aggregate 2017 validation outcomes; these backtests are development diagnostics, not an untouched test.

- Keep the 15-feature contract and two-hour reporting delay. Load only fingerprint-verified train/validation files; never open final holdout inputs.
- Freeze the Part 5 selections: Ridge alpha 1 and histogram boosting with 31 leaves, using the same preprocessing and other settings. Check the saved Part 5 selection before running. No new tuning or model selection in Part 6.
- Evaluate four consecutive, non-overlapping calendar quarters of 2017. At each origin (1 January, April, July and October at 00:00), fit on expanding history with observed labels at or before origin minus two hours, including eligible earlier validation observations. Keep that fitted model fixed throughout its quarter. Forecast features may incorporate observations available at each hourly issue time, never future observations.
- Compare all three existing baselines and both learned models on every observed target in each quarter, including incomplete feature rows. Keep missing targets unscored, genuine zeros intact and the existing seasonal-baseline fallback.
- Also reproduce the Part 5 fixed-origin policy (fit once on 1 January) and score it on the identical quarterly and pooled populations. Report both policies; do not adopt a refitting policy merely because its 2017 score wins. The fixed-origin tree remains the provisional reference pending the later specification freeze.
- Report each fold's time bounds, available fitting labels, observed/missing targets, fallback counts, incomplete inputs and MAE/RMSE/signed error. Pool individual hourly errors; never use an unweighted mean of fold metrics.
- For the quarterly refit policy, break errors down by calendar month, meteorological season (DJF/MAM/JJA/SON within 2017), issue hour, weekday/weekend and complete/incomplete inputs. These are overlapping descriptive views, not independent experiments or causal explanations. Report all bins, including empty bins as unscored.
- List the ten largest tree absolute errors with timestamps, actual/predicted values and input completeness. Do not infer weather, incident or holiday causes without evidence. Do not tune away observed failures.
- Validate origin boundaries, earlier-validation eligibility, unavailable-label isolation, exact-hour feature availability, identical scoring cohorts, pooled metric arithmetic and reproducibility. Keep local predictions ignored and commit aggregate results and a concise written interpretation.

No intervals, operational savings, deployment or final-test results are claimed here. Part 7 must freeze its interval policy before evaluating it, with a distinct calibration period and explicit disclosure that 2017 has been inspected. The 2018+ final holdout remains sealed until Part 9.
