#!/usr/bin/env python3
"""Extract and launch the frozen Midtown showcase. No AI, Blender or npm required."""
import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / 'examples/midtown-apartment'


def extract_demo(example=EXAMPLE, parent=None):
    record = json.loads((example / 'replay.json').read_text(encoding='utf-8'))
    archive = example / 'midtown-playable.zip'
    if hashlib.sha256(archive.read_bytes()).hexdigest() != record['archiveSha256']:
        raise ValueError('Showcase ZIP differs from replay.json. Download a complete repository copy.')
    if parent is None:
        parent = ROOT / 'projects/example-replays'
    parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as package:
        for info in package.infolist():
            path = pathlib.PurePosixPath(info.filename)
            if path.is_absolute() or '..' in path.parts or '\\' in info.filename or ':' in info.filename:
                raise ValueError('Unsafe path in showcase archive')
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Showcase archive contains a symlink')
        metadata = json.loads(package.read('runtime/build.json'))
        if metadata['buildId'] != record['buildId']:
            raise ValueError('Showcase build identity differs from replay.json')
        destination = pathlib.Path(tempfile.mkdtemp(prefix='midtown-', dir=parent))
        package.extractall(destination)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-open', action='store_true', help='Print the local URL without opening the default browser')
    parser.add_argument('--extract-only', action='store_true', help='Extract a fresh copy and print its directory')
    args = parser.parse_args()
    try:
        destination = extract_demo()
        print(f'Extracted game: {destination}', flush=True)
        if args.extract_only:
            return 0
        command = [sys.executable, str(destination / 'launch.py')]
        if args.no_open:
            command.append('--no-open')
        return subprocess.call(command, cwd=destination)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(str(error), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 0


if __name__ == '__main__':
    sys.exit(main())
