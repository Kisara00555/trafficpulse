from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

try:
    from trafficpulse.restore_predictions import restore
    from trafficpulse.holdout import PREDICTIONS
    HAS_MODELS = True
except ModuleNotFoundError as exc:
    if exc.name not in {'numpy', 'scipy', 'sklearn', 'threadpoolctl'}: raise
    HAS_MODELS = False


@unittest.skipUnless(HAS_MODELS, 'Install model extra for restoration tests')
class RestoreTests(unittest.TestCase):
    def test_existing_predictions_are_preserved_without_reading_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); path=root/PREDICTIONS
            path.parent.mkdir(parents=True); path.write_bytes(b'original')
            with patch('trafficpulse.restore_predictions.load_freeze') as loader:
                with self.assertRaises(FileExistsError): restore(root)
                loader.assert_not_called()
            self.assertEqual(path.read_bytes(),b'original')


if __name__ == '__main__': unittest.main()
