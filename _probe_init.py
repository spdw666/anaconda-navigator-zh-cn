# -*- coding: utf-8 -*-
"""探测：能否 patch Shiboken 类型的 __init__（QAction 文案走构造函数）"""
import os, sys
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6 import QtGui, QtWidgets

app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

print('--- 1) QAction 原始行为')
a = QtGui.QAction('Hello', None)
print('   text =', repr(a.text()))

print('--- 2) 直接改 QtGui.QAction.__init__')
orig_init = QtGui.QAction.__init__
print('   orig_init =', orig_init)


def patched_init(self, *args, **kwargs):
    if args and isinstance(args[0], str):
        args = ('ZH:' + args[0],) + args[1:]
    return orig_init(self, *args, **kwargs)


try:
    QtGui.QAction.__init__ = patched_init
    b = QtGui.QAction('World', None)
    print('   after patch text =', repr(b.text()), '=> PATCH OK' if b.text() == 'ZH:World' else '=> NO EFFECT')
except Exception as e:
    print('   FAILED:', type(e).__name__, e)

print('--- 3) 试 QPushButton.__init__（QWidget 子类，看是否同样可行）')
ob = QtWidgets.QPushButton.__init__
def pb_init(self, *args, **kwargs):
    if args and isinstance(args[0], str):
        args = ('ZH:' + args[0],) + args[1:]
    return ob(self, *args, **kwargs)
try:
    QtWidgets.QPushButton.__init__ = pb_init
    p = QtWidgets.QPushButton('Press')
    print('   text =', repr(p.text()), '=> PATCH OK' if p.text() == 'ZH:Press' else '=> NO EFFECT')
except Exception as e:
    print('   FAILED:', type(e).__name__, e)

print('--- 4) QTabWidget.__init__ 是否可行')
ot = QtWidgets.QTabWidget.__init__
def tw_init(self, *args, **kwargs):
    return ot(self, *args, **kwargs)
try:
    QtWidgets.QTabWidget.__init__ = tw_init
    QtWidgets.QTabWidget()
    print('   PATCH OK (no crash)')
except Exception as e:
    print('   FAILED:', type(e).__name__, e)

print('--- 5) QLabel.__init__')
ol = QtWidgets.QLabel.__init__
def lb_init(self, *args, **kwargs):
    if args and isinstance(args[0], str):
        args = ('ZH:' + args[0],) + args[1:]
    return ol(self, *args, **kwargs)
try:
    QtWidgets.QLabel.__init__ = lb_init
    q = QtWidgets.QLabel('Text')
    print('   text =', repr(q.text()), '=> PATCH OK' if q.text() == 'ZH:Text' else '=> NO EFFECT')
except Exception as e:
    print('   FAILED:', type(e).__name__, e)
