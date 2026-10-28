"""UI model/presentation/filter localization must preserve operational values."""
import hashlib
import json
from pathlib import Path
import unittest
from unittest import mock

from PySide6 import QtCore, QtGui, QtWidgets
import zhcn_boot as engine
import nav_content as content


class DisplayRoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def tearDown(self):
        engine.uninstall()

    def test_package_filter_paints_chinese_but_returns_original_keys(self):
        engine.apply()
        from anaconda_navigator.widgets.manager.packages import ComboBoxPackageFilter
        from anaconda_navigator.utils import constants as C
        combo = ComboBoxPackageFilter()
        combo.addItems(C.COMBOBOX_VALUES_ORDERED)
        combo.resize(220, 40); combo.show(); self.app.processEvents()
        combo.grab()
        self.assertEqual(combo.currentText(), 'Installed')
        self.assertEqual(combo.property('_zhcn_display_text'), '已安装')
        self.assertEqual(C.COMBOBOX_VALUES[combo.currentText()], C.INSTALLED)
        menu = QtWidgets.QMenu(combo)
        action = QtGui.QAction('Installed', menu)
        self.assertEqual(action.text(), '已安装')
        self.assertEqual(combo.itemText(0), 'Installed')
        combo.close()

    def test_package_model_translates_headers_and_tooltips_not_values(self):
        engine.apply()
        from anaconda_navigator.widgets.manager.model import CondaPackagesModel
        from anaconda_navigator.utils import constants as C
        row = [0] * len(C.COLUMNS)
        row[C.COL_NAME] = 'Home'; row[C.COL_VERSION] = '1.2'
        row[C.COL_DESCRIPTION] = 'Install'; row[C.COL_PACKAGE_TYPE] = C.CONDA_PACKAGE
        row[C.COL_ACTION] = C.ACTION_NONE; row[C.COL_STATUS] = C.INSTALLED
        model = CondaPackagesModel(None, {}, [row])
        self.assertEqual(model.headerData(C.COL_NAME, QtCore.Qt.Orientation.Horizontal), '名称')
        self.assertEqual(model.headerData(C.COL_DESCRIPTION, QtCore.Qt.Orientation.Horizontal), '描述')
        self.assertEqual(model.data(model.index(0, C.COL_NAME)), 'Home')
        self.assertEqual(model.data(model.index(0, C.COL_DESCRIPTION)), 'Install')
        self.assertEqual(model.data(model.index(0, C.COL_STATUS)), C.INSTALLED)
        tip = model.data(model.index(0, C.COL_PACKAGE_TYPE), QtCore.Qt.ItemDataRole.ToolTipRole)
        self.assertNotEqual(tip, 'Conda package')

    def test_instance_file_filter_display_and_selected_value_are_separate(self):
        engine.apply()
        dialog = QtWidgets.QFileDialog()
        dialog.setOption(QtWidgets.QFileDialog.Option.DontUseNativeDialog)
        original = 'Conda environment files (*.yaml *.yml)'
        dialog.setNameFilters([original, 'All files (*)'])
        self.assertIn('Conda 环境文件', dialog.nameFilters()[0])
        self.assertIn('*.yaml *.yml', dialog.nameFilters()[0])
        dialog.selectNameFilter(original)
        self.assertEqual(dialog.selectedNameFilter(), original)
        dialog.close()

    def test_static_file_filter_reverse_mapping_keeps_backup_extension_logic(self):
        engine.uninstall()
        captured = {}

        def fake(*args, **kwargs):
            captured.update(kwargs)
            return 'D:/fixture/environment', kwargs['filter'].split(';;')[0]

        original = 'Conda environment files (*.yaml *.yml)'
        with mock.patch.object(QtWidgets.QFileDialog, 'getSaveFileName', staticmethod(fake)):
            engine.apply()
            path, selected = QtWidgets.QFileDialog.getSaveFileName(
                caption='Backup Environment', dir='D:/fixture', filter=original + ';;All files (*)')
            self.assertEqual(path, 'D:/fixture/environment')
            self.assertEqual(selected, original)
            self.assertIn('Conda 环境文件', captured['filter'])
            self.assertEqual(captured['dir'], 'D:/fixture')
            engine.uninstall()

    def test_official_qt_catalog_is_pinned_and_used(self):
        manifest = json.loads((content.ROOT / 'assets/qttranslations/UPSTREAM.json').read_text())
        for name, row in manifest['files'].items():
            self.assertEqual(hashlib.sha256((content.ROOT / 'assets/qttranslations' / name).read_bytes()).hexdigest(), row['sha256'])
        self.assertGreater(len(content.qt_catalog()), 1700)
        engine.apply()
        result = QtCore.QCoreApplication.translate('QFileDialog', 'File &name:')
        self.assertIn('文件', result)
        self.assertEqual(QtCore.QCoreApplication.translate('QPlatformTheme', 'Cancel'), '取消')

    def test_rich_ui_keeps_unknown_data_and_link_attributes(self):
        engine.apply()
        unchanged = '<span style="font-size:16px">Home</span>'
        self.assertEqual(engine.tr(unchanged), unchanged)
        linked = '<p>See what has changed <a href="https://example.com/?x=Home">here</a>.</p>'
        result = engine.tr(linked)
        self.assertIn('查看变更', result)
        self.assertIn('https://example.com/?x=Home', result)

    def test_dynamic_messages_preserve_names_and_paths(self):
        self.assertEqual(engine.tr('Clone from environment: Home'), '克隆自环境：Home')
        self.assertEqual(engine.tr("Create new environment for 'numpy'"), '为“numpy”创建新环境')
        result = engine.tr('Environment file "demo.yaml" downloaded to D:\\data\\Home')
        self.assertIn('D:\\data\\Home', result)


if __name__ == '__main__':
    unittest.main()
