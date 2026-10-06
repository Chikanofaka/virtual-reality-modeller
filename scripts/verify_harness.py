#!/usr/bin/env python3
"""Verify the repository and its synthetic projects through extracted delivery.

This integration test approves only bundled test fixtures. It does not accept a
real user's planning pack, infer measurements from photos, or publish anything.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile


ROOT = pathlib.Path(__file__).resolve().parents[1]


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha256(path):
    digest = hashlib.sha256()
    with pathlib.Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path):
    return json.loads(pathlib.Path(path).read_text(encoding='utf-8'))


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def source_files():
    files = {}
    for name in ('runtime', 'scripts', 'schemas', 'templates', 'tests'):
        for path in sorted((ROOT / name).rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                files[path.relative_to(ROOT).as_posix()] = sha256(path)
    return files


def output_directory(requested):
    if requested is None:
        parent = ROOT / 'test-results'
        parent.mkdir(exist_ok=True)
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ-')
        return pathlib.Path(tempfile.mkdtemp(prefix='full-harness-' + stamp, dir=parent))
    candidate = pathlib.Path(requested).expanduser()
    require(not candidate.is_symlink(), 'Output must not be a symlink')
    destination = candidate.resolve()
    if destination.exists():
        require(destination.is_dir() and not any(destination.iterdir()),
                '--output must name a new or empty directory')
    else:
        destination.mkdir(parents=True)
    return destination


class Verification:
    def __init__(self, output, node, browser):
        self.output = output
        self.node = node
        self.browser = browser
        self.logs = output / 'logs'
        self.logs.mkdir()
        self.report = {
            'passed': False,
            'startedAt': utc_now(),
            'scope': 'synthetic integration test; no real-user plan approval',
            'browserRequested': browser,
            'nativeBrowserAcceptance': 'unverified; automated input is separate evidence',
            'outputDirectory': str(output),
            'commands': [],
            'projects': {},
        }

    def relative(self, path):
        return pathlib.Path(path).relative_to(self.output).as_posix()

    def save(self):
        (self.output / 'report.json').write_text(
            json.dumps(self.report, indent=2, ensure_ascii=False, allow_nan=False) + '\n',
            encoding='utf-8')

    def command_record(self, label, argv):
        number = len(self.report['commands']) + 1
        safe = re.sub(r'[^a-zA-Z0-9_-]+', '-', label).strip('-')
        log = self.logs / f'{number:02d}-{safe}.log'
        record = {'label': label, 'argv': [str(arg) for arg in argv],
                  'log': self.relative(log), 'startedAt': utc_now()}
        self.report['commands'].append(record)
        self.save()
        return record, log

    def run(self, label, argv, env=None, timeout=600):
        argv = [str(arg) for arg in argv]
        record, log = self.command_record(label, argv)
        print(f'[{len(self.report["commands"])}] {label}', flush=True)
        started = time.monotonic()
        try:
            with log.open('w', encoding='utf-8') as stream:
                result = subprocess.run(argv, cwd=ROOT, env=env, stdout=stream,
                                        stderr=subprocess.STDOUT, timeout=timeout)
            record.update(exitCode=result.returncode, passed=result.returncode == 0)
            require(result.returncode == 0, f'{label} failed (exit {result.returncode}); see {log}')
        except Exception as error:
            record.update(passed=False, error=str(error))
            raise
        finally:
            record['durationSeconds'] = round(time.monotonic() - started, 3)
            if log.exists():
                record['logSha256'] = sha256(log)
            self.save()
        return log

    def cli(self, label, *arguments):
        return self.run(label, [sys.executable, ROOT / 'scripts/harness.py', *arguments])

    def source_identity(self):
        files = source_files()
        aggregate = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
        identity = {'root': str(ROOT), 'filesSha256': aggregate, 'files': files,
                    'pythonExecutable': sys.executable, 'pythonVersion': sys.version,
                    'nodeExecutable': self.node}
        for key, args in (('commit', ['rev-parse', 'HEAD']), ('gitStatus', ['status', '--short'])):
            try:
                result = subprocess.run(['git', *args], cwd=ROOT, capture_output=True,
                                        text=True, timeout=15)
                identity[key] = result.stdout.strip() if result.returncode == 0 else 'unavailable'
            except (OSError, subprocess.TimeoutExpired):
                identity[key] = 'unavailable'
        self.report['source'] = identity
        self.save()

    def unit_tests(self):
        node_log = self.run('node-version', [self.node, '--version'], timeout=15)
        node_version = node_log.read_text(encoding='utf-8').strip()
        match = re.fullmatch(r'v(\d+)\.\d+\.\d+', node_version)
        require(match is not None and int(match.group(1)) >= 20, 'Node 20+ is required')
        self.report['source']['nodeVersion'] = node_version
        python_log = self.run('python-tests', [sys.executable, '-m', 'unittest', 'discover',
                                               '-s', 'tests', '-p', 'test_*.py'])
        test_files = sorted((ROOT / 'tests').glob('runtime*.mjs'))
        require(bool(test_files), 'No runtime JavaScript tests were found')
        runtime_log = self.run('runtime-tests', [self.node, '--test', *test_files])
        python_text = python_log.read_text(encoding='utf-8')
        runtime_text = runtime_log.read_text(encoding='utf-8')
        python_count = re.search(r'Ran (\d+) tests?', python_text)
        node_count = re.search(r'^# tests (\d+)$', runtime_text, re.MULTILINE)
        require(python_count is not None and int(python_count.group(1)) > 0,
                'Python suite did not report any executed tests')
        require(node_count is not None and int(node_count.group(1)) > 0,
                'Node suite did not report any executed tests')
        python_skipped = re.search(r'skipped=(\d+)', python_text)
        node_skipped = re.search(r'^# skipped (\d+)$', runtime_text, re.MULTILINE)
        self.report['tests'] = {'python': int(python_count.group(1)),
                                'javascript': int(node_count.group(1)), 'passed': True,
                                'pythonSkipped': int(python_skipped.group(1)) if python_skipped else 0,
                                'javascriptSkipped': int(node_skipped.group(1)) if node_skipped else 0}
        self.save()

    def browser_report(self, project, label, build_id):
        directory = self.output / 'browser' / label
        env = os.environ.copy()
        env['SMOKE_OUTPUT'] = str(directory)
        self.run(label + '-browser', [sys.executable, ROOT / 'scripts/run_browser_smoke.py',
                                     '--project', project, '--node', self.node], env=env)
        report_path = directory / 'report.json'
        report = read_json(report_path)
        require(report.get('passed') is True and report.get('buildId') == build_id,
                f'{label} browser report does not verify the selected build')
        return report_path

    @staticmethod
    def stream_contains(stream, marker):
        tail = b''
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            data = tail + chunk
            if marker in data:
                return True
            tail = data[-max(0, len(marker) - 1):]
        return False

    def unpack(self, archive, label, marker):
        destination = self.output / 'extracted' / label
        destination.mkdir(parents=True)
        checked = 0
        with zipfile.ZipFile(archive) as package:
            for info in package.infolist():
                parts = pathlib.PurePosixPath(info.filename).parts
                require(parts and not info.filename.startswith('/') and '..' not in parts
                        and '\\' not in info.filename, 'Package contains an unsafe path')
                require('private' not in parts and 'uploads' not in parts,
                        'Package unexpectedly includes a private upload directory')
                if not info.is_dir():
                    with package.open(info) as stream:
                        require(not self.stream_contains(stream, marker),
                                f'Private sentinel leaked into {info.filename}')
                    checked += 1
            package.extractall(destination)
        return destination, {'passed': True, 'sentinelAbsent': True,
                             'privateUploadDirectoriesAbsent': True, 'filesScanned': checked}

    def standalone(self, extracted, label, metadata):
        argv = [sys.executable, str(extracted / 'launch.py'), '--no-open']
        record, log = self.command_record(label + '-standalone-server', argv)
        started = time.monotonic()
        urls = queue.Queue()
        process = None
        reader = None
        outcome = {'passed': False}
        try:
            with log.open('w', encoding='utf-8') as stream:
                process = subprocess.Popen(argv, cwd=extracted, stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT, text=True, bufsize=1)

                def collect_output():
                    for line in process.stdout:
                        stream.write(line)
                        stream.flush()
                        if re.fullmatch(r'http://127\.0\.0\.1:\d+/\?build=[a-f0-9]+\s*', line):
                            urls.put(line.strip())
                    urls.put(None)

                reader = threading.Thread(target=collect_output, daemon=True)
                reader.start()
                try:
                    url = urls.get(timeout=30)
                    require(url is not None, f'{label} standalone launcher exited before serving; see {log}')
                    parsed = urllib.parse.urlsplit(url)
                    require(urllib.parse.parse_qs(parsed.query).get('build') == [metadata['buildId']],
                            'Standalone URL does not identify the selected build')
                    with urllib.request.urlopen(url, timeout=15) as response:
                        require(response.status == 200, 'Standalone index did not load')
                        require('no-store' in response.headers.get('Cache-Control', ''),
                                'Standalone response lacks no-store')
                    identity_url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, '/__build', '', ''))
                    with urllib.request.urlopen(identity_url, timeout=15) as response:
                        identity = json.load(response)
                    require(identity.get('buildId') == metadata['buildId']
                            and identity.get('planHash') == metadata['planHash']
                            and identity.get('runtimeHash') == metadata['runtimeHash']
                            and identity.get('port') == parsed.port,
                            'Standalone server identity differs from the selected build')
                    stale = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, '/', 'build=stale', ''))
                    try:
                        urllib.request.urlopen(stale, timeout=15).close()
                        raise RuntimeError('Standalone server accepted a stale build URL')
                    except urllib.error.HTTPError as error:
                        require(error.code == 409, 'Stale build URL did not return HTTP 409')
                    outcome.update(url=url, buildId=identity['buildId'], actualPort=identity['port'],
                                   identityMatched=True, noStore=True, staleUrlRejected=True)
                    if self.browser:
                        browser_dir = self.output / 'browser' / (label + '-extracted')
                        env = os.environ.copy()
                        env['SMOKE_OUTPUT'] = str(browser_dir)
                        self.run(label + '-extracted-browser',
                                 [self.node, ROOT / 'tests/browser-smoke.mjs', url], env=env)
                        browser_path = browser_dir / 'report.json'
                        browser = read_json(browser_path)
                        require(browser.get('passed') is True and browser.get('buildId') == metadata['buildId'],
                                'Extracted-package browser report does not match the selected build')
                        outcome['browser'] = {'status': 'passed', 'report': self.relative(browser_path),
                                              'sha256': sha256(browser_path)}
                    else:
                        outcome['browser'] = {'status': 'not-requested'}
                    require(process.poll() is None, 'Standalone server exited unexpectedly during verification')
                    outcome['passed'] = True
                    record['passed'] = True
                finally:
                    if process.poll() is None:
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait(timeout=5)
                    reader.join(timeout=5)
                    require(not reader.is_alive(), 'Standalone output reader did not close')
        except Exception as error:
            record.update(passed=False, error=str(error))
            raise
        finally:
            record['durationSeconds'] = round(time.monotonic() - started, 3)
            if process is not None:
                record.update(exitCode=process.returncode, stopReason='owned test server stopped in finally')
                if process.stdout:
                    process.stdout.close()
            if log.exists():
                record['logSha256'] = sha256(log)
            self.save()
        return outcome

    def deliver(self, project, label, marker):
        current = read_json(project / 'current-build.json')
        build = project / current['path']
        metadata = read_json(build / 'build.json')
        entry = {'project': self.relative(project), 'build': metadata,
                 'buildManifestSha256': sha256(build / 'integrity.json')}
        self.report['projects'][label] = entry
        browser_path = None
        if self.browser:
            browser_path = self.browser_report(project, label, metadata['buildId'])
            entry['browser'] = {'status': 'passed', 'report': self.relative(browser_path),
                                'sha256': sha256(browser_path)}
        else:
            entry['browser'] = {'status': 'not-requested'}
        archive = self.output / 'packages' / (label + '-playable.zip')
        arguments = ['package', project, '--output', archive]
        if browser_path is not None:
            arguments += ['--browser-report', browser_path]
        self.cli(label + '-package', *arguments)
        entry['package'] = {'file': self.relative(archive), 'sha256': sha256(archive)}
        extracted, privacy = self.unpack(archive, label, marker)
        entry['privacy'] = privacy
        validation = read_json(extracted / 'validation.json')
        require(validation.get('passed') is True and validation.get('buildId') == metadata['buildId']
                and validation.get('planHash') == metadata['planHash'],
                'Packaged validation report does not match the selected build')
        entry['packagedValidationSha256'] = sha256(extracted / 'validation.json')
        if browser_path is not None:
            require(sha256(extracted / 'browser-report.json') == sha256(browser_path),
                    'Packaged browser report differs from the supplied report')
        entry['standalone'] = self.standalone(extracted, label, metadata)
        self.save()

    def execute(self):
        self.source_identity()
        self.unit_tests()
        projects = self.output / 'projects'
        pearl = projects / 'pearl'
        self.run('pearl-quickstart', [sys.executable, ROOT / 'scripts/quickstart.py',
                                     '--project', pearl, '--build-only'])
        fixture = ROOT / 'templates/external-user-game.json'
        answers = ROOT / 'templates/external-user-answers.json'
        plan = read_json(fixture)
        require(plan.get('project', {}).get('id') == 'external-user-game'
                and 'synthetic' in plan.get('provenance', {}).get('basis', '').lower(),
                'External-user template must remain an explicitly synthetic fixture')
        marker = ('HARNESS_PRIVATE_SENTINEL_' + uuid.uuid4().hex).encode('ascii')
        source_dir = self.output / 'private-test-inputs'
        source_dir.mkdir()
        sentinel = source_dir / 'private-sentinel.txt'
        sentinel.write_bytes(marker + b'\n')
        self.report['syntheticAuthorization'] = {
            'scope': 'Only this bundled synthetic test fixture; no real-user planning approval',
            'fixtureSha256': sha256(fixture), 'answersSha256': sha256(answers),
            'privateSentinelSha256': sha256(sentinel),
        }
        synthetic = projects / 'external-user'
        self.cli('synthetic-init', 'init', synthetic)
        self.cli('synthetic-ingest', 'ingest', synthetic, fixture, sentinel)
        self.cli('synthetic-questions', 'interrogate', synthetic)
        self.cli('synthetic-answers', 'interrogate', synthetic, '--answers', answers)
        self.cli('synthetic-plan', 'plan', synthetic, '--input', fixture)
        review = read_json(synthetic / 'planning-review.json')
        self.report['syntheticAuthorization']['reviewedPlanHash'] = review['planHash']
        self.cli('synthetic-fixture-approval', 'approve', synthetic, '--accept')
        self.cli('synthetic-build', 'build', synthetic)
        self.cli('synthetic-validate', 'validate', synthetic, '--build')
        self.deliver(pearl, 'pearl', marker)
        self.deliver(synthetic, 'external-user', marker)
        # A separate authored fixture verifies imported material changes and wall
        # occlusion without approving or modifying any real-user planning pack.
        effects = projects / 'interaction-effects'
        self.cli('effects-init', 'init', effects)
        self.run('effects-fixture-inputs', [sys.executable, ROOT / 'tests/make_interaction_fixture.py', effects])
        effect_plan = effects / 'fixture-plan.json'
        self.cli('effects-ingest', 'ingest', effects, effect_plan, effects / 'interaction-fixture.glb', sentinel)
        self.cli('effects-answers', 'interrogate', effects, '--answers', answers)
        self.cli('effects-plan', 'plan', effects, '--input', effect_plan)
        self.report['interactionFixtureAuthorization'] = {
            'scope': 'Only generated synthetic geometry; no real apartment acceptance',
            'generatorSha256': sha256(ROOT / 'tests/make_interaction_fixture.py'),
            'fixtureSha256': sha256(effect_plan),
            'reviewedPlanHash': read_json(effects / 'planning-review.json')['planHash'],
        }
        self.cli('effects-fixture-approval', 'approve', effects, '--accept')
        self.cli('effects-build', 'build', effects)
        self.cli('effects-validate', 'validate', effects, '--build')
        self.deliver(effects, 'interaction-effects', marker)
        final_files = source_files()
        initial_files = self.report['source']['files']
        changed = sorted(name for name in set(final_files) | set(initial_files)
                         if final_files.get(name) != initial_files.get(name))
        self.report['source']['changedDuringRun'] = changed
        require(not changed, 'Source files changed during verification; rerun on a stable checkout')
        self.report.update(passed=True, completedAt=utc_now(),
                           browserStatus='passed' if self.browser else 'not-requested')
        self.save()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', help='New or empty run directory (default: unique test-results/full-harness-* directory)')
    parser.add_argument('--node', default=os.environ.get('NODE_BIN', 'node'), help='Node 20+ executable')
    parser.add_argument('--browser', action='store_true',
                        help='Require automated browser checks for original and extracted builds; uses BROWSER_EXECUTABLE if set')
    args = parser.parse_args(argv)
    try:
        output = output_directory(args.output)
    except (OSError, RuntimeError) as error:
        parser.error(str(error))
    node = shutil.which(args.node) or args.node
    verification = Verification(output, node, args.browser)
    print(f'Whole-harness evidence: {output / "report.json"}', flush=True)
    try:
        verification.execute()
    except KeyboardInterrupt:
        verification.report.update(passed=False, error='Interrupted', completedAt=utc_now())
        verification.save()
        return 130
    except Exception as error:
        verification.report.update(passed=False, error=str(error), completedAt=utc_now())
        verification.save()
        print(f'FAILED: {error}\nEvidence: {output / "report.json"}', file=sys.stderr)
        return 1
    print(f'PASS for requested scope. Evidence: {output / "report.json"}', flush=True)
    if not args.browser:
        print('Browser checks were not requested; use --browser to require them.', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
