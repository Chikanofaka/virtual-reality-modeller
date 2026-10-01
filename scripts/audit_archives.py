#!/usr/bin/env python3
"""Hash supplied evolution ZIPs and compare their text without executing/extracting them.

Usage: python3 scripts/audit_archives.py SOURCE_DIRECTORY --output AUDIT_DIRECTORY
The output includes original archive/member SHA-256, normalized-path comparisons,
and primary-player source diffs. Source absolute paths are never written to reports.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import zipfile

ARCHIVES = [
    'floor_plan_evolution',
    'pearl_office_autonomous_game',
    'pearl_office_compatibility_game',
    'pearl_office_smooth_game',
    'pearl_office_hybrid_hd',
    'pearl_office_ultra_hybrid_v2',
    'pearl_office_mainrepo_drag_v3',
    'pearl_office_mainrepo_runtime_optimized_v4',
    'pearl_office_mainrepo_signalnav_v5',
    'pearl_office_mainrepo_safari_walk_v6',
    'pearl_office_mainrepo_safari_wasd_v7',
]
MAX_MEMBERS = 10_000
MAX_MEMBER_BYTES = 128 * 1024 * 1024
MAX_TOTAL_BYTES = 1024 * 1024 * 1024
MAX_SOURCE_BYTES = 8 * 1024 * 1024


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def safe_member_name(name: str) -> bool:
    # No members are extracted, but report names that must never be extracted blindly.
    pure = PurePosixPath(name)
    return not (pure.is_absolute() or '..' in pure.parts or '\\' in name
                or re.match(r'^[A-Za-z]:', name))


def comparison_path(name: str) -> str | None:
    parts = PurePosixPath(name).parts
    if not parts or not safe_member_name(name):
        return None
    if any(p in {'__MACOSX', '.git', '__pycache__', 'node_modules'} for p in parts):
        return None
    if any(p.startswith('._') for p in parts) or parts[-1] == '.DS_Store':
        return None
    # Supplied ZIPs all use a package root. Keep root-level files if a new ZIP does not.
    return '/'.join(parts[1:]) if len(parts) > 1 else parts[0]


def primary_rank(relative: str) -> int:
    if relative == 'runtime/app_v7.js':
        return 0
    if relative == 'runtime/app.js':
        return 1
    if relative.lower().endswith('.html') and PurePosixPath(relative).name.startswith('PLAY_'):
        return 2
    return 100


def inspect_archive(path: Path) -> tuple[dict, str | None, str | None]:
    manifest = {'archive': path.name, 'sha256': sha_file(path), 'entries': []}
    primary: tuple[int, str, str] | None = None
    with zipfile.ZipFile(path) as archive:
        members = [info for info in archive.infolist() if not info.is_dir()]
        if len(members) > MAX_MEMBERS or sum(i.file_size for i in members) > MAX_TOTAL_BYTES:
            raise ValueError(f'{path.name}: ZIP size/member limits exceeded')
        names: set[str] = set()
        for info in members:
            if info.filename in names:
                raise ValueError(f'{path.name}: duplicate ZIP entry is ambiguous: {info.filename!r}')
            names.add(info.filename)
            if info.file_size > MAX_MEMBER_BYTES:
                raise ValueError(f'{path.name}: member exceeds size limit: {info.filename!r}')
            if info.flag_bits & 1:
                raise ValueError(f'{path.name}: encrypted members are unsupported')
            relative = comparison_path(info.filename)
            rank = primary_rank(relative) if relative else 100
            capture = rank < 100 and info.file_size <= MAX_SOURCE_BYTES
            chunks: list[bytes] = []
            digest = hashlib.sha256()
            count = 0
            with archive.open(info) as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    count += len(block)
                    if count > MAX_MEMBER_BYTES:
                        raise ValueError(f'{path.name}: decompressed member exceeded limit')
                    digest.update(block)
                    if capture:
                        chunks.append(block)
            manifest['entries'].append({
                'path': info.filename, 'size': count, 'sha256': digest.hexdigest(),
                'unsafe_path': not safe_member_name(info.filename),
                'symlink': stat.S_ISLNK(info.external_attr >> 16),
            })
            if capture and (primary is None or rank < primary[0]):
                primary = (rank, relative, b''.join(chunks).decode('utf-8', errors='replace'))
    return manifest, primary[1] if primary else None, primary[2] if primary else None


def compare(before: dict, after: dict) -> dict:
    def normalized(item: dict) -> dict:
        result = {}
        for entry in item['entries']:
            name = comparison_path(entry['path'])
            if name is not None:
                if name in result:
                    raise ValueError(f"{item['archive']}: normalized path collision: {name}")
                result[name] = entry
        return result
    a, b = normalized(before), normalized(after)
    common = set(a) & set(b)
    return {
        'from': before['archive'], 'to': after['archive'],
        'interpretation': 'Supplied comparison order; alternate renderers are branches, not necessarily direct descendants.',
        'added': sorted(set(b) - set(a)), 'removed': sorted(set(a) - set(b)),
        'modified': sorted(p for p in common if a[p]['sha256'] != b[p]['sha256']),
        'unchanged': sorted(p for p in common if a[p]['sha256'] == b[p]['sha256']),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='Directory containing the eleven named ZIPs')
    parser.add_argument('--output', type=Path, required=True, help='Report directory; no ZIP member extraction')
    parser.add_argument('--allow-missing', action='store_true', help='Audit available archives and list missing ones explicitly')
    args = parser.parse_args()
    missing = [name + '.zip' for name in ARCHIVES if not (args.source / (name + '.zip')).is_file()]
    if missing and not args.allow_missing:
        parser.error('Missing archives: ' + ', '.join(missing))
    records, sources = [], []
    for name in ARCHIVES:
        archive = args.source / (name + '.zip')
        if not archive.is_file():
            continue
        record, source_name, source = inspect_archive(archive)
        records.append(record)
        if source is not None:
            sources.append((name, source_name, source))
    args.output.mkdir(parents=True, exist_ok=True)
    def write_json(name: str, value: object) -> None:
        (args.output / name).write_text(json.dumps(value, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')
    write_json('archive-manifest.json', {
        'format': 1, 'scope': 'Content audit only; no member extraction or code execution.',
        'expected_archives': len(ARCHIVES), 'missing_archives': missing, 'archives': records,
    })
    write_json('archive-comparisons.json', [compare(a, b) for a, b in zip(records, records[1:])])
    diff_index = []
    for previous, current in zip(sources, sources[1:]):
        a, a_path, a_text = previous
        b, b_path, b_text = current
        filename = b + '.diff'
        diff = ''.join(difflib.unified_diff(
            a_text.splitlines(keepends=True), b_text.splitlines(keepends=True),
            fromfile=f'{a}/{a_path}', tofile=f'{b}/{b_path}'))
        (args.output / filename).write_text(diff, encoding='utf-8')
        diff_index.append({'from': a + '.zip', 'to': b + '.zip', 'source_from': a_path,
                           'source_to': b_path, 'diff': filename})
    write_json('source-diffs.json', diff_index)
    print(f'Audited {len(records)} archives; {len(diff_index)} source comparisons; {len(missing)} missing.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as error:
        print(f'Audit failed: {error}', file=sys.stderr)
        raise SystemExit(1)
