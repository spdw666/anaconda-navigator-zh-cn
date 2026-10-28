# -*- coding: utf-8 -*-
"""Qt regression tests: no desktop windows and no real Navigator configuration."""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['QT_API'] = 'pyside6'
try:
    from PySide6 import QtCore, QtGui, QtWidgets
except ImportError:
    QtCore = QtGui = QtWidgets = None
import zhcn_boot as engine


def isolated_python(code):
    """Navigator imports see only a temporary profile, never the user's config."""
    with tempfile.TemporaryDirectory(prefix='zh-qt-', dir=str(ROOT.parent)) as tmp:
        home = Path(tmp)
        (home / '.anaconda' / 'navigator').mkdir(parents=True)
        env = os.environ.copy()
        env.update({key: str(home) for key in ('HOME', 'APPDATA', 'USERPROFILE', 'LOCALAPPDATA')})
        env.update(QT_QPA_PLATFORM='offscreen', QT_API='pyside6', PYTHONIOENCODING='utf-8')
        prefix = Path(sys.executable).parent
        env['PATH'] = os.pathsep.join((str(prefix / 'Library' / 'bin'), str(prefix), env.get('PATH', '')))
        script = 'import sys\nsys.path.insert(0, ' + repr(str(ROOT)) + ')\n' + code
        result = subprocess.run([sys.executable, '-c', script], env=env, capture_output=True,
                                text=True, encoding='utf-8', timeout=60)
        if result.returncode:
            raise AssertionError('Isolated subprocess failed:\n' + result.stdout + result.stderr)
        return result.stdout


def qt_classes():
    names = ('QLabel', 'QAbstractButton', 'QWidget', 'QLineEdit', 'QTextEdit',
             'QTextBrowser', 'QPlainTextEdit', 'QGroupBox', 'QMessageBox',
             'QCheckBox', 'QRadioButton', 'QPushButton', 'QToolButton', 'QMenu',
             'QMenuBar', 'QStatusBar', 'QProgressBar', 'QTableWidget',
             'QTreeWidget', 'QTabWidget', 'QComboBox')
    return [getattr(QtWidgets, name) for name in names] + [QtGui.QAction, QtGui.QStandardItemModel]


def snapshot():
    return {cls: dict(vars(cls)) for cls in qt_classes()}


def typed_widget(name, base, module):
    return type(name, (base,), {'__module__': module})


