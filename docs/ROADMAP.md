# Guided project roadmap

Autonomous daily development was authorized on 6 October 2026. Complete at most one next unfinished part per Asia/Colombo calendar day at the existing 19:00 scheduled run, without requiring a learner reply. Each part gets a short daily note, a reproducible artifact, checks, and a meaningful commit. Resume incomplete parts before advancing; duplicate runs must not start additional parts on the same day. The optional exercises help the learner prepare for interviews but do not block the next day's work. Dates of completion depend on validation and access; never mark unfinished work complete to meet a daily target.

| Part | Deliverable | Main interview question | Status |
|---|---|---|---|
| 1 | Problem contract, source pipeline, structural audit | Why can data with no nulls still be incomplete? | Complete, 2026-10-04 |
| 2 | Clean hourly table, split manifests, quality notebook | What does one row represent? | Next |
| 3 | Training-only exploration and simple baselines | What must your model beat? | Planned |
| 4 | Leakage-tested lag/calendar features | What information exists at prediction time? | Planned |
| 5 | Regularized and tree-based models | Why this model and how was it tuned? | Planned |
| 6 | Temporal backtesting and error analysis | Does it work across seasons? | Planned |
| 7 | Uncertainty and interval evaluation | How do you communicate unreliable forecasts? | Planned |
| 8 | Simulated operational decision study | How does predictive accuracy affect a decision? | Planned |
| 9 | Final holdout evaluation and small demo | What happens on unseen data? | Planned |
| 10 | GitHub presentation, resume evidence, mock interview | What did you personally decide and learn? | Planned |

## Session template

1. A two-minute recap in plain English.
2. One technical part, with a reproducible result.
3. Explain what changed, why it matters, and what remains uncertain.
4. One small learner exercise and two interview questions.
5. Commit only completed work and record the next part.

## Scope control

Do not chase deep learning or an LLM unless a measured baseline limitation justifies it. The distinguishing work is trustworthy evaluation and a defensible decision study. A negative modeling result can still demonstrate strong scientific judgment.
