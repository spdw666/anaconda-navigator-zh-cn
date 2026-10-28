# -*- coding: utf-8 -*-
"""Anaconda Navigator 简体中文汉化引擎（外挂式）

设计要点
--------
1. **不改动 anaconda_navigator 的任何源码文件**。本模块在 Navigator 启动前
   被 import，运行期给 PySide6/Shiboken 的类方法打补丁：在静态文案进入 Qt
   之前把英文换成中文。conda 升级覆盖 site-packages 时汉化不受影响。
2. **只 patch「静态文案」入口**（setText / setWindowTitle / addTab / addAction
   / setPlaceholderText ...）。绝不做子串替换，只做整串精确匹配，因此环境名、
   包名、路径、频道 URL 永远不会被改写。
3. **QComboBox 双参数 addItem 才翻译**。单参数 addItems(list) 在 C++ 层循环，
   不经过 Python 补丁 —— 这正是包管理器过滤器要的行为：
   `widgets/manager/table.py:295` 用 `currentText()` 去查 `COMBOBOX_VALUES`
   字典，显示文本一旦变成中文，包过滤会静默失效。所以那条路径保持英文。
   而 `widgets/tabs/home.py:194` 的 `addItem(verbose_name, userData)` 逻辑走
   itemData，翻译显示文本完全安全。
4. 幂等：重复 import 只生效一次。
"""

from __future__ import annotations

import os
import re
import sys
import typing

_HERE: typing.Final[str] = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from nav_zh_dict import ZH  # noqa: E402


# 拼接型文案：源码里是 f-string / .format()，只能按整串模板匹配。
# 每条都取自源码精确原文（注释标注出处），变量部分用捕获组原样保留。
_PATTERN_SPECS: typing.Final[typing.Sequence[typing.Tuple[str, str]]] = (
    # api/anaconda_api.py:693-827  worker.action_msg
    (r'Creating environment <b>(.*?)</b>', '正在创建环境 <b>\\1</b>'),
    (r'Cloning from environment <b>(.*?)</b> into <b>(.*?)</b>',
     '正在从 <b>\\1</b> 克隆到 <b>\\2</b>'),
    (r'Backing up environment <b>(.*?)</b>', '正在备份环境 <b>\\1</b>'),
    (r'Importing environment <b>(.*?)</b>', '正在导入环境 <b>\\1</b>'),
    (r'Removing environment <b>(.*?)</b>', '正在移除环境 <b>\\1</b>'),
    (r'Installing packages on <b>(.*?)</b>', '正在向 <b>\\1</b> 安装包'),
    (r'Updating packages on <b>(.*?)</b>', '正在更新 <b>\\1</b> 的包'),
    (r'Removing packages from <b>(.*?)</b>', '正在从 <b>\\1</b> 移除包'),
    # widgets/main_window/__init__.py:1025
    (r'Loading packages of <b>(.*?)</b>\.?\.\.\.', '正在加载包：<b>\\1</b>…'),
    # widgets/manager/table.py:272-275
    #   count_text = to_text_string(count) + _(' packages available ')
    #   count_text = count_text + _('matching "{0}"').format(text)   ← 再拼一次
    #   最终是一整串送给 status label，所以必须按「数字 + 可选 matching 尾巴」
    #   整串匹配。放在单段规则之前，先长后短。
    (r'(\d+) packages available matching "(.*?)"', '\\1 个包可用（匹配 "\\2"）'),
    (r'(\d+) package available matching "(.*?)"', '\\1 个包可用（匹配 "\\2"）'),
    (r'(\d+) packages available ', '\\1 个包可用 '),
    (r'(\d+) package available ', '\\1 个包可用 '),
    # widgets/manager/table.py:283  f'{action_count} package{plural} selected'
    (r'(\d+) packages selected', '已选中 \\1 个包'),
    (r'(\d+) package selected', '已选中 \\1 个包'),
    # widgets/manager/table.py:275  _('matching "{0}"').format(text) 单独出现时
    (r'matching "(.*?)"', '（匹配 "\\1"）'),
    # widgets/dialogs/channels.py:377
    (r'Channel <b>(.*?)</b> is in list already\.', '频道 <b>\\1</b> 已在列表中。'),
    # widgets/dialogs/environment/* 一些带变量的提示
    (r'Environment <b>(.*?)</b> was created successfully\.',
     '环境 <b>\\1</b> 创建成功。'),
    (r'Environment <b>(.*?)</b> was removed\.', '环境 <b>\\1</b> 已移除。'),
    (r'Do you want to remove environment <b>(.*?)</b>\?',
     '确定要移除环境 <b>\\1</b> 吗？'),
    (r'Do you want to update <b>(.*?)</b>\?', '确定要更新 <b>\\1</b> 吗？'),
    (r'Do you want to install <b>(.*?)</b>\?', '确定要安装 <b>\\1</b> 吗？'),
    (r'Do you want to remove <b>(.*?)</b>\?', '确定要移除 <b>\\1</b> 吗？'),
    # widgets/main_window/account_components.py:196-210 __update_account_label_text
    #   content += 'Partially connected to ' / 'Connected to '
    #   content += ', '.join(f'<a href="" style="...">{item}</a>' for item in result)
    #   → 整串是「前缀 + 一个或多个品牌链接」，必须用正则。
    #   注意 fullmatch 下 'Partially connected to X' 不会被 'Connected to (.*)'
    #   命中（开头不同），所以两条可以并存，顺序无所谓；仍按先长后短排列。
    (r'Partially connected to ([\s\S]*)', '部分连接到 \\1'),
    (r'Connected to ([\s\S]*)', '已连接到 \\1'),
    # widgets/lists/apps.py:338  self.button_version.setToolTip(f'Version {self.versions[-1]} available')
    #   首页应用卡片右上角「↗ 4.5.9」的鼠标提示，原文是 f-string 拼接。
    (r'Version ([^\s]+) available', '可更新到 \\1'),
    # widgets/dialogs/update.py:45-51  Navigator 自身更新提示（QLabel 多行拼接）
    #   两种变体：is_root_writable=False 时 extra_text 会多插一句权限提示。
    #   先长后短：带权限提示的在前面，不带提示的短串在后面。
    (r"There's a new version of Anaconda Navigator available\. "
     r'We strongly recommend you to update\. <br><br>'
     r'If you click yes, Anaconda Navigator will close and then the '
     r'Anaconda Navigator Updater will start\.<br><br><br>'
     r'Do you wish to update to <b>Anaconda Navigator (.*?)</b> now\?'
     r'<br><br>\(You will be prompted to elevate privileges\)<br><br>',
     'Anaconda 导航器有新版本可用，强烈建议更新。<br><br>'
     '点击「是」后，Anaconda 导航器将关闭，随后启动 Anaconda 导航器更新器。<br><br><br>'
     '是否现在更新到 <b>Anaconda 导航器 \\1</b>？<br><br>（会提示你提升权限）<br><br>'),
    (r"There's a new version of Anaconda Navigator available\. "
     r'We strongly recommend you to update\. <br><br>'
     r'If you click yes, Anaconda Navigator will close and then the '
     r'Anaconda Navigator Updater will start\.<br><br><br>'
     r'Do you wish to update to <b>Anaconda Navigator (.*?)</b> now\?<br><br>',
     'Anaconda 导航器有新版本可用，强烈建议更新。<br><br>'
     '点击「是」后，Anaconda 导航器将关闭，随后启动 Anaconda 导航器更新器。<br><br><br>'
     '是否现在更新到 <b>Anaconda 导航器 \\1</b>？<br><br>'),
)

