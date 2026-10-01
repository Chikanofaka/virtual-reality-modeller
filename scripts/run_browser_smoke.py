#!/usr/bin/env python3
"""Serve the current approved example and run the optional Playwright smoke test."""
import argparse
import os
import pathlib
import subprocess
import threading

import harness


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', default=str(harness.ROOT / 'projects' / 'pearl-office'))
    parser.add_argument('--node', default=os.environ.get('NODE_BIN', 'node'))
    args = parser.parse_args()
    project = harness.project(args.project)
    server = harness.make_server(harness.current_build(project))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    url = 'http://127.0.0.1:{}/?build={}'.format(server.server_port, server.metadata['buildId'])
    try:
        return subprocess.run([args.node, str(harness.ROOT / 'tests' / 'browser-smoke.mjs'), url],
                              cwd=harness.ROOT).returncode
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


if __name__ == '__main__':
    raise SystemExit(main())
