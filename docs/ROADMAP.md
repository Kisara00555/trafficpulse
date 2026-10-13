# Guided project roadmap

Autonomous daily development was authorized on 6 October 2026. Complete at most one next unfinished part per Asia/Colombo calendar day at the existing 19:00 scheduled run, without requiring a learner reply. Each part gets a short daily note, a reproducible artifact, checks, and a meaningful commit. Resume incomplete parts before advancing; duplicate runs must not start additional parts on the same day. The optional exercises help the learner prepare for interviews but do not block the next day's work. Dates of completion depend on validation and access; never mark unfinished work complete to meet a daily target.

| Part | Deliverable | Main interview question | Status |
|---|---|---|---|
| 1 | Problem contract, source pipeline, structural audit | Why can data with no nulls still be incomplete? | Complete, 2026-10-04 |
| 2 | Clean hourly table, split manifests, quality notebook | What does one row represent? | Complete, 2026-10-07 |
| 3 | Training-only exploration and simple baselines | What must your model beat? | Complete, 2026-10-12 |
| 4 | Leakage-tested lag/calendar features | What information exists at prediction time? | Complete, 2026-10-14 |
| 5 | Regularized and tree-based models | Why this model and how was it tuned? | Next |
| 6 | Temporal backtesting and error analysis | Does it work across seasons? | Planned |
| 7 | Uncertainty and interval evaluation | How do you communicate unreliable forecasts? | Planned |
| 8 | Simulated operational decision study | How does predictive accuracy affect a decision? | Planned |
| 9 | Final holdout evaluation and small demo | What happens on unseen data? | Planned |
| 10 | GitHub presentation, resume evidence, mock interview | What did you personally decide and learn? | Planned |

## Delivery timeline agreed 12 October 2026

Deadline: **26 October 2026, Asia/Colombo**. Continue daily at 19:00, at most one new part per calendar day. The dates below are targets, not completion claims. Resume unfinished work first and use the review buffer for delays; never skip checks or rush a second part into one day to catch up. Report any threat to the deadline promptly with the blocker and revised remaining dates.

| Target date | Work and acceptance gate |
|---|---|
| 12 October | Recheck Parts 1–3; correct baseline fitting availability; record this timeline |
| 14 October | Part 4: calendar and exact-time lag features; tests prove all observed inputs and fitted transformations satisfy the reporting cutoff |
| 15 October | Part 5: regularized and tree models with bounded, documented tuning; compare with baselines on identical validation hours |
| 16 October | Part 6: chronological backtests and seasonal/error breakdowns; document coverage and failure cases |
| 17 October | Part 7: intervals with a distinct calibration period; report coverage and width without using final holdout outcomes |
| 18 October | Part 8: explicitly hypothetical decision-cost study with sensitivity analysis; no real savings claims |
| 19 October | Part 9: freeze model, features, fallback, calibration and evaluation specification before opening holdout; evaluate once and build a small demo |
| 20 October | Part 10: evidence-based README, resume bullets, limitations and interview guide; verify profile claims |
| 21–23 October | Reproducibility and presentation review of completed parts; fix defects and verify setup, demo, links and CI |
| 24–25 October | Buffer for incomplete work or failed checks; no new scientific scope and no tuning against holdout results |
| 26 October | Final acceptance review and handoff; report completed deliverables and any remaining limitations honestly |

The final review must reconcile the brief's acceptance criteria with saved evidence: reproducible data and features, leakage checks, fair comparisons, untouched holdout until specification freeze, interval and decision-study caveats, a working demo, clean Git status and verified publication. Once complete, switch to warranted maintenance only. Empty days do not require commits.

### Schedule revision on 14 October

Part 4 was still unfinished at the first 14 October run and is now complete. Its original target was 13 October; no work has been backdated. Remaining part targets move one day to 15-20 October. The review buffer absorbs the delay and the 26 October deadline stays unchanged. Part 5 must not start before 15 October under the one-part-per-day rule.

## Session format

1. A two-minute recap in plain English.
2. One technical part, with a reproducible result.
3. Explain what changed, why it matters, and what remains uncertain.
4. One small learner exercise and two interview questions.
5. Commit only completed work and record the next part.

## Scope control

Do not chase deep learning or an LLM unless a measured baseline limitation justifies it. The distinguishing work is trustworthy evaluation and a defensible decision study. A negative modeling result can still demonstrate strong scientific judgment.