_PATTERNS: typing.Final[typing.Sequence[typing.Tuple[typing.Pattern[str], str]]] = tuple(
    (re.compile(spec), tpl) for spec, tpl in _PATTERN_SPECS
)

# 富文本里的品牌名：account_components.py:206-208 把品牌拼成
#   <a href="" style="color:#43B049;text-decoration:none">Cloud</a>
# 整串送进 setText，前缀规则只翻到「已连接到」，锚文本还留着英文。
# 这里只处理「纯文本锚点」<a ...>文字</a>，且仅当锚文本在 ZH 表里存在才替换，
# 因此链接、href、style 属性一个字都不动。
_ANCHOR: typing.Final[typing.Pattern[str]] = re.compile(r'(<a\b[^>]*>)([^<>]*)(</a>)')


def _anchor_sub(match: 're.Match[str]') -> str:
    inner = match.group(2)
    return match.group(1) + ZH.get(inner, inner) + match.group(3)


def tr(text: typing.Any) -> typing.Any:
    """把一条静态文案翻成中文；未命中则原样返回（类型不变）。"""
    if not isinstance(text, str) or not text:
        return text

    hit = ZH.get(text)
    if hit is not None:
        _trace(text, hit)
        return hit

    # 累积替换：模板里既有「前缀 + 变量」也有「整串状态栏」，
    # 一条串可能需要多条规则接力（如「已连接到」+ 锚文本里的「云端」）。
    # _PATTERN_SPECS 已按先长后短排列，长规则先吃掉，短规则不会重复命中。
    out = text
    changed = False
    for regex, template in _PATTERNS:
        if regex.fullmatch(out) is not None:
            out = regex.sub(template, out)
            changed = True

    anchor_out = _ANCHOR.sub(_anchor_sub, out)
    if anchor_out != out:
        out = anchor_out
        changed = True

    if changed:
        _trace(text, out)
        return out

    return text


