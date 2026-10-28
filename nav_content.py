"""Contextual localization for public Navigator content, not user identifiers."""
from __future__ import annotations

import html
import json
import os
from pathlib import Path
import re
from functools import lru_cache
import xml.etree.ElementTree as ET

from nav_assets import localized_badge

ROOT = Path(__file__).resolve().parent


def _load(name: str) -> dict[str, str]:
    path = ROOT / name
    if not path.is_file():
        return {}
    with path.open(encoding='utf-8-sig') as stream:
        result = json.load(stream)
    if not isinstance(result, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in result.items()):
        raise ValueError('Invalid translation dictionary: ' + str(path))
    return result


CONTENT_ZH = _load('content_zh.json')
UI_ZH = _load('ui_zh_extra.json')


def _normalized(value: str) -> str:
    return re.sub(r'\s+', ' ', html.unescape(value)).strip()


_NORMALIZED_CONTENT = {_normalized(key): value for key, value in CONTENT_ZH.items()}
_NORMALIZED_UI = {_normalized(key): value for key, value in UI_ZH.items()}


def tr_ui(text):
    if not isinstance(text, str):
        return text
    return UI_ZH.get(text, _NORMALIZED_UI.get(_normalized(text), text))


def tr_content(text):
    """Translate whole audited display fields; callers never pass IDs/paths here."""
    if not isinstance(text, str):
        return text
    return CONTENT_ZH.get(text, _NORMALIZED_CONTENT.get(_normalized(text), tr_ui(text)))


def tr_rich_content(text: str) -> str:
    """Localize text nodes, leaving attributes, hrefs, tags and original data intact."""
    parts = re.split(r'(<[^>]+>)', text)
    for index in range(0, len(parts), 2):
        original = html.unescape(parts[index])
        translated = tr_content(original)
        if translated != original:
            parts[index] = html.escape(translated, quote=False)
    return ''.join(parts)


def tr_rich_ui(text: str) -> str:
    """Translate only catalogued static HTML text nodes, never arbitrary spans."""
    snippets = {
        'See what has changed ': '查看变更内容：',
        "I acknowledge that I have read and consent to Anaconda's": '我确认已阅读并同意 Anaconda 的',
        'Privacy Policy': '隐私政策', 'Terms of Service': '服务条款',
        ', including the collection, use, and processing of my personal data as described therein.':
            '，包括其中所述对我的个人数据的收集、使用和处理。',
    }
    if 'See what has changed' in text or 'Log in to Anaconda.org' in text:
        snippets['here'] = '此处'
    if 'Privacy Policy' in text and 'Terms of Service' in text:
        snippets[' and '] = '和'
    if 'Forget your ' in text:
        snippets.update({'Forget your ': '忘记了你的', 'username': '用户名', 'password': '密码',
                         ' or ': '或', 'Login via cloud': '通过云端登录'})
    if 'Log in to Anaconda.org' in text:
        snippets['Log in to Anaconda.org to access private channels and packages. If you don’t have an account, click '] = (
            '登录 Anaconda.org 以使用私有频道和包。还没有账号？点击')
    if 'Do you want to install the package in an existing ' in text:
        snippets['Do you want to install the package in an existing environment or '] = '要将此包安装到已有环境，还是'
        snippets['create a new environment?'] = '创建新环境？'
        snippets[' cannot be installed on this environment.'] = ' 不适用于当前环境。'
    parts = re.split(r'(<[^>]+>)', text)
    for index in range(0, len(parts), 2):
        original = html.unescape(parts[index])
        translated = snippets.get(original, tr_ui(original))
        stripped = original.strip()
        about = {'Copyright © 2016 Anaconda, Inc.': '版权所有 © 2016 Anaconda, Inc.',
                 'Created by Anaconda': '由 Anaconda 开发',
                 'For bug reports and feature requests, please visit our': '报告问题或提出功能建议，请访问我们的'}
        if stripped in about:
            translated = original.replace(stripped, about[stripped])
        if translated != original:
            parts[index] = html.escape(translated, quote=False)
    return ''.join(parts)


