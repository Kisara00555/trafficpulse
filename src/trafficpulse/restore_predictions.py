"""Restore ignored predictions from frozen inputs without replacing the final report."""
from pathlib import Path
import json

from .data import ROOT
from .features import load_verified_inputs
from .baselines import read_hourly
from .holdout import (FREEZE_COMMIT, PREDICTIONS, REPORT, experiment, load_freeze,
                      prediction_bytes, run as verify_run, sha, text_bytes)


def restore(root=ROOT):
    root = Path(root)
    destination = root/PREDICTIONS
    if destination.exists():
        raise FileExistsError('Predictions already exist; use trafficpulse.holdout --verify')
    report = json.loads((root/REPORT).read_text(encoding='utf-8'))
    freeze = load_freeze(root)
    if (report['freeze_commit'] != FREEZE_COMMIT
            or report['freeze_sha256'] != sha(text_bytes(root/'reports/part09_freeze.json'))
            or report['runner_sha256'] != sha(text_bytes(root/'src/trafficpulse/holdout.py'))):
        raise ValueError('Saved report provenance differs from frozen implementation')
    dev, fingerprints = load_verified_inputs(root)
    if any(fingerprints[s] != freeze['input_sha256'][s] for s in fingerprints):
        raise ValueError('Development inputs differ from freeze')
    path = root/'data/processed/test.csv'
    if sha(path.read_bytes()) != freeze['input_sha256']['test']:
        raise ValueError('Holdout fingerprint mismatch')
    _, rows, points, intervals = experiment(dev, read_hourly(path), freeze)
    data = prediction_bytes(rows, points, intervals)
    if sha(data) != report['prediction_csv_sha256']:
        raise ValueError('Reproduced predictions differ; no output written')
    with destination.open('xb') as handle:
        handle.write(data)
    # Compare the entire assessment with its saved report; never replace that report.
    verify_run(root, verify=True)
    return destination


if __name__ == '__main__':
    print(f'Restored byte-identical predictions and verified unchanged report: {restore()}')