@unittest.skipIf(QtWidgets is None, 'PySide6 is not installed')
class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def setUp(self):
        engine.uninstall()

    def tearDown(self):
        engine.uninstall()

    def test_checkout_identity(self):
        path = Path(engine.__file__).resolve()
        self.assertEqual(path, ROOT / 'zhcn_boot.py')
        self.assertEqual(len(hashlib.sha256(path.read_bytes()).hexdigest()), 64)

    def test_editable_contents_do_not_translate_collisions(self):
        engine.apply()
        for cls in (QtWidgets.QLineEdit, QtWidgets.QTextEdit, QtWidgets.QPlainTextEdit):
            for value in ('Home', 'on', 'Installed', 'All'):
                with self.subTest(widget=cls.__name__, value=value):
                    widget = cls()
                    if isinstance(widget, QtWidgets.QLineEdit):
                        widget.setText(value)
                        actual = widget.text()
                    elif isinstance(widget, QtWidgets.QPlainTextEdit):
                        widget.setPlainText(value)
                        actual = widget.toPlainText()
                    else:
                        widget.setText(value)
                        actual = widget.toPlainText()
                    self.assertEqual(actual, value)
            widget.setPlaceholderText('Search Packages')
            self.assertEqual(widget.placeholderText(), '搜索包')

    def test_native_environment_paste_stays_valid(self):
        spec = importlib.util.find_spec('anaconda_navigator')
        if spec is None:
            self.skipTest('Navigator integration dependency is not installed')
        source = Path(spec.origin).parent / 'widgets' / 'dialogs' / 'environment' / 'common.py'
        node = next(node for node in ast.parse(source.read_text(encoding='utf-8')).body
                    if isinstance(node, ast.ClassDef) and node.name == 'LineEditEnvironment')
        namespace = dict(QtWidgets=QtWidgets, QtGui=QtGui, QtCore=QtCore,
                         widgets=types.SimpleNamespace(LineEditBase=QtWidgets.QLineEdit))
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), 'exec'), namespace)
        engine.apply()
        widget = namespace['LineEditEnvironment']()
        previous = self.app.clipboard().text()
        try:
            self.app.clipboard().setText('Home')
            event = QtGui.QKeyEvent(QtCore.QEvent.Type.KeyPress, QtCore.Qt.Key.Key_V,
                                   QtCore.Qt.KeyboardModifier.ControlModifier)
            widget.keyPressEvent(event)
            self.assertEqual(widget.text(), 'Home')
            self.assertTrue(widget.hasAcceptableInput())
        finally:
            self.app.clipboard().setText(previous)

    def test_environment_comboboxes_keep_names_and_data(self):
        environment = typed_widget('ComboHomeEnvironment', QtWidgets.QComboBox,
                                   'anaconda_navigator.widgets.tabs.home')
        engine.apply()
        for cls in (QtWidgets.QComboBox, environment):
            combo = cls()
            for name in ('Home', 'on', 'Installed', 'All'):
                combo.addItem(name, '/envs/' + name)
            self.assertEqual([combo.itemText(i) for i in range(4)], ['Home', 'on', 'Installed', 'All'])
            self.assertEqual([combo.itemData(i) for i in range(4)], ['/envs/' + n for n in ('Home', 'on', 'Installed', 'All')])

    def test_real_navigator_environment_paste_stays_valid(self):
        if importlib.util.find_spec('anaconda_navigator') is None:
            self.skipTest('Navigator integration dependency is not installed')
        output = isolated_python('''
import json
import zhcn_boot
zhcn_boot.apply()
from PySide6 import QtCore, QtGui, QtWidgets
app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
from anaconda_navigator.widgets.dialogs.environment.common import LineEditEnvironment
from anaconda_navigator.config.base import get_conf_path
import os
assert get_conf_path().startswith(os.environ['HOME'])
widget = LineEditEnvironment()
app.clipboard().setText('Home')
event = QtGui.QKeyEvent(QtCore.QEvent.Type.KeyPress, QtCore.Qt.Key.Key_V,
                       QtCore.Qt.KeyboardModifier.ControlModifier)
widget.keyPressEvent(event)
print('REAL_PASTE=' + json.dumps({'text': widget.text(),
      'acceptable': widget.hasAcceptableInput()}, ensure_ascii=False))
''')
        result = json.loads(next(line.removeprefix('REAL_PASTE=') for line in output.splitlines()
                                 if line.startswith('REAL_PASTE=')))
        self.assertEqual(result, {'text': 'Home', 'acceptable': True})

    def test_application_filter_uses_explicit_pair_whitelist(self):
        filter_type = typed_widget('ComboHomeFilter', QtWidgets.QComboBox,
                                   'anaconda_navigator.widgets.tabs.home')
        unrelated = typed_widget('ComboHomeFilter', QtWidgets.QComboBox, 'unrelated.module')
        engine.apply()
        expected = [('All applications', 'all', '所有应用'),
                    ('Installed applications', 'installed', '已安装应用'),
                    ('Not installed applications', 'uninstalled', '未安装应用'),
                    ('Updatable applications', 'updatable', '可更新应用')]
        combo = filter_type()
        for text, data, translated in expected:
            combo.addItem(text, data)
            self.assertEqual(engine.tr_app_filter(text, data), translated)
        self.assertEqual([combo.itemText(i) for i in range(4)], [row[2] for row in expected])
        self.assertEqual([combo.itemData(i) for i in range(4)], [row[1] for row in expected])
        for cls in (QtWidgets.QComboBox, unrelated):
            other = cls(); other.addItem('All applications', 'all')
            self.assertEqual(other.itemText(0), 'All applications')
        combo.addItem('Home', 'all')
        combo.addItem('All applications', '/envs/Home')
        self.assertEqual(combo.itemText(4), 'Home')
        self.assertEqual(combo.itemText(5), 'All applications')

    def test_filter_programmatic_selection(self):
        cls = typed_widget('ComboHomeFilter', QtWidgets.QComboBox,
                           'anaconda_navigator.widgets.tabs.home')
        engine.apply()
        combo = cls()
        combo.addItem('All applications', 'all')
        combo.addItem('Installed applications', 'installed')
        combo.setCurrentText('Installed applications')
        self.assertEqual(combo.currentData(), 'installed')
        self.assertEqual(combo.currentText(), '已安装应用')
        environment = QtWidgets.QComboBox(); environment.addItem('Home', '/envs/Home')
        environment.setCurrentText('Home')
        self.assertEqual(environment.currentText(), 'Home')

    def test_real_navigator_filter_environment_and_popup(self):
        if importlib.util.find_spec('anaconda_navigator') is None:
            self.skipTest('Navigator integration dependency is not installed')
        output = isolated_python('''
import json
import zhcn_boot
zhcn_boot.apply()
from PySide6 import QtWidgets
app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
from anaconda_navigator.config.base import get_conf_path
from anaconda_navigator.widgets.tabs.home import ComboHomeFilter, ComboHomeEnvironment
from anaconda_navigator.widgets.lists.environments import ButtonEnvironmentName
filters = ComboHomeFilter()
filters.addItem('All applications', 'all')
filters.addItem('Installed applications', 'installed')
filters.setCurrentText('Installed applications')
environment = ComboHomeEnvironment()
environment.addItem('Home', '/envs/Home')
environment.addItem('on', '/envs/on')
environment.showPopup()
menus = environment.findChildren(QtWidgets.QMenu)
popup_text = [action.text() for action in menus[-1].actions()]
menus[-1].close()
button = ButtonEnvironmentName('Home')
button.setText('on')
result = {'filter_text': filters.currentText(), 'filter_data': filters.currentData(),
          'environment_text': [environment.itemText(i) for i in range(2)],
          'environment_data': [environment.itemData(i) for i in range(2)],
          'popup_text': popup_text, 'button_text': button.text()}
import os
assert get_conf_path().startswith(os.environ['HOME'])
print('NATIVE=' + json.dumps(result, ensure_ascii=False))
''')
        result = json.loads(next(line.removeprefix('NATIVE=') for line in output.splitlines()
                                 if line.startswith('NATIVE=')))
        self.assertEqual(result, {
            'filter_text': '已安装应用', 'filter_data': 'installed',
            'environment_text': ['Home', 'on'],
            'environment_data': ['/envs/Home', '/envs/on'],
            'popup_text': ['Home', 'on'], 'button_text': 'on',
        })

    def test_environment_popup_actions_keep_names(self):
        engine.apply()
        combo = QtWidgets.QComboBox(); combo.addItem('Home', '/envs/Home')
        menu = QtWidgets.QMenu(combo)
        action = menu.addAction('Home')
        direct = QtGui.QAction('Installed', combo)
        nested_menu = QtWidgets.QMenu(menu)
        nested = nested_menu.addAction('All')
        self.assertEqual(action.text(), 'Home')
        self.assertEqual(direct.text(), 'Installed')
        self.assertEqual(nested.text(), 'All')
        ordinary = QtWidgets.QMenu()
        self.assertEqual(ordinary.addAction('Home').text(), '主页')

    def test_environment_name_buttons_keep_collisions(self):
        cls = typed_widget('ButtonEnvironmentName', QtWidgets.QPushButton,
                           'anaconda_navigator.widgets.lists.environments')
        engine.apply()
        widget = cls('Home')
        self.assertEqual(widget.text(), 'Home')
        widget.setText('Installed')
        self.assertEqual(widget.text(), 'Installed')
        self.assertEqual(QtWidgets.QPushButton('Home').text(), '主页')

    def test_icon_overloads_translate_text_without_touching_icon(self):
        engine.apply()
        tabs = QtWidgets.QTabWidget()
        tabs.addTab(QtWidgets.QWidget(), QtGui.QIcon(), 'Home')
        self.assertEqual(tabs.tabText(0), '主页')
        action = QtGui.QAction(QtGui.QIcon(), 'Home', tabs)
        self.assertEqual(action.text(), '主页')
        button = QtWidgets.QPushButton(QtGui.QIcon(), 'Home')
        self.assertEqual(button.text(), '主页')

    def test_apply_is_idempotent(self):
        engine.apply()
        before = snapshot()
        count = len(engine._PATCHES)
        engine.apply(); engine.apply()
        self.assertEqual(snapshot(), before)
        self.assertEqual(len(engine._PATCHES), count)

    def test_uninstall_restores_own_and_inherited_attributes(self):
        before = snapshot()
        engine.apply()
        self.assertNotEqual(snapshot(), before)
        engine.uninstall()
        self.assertEqual(snapshot(), before)
        self.assertEqual(engine._PATCHES, [])
        self.assertFalse(engine._APPLIED)
        engine.uninstall()
        self.assertEqual(snapshot(), before)
        self.assertEqual(QtWidgets.QLabel('Home').text(), 'Home')
        engine.apply()
        self.assertEqual(QtWidgets.QLabel('Home').text(), '主页')

    def test_mid_install_failure_rolls_back_every_attribute(self):
        before = snapshot()
        original = engine._patch
        calls = []
        def fail_after_some_patches(*args, **kwargs):
            calls.append(args[:2])
            if len(calls) == 8:
                raise RuntimeError('injected eighth patch failure')
            return original(*args, **kwargs)
        with mock.patch.object(engine, '_patch', side_effect=fail_after_some_patches):
            with self.assertRaisesRegex(RuntimeError, 'injected eighth patch failure'):
                engine.apply()
        self.assertEqual(len(calls), 8)
        self.assertEqual(snapshot(), before)
        self.assertEqual(engine._PATCHES, [])
        self.assertFalse(engine._APPLIED)
        self.assertEqual(QtWidgets.QLabel('Home').text(), 'Home')

    def test_legacy_38_semantics(self):
        """Original 38 assertions; generic data combos now intentionally stay raw."""
        if importlib.util.find_spec('anaconda_navigator') is None:
            self.skipTest('Navigator integration dependency is not installed')
        engine.apply()
        checks = []
        def check(name, actual, expected):
            with self.subTest(legacy=name):
                self.assertEqual(actual, expected)
            checks.append(name)
        label=QtWidgets.QLabel(); label.setText('Cancel'); check('QLabel.setText', label.text(), '取消')
        button=QtWidgets.QPushButton(); button.setText('Apply'); check('button',button.text(),'应用')
        widget=QtWidgets.QWidget();widget.setWindowTitle('Conda Package Manager');check('title',widget.windowTitle(),'Conda 包管理器')
        tabs=QtWidgets.QTabWidget();tabs.addTab(QtWidgets.QWidget(),'Home');tabs.addTab(QtWidgets.QWidget(),'Environments');check('tabs',[tabs.tabText(i) for i in range(2)],['主页','环境'])
        line=QtWidgets.QLineEdit();line.setPlaceholderText('Search Packages');check('placeholder',line.placeholderText(),'搜索包')
        table=QtWidgets.QTableWidget(1,2);table.setHorizontalHeaderLabels(['Installed','All']);check('headers',[table.horizontalHeaderItem(i).text() for i in range(2)],['已安装','全部'])
        check('action ctor',QtGui.QAction('&Copy',None).text(),'&复制')
        check('label ctor',QtWidgets.QLabel('About Anaconda Navigator').text(),'关于 Anaconda 导航器')
        check('button ctor',QtWidgets.QPushButton('Report Issue').text(),'报告问题')
        check('checkbox ctor',QtWidgets.QCheckBox('Do not show again').text(),'不再显示')
        integration = isolated_python('''
import json
import zhcn_boot
zhcn_boot.apply()
from PySide6 import QtWidgets
from anaconda_navigator.widgets.dialogs import MessageBox
app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
box = MessageBox(MessageBox.INFORMATION_BOX, error='boom', title='Anaconda error', text='Anaconda warning')
values = [box.label_title_bar.text(), box.label_text.text()] + [getattr(box, name).text() for name in
    ('button_ok','button_yes','button_no','button_copy','button_learn','button_remove','button_cancel','button_send')]
print('MESSAGEBOX=' + json.dumps(values, ensure_ascii=False))
''')
        values = json.loads(next(line.removeprefix('MESSAGEBOX=') for line in integration.splitlines() if line.startswith('MESSAGEBOX=')))
        for index,(actual,expected) in enumerate(zip(values,['Anaconda 错误','Anaconda 警告','确定','是','否','复制文本','了解更多','移除','取消','报告问题'])):
            check('MessageBox '+str(index),actual,expected)
        check('plural count',engine.tr('1234 packages available '),'1234 个包可用 ')
        check('single count',engine.tr('1 package available '),'1 个包可用 ')
        check('matching',engine.tr('12 packages available matching "np"'),'12 个包可用（匹配 "np"）')
        check('plural selection',engine.tr('3 packages selected'),'已选中 3 个包')
        check('single selection',engine.tr('1 package selected'),'已选中 1 个包')
        combo=QtWidgets.QComboBox();combo.addItem('All applications','all')
        check('generic combo raw',combo.itemText(0),'All applications');check('combo data',combo.itemData(0),'all')
        filters=['Installed','Not installed','Updatable','Selected','All'];cf=QtWidgets.QComboBox();cf.addItems(filters)
        check('package filters',[cf.itemText(i) for i in range(cf.count())],filters)
        check('filter key remains valid',{'Installed':200}.get(cf.currentText()),200)
        for value in ('base','numpy','pandas','scikit-learn','pytorch',r'D:\anaconda3\envs\demo','https://repo.anaconda.com/pkgs/main'):
            check('passthrough '+value,engine.tr(value),value)
        method=QtWidgets.QLabel.setText;engine.apply();engine.apply()
        check('idempotent',QtWidgets.QLabel('Cancel').text(),'取消')
        check('no double wrap',QtWidgets.QLabel.setText is method,True)
        self.assertEqual(len(checks),38)
        print('LEGACY_CHECKS=38',flush=True)


if __name__ == '__main__':
    unittest.main()