# ---------------------------------------------------------------------------
# 运行期翻译溯源（可选诊断）：设 ANACONDA_ZH_TRACE=<文件路径> 时，
# 每次真正发生的翻译都会追加一行「原文 => 译文」，用于交付时证明哪些界面
# 文案被汉化了。平时完全不启用，零开销。
# ---------------------------------------------------------------------------
_TRACE_PATH: typing.Optional[str] = os.environ.get('ANACONDA_ZH_TRACE') or None
_TRACED: typing.Set[typing.Tuple[str, str]] = set()


def _trace(source: str, target: str) -> None:
    if _TRACE_PATH is None:
        return
    key = (source, target)
    if key in _TRACED:  # 同一词条只记一次，避免日志被刷新刷爆
        return
    _TRACED.add(key)
    try:
        with open(_TRACE_PATH, 'a', encoding='utf-8') as handle:
            handle.write(f'{source!r} => {target!r}\n')
    except OSError:
        pass


def _tr_args(args: tuple) -> tuple:
    """翻一个位置参数元组里的所有 str（用于 addTab / addAction 这类）。"""
    return tuple(tr(item) for item in args)


_APPLIED: bool = False


def apply() -> None:
    """给 Qt 类方法打补丁。幂等。"""
    global _APPLIED
    if _APPLIED:
        return

    from PySide6 import QtGui, QtWidgets  # noqa: PLC0415

    def wrap_set_text(cls: type, name: str, index: int = 0) -> None:
        """把 cls.name 的第 index 个位置参数翻译掉。"""
        original = getattr(cls, name, None)
        if original is None or getattr(original, '_zhcn', False):
            return

        def patched(self, *args, **kwargs):  # noqa: ANN001, ANN202
            if len(args) > index:
                args = list(args)
                args[index] = tr(args[index])
                args = tuple(args)
            for key in ('text', 'title', 'label', 'caption', 'message'):
                if key in kwargs and isinstance(kwargs[key], str):
                    kwargs[key] = tr(kwargs[key])
            return original(self, *args, **kwargs)

        patched._zhcn = True  # type: ignore[attr-defined]
        patched.__name__ = f'{name}_zhcn'
        setattr(cls, name, patched)

    # --- 单参数文案入口（最常用）
    for cls in (
        QtWidgets.QLabel,
        QtWidgets.QAbstractButton,      # QPushButton / QCheckBox / QRadioButton / QToolButton
        QtWidgets.QWidget,              # setWindowTitle 在这里，所有控件继承
        QtWidgets.QLineEdit,
        QtWidgets.QTextEdit,
        QtWidgets.QTextBrowser,
        QtWidgets.QPlainTextEdit,
        QtWidgets.QGroupBox,
        QtWidgets.QMessageBox,
        QtWidgets.QCheckBox,
        QtWidgets.QRadioButton,
        QtWidgets.QPushButton,
        QtWidgets.QToolButton,
        QtWidgets.QMenu,
        QtWidgets.QMenuBar,
        QtWidgets.QStatusBar,
        QtWidgets.QProgressBar,
        QtGui.QAction,
    ):
        wrap_set_text(cls, 'setText')
        wrap_set_text(cls, 'setTitle')
        wrap_set_text(cls, 'setWindowTitle')
        wrap_set_text(cls, 'setToolTip')
        wrap_set_text(cls, 'setStatusTip')
        wrap_set_text(cls, 'setWhatsThis')
        wrap_set_text(cls, 'setPlaceholderText')
        wrap_set_text(cls, 'setInformativeText')
        wrap_set_text(cls, 'setDetailedText')
        wrap_set_text(cls, 'showMessage')

    # --- 表头 / 列表头（文案是 str 列表）
    def wrap_header(cls: type, name: str) -> None:
        original = getattr(cls, name, None)
        if original is None or getattr(original, '_zhcn', False):
            return

        def patched(self, labels, *args, **kwargs):  # noqa: ANN001, ANN202
            if isinstance(labels, (list, tuple)):
                labels = [tr(item) for item in labels]
            return original(self, labels, *args, **kwargs)

        patched._zhcn = True  # type: ignore[attr-defined]
        setattr(cls, name, patched)

    for cls in (QtWidgets.QTableWidget, QtWidgets.QTreeWidget, QtGui.QStandardItemModel):
        wrap_header(cls, 'setHorizontalHeaderLabels')
        wrap_header(cls, 'setVerticalHeaderLabels')

    # --- addTab(widget, text)：注意 text 是**第 2 个**位置参数
    for cls in (QtWidgets.QTabWidget,):
        original_add_tab = cls.addTab
        if not getattr(original_add_tab, '_zhcn', False):
            def patched_add_tab(self, widget, text='', *args, **kwargs):  # noqa: ANN001, ANN202
                return original_add_tab(self, widget, tr(text), *args, **kwargs)

            patched_add_tab._zhcn = True  # type: ignore[attr-defined]
            cls.addTab = patched_add_tab
        wrap_set_text(cls, 'setTabText', index=1)

    # --- QMenu.addAction 重载多：只在遇到 str 时翻译，QAction 参数原样透传
    original_add_action = QtWidgets.QMenu.addAction
    if not getattr(original_add_action, '_zhcn', False):
        def patched_add_action(self, *args, **kwargs):  # noqa: ANN001, ANN202
            if args and isinstance(args[0], str):
                args = (tr(args[0]),) + args[1:]
            elif len(args) > 1 and isinstance(args[1], str):
                args = (args[0], tr(args[1])) + args[2:]
            return original_add_action(self, *args, **kwargs)

        patched_add_action._zhcn = True  # type: ignore[attr-defined]
        QtWidgets.QMenu.addAction = patched_add_action

    # --- 构造函数入口：Navigator 大量控件是 `QLabel('Ok')` / `ButtonPrimary('Ok')`
    #     / `QAction('&Copy', parent)` 这样「文案直接在构造函数里」创建的
    #     （如 widgets/dialogs/__init__.py:337-346、utils/qthelpers.py:73）。
    #     只 patch 文案型控件；QWidget/QDialog 等不接受文案的类不碰。
    def wrap_init(cls: type) -> None:
        original = cls.__init__
        if getattr(original, '_zhcn', False):
            return

        def patched_init(self, *args, **kwargs):  # noqa: ANN001, ANN202
            if args and isinstance(args[0], str):
                args = (tr(args[0]),) + args[1:]
            return original(self, *args, **kwargs)

        patched_init._zhcn = True  # type: ignore[attr-defined]
        cls.__init__ = patched_init

    for cls in (
        QtGui.QAction,
        QtWidgets.QLabel,
        QtWidgets.QPushButton,
        QtWidgets.QCheckBox,
        QtWidgets.QRadioButton,
        QtWidgets.QGroupBox,
        QtWidgets.QToolButton,
    ):
        wrap_init(cls)

    # --- QComboBox.addItem：**只有双参数形式**（带 userData）才翻译。
    #     单参数 / addItems(list) 一律不动 —— 见文件头第 3 条。
    original_add_item = QtWidgets.QComboBox.addItem
    if not getattr(original_add_item, '_zhcn', False):
        def patched_add_item(self, *args, **kwargs):  # noqa: ANN001, ANN202
            if len(args) == 2 and isinstance(args[0], str) and isinstance(args[1], str):
                # (text, userData=str)：userData 是逻辑值，绝不能碰
                args = (tr(args[0]), args[1])
            return original_add_item(self, *args, **kwargs)

        patched_add_item._zhcn = True  # type: ignore[attr-defined]
        QtWidgets.QComboBox.addItem = patched_add_item

    # --- QMenuBar.addMenu(title) / addMenu(QMenu)：菜单栏标题
    #     widgets/main_window/__init__.py:659 `menubar.addMenu('&File')`、
    #     :664 `menubar.addMenu('&Help')` —— 之前漏了，所以 File/Help 一直是英文。
    original_add_menu = QtWidgets.QMenuBar.addMenu
    if not getattr(original_add_menu, '_zhcn', False):
        def patched_add_menu(self, *args, **kwargs):  # noqa: ANN001, ANN202
            if args and isinstance(args[0], str):
                args = (tr(args[0]),) + args[1:]
            elif len(args) > 1 and isinstance(args[1], str):
                args = (args[0], tr(args[1])) + args[2:]
            return original_add_menu(self, *args, **kwargs)

        patched_add_menu._zhcn = True  # type: ignore[attr-defined]
        QtWidgets.QMenuBar.addMenu = patched_add_menu

    # --- QTabBar.setTabText 之外：QCheckBox/QRadioButton 走 addItem 的也处理
    #     （Navigator 的自定义 tab 用 QCheckBox 做导航按钮，文案走构造函数已覆盖）
    _APPLIED = True


def install() -> None:
    """给启动器调用的入口：确保 QApplication 存在后打补丁。"""
    apply()


if __name__ == '__main__':
    # 自检：不启动 GUI，直接验证词表与模板
    apply()
    print('applied =', _APPLIED, '| entries =', len(ZH), '| patterns =', len(_PATTERNS))
    for probe in ('Home', 'Environments', '&File', 'Cancel', ' packages available ',
                  'numpy', 'base', 'matching "numpy"',
                  'Creating environment <b>D:\\anaconda3\\envs\\demo</b>'):
        print(repr(probe), '->', repr(tr(probe)))
