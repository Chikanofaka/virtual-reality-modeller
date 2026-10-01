"""Run inside Blender; inspect evaluated geometry without modifying the scene."""
import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def audit():
    depsgraph = bpy.context.evaluated_depsgraph_get()
    objects = []
    failures = []
    for source in bpy.context.scene.objects:
        if source.type != 'MESH':
            continue
        evaluated = source.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            mesh.calc_loop_triangles()
            vertices = [evaluated.matrix_world @ v.co for v in mesh.vertices]
            if not vertices:
                failures.append(source.name + ': empty geometry')
                continue
            normal_matrix = evaluated.matrix_world.to_3x3().inverted_safe().transposed()
            normals = [(normal_matrix @ p.normal).normalized() for p in mesh.polygons]
            edge_uses = {tuple(sorted(e.vertices)): 0 for e in mesh.edges}
            for face in mesh.polygons:
                ids = list(face.vertices)
                for a, b in zip(ids, ids[1:] + ids[:1]):
                    key = tuple(sorted((a, b)))
                    edge_uses[key] = edge_uses.get(key, 0) + 1
            floor = source.get('role') == 'floor' or source.name.lower().startswith('floor')
            up = sum(n.dot(Vector((0, 0, 1))) > .95 for n in normals)
            down = sum(n.dot(Vector((0, 0, 1))) < -.95 for n in normals)
            if floor and not up:
                failures.append(source.name + ': no upward floor face')
            objects.append({
                'name': source.name, 'role': source.get('role', ''),
                'vertices': len(vertices), 'triangles': len(mesh.loop_triangles),
                'bounds': [[min(v[i] for v in vertices) for i in range(3)],
                           [max(v[i] for v in vertices) for i in range(3)]],
                'nonmanifold_edges': sum(n != 2 for n in edge_uses.values()),
                'floor': floor, 'upward_faces': up, 'downward_faces': down,
            })
        finally:
            evaluated.to_mesh_clear()
    if not objects:
        failures.append('Scene contains no evaluated mesh geometry')
    return {'schemaVersion': 1, 'blender': bpy.app.version_string,
            'units': bpy.context.scene.unit_settings.system,
            'scale_length': bpy.context.scene.unit_settings.scale_length,
            'objects': objects, 'triangles': sum(o['triangles'] for o in objects),
            'failures': failures, 'passed': not failures,
            'limits': ['Does not certify floor-plan parity, openings or runtime navigation.',
                       'Nonmanifold counts are reported for review, not automatically rejected.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    report = audit()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': report['passed'], 'objects': len(report['objects']),
                      'triangles': report['triangles']}))
    if not report['passed']:
        raise SystemExit(1)