def _class_is(obj, module: str, name: str) -> bool:
    return any(cls.__module__ == module and cls.__name__ == name for cls in type(obj).__mro__)


CONTENT_WIDGETS = {
    ('anaconda_navigator.widgets.lists.apps', 'LabelApplicationDescription'),
    ('anaconda_navigator.widgets.lists.content', 'LabelContentTitle'),
    ('anaconda_navigator.widgets.lists.content', 'ButtonContentText'),
}
DISPLAY_NAMES = {
    'anaconda_prompt': 'Anaconda 命令提示符',
    'Qt Console': 'Qt 控制台',
    'Anaconda Toolbox': 'Anaconda 工具箱',
    'Anaconda Cloud Notebooks': 'Anaconda 云端笔记本',
    'PyCharm Community': 'PyCharm 社区版', 'PyCharm Professional': 'PyCharm 专业版',
    'Oracle Data Science Service': 'Oracle 数据科学服务',
    'CMD.exe Prompt': 'CMD 命令提示符', 'Powershell Prompt': 'PowerShell 命令提示符',
}


def is_content_widget(widget) -> bool:
    return any((cls.__module__, cls.__name__) in CONTENT_WIDGETS for cls in type(widget).__mro__)


def display_text(widget, text, static_translator):
    if _class_is(widget, 'anaconda_navigator.widgets.lists.apps', 'LabelApplicationName'):
        return DISPLAY_NAMES.get(text, text)
    if is_content_widget(widget):
        translated = tr_content(text)
        return static_translator(text) if translated == text else translated
    return static_translator(text)


PACKAGE_FILTER_LABELS = {
    'Installed': '已安装', 'Not installed': '未安装', 'Updatable': '可更新',
    'Selected': '已选择', 'All': '全部',
}


def is_package_filter(widget) -> bool:
    return _class_is(widget, 'anaconda_navigator.widgets.manager.packages', 'ComboBoxPackageFilter')


def package_filter_display_text(widget) -> str:
    value = widget.currentText()
    return PACKAGE_FILTER_LABELS.get(value, value) if is_package_filter(widget) else value


def localized_file_filter(value: str) -> str:
    """Translate human filter labels; preserve wildcard expressions byte-for-byte."""
    result = []
    labels = {'Conda environment files': 'Conda 环境文件', 'All files': '所有文件',
              'All Files': '所有文件', 'Environment files': '环境文件',
              'Environment specification': '环境规格', 'Conda explicit specification': 'Conda 显式规格',
              'Conda explicit specification files': 'Conda 显式规格文件', 'Pip requirement files': 'Pip 依赖文件',
              'YAML files': 'YAML 文件', 'JSON files': 'JSON 文件', 'Text files': '文本文件'}
    for entry in value.split(';;'):
        full = tr_ui(entry)
        if full != entry and re.findall(r'\([^)]*\)', full) == re.findall(r'\([^)]*\)', entry):
            result.append(full)
            continue
        match = re.fullmatch(r'(.*?)(\s*\([^)]*\))', entry)
        if match:
            label, patterns = match.groups()
            result.append(labels.get(label, tr_ui(label)) + patterns)
        else:
            result.append(labels.get(entry, tr_ui(entry)))
    return ';;'.join(result)


_TRANSLATOR = None


@lru_cache(maxsize=1)
def qt_catalog():
    """Read the pinned, unmodified official QtBase TS catalog without a compiler."""
    path = ROOT / 'assets/qttranslations/qtbase_zh_CN.ts'
    if not path.is_file():
        return {}
    entries = {}
    for context in ET.parse(path).getroot().findall('context'):
        name = context.findtext('name', '')
        for message in context.findall('message'):
            source = message.findtext('source', '')
            translation = message.find('translation')
            if translation is None or translation.get('type') in {'unfinished', 'obsolete', 'vanished'}:
                continue
            forms = translation.findall('numerusform')
            target = ''.join((forms[0] if forms else translation).itertext())
            if not target:
                continue
            # A bad placeholder must not corrupt a Qt path/number/message value.
            if sorted(re.findall(r'%(?:L?\d+|n)', source)) != sorted(re.findall(r'%(?:L?\d+|n)', target)):
                continue
            comment = message.findtext('comment', '')
            entries[(name, source, comment)] = target
            if not comment:
                entries[(name, source, '')] = target
    return entries


