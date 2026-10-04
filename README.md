# TrafficPulse

**Hourly traffic forecasting with honest evaluation and uncertainty.**

Status: **Part 1 complete — source ingestion and structural audit.** No model has been trained. No performance or operational impact is claimed.

[![Data contract tests](https://github.com/Kisara00555/trafficpulse/actions/workflows/tests.yml/badge.svg)](https://github.com/Kisara00555/trafficpulse/actions/workflows/tests.yml)

## The question

Can we forecast the next hour's reported westbound I-94 traffic volume more reliably than simple historical baselines, using only information available before that hour starts?

This is a historical research prototype for a hypothetical traffic-operations analyst. A later, explicitly simulated staffing exercise will test the cost of under- and over-predicting demand. The data do not contain staffing, costs, speed, incidents, or travel time. Traffic volume is not a direct measure of congestion, and this project cannot demonstrate reduced congestion or real savings.

## What makes the planned project useful in an interview

- Forecasting with time-based evaluation and explicit information-availability rules.
- Data engineering that catches missing hours and repeated timestamps, not just null cells.
- Simple baselines before complex models; error analysis by time and season.
- Prediction intervals, calibration checks, and transparent operational scenarios.
- Reproducible code, meaningful tests, documented decisions, and incremental Git history.

These are planned capabilities. See [the roadmap](docs/ROADMAP.md) for completion status.

## Today's verified findings

| Structural check | Result |
|---|---:|
| Raw rows | 48,204 |
| Distinct source timestamps | 40,575 |
| Hourly slots from first to last timestamp | 52,551 |
| Absent hourly slots | 11,976 |
| Timestamps represented by multiple rows | 5,445 |
| Exact duplicate rows | 17 |
| Timestamps with conflicting traffic counts | 0 |
| Rows with nonpositive Kelvin temperature | 10 |

No blank cells were found. Missing hours and duplicate observations still require explicit treatment. Counts use a naive hourly grid because the source labels times as local CST without resolving daylight-saving interpretation. The largest gap spans 7,386 missing hourly slots. We will not interpolate traffic through that gap.

The full evidence is in [day01_audit.json](reports/day01_audit.json); the input fingerprint and attribution are in [source_manifest.json](reports/source_manifest.json).

## Run Part 1

Python 3.10 or later; the data pipeline and tests use only the standard library.

```sh
python -m venv .venv
# Activate on Windows PowerShell:
.venv\Scripts\Activate.ps1
# Or on macOS/Linux: source .venv/bin/activate
python -m pip install -e .
python -m trafficpulse.data --download
python -m unittest discover -s tests -v
```

An installation-free alternative is to set `PYTHONPATH` to `src`, then run the last two commands. On PowerShell use `$env:PYTHONPATH='src'`; on macOS/Linux use `export PYTHONPATH=src`.

The download is about 396 KB. Repeated runs reuse the local archive and verify it against the recorded SHA-256 checksum. The archive is excluded from Git. Delete or move the local archive yourself only if intentionally requesting a fresh download. If UCI changes the archive, the pipeline stops for review instead of silently accepting changed inputs.

## Repository guide

- `src/trafficpulse/data.py`: download, source verification, structural audit.
- `tests/test_data.py`: small examples that test consequential data failure modes.
- `docs/PROJECT_BRIEF.md`: forecasting contract and evaluation plan.
- `docs/DATA_CARD.md`: field meanings, source, license, and limits.
- `docs/ROADMAP.md`: one learning milestone per session.
- `docs/daily/2026-10-04.md`: today's plain-language explanation and interview practice.
- `.github/workflows/tests.yml`: automated tests on each push and pull request. [Initial GitHub verification passed](https://github.com/Kisara00555/trafficpulse/actions/runs/37206079243).

## Source and license

Hogue, J. (2019). *Metro Interstate Traffic Volume*. UCI Machine Learning Repository. [DOI: 10.24432/C5X60B](https://doi.org/10.24432/C5X60B). [Official dataset page](https://archive.ics.uci.edu/dataset/492/metro+interstate+traffic+volume).

Source data are licensed **CC BY 4.0**. The source covers a single historical Minnesota traffic station and does not establish performance on current traffic or other locations. No software license has been selected yet; choose one before broader distribution.

## Portfolio integrity

This repository is being developed with AI assistance as a guided learning project. The learner should run each milestone, explain its assumptions, and make substantive choices before describing the finished project as their own interview work. Resume claims must describe completed, measured work. No invented accuracy, savings, deployment, or users.
