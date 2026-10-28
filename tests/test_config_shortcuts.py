"""Isolated config/Windows shortcut regressions. No real user settings are touched."""
from __future__ import annotations

import codecs
import configparser
import contextlib
import ctypes
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fix_pycharm_under_test', REPO / 'fix_pycharm.py')
fix = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fix)


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='config-regression-', dir=REPO.parent)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'PyCharm with spaces'
        (self.root / 'bin').mkdir(parents=True)
        (self.root / 'bin' / 'pycharm64.exe').write_bytes(b'fixture executable; never launched')
        (self.root / 'product-info.json').write_text(json.dumps({'productCode': 'PY', 'version': '2025.3'}), encoding='utf-8')
        self.conf = self.base / 'anaconda-navigator.ini'
        self.key = 'pycharm_pro_path'
        self.patch = mock.patch.object(fix, 'CONF', self.conf)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def write(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return fix.write_config(self.key, self.root)

    def value(self):
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(self.conf, encoding='utf-8-sig')
        return parser.get('applications', self.key)

    def test_exact_section_crlf_backup_and_idempotence(self):
        original = b'[main]\r\nkeep = 100%\r\n[applications]\r\npycharm_pro_path = OLD\r\n[other]\r\npycharm_pro_path = DO_NOT_CHANGE\r\n'
        self.conf.write_bytes(original)
        self.assertTrue(self.write())
        self.assertEqual(self.conf.read_bytes(), original.replace(b'pycharm_pro_path = OLD', f'{self.key} = {self.root}'.encode()))
        backup = self.conf.with_suffix('.ini.bak_fix_pycharm')
        self.assertEqual(backup.read_bytes(), original)
        changed = self.conf.read_bytes()
        stamp = self.conf.stat().st_mtime_ns
        self.assertFalse(self.write())
        self.assertEqual(self.conf.read_bytes(), changed)
        self.assertEqual(self.conf.stat().st_mtime_ns, stamp)
        self.assertEqual(backup.read_bytes(), original)

    def test_missing_section_does_not_change_other_section(self):
        original = b'[other]\npycharm_pro_path = KEEP\n'
        self.conf.write_bytes(original)
        self.assertTrue(self.write())
        self.assertTrue(self.conf.read_bytes().startswith(original))
        self.assertEqual(self.value(), str(self.root))

    def test_missing_key_added_inside_applications(self):
        self.conf.write_bytes(b'[applications]\nvscode_path = KEEP\n[other]\npycharm_pro_path = KEEP_TOO\n')
        self.assertTrue(self.write())
        self.assertEqual(self.value(), str(self.root))
        self.assertIn(b'[other]\npycharm_pro_path = KEEP_TOO\n', self.conf.read_bytes())

    def test_duplicate_key_even_when_first_matches_is_rejected(self):
        raw = f'[applications]\n{self.key} = {self.root}\n{self.key} = OTHER\n'.encode()
        self.conf.write_bytes(raw)
        with self.assertRaises(SystemExit):
            self.write()
        self.assertEqual(self.conf.read_bytes(), raw)
        self.assertFalse(self.conf.with_suffix('.ini.bak_fix_pycharm').exists())

    def test_duplicate_section_rejected(self):
        raw = b'[applications]\npycharm_pro_path = OLD\n[applications]\nx = y\n'
        self.conf.write_bytes(raw)
        with self.assertRaises(SystemExit):
            self.write()
        self.assertEqual(self.conf.read_bytes(), raw)

    def test_unrelated_duplicate_is_checked_before_idempotence(self):
        raw = f'[applications]\n{self.key} = {self.root}\n[other]\nx=1\nx=2\n'.encode()
        self.conf.write_bytes(raw)
        with self.assertRaises(SystemExit):
            self.write()
        self.assertEqual(self.conf.read_bytes(), raw)

    def test_bom_mixed_newlines_and_equal_spacing_preserved(self):
        original = codecs.BOM_UTF8 + b'[main]\r\nx = 1\n[applications]\r\npycharm_pro_path=OLD\n[other]\r\ny = 2'
        self.conf.write_bytes(original)
        self.assertTrue(self.write())
        self.assertEqual(self.conf.read_bytes(), original.replace(b'pycharm_pro_path=OLD', f'{self.key} = {self.root}'.encode()))

    def test_existing_backup_not_overwritten(self):
        self.conf.write_bytes(b'[applications]\npycharm_pro_path = OLD\n')
        backup = self.conf.with_suffix('.ini.bak_fix_pycharm')
        backup.write_bytes(b'FIRST ORIGINAL')
        self.assertTrue(self.write())
        self.assertEqual(backup.read_bytes(), b'FIRST ORIGINAL')

    def test_relative_explicit_is_resolved(self):
        previous = Path(os.getcwd())
        try:
            os.chdir(self.base)
            self.assertEqual(fix.find_pycharm(self.root.name), self.root.resolve())
        finally:
            os.chdir(previous)

    def test_explicit_missing_executable_rejected(self):
        (self.root / 'bin' / 'pycharm64.exe').unlink()
        with self.assertRaises(SystemExit):
            fix.find_pycharm(str(self.root))

    def test_default_inheritance_still_adds_local_applications_key(self):
        self.conf.write_text(f'[DEFAULT]\n{self.key} = {self.root}\n[applications]\nvscode_path = KEEP\n', encoding='utf-8')
        self.assertTrue(self.write())
        self.assertIn(f'[applications]\nvscode_path = KEEP\n{self.key} = {self.root}\n', self.conf.read_text(encoding='utf-8'))

    def test_explicit_invalid_metadata_rejected(self):
        for content in ('{}', '{bad', '{"productCode":"PY","version":""}', '{"productCode":"DS","version":"1"}'):
            with self.subTest(content=content):
                (self.root / 'product-info.json').write_text(content, encoding='utf-8')
                with self.assertRaises(SystemExit):
                    fix.find_pycharm(str(self.root))

    def test_mismatched_key_rejected(self):
        self.conf.write_bytes(b'[applications]\npycharm_ce_path = OLD\n')
        with self.assertRaises(SystemExit):
            fix.write_config('pycharm_ce_path', self.root)
        self.assertEqual(self.conf.read_bytes(), b'[applications]\npycharm_ce_path = OLD\n')

    def test_atomic_replace_failure_preserves_original_and_cleans_temp(self):
        original = b'[applications]\npycharm_pro_path = OLD\n'
        self.conf.write_bytes(original)
        with mock.patch.object(fix.os, 'replace', side_effect=PermissionError('fixture failure')):
            with self.assertRaises(PermissionError):
                self.write()
        self.assertEqual(self.conf.read_bytes(), original)
        self.assertEqual(self.conf.with_suffix('.ini.bak_fix_pycharm').read_bytes(), original)
        self.assertEqual(list(self.base.glob('*.tmp')), [])

    def test_concurrent_config_change_not_overwritten(self):
        self.conf.write_bytes(b'[applications]\npycharm_pro_path = OLD\n')
        concurrent = b'[applications]\npycharm_pro_path = OTHER_PROCESS\n'
        with mock.patch.object(fix.shutil, 'copymode', side_effect=lambda *args: self.conf.write_bytes(concurrent)):
            with self.assertRaises(SystemExit):
                self.write()
        self.assertEqual(self.conf.read_bytes(), concurrent)
        self.assertEqual(list(self.base.glob('*.tmp')), [])

    def test_missing_config_is_not_created(self):
        with self.assertRaises(SystemExit):
            self.write()
        self.assertFalse(self.conf.exists())

    def test_cli_config_override_and_nonzero_error(self):
        self.conf.write_bytes(b'[applications]\npycharm_pro_path = OLD\n')
        env = dict(os.environ, PYTHONIOENCODING='utf-8')
        args = [sys.executable, str(REPO / 'fix_pycharm.py'), str(self.root), '--config', str(self.conf)]
        result = subprocess.run(args, capture_output=True, encoding='utf-8', env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.value(), str(self.root))
        self.conf.write_bytes(b'not-an-ini')
        result = subprocess.run(args, capture_output=True, encoding='utf-8', env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.conf.read_bytes(), b'not-an-ini')


@unittest.skipUnless(os.name == 'nt' and shutil.which('powershell.exe'), 'Windows PowerShell/COM required')
class ShortcutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='shortcut-regression-', dir=REPO.parent)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'Anaconda with spaces'
        for relative in ('pythonw.exe', 'cwp.py', 'Scripts/anaconda-navigator-script.py', 'Menu/anaconda-navigator.ico'):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'fixture only; never executed')
        self.package = self.base / 'Chinese package with spaces'
        self.package.mkdir()
        for name in ('manage_shortcuts.ps1', 'launch_zh.py', 'zhcn_boot.py', 'nav_zh_dict.py', '安装汉化.cmd', '还原英文.cmd'):
            shutil.copy2(REPO / name, self.package / name)
        self.desktop = self.base / 'redirected desktop'
        self.menu = self.base / 'custom start menu'
        self.backup = self.package / 'shortcut_backup'

    def options(self, root=True):
        args = ['-DesktopDirectory', str(self.desktop), '-StartMenuDirectory', str(self.menu), '-NonInteractive']
        if root:
            args += ['-AnacondaRoot', str(self.root)]
        return args

    def run_manager(self, action, root=True, extra=(), ok=True):
        result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', str(self.package / 'manage_shortcuts.ps1'), '-Action', action] + self.options(root) + list(extra), capture_output=True, encoding='utf-8', errors='replace', timeout=30)
        if ok:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('SUCCESS ' + action, result.stdout)
            self.assertEqual(result.stdout.count('VERIFIED '), 2)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn('SUCCESS ', result.stdout)
        return result

    def paths(self):
        return [self.desktop / 'Anaconda Navigator.lnk', self.menu / 'Anaconda Navigator.lnk']

    def snapshots(self):
        env = dict(os.environ, ZH_TEST_DESKTOP=str(self.paths()[0]), ZH_TEST_MENU=str(self.paths()[1]))
        code = "[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false); $s=New-Object -ComObject WScript.Shell; $items=@(); foreach($p in @($env:ZH_TEST_DESKTOP,$env:ZH_TEST_MENU)) {$l=$s.CreateShortcut($p);$items+=@{TargetPath=$l.TargetPath;Arguments=$l.Arguments;WorkingDirectory=$l.WorkingDirectory;IconLocation=$l.IconLocation;Description=$l.Description;WindowStyle=$l.WindowStyle}}; ConvertTo-Json -InputObject $items -Compress"
        result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', code], env=env, capture_output=True, encoding='utf-8', timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_no_backup_install_restore_both_links_and_spaces(self):
        self.run_manager('Install')
        for snapshot in self.snapshots():
            self.assertEqual(snapshot['TargetPath'].lower(), str(self.root / 'pythonw.exe').lower())
            self.assertEqual(snapshot['Arguments'], ' '.join(f'"{path}"' for path in (self.root / 'cwp.py', self.root, self.root / 'pythonw.exe', self.package / 'launch_zh.py')))
        self.run_manager('Restore')
        for snapshot in self.snapshots():
            self.assertIn('anaconda-navigator-script.py', snapshot['Arguments'])
            self.assertNotIn('launch_zh.py', snapshot['Arguments'])

    def test_legacy_backups_restore_exact_bytes(self):
        self.run_manager('Restore')
        original = [p.read_bytes() for p in self.paths()]
        self.run_manager('Install')
        for label, data in zip(('desktop', 'startmenu'), original):
            self.assertEqual((self.backup / f'{label}_Anaconda Navigator.lnk').read_bytes(), data)
        self.run_manager('Restore')
        self.assertEqual([p.read_bytes() for p in self.paths()], original)

    def test_install_and_restore_are_idempotent(self):
        for action in ('Install', 'Restore'):
            self.run_manager(action)
            original = [(p.read_bytes(), p.stat().st_mtime_ns) for p in self.paths()]
            self.run_manager(action)
            self.assertEqual([(p.read_bytes(), p.stat().st_mtime_ns) for p in self.paths()], original)

    def test_moved_package_uses_current_directory_and_autodetects_root(self):
        self.run_manager('Restore')
        self.run_manager('Install')
        moved = self.base / 'moved Chinese package'
        self.package.rename(moved)
        self.package = moved
        self.backup = moved / 'shortcut_backup'
        self.run_manager('Install', root=False)
        for snapshot in self.snapshots():
            self.assertIn(str(moved / 'launch_zh.py'), snapshot['Arguments'])
        self.run_manager('Restore', root=False)
        for snapshot in self.snapshots():
            self.assertIn('anaconda-navigator-script.py', snapshot['Arguments'])

    def test_moved_anaconda_ignores_stale_backups(self):
        self.run_manager('Restore')
        self.run_manager('Install')
        moved = self.base / 'moved Anaconda'
        self.root.rename(moved)
        self.root = moved
        self.run_manager('Restore')
        for snapshot in self.snapshots():
            self.assertEqual(snapshot['TargetPath'].lower(), str(moved / 'pythonw.exe').lower())
            self.assertIn(str(moved / 'Scripts' / 'anaconda-navigator-script.py'), snapshot['Arguments'])

    def test_backup_with_missing_executable_uses_valid_generated_entry(self):
        self.run_manager('Restore')
        self.run_manager('Install')
        env = dict(os.environ, ZH_TEST_BACKUP=str(self.backup / 'desktop_Anaconda Navigator.lnk'), ZH_TEST_MISSING=str(self.root / 'Scripts' / 'anaconda-navigator.exe'))
        code = '$s=New-Object -ComObject WScript.Shell; $l=$s.CreateShortcut($env:ZH_TEST_BACKUP); $l.TargetPath=$env:ZH_TEST_MISSING; $l.Save()'
        result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', code], env=env, capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.run_manager('Restore')
        for snapshot in self.snapshots():
            self.assertEqual(snapshot['TargetPath'].lower(), str(self.root / 'pythonw.exe').lower())
            self.assertIn('anaconda-navigator-script.py', snapshot['Arguments'])

    def test_invalid_root_fails_without_changing_links(self):
        self.run_manager('Install')
        original = [p.read_bytes() for p in self.paths()]
        (self.root / 'Menu' / 'anaconda-navigator.ico').unlink()
        self.run_manager('Restore', ok=False)
        self.assertEqual([p.read_bytes() for p in self.paths()], original)

    def test_stage_failure_leaves_originals_unchanged(self):
        self.run_manager('Restore')
        paths = self.paths()
        original = [p.read_bytes() for p in paths]
        blocked = self.base / 'blocked directory'
        blocked.write_bytes(b'not a directory')
        self.menu = blocked
        self.run_manager('Install', ok=False)
        self.assertEqual([p.read_bytes() for p in paths], original)
        self.assertEqual(list(self.desktop.glob('.anaconda-zh-*.lnk')), [])

    def test_missing_autodetected_root_is_nonzero(self):
        self.run_manager('Install', root=False, ok=False)
        self.assertFalse(self.desktop.exists())
        self.assertFalse(self.menu.exists())

    def test_commit_failure_rolls_back_first_shortcut(self):
        self.run_manager('Restore')
        paths = self.paths()
        original = [p.read_bytes() for p in paths]
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
        kernel.CreateFileW.restype = ctypes.c_void_p
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        # Readable but not replaceable: staging succeeds, second commit fails.
        handle = kernel.CreateFileW(str(paths[1]), 0x80000000, 1, None, 3, 0, None)
        self.assertNotEqual(handle, ctypes.c_void_p(-1).value)
        try:
            result = self.run_manager('Install', ok=False)
            self.assertNotIn('ROLLBACK ERROR', result.stderr)
        finally:
            kernel.CloseHandle(handle)
        self.assertEqual([p.read_bytes() for p in paths], original)
        self.assertEqual(list(self.desktop.glob('.anaconda-zh-*.lnk')), [])
        self.assertEqual(list(self.menu.glob('.anaconda-zh-*.lnk')), [])

    def test_custom_backup_directory(self):
        self.run_manager('Restore')
        original = [p.read_bytes() for p in self.paths()]
        custom = self.base / 'custom backup with spaces'
        self.run_manager('Install', extra=('-BackupDirectory', str(custom)))
        self.assertTrue((custom / 'desktop_Anaconda Navigator.lnk').exists())
        self.assertFalse(self.backup.exists())
        self.run_manager('Restore', extra=('-BackupDirectory', str(custom)))
        self.assertEqual([p.read_bytes() for p in self.paths()], original)

    def test_cmd_wrappers_forward_parameters_and_failures(self):
        for wrapper, action in (('安装汉化.cmd', 'Install'), ('还原英文.cmd', 'Restore')):
            command = 'cmd.exe /d /s /c "' + subprocess.list2cmdline([str(self.package / wrapper)] + self.options()) + '"'
            result = subprocess.run(command, capture_output=True, encoding='utf-8', errors='replace', timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('SUCCESS ' + action, result.stdout)
        (self.root / 'cwp.py').unlink()
        command = 'cmd.exe /d /s /c "' + subprocess.list2cmdline([str(self.package / '还原英文.cmd')] + self.options()) + '"'
        result = subprocess.run(command, capture_output=True, encoding='utf-8', errors='replace', timeout=30)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('SUCCESS ', result.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