def ensure_display_fonts():
    """Offscreen Qt can have no font database; read system fonts, never ship them."""
    from PySide6 import QtGui
    if QtGui.QFontDatabase.families() or os.name != 'nt':
        return
    fonts = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'
    for name in ('msyh.ttc', 'msyhbd.ttc', 'segoeui.ttf'):
        path = fonts / name
        if path.is_file():
            QtGui.QFontDatabase.addApplicationFont(str(path))


def install_qt_translator():
    global _TRANSLATOR
    from PySide6 import QtCore, QtWidgets
    app = QtWidgets.QApplication.instance()
    if app is None or _TRANSLATOR is not None:
        return
    ensure_display_fonts()
    native = {
        'OK': '确定', '&OK': '确定', 'Cancel': '取消', '&Cancel': '取消', 'Yes': '是', '&Yes': '是',
        'No': '否', '&No': '否', 'Open': '打开', '&Open': '打开', 'Save': '保存', '&Save': '保存',
        'Save All': '全部保存', 'Close': '关闭', '&Close': '关闭', 'Discard': '放弃',
        'Apply': '应用', '&Apply': '应用', 'Reset': '重置', 'Restore Defaults': '恢复默认值',
        'Help': '帮助', 'Retry': '重试', 'Ignore': '忽略', 'Abort': '中止',
        'Look in:': '查找位置：', 'File name:': '文件名：', 'Files of type:': '文件类型：',
        'All Files (*)': '所有文件 (*)', 'Show ': '显示 ', 'Name': '名称', 'Size': '大小',
        'Type': '类型', 'Date Modified': '修改日期', 'Back': '返回', 'Forward': '前进',
        'Parent Directory': '上级目录', 'Create New Folder': '新建文件夹', 'List View': '列表视图',
        'Detail View': '详细信息', 'Folder': '文件夹', 'Open File': '打开文件', 'Save As': '另存为',
        'Select All': '全选', '&Select All': '全选', 'Undo': '撤销', '&Undo': '撤销',
        'Redo': '重做', '&Redo': '重做', 'Cut': '剪切', 'Cu&t': '剪切', 'Copy': '复制',
        '&Copy': '复制', 'Paste': '粘贴', '&Paste': '粘贴', 'Delete': '删除', 'Delete...': '删除…',
        '&Delete': '删除', 'Rename': '重命名', '&Rename': '重命名', 'Show Details...': '显示详情…',
        'Hide Details...': '隐藏详情…', 'New Folder': '新建文件夹', 'Find Directory': '选择目录',
    }
    contexts = {'QPlatformTheme', 'QDialogButtonBox', 'QFileDialog', 'QMessageBox',
                'QLineEdit', 'QWidgetTextControl', 'QTextControl', 'QFileSystemModel',
                'QFileSystemModelPrivate', 'QProgressDialog'}

    class NativeTranslator(QtCore.QTranslator):
        def isEmpty(self):
            return False

        def translate(self, context, source_text, disambiguation=None, n=-1):
            catalog = qt_catalog()
            target = catalog.get((context, source_text, disambiguation or ''), '')
            if target:
                return target
            if context in contexts:
                return native.get(source_text, UI_ZH.get(source_text, ''))
            return ''

    translator = NativeTranslator(app)
    _TRANSLATOR = translator
    if not app.installTranslator(translator):
        _TRANSLATOR = None
        raise RuntimeError('Qt native translation installation failed')


def remove_qt_translator():
    global _TRANSLATOR
    if _TRANSLATOR is not None:
        from PySide6 import QtWidgets
        app = QtWidgets.QApplication.instance()
        if app is not None:
            app.removeTranslator(_TRANSLATOR)
        _TRANSLATOR = None


