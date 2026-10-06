#!/usr/bin/env python3
"""Verify an already approved apartment, then package and replay its extracted ZIP.

Does not approve, mutate or rebuild the project. Requires local Playwright/Chrome.
"""
import argparse
import os
import sys
import threading
import uuid
from pathlib import Path

import harness
from verify_harness import Verification, ROOT, output_directory, read_json, require, source_files, utc_now


class ApartmentVerification(Verification):
    def relative(self, path):
        return os.path.relpath(path, self.output)

    def run(self, label, argv, env=None, timeout=900):
        argv = [str(a) for a in argv]
        if str(ROOT / 'tests/browser-smoke.mjs') in argv:
            argv[argv.index(str(ROOT / 'tests/browser-smoke.mjs'))] = str(ROOT / 'tests/browser-apartment.mjs')
            env = dict(env or os.environ)
            env['APARTMENT_OUTPUT'] = env['SMOKE_OUTPUT']
        return super().run(label, argv, env, timeout)

    def browser_report(self, project, label, build_id):
        directory = self.output / 'browser' / label
        server = harness.make_server(harness.current_build(project))
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            url = f'http://127.0.0.1:{server.server_port}/?build={build_id}'
            env = dict(os.environ, APARTMENT_OUTPUT=str(directory))
            self.run(label + '-browser', [self.node, ROOT / 'tests/browser-apartment.mjs', url], env)
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=5)
        path = directory / 'report.json'
        report = read_json(path)
        require(report.get('passed') is True and report.get('buildId') == build_id,
                'Browser report must match this apartment build')
        return path

    def execute_apartment(self, project):
        self.report['scope'] = 'Owner-approved apartment: actual keyboard traversal, interactions, reset, package, independent extraction and replay'
        self.source_identity()
        self.cli('apartment-validate', 'validate', project, '--build')
        marker = ('APARTMENT_PRIVATE_' + uuid.uuid4().hex).encode()
        sentinel = project / 'private/delivery-sentinel.txt'
        sentinel.parent.mkdir(exist_ok=True)
        sentinel.write_bytes(marker)
        self.deliver(project, 'midtown-apartment', marker)
        final = source_files()
        initial = self.report['source']['files']
        changed = sorted(n for n in set(final) | set(initial) if final.get(n) != initial.get(n))
        self.report['source']['changedDuringRun'] = changed
        require(not changed, 'Verification source changed during run')
        self.report.update(passed=True, completedAt=utc_now(), browserStatus='passed')
        self.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', default='projects/photo-game-intake')
    parser.add_argument('--output', required=True)
    parser.add_argument('--node', default=os.environ.get('NODE_BIN', 'node'))
    args = parser.parse_args()
    # The public showcase uses the same acceptance route with a public project ID.
    os.environ['APARTMENT_PROJECT_ID'] = read_json(Path(args.project) / 'planning.json')['project']['id']
    verify = ApartmentVerification(output_directory(args.output), args.node, True)
    try:
        verify.execute_apartment(Path(args.project).resolve())
    except Exception as error:
        verify.report.update(passed=False, error=str(error), completedAt=utc_now())
        verify.save()
        print(f'FAILED: {error}', file=sys.stderr)
        return 1
    print(f'PASS: {verify.output / "report.json"}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
