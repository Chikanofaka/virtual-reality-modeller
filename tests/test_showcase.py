"""Protect the public replay's identity and extraction boundary."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('replay_midtown', ROOT / 'scripts/replay_midtown.py')
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


class ShowcaseTests(unittest.TestCase):
    def test_bundled_replay_extracts_with_bound_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = replay.extract_demo(parent=Path(tmp))
            self.assertTrue((dest / 'launch.py').is_file())
            self.assertEqual(json.loads((dest / 'runtime/build.json').read_text())['buildId'],
                             json.loads((replay.EXAMPLE / 'replay.json').read_text())['buildId'])
            self.assertIn(".DS_Store", (dest / 'launch.py').read_text())

    def test_tampered_archive_and_unsafe_members_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            archive = folder / 'midtown-playable.zip'
            with zipfile.ZipFile(archive, 'w') as z:
                z.writestr('../outside.txt', 'unwanted')
            record = {'buildId': 'fixture', 'archiveSha256': '0' * 64}
            (folder / 'replay.json').write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, 'differs'):
                replay.extract_demo(folder, folder / 'output')
            record['archiveSha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
            (folder / 'replay.json').write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, 'Unsafe path'):
                replay.extract_demo(folder, folder / 'output')
            self.assertFalse((folder / 'outside.txt').exists())


if __name__ == '__main__':
    unittest.main()
