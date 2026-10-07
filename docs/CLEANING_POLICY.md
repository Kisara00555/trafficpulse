# Part 2: hourly target table and frozen splits

Implemented 7 October 2026. Run `python -m trafficpulse.prepare` after downloading the source with Part 1. Generated CSVs stay local and are ignored by Git; committed manifests contain their hashes and structural counts.

## Grain and missingness

Each row represents one naive source-clock hour, from 2012-10-02 09:00 through 2018-09-30 23:00 inclusive. Raw rows sharing a timestamp must agree on traffic count; disagreement stops processing. Keep that count once, never sum or average it. Retain `source_row_count` as audit metadata, including exact duplicates, to trace multiplicity.

Insert absent hours with an empty target cell and `observed=0`. Preserve observed zero counts and flag them separately. No imputation or interpolation is performed. The meaning of zeros remains unresolved; they are not automatically treated as sensor faults. All timestamps stay in the source clock. CST versus daylight-saving interpretation remains unresolved, so these are source-clock coverage counts, not verified UTC durations.

## Scope of the cleaned table

This is a **target-only** table. Weather and holiday fields remain unaltered in the raw source and are not copied into model-ready data. This avoids arbitrary aggregation of multiple weather rows and preserves the ability to investigate temperature faults and holiday encoding later. Future weather features need historical lags or archived forecasts; actual weather during the predicted hour is unavailable at issue time.

`observed`, `source_row_count`, `zero_volume_flag`, and `split` are audit/partition metadata, **never predictive inputs**. They can reveal the target or observation process. Calendar features and permissible historical lags will be built separately in later parts.

## Frozen partitions

| Partition | Source-clock range | Observed / hourly slots | Missing |
|---|---|---:|---:|
| Training | Start through 2016-12-31 23:00 | 25,329 / 37,239 | 11,910 |
| Validation | 2017-01-01 00:00 through 2017-12-31 23:00 | 8,713 / 8,760 | 47 |
| Final test | 2018-01-01 00:00 through source end | 6,533 / 6,552 | 19 |

These boundaries retain the pre-modeling proposal. Structural completeness was checked across partitions; target distributions and model performance were not explored. Do not tune on final test outcomes. Missing targets are ineligible for scoring; report eligible sample counts. Future lag features must align by timestamp and respect the t-2 availability rule, including across partition boundaries.

Training coverage is 68.02%, versus 99.46% and 99.71% for validation and test. Missing history can limit representativeness and usable lag windows. This is a high-impact modeling limitation, not proof of why the readings are absent. Preserve gaps, report eligibility, and assess training-only temporal coverage in Part 3. No model has been trained.

## Evidence and validation

`reports/part02_manifest.json` records the source fingerprint, generated file hashes, boundaries and coverage. `notebooks/02_hourly_quality.ipynb` executes the pipeline and independently reconciles observed timestamps, hourly spacing, missing encoding, boundaries and hashes. Tests cover repeated and conflicting counts, zero versus missing, chronological boundaries, leap-day gaps, invalid inputs, and input order. A rerun must produce identical CSV fingerprints from the same source.