def install_content_hooks(patch):
    """Patch only public-card display, summaries, search and audited graphics."""
    from PySide6 import QtCore, QtGui, QtWidgets
    # Navigator 2.7.1 selects this backend in its official entry point too.
    os.environ['QT_API'] = 'pyside6'
    from anaconda_navigator import widgets
    from anaconda_navigator.widgets.lists.content import ListItemContent
    from anaconda_navigator.widgets.tabs.community import CommunityTab
    from anaconda_navigator.widgets.manager.model import CondaPackagesModel
    from nav_assets import badge_kind, localized_badge, localized_sidebar, is_quickstart_banner, BADGE_LABELS, SIDEBAR_TEXT

    original_summary_html = QtGui.QTextDocument.setHtml

    def summary_html(self, value):
        parent = self.parent()
        if parent is not None and _class_is(parent, 'anaconda_navigator.widgets.lists.content', 'FrameContentHover'):
            value = tr_rich_content(value)
        return original_summary_html(self, value)

    patch(QtGui.QTextDocument, 'setHtml', summary_html)
    original_card_init = ListItemContent.__init__

    def card_init(self, *args, **kwargs):
        original_card_init(self, *args, **kwargs)
        self.frame_hover.summary = tr_rich_content(self.frame_hover.summary)

    patch(ListItemContent, '__init__', card_init)
    original_thumbnail = ListItemContent.update_thumbnail

    def thumbnail(self, pixmap=None):
        kind = badge_kind(self.banner) or badge_kind(self.path)
        if kind:
            size = QtCore.QSize(max(100, self.frame_icon.width() - 2), max(60, self.frame_icon.height() - 2))
            pixmap = localized_badge(kind, size)
            self.label_icon.setAccessibleName(BADGE_LABELS[kind])
        return original_thumbnail(self, pixmap)

    patch(ListItemContent, 'update_thumbnail', thumbnail)
    original_ad = widgets.LabelImageLinkVertical.__init__

    def advertisement(self, text, url, image, width, height, margin):
        original_ad(self, tr_content(text), url, image, width, height, margin)
        if is_quickstart_banner(image, url):
            self.image_label.setPixmap(localized_sidebar(QtCore.QSize(width, height)))
            self.image_label.setAccessibleName(SIDEBAR_TEXT)
            self.image_label.setToolTip(SIDEBAR_TEXT)

    patch(widgets.LabelImageLinkVertical, '__init__', advertisement)
    original_filter = CommunityTab._CommunityTab__filter_content

    def content_filter(self):
        original_filter(self)
        query = self._CommunityTab__text_filter.text().casefold()
        if not re.search(r'[\u3400-\u9fff]', query):
            return
        tokens = [part for part in re.split(r'\W', query) if part.strip()]
        tags = {w.objectName().lower() for w in self._CommunityTab__filter_widgets if w.isChecked()}
        listing = self._CommunityTab__list
        for index in range(listing.count()):
            item = listing.item(index)
            searchable = ' '.join((item.title, item.summary, item.venue, ' '.join(item.authors),
                                   tr_content(item.title), tr_content(item.summary))).casefold()
            matches = all(token in searchable for token in tokens) and any(str(tag).lower() in tags for tag in item.tags)
            item.setHidden(not matches)

    patch(CommunityTab, '_CommunityTab__filter_content', content_filter)
    original_header = CondaPackagesModel.headerData

    def package_header(self, section, orientation, role=QtCore.Qt.ItemDataRole.DisplayRole):
        value = original_header(self, section, orientation, role)
        if role in (QtCore.Qt.ItemDataRole.DisplayRole, QtCore.Qt.ItemDataRole.ToolTipRole) and isinstance(value, str):
            from zhcn_boot import tr
            return tr(value)
        return value

    patch(CondaPackagesModel, 'headerData', package_header)
    original_data = CondaPackagesModel.data

    def package_data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        value = original_data(self, index, role)
        if role == QtCore.Qt.ItemDataRole.ToolTipRole and isinstance(value, str):
            from zhcn_boot import tr
            return tr(value)
        return value  # names, versions, summaries and status codes remain model data

    patch(CondaPackagesModel, 'data', package_data)
    original_set_filters = QtWidgets.QFileDialog.setNameFilters
    original_selected_filter = QtWidgets.QFileDialog.selectedNameFilter
    original_select_filter = QtWidgets.QFileDialog.selectNameFilter

    def set_filters(self, filters):
        translated = [localized_file_filter(value) for value in filters]
        # Ambiguous labels cannot be reverse-mapped reliably; keep those original.
        for index, value in enumerate(translated):
            if translated.count(value) > 1:
                translated[index] = filters[index]
        self._zhcn_filter_reverse = dict(zip(translated, filters))
        return original_set_filters(self, translated)

    def set_filter(self, value):
        return set_filters(self, value.split(';;'))

    def selected_filter(self):
        value = original_selected_filter(self)
        return getattr(self, '_zhcn_filter_reverse', {}).get(value, value)

    def select_filter(self, value):
        reverse = getattr(self, '_zhcn_filter_reverse', {})
        forward = {original: translated for translated, original in reverse.items()}
        return original_select_filter(self, forward.get(value, value))

    patch(QtWidgets.QFileDialog, 'setNameFilters', set_filters)
    patch(QtWidgets.QFileDialog, 'setNameFilter', set_filter)
    patch(QtWidgets.QFileDialog, 'selectedNameFilter', selected_filter)
    patch(QtWidgets.QFileDialog, 'selectNameFilter', select_filter)

    def wrap_file_dialog(name):
        original = getattr(QtWidgets.QFileDialog, name)

        def invoke(*args, **kwargs):
            from zhcn_boot import tr
            changed = list(args)
            if len(changed) > 1:
                changed[1] = tr(changed[1])
            elif 'caption' in kwargs:
                kwargs['caption'] = tr(kwargs['caption'])
            filters = changed[3] if len(changed) > 3 else kwargs.get('filter', '')
            reverse = {}
            if isinstance(filters, str) and filters:
                translated = localized_file_filter(filters)
                reverse = dict(zip(translated.split(';;'), filters.split(';;')))
                if len(changed) > 3:
                    changed[3] = translated
                else:
                    kwargs['filter'] = translated
                if 'selectedFilter' in kwargs:
                    forward = {value: key for key, value in reverse.items()}
                    kwargs['selectedFilter'] = forward.get(kwargs['selectedFilter'], kwargs['selectedFilter'])
                if len(changed) > 4 and isinstance(changed[4], str):
                    forward = {value: key for key, value in reverse.items()}
                    changed[4] = forward.get(changed[4], changed[4])
            result = original(*changed, **kwargs)
            if isinstance(result, tuple) and len(result) == 2:
                return result[0], reverse.get(result[1], result[1])
            return result

        patch(QtWidgets.QFileDialog, name, staticmethod(invoke))

    for name in ('getOpenFileName', 'getOpenFileNames', 'getSaveFileName', 'getExistingDirectory'):
        wrap_file_dialog(name)
    original_paint = QtWidgets.QComboBox.paintEvent

    def package_paint(self, event):
        if not is_package_filter(self):
            return original_paint(self, event)
        option = QtWidgets.QStyleOptionComboBox()
        self.initStyleOption(option)
        option.currentText = package_filter_display_text(self)
        if self.property('_zhcn_display_text') != option.currentText:
            self.setProperty('_zhcn_display_text', option.currentText)
        painter = QtWidgets.QStylePainter(self)
        painter.drawComplexControl(QtWidgets.QStyle.ComplexControl.CC_ComboBox, option)
        painter.drawControl(QtWidgets.QStyle.ControlElement.CE_ComboBoxLabel, option)

    patch(QtWidgets.QComboBox, 'paintEvent', package_paint)
    original_app_init = QtWidgets.QApplication.__init__

    def application_init(self, *args, **kwargs):
        original_app_init(self, *args, **kwargs)
        install_qt_translator()

    patch(QtWidgets.QApplication, '__init__', application_init)
    install_qt_translator()
