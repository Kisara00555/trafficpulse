# Part 8: decisions depend on the cost of being wrong

**Completed 21 October 2026. This is a hypothetical sensitivity study, not measured staffing savings or a traffic-control recommendation.** All four rules score the same 4,397 observed July-December 2017 development hours; 19 missing targets are excluded. The final holdout remains sealed.

A resource block is an invented unit of hourly capacity. We round either the point forecast or the upper prediction bound up to whole blocks. Shortfall and unused capacity receive explicit penalties. The [specification](DECISION_PLAN.md) fixes all nine scenarios, the formula and limitations; the [full report](../reports/part08_decisions.json) includes every result and input fingerprints.

## Reference illustration: 500 vehicle-equivalents per block-hour

The same allocations apply at every penalty ratio. Raising the shortfall penalty changes the score, not the chosen allocation.

| Policy | Mean blocks/hour | Hours with shortfall | Mean shortfall/hour | Mean unused capacity/hour |
|---|---:|---:|---:|---:|
| Tree point | 7.17 | 840 (19.1%) | 43.5 | 254.3 |
| Tree upper bound | 8.03 | 118 (2.7%) | 9.5 | 653.4 |
| Baseline point | 7.00 | 1,469 (33.4%) | 93.7 | 221.9 |
| Baseline upper bound | 8.21 | 124 (2.8%) | 9.2 | 738.9 |

Shortfall and unused capacity are vehicle-equivalents, not counts of missed incidents or customers. The tree upper-bound rule reduces shortfall from 840 hours to 118, while unused capacity rises from 254.3 to 653.4 per hour. It does not eliminate shortages. Greater allocation has a cost even when its forecast is well calibrated overall.

## All nine cost scenarios

Mean loss per scored hour, in arbitrary penalty units. Unused capacity has penalty 1; r is the shortfall penalty. Smaller is better **within the same row**. The values across rows use different assumptions and are not directly comparable operating savings.

| Block size | r | Tree point | Tree upper bound | Baseline point | Baseline upper bound |
|---|---:|---:|---:|---:|---:|
| 250 | 1 | 228.9 | 553.3 | 289.0 | 639.2 |
| 250 | 3 | 359.5 | 578.7 | 553.9 | 664.7 |
| 250 | 10 | 816.3 | 667.5 | 1,481.3 | 754.2 |
| 500 | 1 | 297.8 | 662.9 | 315.6 | 748.1 |
| 500 | 3 | 384.9 | 682.0 | 503.0 | 766.5 |
| 500 | 10 | 689.7 | 748.6 | 1,158.9 | 830.8 |
| 1000 | 1 | 512.7 | 901.0 | 478.3 | 985.8 |
| 1000 | 3 | 561.1 | 911.9 | 595.9 | 997.8 |
| 1000 | 10 | 730.5 | 950.2 | 1,007.6 | 1,039.7 |

Three conclusions matter:

- More conservative planning is not always cheaper. At block size 500 and r=3, tree point loss is 384.9 versus 682.0 for tree upper-bound planning.
- The answer depends on the assumptions. At block size 250 and r=10, tree upper-bound planning has lower loss (667.5) than tree point planning (816.3). We did not choose this scenario as an optimum or tune either rule.
- Better MAE does not guarantee better decisions after rounding and asymmetric penalties. At block size 1000 and r=1, baseline point loss (478.3) is below tree point loss (512.7), despite the tree's better predictive MAE. The tree point rule has lower loss than baseline point in the other eight specified scenarios. This is descriptive evidence, not a significance test.

## Limits and what comes next

These data have no real staff counts, capacity estimates, service rates, wages or operating outcomes. The invented mapping ignores shift constraints, queues, carryover and allocation limits. It cannot demonstrate reduced congestion, optimal staffing, causal impact, currency savings or deployment readiness. Source volume comes from one historical station; source-clock/DST ambiguity remains.

The reused development year is not an independent test. Part 7's intervals had weak coverage at some hours (76.6% at 22:00), and their upper bounds are neither a service guarantee nor cost-specific optimal quantiles. No model, interval radius, cost grid or decision rule was changed after these results. Part 9 must freeze its specification before opening holdout and report that result once without tuning on it.

## Reproduce and verify

After the documented data/model setup and Part 7, run `python -m trafficpulse.decisions`, then `python -m unittest discover -s tests -v`. The input prediction CSV stays ignored; its SHA-256 must match Part 7 before it can be scored. The report records the source report and decision-plan fingerprints too.

All 57 local tests passed, including eight decision tests for rounding, loss arithmetic, unavailable targets, fingerprints, population consistency and outcome-independent allocation. Independent Decimal arithmetic checked all 288 reported metric fields across all 36 policy/scenario combinations; a second run produced byte-identical JSON. These checks verify the implementation under its assumptions, not the realism of the assumptions.
