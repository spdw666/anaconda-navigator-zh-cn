"""JupyterLab locale regression and isolated native settings integration."""
import importlib.util
import json
import logging
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

import configure_jupyterlab as locale_config


class LocaleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.target = self.root / '@jupyterlab/translation-extension/plugin.jupyterlab-settings'
        fake = [types.SimpleNamespace(name='zh_CN')]
        self.points = patch.object(locale_config.metadata, 'entry_points', return_value=fake)
        self.points.start()
        self.addCleanup(self.points.stop)

    def test_new_locale_and_idempotency(self):
        self.assertTrue(locale_config.configure(self.root)['changed'])
        self.assertEqual(json.loads(self.target.read_text())['locale'], 'zh_CN')
        before = self.target.read_bytes()
        self.assertFalse(locale_config.configure(self.root)['changed'])
        self.assertEqual(self.target.read_bytes(), before)

    def test_json5_other_settings_and_original_backup(self):
        self.target.parent.mkdir(parents=True)
        original = b'{// comment\n"locale": "en", "displayStringsPrefix": true,}\n'
        self.target.write_bytes(original)
        locale_config.configure(self.root)
        self.assertTrue(json.loads(self.target.read_text())['displayStringsPrefix'])
        self.assertEqual(self.target.with_name(self.target.name + '.bak_zhcn').read_bytes(), original)

    def test_dry_run_and_invalid_locale_do_not_write(self):
        self.assertTrue(locale_config.configure(self.root, dry_run=True)['changed'])
        self.assertFalse(self.target.exists())
        with self.assertRaises(ValueError):
            locale_config.configure(self.root, 'not-installed')
        self.assertFalse(self.target.exists())

    def test_bad_json_leaves_original_untouched(self):
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(b'{malformed')
        with self.assertRaises(ValueError):
            locale_config.configure(self.root)
        self.assertEqual(self.target.read_bytes(), b'{malformed')

    def test_remove_only_legacy_key_and_keep_backup(self):
        legacy = self.root / 'jupyter_config.json'
        original = b'{"Language":"zh_CN","ServerApp":{"port":8899}}'
        legacy.write_bytes(original)
        self.assertTrue(locale_config.configure(self.root, legacy_config=legacy)['legacy_language_removed'])
        self.assertEqual(json.loads(legacy.read_text()), {'ServerApp': {'port': 8899}})
        self.assertEqual(legacy.with_name(legacy.name + '.bak_zhcn').read_bytes(), original)

    def test_atomic_replace_failure_keeps_target(self):
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(b'{"locale":"en"}')
        with patch.object(locale_config.os, 'replace', side_effect=OSError('injected')):
            with self.assertRaises(OSError):
                locale_config.configure(self.root)
        self.assertEqual(self.target.read_bytes(), b'{"locale":"en"}')
        self.assertEqual(list(self.target.parent.glob('*.tmp')), [])

    @unittest.skipUnless(importlib.util.find_spec('jupyterlab_server'), 'Requires JupyterLab server')
    def test_native_resolver_uses_plugin_setting_not_top_level_language(self):
        import sys
        import jupyterlab_server.settings_utils as settings
        schemas = Path(sys.prefix) / 'share/jupyter/lab/schemas'
        self.assertTrue(schemas.is_dir(), 'Installed JupyterLab schemas required')
        app = self.root / 'app'; app.mkdir()
        user = self.root / 'user'; user.mkdir()
        obj = types.SimpleNamespace(app_settings_dir=str(app), schemas_dir=str(schemas),
                                    settings_dir=str(user), overrides={}, labextensions_path=[],
                                    log=logging.getLogger('locale-tests'))
        (self.root / 'jupyter_config.json').write_text('{"Language":"zh_CN"}')
        with patch.object(settings, 'SYS_LOCALE', 'en_US'):
            self.assertEqual(settings.SchemaHandler.get_current_locale(obj), 'en_US')
            locale_config.configure(user)
            self.assertEqual(settings.SchemaHandler.get_current_locale(obj), 'zh_CN')


if __name__ == '__main__':
    unittest.main()
