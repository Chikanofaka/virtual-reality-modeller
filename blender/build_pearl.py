"""Run the historical companion builder with a small, checked API adapter.

blender --background --factory-startup --python-exit-code 1 \
    --python blender/build_pearl.py -- --output output/pearl-companion
The archived source remains unchanged; this does not recreate the browser V7 scene.
"""
import argparse
import hashlib
import json
import runpy
import struct
import sys
from pathlib import Path

import bpy


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise RuntimeError('Archived builder changed; review compatibility adapter: ' + old)
    return source.replace(old, new, 1)


def supported_eevee():
    for engine in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
        try:
            bpy.context.scene.render.engine = engine
            return engine
        except (TypeError, ValueError):
            continue
    raise RuntimeError('This Blender installation has no supported Eevee render engine')


def check_outputs(output):
    files = {}
    for name in ('pearl_office_preview.png', 'pearl_office.blend', 'pearl_office.glb'):
        path = output / name
        if not path.is_file() or path.stat().st_size < 20:
            raise RuntimeError('Builder did not produce a complete output: ' + name)
        data = path.read_bytes()
        if name.endswith('.png'):
            if data[:8] != b'\x89PNG\r\n\x1a\n' or data[12:16] != b'IHDR':
                raise RuntimeError('Invalid preview PNG header')
            if min(struct.unpack('>II', data[16:24])) < 1:
                raise RuntimeError('Preview PNG has no pixels')
        if name.endswith('.glb'):
            if struct.unpack('<III', data[:12]) != (0x46546C67, 2, len(data)):
                raise RuntimeError('Invalid GLB header or incomplete export')
            length, kind = struct.unpack('<II', data[12:20])
            if kind != 0x4E4F534A or 20 + length > len(data):
                raise RuntimeError('Invalid GLB JSON chunk')
            model = json.loads(data[20:20 + length])
            if not model.get('meshes'):
                raise RuntimeError('Exported GLB contains no meshes')
        files[name] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    return files


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=root.parent / 'output' / 'pearl-companion')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    output = args.output.resolve()
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise RuntimeError('Use an empty output directory so stale artifacts cannot pass: ' + str(output))
    output.mkdir(parents=True, exist_ok=True)
    source_path = root / 'BUILD_PEARL_OFFICE_UPSTREAM.py'
    archived = source_path.read_bytes()
    source = archived.decode('utf-8')
    engine = supported_eevee()
    source = replace_once(source, "scene.render.engine = 'BLENDER_EEVEE_NEXT'", 'scene.render.engine = ' + repr(engine))
    source = replace_once(source, "OUT = os.path.join(ROOT, 'output')", 'OUT = ' + repr(str(output)))
    print('Historical Pearl companion: Blender', bpy.app.version_string, 'engine', engine, flush=True)
    exec(compile(source, str(source_path), 'exec'), {'__name__': '__main__', '__file__': str(source_path)})
    files = check_outputs(output)
    audit = runpy.run_path(str(root / 'audit_scene.py'))['audit']()
    (output / 'audit.json').write_text(json.dumps(audit, indent=2) + '\n')
    if not audit['passed']:
        raise RuntimeError('Evaluated geometry audit failed: ' + '; '.join(audit['failures']))
    report = {
        'passed': True, 'blender': bpy.app.version_string, 'engine': engine,
        'upstreamSha256': hashlib.sha256(archived).hexdigest(), 'files': files,
        'meshObjects': len(audit['objects']), 'triangles': audit['triangles'],
        'limitations': [
            'Historical approximate companion; not visual parity with the browser V7 scene.',
            'Geometry and file checks do not certify openings, photo fidelity or runtime navigation.',
        ],
    }
    (output / 'build-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
