# Guided project roadmap

One part per session. Advance after the learner can explain the previous part; do not generate the full project unattended. Each completed session gets a short daily note, a reproducible artifact, checks, and one meaningful commit. Dates after Part 1 are not promises or scheduled work.

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
