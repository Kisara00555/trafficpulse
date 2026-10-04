# Data card

Source: [UCI Metro Interstate Traffic Volume](https://archive.ics.uci.edu/dataset/492/metro+interstate+traffic+volume), John Hogue (2019), [DOI](https://doi.org/10.24432/C5X60B), CC BY 4.0. Download URL and SHA-256 are recorded in `reports/source_manifest.json`. Audit performed 4 October 2026; observations themselves are historical.

## Grain and fields

The intended modeling grain is one hour. Raw rows are not unique by timestamp. Do not add repeated traffic counts together.

| Field | Source meaning | Planned availability |
|---|---|---|
| date_time | Local CST source hour, timezone handling unresolved | Calendar features known for forecast hour |
| traffic_volume | Reported westbound hourly count | Target; only permitted historical lags may be features |
| holiday | Holiday/event category; `None` is a literal category | Rebuild/check calendar encoding before use |
| temp | Temperature in Kelvin | Historical lags only; nonpositive values flagged |
| rain_1h | Rain during hour, mm | Historical lags only |
| snow_1h | Snow during hour, mm | Historical lags only |
| clouds_all | Cloud cover percentage | Historical lags only |
| weather_main | Weather category | Historical lags only |
| weather_description | More detailed weather text | Historical lags only |

## Fitness and limitations

The source is appropriate for learning time-series methods and data-quality reasoning. It is not current evidence for traffic operations. It represents one station, one direction, and historical conditions. There are no interventions, outcomes about safety, or operational cost labels. Do not make causal claims about weather, congestion reduction, or staffing benefits.

The audit distinguishes blank cells from absent time slots, exact duplicate records from multiple observations at one timestamp, and repeated targets from conflicting targets. It flags a small set of impossible ranges; it is not an exhaustive physical plausibility audit. Rainfall extremes, target zeros and holiday behavior remain for Part 2. No raw values have been altered.

Preserve naive source timestamps for now. Do not arbitrarily localize them to America/Chicago or UTC without settling the CST/DST interpretation. Missing-slot counts are conditional on this documented source-clock assumption.
