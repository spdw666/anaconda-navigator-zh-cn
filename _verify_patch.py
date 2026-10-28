# -*- coding: utf-8 -*-
"""真机验证 v2：补上构造函数入口 + 数字拼接"""
import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, r'D:\AnacondaHanhua')

import zhcn_boot
zhcn_boot.apply()

from PySide6 import QtGui, QtWidgets
from anaconda_navigator.utils import constants as C
from anaconda_navigator.widgets.dialogs import MessageBox

app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
ok, bad = [], []


def check(name, got, want):
    if got == want:
        ok.append(f'OK   {name}: {got!r}')
    else:
        bad.append(f'FAIL {name}: got {got!r} want {want!r}')


# ---------- A. setText 系 ----------
lab = QtWidgets.QLabel(); lab.setText('Cancel')
check('QLabel.setText', lab.text(), '取消')
btn = QtWidgets.QPushButton(); btn.setText('Apply')
check('QPushButton.setText', btn.text(), '应用')
w = QtWidgets.QWidget(); w.setWindowTitle('Conda Package Manager')
check('setWindowTitle', w.windowTitle(), 'Conda 包管理器')
tabs = QtWidgets.QTabWidget()
tabs.addTab(QtWidgets.QWidget(), 'Home')
tabs.addTab(QtWidgets.QWidget(), 'Environments')
check('addTab', [tabs.tabText(i) for i in range(2)], ['主页', '环境'])
le = QtWidgets.QLineEdit(); le.setPlaceholderText('Search Packages')
check('setPlaceholderText', le.placeholderText(), '搜索包')
tw = QtWidgets.QTableWidget(1, 2); tw.setHorizontalHeaderLabels(['Installed', 'All'])
check('setHorizontalHeaderLabels',
      [tw.horizontalHeaderItem(i).text() for i in range(2)], ['已安装', '全部'])

# ---------- B. 构造函数入口（新增） ----------
a1 = QtGui.QAction('&Copy', None)
check('QAction(ctor)', a1.text(), '&复制')
lab2 = QtWidgets.QLabel('About Anaconda Navigator')
check('QLabel(ctor)', lab2.text(), '关于 Anaconda 导航器')
btn2 = QtWidgets.QPushButton('Report Issue')
check('QPushButton(ctor)', btn2.text(), '报告问题')
cb2 = QtWidgets.QCheckBox('Do not show again')
check('QCheckBox(ctor)', cb2.text(), '不再显示')

# ---------- C. 真实 MessageBox（Navigator 自己的对话框） ----------
box = MessageBox(MessageBox.INFORMATION_BOX, error='boom', title='Anaconda error',
                 text='Anaconda warning')
# 注意：DialogBase 在 widgets/dialogs/__init__.py:182 重写了 setWindowTitle，
# 它只把标题写进 label_title_bar（QLabel），所以 windowTitle() 恒为空串 ——
# 真实显示的标题要查 label_title_bar.text()，正好走 QLabel.setText 补丁。
check('MessageBox title (label_title_bar)', box.label_title_bar.text(), 'Anaconda 错误')
check('MessageBox text label', box.label_text.text(), 'Anaconda 警告')
check('MessageBox button_ok', box.button_ok.text(), '确定')
check('MessageBox button_yes', box.button_yes.text(), '是')
check('MessageBox button_no', box.button_no.text(), '否')
check('MessageBox button_copy', box.button_copy.text(), '复制文本')
check('MessageBox button_learn', box.button_learn.text(), '了解更多')
check('MessageBox button_remove', box.button_remove.text(), '移除')
check('MessageBox button_cancel', box.button_cancel.text(), '取消')
check('MessageBox button_send', box.button_send.text(), '报告问题')

# ---------- D. 数字拼接 ----------
check('count 1234', zhcn_boot.tr('1234' + ' packages available '), '1234 个包可用 ')
check('count 1', zhcn_boot.tr('1 package available '), '1 个包可用 ')
check('matching', zhcn_boot.tr('12 packages available ' + 'matching "np"'),
      '12 个包可用（匹配 "np"）')
check('selected plural', zhcn_boot.tr('3 packages selected'), '已选中 3 个包')
check('selected single', zhcn_boot.tr('1 package selected'), '已选中 1 个包')

# ---------- E. 安全边界 ----------
cb = QtWidgets.QComboBox(); cb.addItem('All applications', 'all')
check('combo dual-arg text', cb.itemText(0), '所有应用')
check('combo dual-arg data kept', cb.itemData(0), 'all')
cf = QtWidgets.QComboBox(); cf.addItems(C.COMBOBOX_VALUES_ORDERED[:])
check('combo addItems MUST stay English',
      [cf.itemText(i) for i in range(cf.count())], C.COMBOBOX_VALUES_ORDERED[:])
check('COMBOBOX_VALUES still resolves', C.COMBOBOX_VALUES.get(cf.currentText()), C.INSTALLED)
for name in ('base', 'numpy', 'pandas', 'scikit-learn', 'pytorch',
             'D:\\anaconda3\\envs\\demo', 'https://repo.anaconda.com/pkgs/main'):
    check(f'passthrough {name}', zhcn_boot.tr(name), name)

# ---------- F. 幂等 ----------
before = len([k for k in dir(QtWidgets.QLabel) if k == 'setText'])
zhcn_boot.apply()
zhcn_boot.apply()
lab3 = QtWidgets.QLabel(); lab3.setText('Cancel')
check('idempotent', lab3.text(), '取消')
check('no double-wrap', QtWidgets.QLabel.setText.__name__, 'setText_zhcn')

print('\n'.join(ok))
print()
if bad:
    print('\n'.join(bad))
    print(f'\n=== {len(bad)} FAILED / {len(ok) + len(bad)} ===')
    sys.exit(1)
print(f'=== ALL {len(ok)} CHECKS PASSED ===')
