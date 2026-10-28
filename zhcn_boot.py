# -*- coding: utf-8 -*-
"""Anaconda Navigator display-text translation (external runtime patch).

Editable values and generic combobox items are data, not translation targets.
Only Navigator's dedicated ComboHomeFilter has translated item labels. Every
method replacement is recorded and restored on failure or uninstall(); no
anaconda_navigator package file is modified. Compatibility is tested per version,
not guaranteed for arbitrary future Qt/Navigator releases.
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
from nav_content import tr_ui, tr_rich_ui, display_text, is_package_filter, install_content_hooks, remove_qt_translator


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
    (r'Application <b>(.*?)</b> launch may have produced errors\.', '应用 <b>\\1</b> 启动时可能产生错误。'),
    (r"Create new environment for '(.*?)'", '为“\\1”创建新环境'),
    (r'Clone from environment: ([\s\S]*)', '克隆自环境：\\1'),
    (r'Open with ([\s\S]*)', '使用 \\1 打开'),
    (r'Environment file "(.*?)" downloaded to ([\s\S]*)', '环境文件“\\1”已下载到 \\2'),
    (r'Path to configuration file: ([\s\S]*)', '配置文件路径：\\1'),
    (r'<b>(.*?)</b> is not a valid conda channel\.', '<b>\\1</b> 不是有效的 conda 频道。'),
    (r'Launching <b>(.*?)</b>', '正在启动 <b>\\1</b>'),
    (r'Installing application <b>(.*?)</b> in new a environment <b>(.*?)</b>',
     '正在新环境 <b>\\2</b> 中安装应用 <b>\\1</b>'),
    (r'Installing application <b>(.*?)</b> on <b>(.*?)</b>', '正在向 <b>\\2</b> 安装应用 <b>\\1</b>'),
    (r'Install application <b>(.*?)</b> on <b>(.*?)</b>', '正在向 <b>\\2</b> 安装应用 <b>\\1</b>'),
    (r'Updating application <b>(.*?)</b> on <b>(.*?)</b>', '正在更新 <b>\\2</b> 中的应用 <b>\\1</b>'),
    (r'Removing application <b>(.*?)</b> from <b>(.*?)</b>', '正在从 <b>\\2</b> 移除应用 <b>\\1</b>'),
    (r'Directory path where (.*?) is installed on your machine\.\s+To see \1 on the home tab, you will also need to click\s+the Refresh button on the home tab\.',
     '\\1 在本机的安装目录。要在主页中看到 \\1，还需要点击主页上的刷新按钮。'),
    (r'((?:PyCharm(?: Community| Professional)?|VS Code|Kilo Desktop|DataSpell)) path', '\\1 路径'),
    (r'(<span\b[^>]*>)No environments available for ([^<>]*)(</span>)', '\\1\\2 没有可用环境\\3'),
    (r'(<span\b[^>]*>)(\d+) environments? available for ([^<>]*)(</span>)', '\\1\\3 有 \\2 个可用环境\\4'),
    (r'(<span\b[^>]*>)You are signed in as ([^<>]*)(</span>)', '\\1你当前登录的账号是 \\2\\3'),
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

    extra = tr_ui(text)
    if extra != text:
        _trace(text, extra)
        return extra
    counted = re.fullmatch(r'(Documentation|Training|Webinar|Event|Forum|Social|Video)\s*\((\d+)\)', text)
    if counted:
        labels = {'Documentation': '文档', 'Training': '培训', 'Webinar': '在线讲座',
                  'Event': '活动', 'Forum': '论坛', 'Social': '社交', 'Video': '视频'}
        out = f'{labels[counted.group(1)]}（{counted.group(2)}）'
        _trace(text, out)
        return out
    if re.fullmatch(r'(?:\s*\d+ packages? will be (?:modified|removed|installed)\s*)+', text):
        actions = {'modified': '修改', 'removed': '移除', 'installed': '安装'}
        out = '；'.join(f'将{actions[action]} {count} 个包'
                       for count, action in re.findall(r'(\d+) packages? will be (modified|removed|installed)', text))
        _trace(text, out)
        return out

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

    if '<' in out and '>' in out:
        rich_out = tr_rich_ui(out)
        if rich_out != out:
            out = rich_out
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


# Only these exact label/value pairs on Navigator's dedicated application filter
# are presentation strings. A generic addItem(str, str) may contain an env name.
_APP_FILTER_LABELS: typing.Final[dict[str, str]] = {
    'all': 'All applications',
    'installed': 'Installed applications',
    'uninstalled': 'Not installed applications',
    'updatable': 'Updatable applications',
}


def tr_app_filter(text: typing.Any, user_data: typing.Any) -> typing.Any:
    """Translate a verified static filter label without touching its logical key."""
    if isinstance(user_data, str) and _APP_FILTER_LABELS.get(user_data) == text:
        return tr(text)
    return text


def _is_app_filter(widget: typing.Any) -> bool:
    return any(cls.__name__ == 'ComboHomeFilter'
               and cls.__module__ == 'anaconda_navigator.widgets.tabs.home'
               for cls in type(widget).__mro__)


def _preserve_data_text(widget: typing.Any, args: tuple = (), kwargs: dict | None = None) -> bool:
    """Protect environment labels and the QAction-based popup of data combos."""
    if any(cls.__name__ == 'ButtonEnvironmentName'
           and cls.__module__ == 'anaconda_navigator.widgets.lists.environments'
           for cls in type(widget).__mro__):
        return True
    candidates = [widget, *args]
    if kwargs and kwargs.get('parent') is not None:
        candidates.append(kwargs['parent'])
    for candidate in candidates:
        seen = set()
        while candidate is not None and id(candidate) not in seen:
            seen.add(id(candidate))
            if any(cls.__name__ == 'QComboBox' and cls.__module__ == 'PySide6.QtWidgets'
                   for cls in type(candidate).__mro__):
                if is_package_filter(candidate):
                    return False  # popup action labels are presentation, not currentText()
                return not _is_app_filter(candidate)
            try:
                candidate = candidate.parent()
            except (AttributeError, RuntimeError, TypeError):
                break  # constructors may not yet have initialized their QObject
    return False


_APPLIED: bool = False
# (class, attribute, originally owned here, original own value). Inherited
# attributes must be deleted on restore, not shadowed with an inherited method.
_PATCHES: list[tuple[type, str, bool, typing.Any]] = []


def _patch(cls: type, name: str, replacement: typing.Any) -> None:
    owned = name in vars(cls)
    original = vars(cls).get(name)
    setattr(cls, name, replacement)
    _PATCHES.append((cls, name, owned, original))


def uninstall() -> None:
    """Restore exact pre-install attributes, including inherited ownership."""
    global _APPLIED
    remove_qt_translator()
    remaining = []
    errors = []
    for cls, name, owned, original in reversed(_PATCHES):
        try:
            if owned:
                setattr(cls, name, original)
            else:
                delattr(cls, name)
        except Exception as exc:
            remaining.append((cls, name, owned, original))
            errors.append(f'{cls.__name__}.{name}: {exc!r}')
    _PATCHES[:] = reversed(remaining)
    _APPLIED = bool(remaining)
    if errors:
        raise RuntimeError('Patch restore failed: ' + '; '.join(errors))


def apply() -> None:
    """Install atomically; any installation exception restores earlier changes."""
    global _APPLIED
    if _APPLIED:
        return
    if _PATCHES:
        uninstall()
    try:
        _install_patches()
    except BaseException:
        uninstall()
        raise
    _APPLIED = True


def _install_patches() -> None:
    from PySide6 import QtGui, QtWidgets

    def wrap_set_text(cls: type, name: str, index: int = 0) -> None:
        original = getattr(cls, name, None)
        if original is None or getattr(original, '_zhcn', False):
            return

        def patched(self, *args, **kwargs):
            if _preserve_data_text(self):
                return original(self, *args, **kwargs)
            if len(args) > index:
                changed = list(args)
                changed[index] = display_text(self, changed[index], tr)
                args = tuple(changed)
            for key in ('text', 'title', 'label', 'caption', 'message'):
                if key in kwargs:
                    kwargs[key] = display_text(self, kwargs[key], tr)
            return original(self, *args, **kwargs)

        patched._zhcn = True
        patched.__name__ = f'{name}_zhcn'
        _patch(cls, name, patched)

    # Do not translate the actual content of input editors/log viewers.
    for cls in (QtWidgets.QLabel, QtWidgets.QAbstractButton, QtWidgets.QGroupBox,
                QtWidgets.QMessageBox, QtWidgets.QMenu, QtWidgets.QStatusBar,
                QtWidgets.QProgressBar, QtGui.QAction):
        for name in ('setText', 'setTitle', 'setInformativeText', 'setDetailedText', 'showMessage'):
            wrap_set_text(cls, name)
    # These QWidget display attributes are inherited by all relevant controls.
    for name in ('setWindowTitle', 'setToolTip', 'setStatusTip', 'setWhatsThis'):
        wrap_set_text(QtWidgets.QWidget, name)
    for cls in (QtWidgets.QLineEdit, QtWidgets.QTextEdit, QtWidgets.QPlainTextEdit):
        wrap_set_text(cls, 'setPlaceholderText')
    for name in ('setToolTip', 'setStatusTip', 'setWhatsThis'):
        wrap_set_text(QtGui.QAction, name)

    def wrap_header(cls: type, name: str) -> None:
        original = getattr(cls, name, None)
        if original is None:
            return

        def patched(self, labels, *args, **kwargs):
            if isinstance(labels, (list, tuple)):
                labels = [tr(item) for item in labels]
            return original(self, labels, *args, **kwargs)

        patched._zhcn = True
        _patch(cls, name, patched)

    for cls in (QtWidgets.QTableWidget, QtWidgets.QTreeWidget, QtGui.QStandardItemModel):
        for name in ('setHorizontalHeaderLabels', 'setVerticalHeaderLabels'):
            wrap_header(cls, name)

    original_add_tab = QtWidgets.QTabWidget.addTab

    def patched_add_tab(self, *args, **kwargs):
        changed = list(args)
        # (widget, label) and (widget, icon, label) are different Qt overloads.
        index = 1 if len(changed) > 1 and isinstance(changed[1], str) else 2
        if len(changed) > index:
            changed[index] = tr(changed[index])
        for key in ('text', 'label'):
            if key in kwargs:
                kwargs[key] = tr(kwargs[key])
        return original_add_tab(self, *changed, **kwargs)

    _patch(QtWidgets.QTabWidget, 'addTab', patched_add_tab)
    wrap_set_text(QtWidgets.QTabWidget, 'setTabText', 1)

    def wrap_first_text(cls: type, name: str) -> None:
        original = getattr(cls, name)

        def patched(self, *args, **kwargs):
            if not _preserve_data_text(self, args, kwargs):
                changed = list(args)
                for index in range(min(2, len(changed))):
                    if isinstance(changed[index], str):
                        changed[index] = display_text(self, changed[index], tr)
                        break
                args = tuple(changed)
                for key in ('text', 'title'):
                    if key in kwargs:
                        kwargs[key] = display_text(self, kwargs[key], tr)
            return original(self, *args, **kwargs)

        patched._zhcn = True
        _patch(cls, name, patched)

    wrap_first_text(QtWidgets.QMenu, 'addAction')
    wrap_first_text(QtWidgets.QMenuBar, 'addMenu')
    for cls in (QtGui.QAction, QtWidgets.QLabel, QtWidgets.QPushButton,
                QtWidgets.QCheckBox, QtWidgets.QRadioButton, QtWidgets.QGroupBox,
                QtWidgets.QToolButton):
        wrap_first_text(cls, '__init__')

    original_add_item = QtWidgets.QComboBox.addItem

    def patched_add_item(self, *args, **kwargs):
        if _is_app_filter(self):
            changed = list(args)
            if len(changed) == 2 and isinstance(changed[0], str):
                changed[0] = tr_app_filter(changed[0], changed[1])
            elif len(changed) == 3 and isinstance(changed[1], str):
                changed[1] = tr_app_filter(changed[1], changed[2])
            elif len(changed) == 1 and 'userData' in kwargs:
                changed[0] = tr_app_filter(changed[0], kwargs['userData'])
            elif 'text' in kwargs and 'userData' in kwargs:
                kwargs['text'] = tr_app_filter(kwargs['text'], kwargs['userData'])
            args = tuple(changed)
        return original_add_item(self, *args, **kwargs)

    _patch(QtWidgets.QComboBox, 'addItem', patched_add_item)
    original_current_text = QtWidgets.QComboBox.setCurrentText

    def patched_current_text(self, text):
        if _is_app_filter(self) and text in _APP_FILTER_LABELS.values():
            text = tr(text)
        return original_current_text(self, text)

    _patch(QtWidgets.QComboBox, 'setCurrentText', patched_current_text)
    install_content_hooks(_patch)


def install() -> None:
    """Compatibility alias; install before creating Navigator controls."""
    apply()


if __name__ == '__main__':
    apply()
    print('applied =', _APPLIED, '| entries =', len(ZH), '| patterns =', len(_PATTERNS))
    for probe in ('Home', 'Environments', '&File', 'Cancel', ' packages available ',
                  'numpy', 'base', 'matching "numpy"'):
        print(repr(probe), '->', repr(tr(probe)))
