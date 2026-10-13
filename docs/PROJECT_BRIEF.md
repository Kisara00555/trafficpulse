# Project brief and forecasting contract

## Intended decision

A hypothetical traffic-operations analyst needs an hourly demand forecast and uncertainty range. Later, compare simple staffing rules under assumed costs. This is decision-support research, not an operational traffic-control system.

## Forecasting contract, version 0.1

- Unit: one source-clock hour at Minnesota DoT ATR station 301, westbound I-94.
- Target: reported traffic count for hour t.
- Issue time: the start of hour t; one-hour horizon.
- Conservative availability assumption: only observations timestamped at or before t-2 are usable, allowing one extra hour for reporting. Real reporting latency is unknown. Test sensitivity later.
- Calendar features for t are knowable. Holiday features require a documented calendar, not simply copying a sparse raw label.
- Actual weather during t is not known at issue time. Exclude it from the production-style feature set. Archived weather forecasts are not currently available. Historical weather could be used only at permitted lags.
- No random row split. Repeated timestamps must belong to one partition.
- Split proposal, frozen before model exploration: training before 2017-01-01; validation during 2017; final holdout from 2018-01-01 through the last source timestamp. Part 2 will verify coverage and record any necessary revision before model work.
- Structural checks can inspect all partitions. Model selection, feature tuning, and outcome-distribution exploration must not use final holdout outcomes.
- Rolling evaluation may use genuinely earlier test-period observations once they satisfy the availability rule; no refitting on future outcomes. Document this distinction.

## Planned evaluation

1. Training-only hour-of-week average and same-hour-last-week baselines.
2. MAE in vehicles/hour as the primary error metric, RMSE as a large-error measure.
3. Report coverage and sample counts. Compare models on identical eligible timestamps; separately report performance and coverage on the full scored population with a documented fallback.
4. Calendar-based backtesting on contiguous validation windows. Never assume adjacent rows are adjacent hours.
5. Later quantile or calibrated intervals: empirical coverage, interval width, and breakdowns by season/time. Time dependence means nominal coverage is not guaranteed.
6. Simulated decision costs with explicit staffing capacity and under/over-cost assumptions. Sensitivity analysis, not real savings claims.
7. Evaluate the final selected approach on holdout once, after freezing the specification.

## Acceptance criteria by the final milestone

- Rebuild features and results from attributed, fingerprinted input.
- Test time boundaries and feature availability; no future observations in a forecast.
- Report baseline and selected model on the same population, including failures and uncertainty.
- Explain the main error patterns, limitations, and operational assumptions in ordinary language.
- Provide a small demo and a reproducible run path. Deployment is optional and cannot be claimed unless verified.

## Current decisions and open questions

Part 4 completed on 14 October 2026: 15 calendar, exact-timestamp lag and rolling-history predictors with no learned preprocessing. All observed inputs are at t-2 or older. Missing inputs are preserved; 8,148 of 8,713 observed validation targets have complete inputs. The final holdout remains sealed. See [FEATURE_CONTRACT.md](FEATURE_CONTRACT.md) for the allowlist, coverage and rules for Part 5 fitting.

The 12 October review corrected Part 3 fitting to stop at 2016-12-31 22:00 inclusive, respecting the two-hour delay at the first validation forecast. The fixed models use 25,328 observed training labels; descriptive profiles retain all 25,329. A regression test changes the unavailable last training label and confirms it cannot change the first forecast. Rounded scores below are unchanged. The delivery deadline is 26 October 2026; see the dated roadmap.

Part 2 implemented the proposed split boundaries without alteration on 7 October 2026. The cleaned output is target-only: one agreed count per source-clock hour, blanks for absent hours, and no interpolation. Weather/holiday fields remain raw and excluded pending later feature decisions. See `CLEANING_POLICY.md` for the frozen rules and structural coverage; timezone interpretation and zero-count meaning remain open.

Part 3, completed on 12 October 2026, summarizes observed training targets and compares three simple baselines on 8,667 common eligible hours in 2017 validation. The training weekday-hour mean achieved MAE 279.1 and RMSE 461.7 vehicles/hour; same-hour-last-week achieved 302.6 and 564.2; the training global mean achieved 1,742.8 and 1,985.1. The exact one-week lag was present for 99.5% of observed validation targets. The analysis loads only the training and validation partitions; the final holdout remains unused. See `reports/part03_baselines.json` and `notebooks/03_training_baselines.ipynb`. These scores are a baseline reference for one station/year, not operational performance.

Part 1 chooses the problem and preserves raw evidence. It does not deduplicate, impute, train, or score a model. We must resolve repeated weather records, missing-hour policy, DST/source-time ambiguity, zero-volume interpretation, temperature faults, and holiday encoding. Long gaps will stay missing. Suitability of the eventual staffing proxy must be evaluated, not assumed.
