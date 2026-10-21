# Part 8: hypothetical capacity-planning specification

Specified on 21 October 2026 before calculating the decision comparisons. This is a toy staffing-demand proxy, not a claim about road capacity or how many staff a traffic station needs. No staffing observations, service rates, wages, queues, incidents or congestion outcomes exist in this dataset.

## Fixed inputs and actions

Reuse the fingerprinted Part 7 predictions on exactly the same 4,397 observed July-December 2017 hours; 19 missing targets remain excluded for all policies. The models, features, two-hour observation delay and interval radii stay unchanged. Read only the Part 7 prediction CSV and its report, never the final holdout. These are previously examined development outcomes, not a new independent evaluation.

For each model (fixed histogram boosting and weekday/hour baseline), compare two rules: allocate from its point forecast, or from its upper interval bound. A rule uses its forecast only, never the actual target. A hypothetical resource block covers B vehicle-equivalents per hour. Required blocks = ceil(forecast / B), planned capacity C = B * blocks. Zero forecast allocates zero blocks. There is no maximum staffing constraint, carryover, queue, or cross-hour scheduling model. These simplifications make this unsuitable as an operational staffing recommendation.

## Assumptions and sensitivity grid

Use all nine combinations of B in {250, 500, 1000} vehicle-equivalents per block-hour and shortfall penalty r in {1, 3, 10}. Unused capacity has unit penalty 1. The values are illustrative, not estimated or endorsed operating parameters. B=500 is a reference illustration, not a selected optimum. Do not tune a rule or choose a scenario using the resulting costs.

For actual count y, shortfall = max(y-C, 0), unused capacity = max(C-y, 0), and loss = r * shortfall + unused capacity. Both quantities are vehicle-equivalents within an hour; loss has arbitrary penalty units, not currency. This loss is not payroll or realized savings and has no additional per-block charge. Missing hours are unscored rather than treated as zero.

Report every scenario and all four policies: mean loss per scored hour, total loss, shortfall hours/rate, mean shortfall, mean unused capacity, and mean blocks. Compare model policies on identical timestamps. Show how a more conservative action changes both sides of the tradeoff, including cases where its loss rises. No statistical significance or optimized-policy claim is planned. The upper bound is not a staffing guarantee: Part 7 found weaker coverage in some hours, and it is not calibrated to any of these cost ratios.

## Validation and scope boundary

Test arithmetic, rounding, zero and exact boundaries, invalid inputs, identical populations, altered outcomes not changing allocations, malformed/duplicate/out-of-window inputs, and fingerprint failures. Independently recompute all scenario metrics from the input CSV without the production decision helpers; rerun and check identical output. Save input/report/plan fingerprints. Keep generated source-level predictions ignored. Part 9 will separately freeze the final forecast specification before opening holdout; Part 8 does not open it or change the provisional forecast.
