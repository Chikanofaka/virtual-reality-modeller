"""Delivery evidence must describe the exact package and preserve its limits."""
import contextlib
import copy
import io
import json
import pathlib
import sys
import tempfile
import unittest
import zipfile
from unittest import mock

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import harness as h


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.base=pathlib.Path(self.tmp.name)
        self.p=self.base/'project'
        self.call('init',self.p)
        h.write(self.p/'planning.json',h.read(ROOT/'templates/measured-studio.json'))
        self.call('interrogate',self.p,'--answers',ROOT/'templates/answers.example.json')

    def tearDown(self):
        self.tmp.cleanup()

    def call(self,*args,expected=0):
        out=io.StringIO();err=io.StringIO()
        with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
            result=h.main([str(a) for a in args])
        self.assertEqual(result,expected,err.getvalue())
        return out.getvalue(),err.getvalue()

    def build(self):
        self.call('plan',self.p)
        self.call('approve',self.p,'--accept')
        self.call('build',self.p)
        return h.current_build(self.p)

    def browser_report(self,dest):
        meta=h.read(dest/'build.json')
        return {'passed':True,'browser':'chromium','browserVersion':'test-fixture',
                'buildId':meta['buildId'],'planHash':meta['planHash'],
                'checks':[{'check':'fixture check, not a browser execution','passed':True}],
                'errors':[],'externalRequests':[],
                'final':{'buildId':meta['buildId'],'errors':[]}}

    def test_validation_distinguishes_planning_from_exact_build(self):
        config=h.read(self.p/'planning.json');config['runtime']['browsers']=['chrome']
        h.write(self.p/'planning.json',config)
        self.call('validate',self.p)
        planning=h.read(self.p/'validation.json')
        self.assertEqual(planning['scope'],'planning-only')
        self.assertIsNone(planning['buildId'])
        self.assertEqual(planning['planHash'],h.plan_hash(self.p))
        self.assertEqual(planning['targetBrowsers'],['chrome'])
        dest=self.build()
        self.call('validate',self.p,'--build')
        report=h.read(self.p/'validation.json');meta=h.read(dest/'build.json')
        self.assertEqual(report['scope'],'planning-and-build')
        self.assertEqual(report['evidenceType'],'structural')
        self.assertEqual(report['targetBrowsers'],['chrome'])
        self.assertIn('declared target browsers',report['browserAcceptance'])
        self.assertNotIn('Safari',report['browserAcceptance'])
        for key in ('buildId','planHash'):self.assertEqual(report[key],meta[key])
        self.assertIn('build',report['result'])
        self.assertEqual(report['automatedBrowserEvidence']['status'],'not-supplied')
        self.assertIn('unverified',report['browserAcceptance'])

    def test_package_regenerates_evidence_and_excludes_private_uploads(self):
        private=self.base/'PRIVATE-survey.txt'
        secret=b'PRIVATE SURVEY CONTENT must never be copied into a playable'
        private.write_bytes(secret)
        self.call('ingest',self.p,private)
        dest=self.build();meta=h.read(dest/'build.json')
        h.write(self.p/'validation.json',{'passed':True,'buildId':'stale',
                                         'browserAcceptance':'incorrect stale acceptance'})
        output=self.base/'playable.zip'
        self.call('package',self.p,'--output',output)
        with zipfile.ZipFile(output) as archive:
            report=json.loads(archive.read('validation.json'))
            self.assertNotIn('browser-report.json',archive.namelist())
            self.assertIn('runtime/integrity.json',archive.namelist())
            for key in ('buildId','planHash'):self.assertEqual(report[key],meta[key])
            self.assertTrue(report['passed'])
            self.assertEqual(report['evidenceType'],'structural')
            self.assertEqual(report['targetBrowsers'],h.read(dest/'config.json')['runtime']['browsers'])
            self.assertIn('unverified',report['browserAcceptance'])
            self.assertFalse(any('uploads' in name or 'PRIVATE' in name for name in archive.namelist()))
            for name in archive.namelist():self.assertNotIn(secret,archive.read(name))
        # Report generation is outside the immutable runtime.
        h.verify_build(dest)

    def test_explicit_browser_report_retains_identity_and_limited_claim(self):
        dest=self.build();source=self.base/'browser.json'
        h.write(source,self.browser_report(dest))
        output=self.base/'with-browser.zip'
        self.call('package',self.p,'--output',output,'--browser-report',source)
        with zipfile.ZipFile(output) as archive:
            self.assertEqual(archive.read('browser-report.json'),source.read_bytes())
            report=json.loads(archive.read('validation.json'))
            supplied=report['automatedBrowserEvidence']
            self.assertEqual(supplied['status'],'supplied')
            self.assertEqual(supplied['evidenceType'],'supplied-automated-browser-report')
            self.assertEqual(supplied['sha256'],h.sha(source))
            self.assertEqual(supplied['buildId'],report['buildId'])
            self.assertTrue(supplied['planHashPresent'])
            self.assertTrue(any('not rerun' in item for item in supplied['limitations']))
            self.assertIn('unverified',report['browserAcceptance'])

    def test_browser_report_without_plan_hash_is_explicitly_identified(self):
        dest=self.build();report=self.browser_report(dest);del report['planHash']
        path=self.base/'legacy-browser.json';h.write(path,report)
        _,evidence=h.supplied_browser_evidence(path,h.structural_validation(self.p,dest))
        self.assertFalse(evidence['planHashPresent'])
        self.assertEqual(evidence['status'],'supplied')

    def test_stale_or_contradictory_browser_reports_cannot_be_packaged(self):
        dest=self.build();valid=self.browser_report(dest)
        variants=[{'buildId':'stale'}, {'planHash':'stale'}, {'passed':False},
                  {'checks':[]}, {'checks':[{'check':'failed','passed':False}]},
                  {'checks':['invalid']}, {'errors':['runtime error']},
                  {'externalRequests':['https://example.invalid']},
                  {'final':{'buildId':'stale'}}, {'final':{'errors':['runtime error']}}]
        path=self.base/'report.json'
        for index,patch in enumerate(variants):
            with self.subTest(patch=patch):
                candidate=copy.deepcopy(valid);candidate.update(patch);h.write(path,candidate)
                output=self.base/f'rejected-{index}.zip'
                self.call('package',self.p,'--output',output,'--browser-report',path,expected=2)
                self.assertFalse(output.exists())

    def test_changed_plan_rejects_validation_and_package(self):
        self.build()
        plan=h.read(self.p/'planning.json');plan['runtime']['speed']+=.1
        h.write(self.p/'planning.json',plan)
        self.call('validate',self.p,'--build',expected=2)
        output=self.base/'stale.zip'
        self.call('package',self.p,'--output',output,expected=2)
        self.assertFalse(output.exists())

    def test_tampered_build_rejects_validation_and_package(self):
        dest=self.build();(dest/'index.html').write_text('tampered',encoding='utf-8')
        self.call('validate',self.p,'--build',expected=2)
        output=self.base/'tampered.zip'
        self.call('package',self.p,'--output',output,expected=2)
        self.assertFalse(output.exists())

    def test_packaging_cannot_mutate_immutable_build(self):
        dest=self.build();output=dest/'playable.zip'
        _,error=self.call('package',self.p,'--output',output,expected=2)
        self.assertIn('outside the immutable build',error)
        self.assertFalse(output.exists())
        h.verify_build(dest)

    def test_package_cannot_overwrite_existing_project_input(self):
        self.build();output=self.p/'planning.json';before=output.read_bytes()
        _,error=self.call('package',self.p,'--output',output,expected=2)
        self.assertIn('Output exists',error)
        self.assertEqual(output.read_bytes(),before)

    def test_build_edit_during_packaging_cannot_publish_passing_report(self):
        dest=self.build();output=self.base/'race.zip';original=zipfile.ZipFile.write
        def changing_write(archive,filename,*args,**kwargs):
            if pathlib.Path(filename)==dest/'index.html':
                pathlib.Path(filename).write_text('edited while packaging',encoding='utf-8')
            return original(archive,filename,*args,**kwargs)
        with mock.patch.object(zipfile.ZipFile,'write',changing_write):
            _,error=self.call('package',self.p,'--output',output,expected=2)
        self.assertIn('package integrity verification failed',error)
        self.assertFalse(output.exists())
        self.assertEqual(list(self.base.glob('.playable-*')),[])

    def test_atomic_package_publish_never_overwrites_concurrent_output(self):
        self.build();output=self.base/'race.zip';original=h.inspect_zip
        def create_competing_output(path):
            inventory=original(path);output.write_bytes(b'Created by another task')
            return inventory
        with mock.patch.object(h,'inspect_zip',create_competing_output):
            self.call('package',self.p,'--output',output,expected=2)
        self.assertEqual(output.read_bytes(),b'Created by another task')
        self.assertEqual(list(self.base.glob('.playable-*')),[])


if __name__=='__main__':unittest.main()
