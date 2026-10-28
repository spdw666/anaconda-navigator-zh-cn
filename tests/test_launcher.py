# -*- coding: utf-8 -*-
"""Launcher and checkout selection tests run with stub main(), never a GUI."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LauncherTests(unittest.TestCase):
    def run_launcher(self, *, fail_patch=False, streams='normal', executable=None):
        with tempfile.TemporaryDirectory(prefix='zh-launch-', dir=str(ROOT.parent)) as tmp:
            output = Path(tmp) / 'result.json'
            script = textwrap.dedent('''
                import json, pathlib, runpy, sys, types
                original_stderr, original_dunder_stderr = sys.stderr, sys.__stderr__
                result = {'apply': 0, 'uninstall': 0, 'main': 0,
                          'original_stderr_none': sys.stderr is None}
                engine = types.ModuleType('zhcn_boot')
                def apply():
                    result['apply'] += 1
                    if FAIL_PATCH:
                        raise RuntimeError('injected patch failure')
                def uninstall():
                    result['uninstall'] += 1
                engine.apply = apply
                engine.uninstall = uninstall
                sys.modules['zhcn_boot'] = engine
                entry = types.ModuleType('anaconda_navigator.app.main')
                def main():
                    result['main'] += 1
                    return 0
                entry.main = main
                sys.modules['anaconda_navigator.app.main'] = entry
                if STREAMS == 'none':
                    sys.stderr = sys.__stderr__ = None
                elif STREAMS == 'broken':
                    class BrokenStream:
                        def write(self, value):
                            raise OSError('injected closed diagnostic stream')
                    sys.stderr = sys.__stderr__ = BrokenStream()
                try:
                    runpy.run_path(str(ROOT / 'launch_zh.py'), run_name='__main__')
                    result['status'] = 'returned'
                except SystemExit as exc:
                    result['status'] = 'SystemExit'
                    result['exit_code'] = exc.code
                except BaseException as exc:
                    result['status'] = type(exc).__name__ + ': ' + str(exc)
                sys.stderr, sys.__stderr__ = original_stderr, original_dunder_stderr
                OUTPUT.write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
            ''')
            config = ('import pathlib\nROOT=pathlib.Path(' + repr(str(ROOT)) + ')\n'
                      'OUTPUT=pathlib.Path(' + repr(str(output)) + ')\n'
                      'FAIL_PATCH=' + repr(fail_patch) + '\nSTREAMS=' + repr(streams) + '\n')
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            options = {} if executable is not None else {'capture_output': True}
            process = subprocess.run([str(executable or sys.executable), '-c', config + script],
                                     env=env, cwd=tmp, timeout=30, **options)
            self.assertEqual(process.returncode, 0, (process.stderr or b'').decode('utf-8', errors='replace'))
            self.assertTrue(output.is_file(), 'Launcher child did not produce its result file')
            result = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(result['status'], 'SystemExit', result)
            self.assertEqual(result['exit_code'], 0, result)
            self.assertEqual(result['main'], 1, result)
            self.assertEqual(result['apply'], 1, result)
            self.assertEqual(result['uninstall'], int(fail_patch), result)
            return result

    def test_success_calls_official_main(self):
        self.run_launcher()

    def test_patch_failure_calls_english_main(self):
        self.run_launcher(fail_patch=True)

    def test_missing_stderr_does_not_break_fallback(self):
        self.run_launcher(fail_patch=True, streams='none')

    def test_broken_diagnostic_stream_does_not_break_fallback(self):
        self.run_launcher(fail_patch=True, streams='broken')

    @unittest.skipUnless(os.name == 'nt', 'pythonw is Windows-specific')
    def test_actual_pythonw_fallback(self):
        pythonw = Path(sys.executable).with_name('pythonw.exe')
        if not pythonw.is_file():
            self.skipTest('The selected Python installation has no pythonw.exe')
        result = self.run_launcher(fail_patch=True, executable=pythonw)
        self.assertTrue(result['original_stderr_none'], result)

    def test_verifier_uses_checkout_from_unrelated_working_directory(self):
        with tempfile.TemporaryDirectory(prefix='zh-path-', dir=str(ROOT.parent)) as tmp:
            shadow = Path(tmp) / 'shadow'
            shadow.mkdir()
            (shadow / 'zhcn_boot.py').write_text("raise RuntimeError('wrong shadow engine')\n", encoding='utf-8')
            env = os.environ.copy()
            env['PYTHONPATH'] = str(shadow)
            env['PYTHONIOENCODING'] = 'utf-8'
            process = subprocess.run([sys.executable, str(ROOT / '_verify_patch.py'), '--engine-info'],
                                     cwd=tmp, env=env, capture_output=True, text=True,
                                     encoding='utf-8', timeout=30)
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
            engine = ROOT / 'zhcn_boot.py'
            self.assertIn('ENGINE_PATH=' + str(engine), process.stdout)
            self.assertIn('ENGINE_SHA256=' + hashlib.sha256(engine.read_bytes()).hexdigest(), process.stdout)

    def test_verifier_marks_skipped_suite_incomplete(self):
        with tempfile.TemporaryDirectory(prefix='zh-incomplete-', dir=str(ROOT.parent)) as tmp:
            checkout = Path(tmp)
            (checkout / '_verify_patch.py').write_bytes((ROOT / '_verify_patch.py').read_bytes())
            (checkout / 'zhcn_boot.py').write_text('# local engine fixture\n', encoding='utf-8')
            tests = checkout / 'tests'
            tests.mkdir()
            (tests / '__init__.py').write_text('', encoding='utf-8')
            (tests / 'test_missing_dependency.py').write_text(
                "import unittest\nclass MissingDependency(unittest.TestCase):\n"
                "    @unittest.skip('injected missing dependency')\n"
                "    def test_incomplete(self): pass\n", encoding='utf-8')
            process = subprocess.run([sys.executable, str(checkout / '_verify_patch.py')],
                                     cwd=tmp, capture_output=True, text=True,
                                     encoding='utf-8', timeout=30)
            self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
            self.assertIn('INCOMPLETE: 1 TESTS SKIPPED', process.stdout)
            self.assertNotIn('ALL 1 TESTS PASSED', process.stdout)


if __name__ == '__main__':
    unittest.main()
