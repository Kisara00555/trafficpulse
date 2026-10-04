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

Part 1 chooses the problem and preserves raw evidence. It does not deduplicate, impute, train, or score a model. We must resolve repeated weather records, missing-hour policy, DST/source-time ambiguity, zero-volume interpretation, temperature faults, and holiday encoding. Long gaps will stay missing. Suitability of the eventual staffing proxy must be evaluated, not assumed.
