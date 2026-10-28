"""Chinese, repo-native display assets for known Navigator content graphics.

The original package images and the navigation/click targets are never changed.
Matching is deliberately limited to official category artwork and one audited
Quick Start banner, not arbitrary images containing English product names.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
from pathlib import Path
import re
from urllib.parse import urlsplit


ASSET_ROOT = Path(__file__).resolve().parent / 'assets' / 'zh_cn'
BADGE_LABELS = {
    'course': '课程',
    'learning_path': '学习路径',
    'certification': '认证',
    'documentation': '文档',
    'webinar': '在线讲座',
    'video': '视频',
    'event': '活动',
    'forum': '论坛',
    'social': '社区',
}
SIDEBAR_TEXT = 'Anaconda 快速起步环境。按项目或行业选用预配置环境，理清依赖，快速开发。启动环境。'
QUICKSTART_IMAGE_SHA256 = '39f07fb991120d5f30ac6b1fee8445006b3550ae039281e6c97e8b3c5b25fccb'
_BADGE_BASENAMES = {
    'anaconda-course.37528.svg': 'course',
    'anaconda-learning-path.b7525.svg': 'learning_path',
    'anaconda-certification.aed3f.svg': 'certification',
}


def badge_kind(source: str) -> str | None:
    """Return a category only for an audited official URI or its cache basename."""
    if not isinstance(source, str) or not source:
        return None
    try:
        parts = urlsplit(source)
    except ValueError:
        return None
    if parts.scheme or parts.netloc:
        if parts.scheme != 'https' or parts.hostname not in {'anaconda.com', 'www.anaconda.com'}:
            return None
        prefix = '/api/navigator/static/community/'
        if not parts.path.startswith(prefix):
            return None
        return _BADGE_BASENAMES.get(parts.path[len(prefix):])
    # Navigator's safe_file_name cache adds an eight-hex prefix to the basename.
    name = Path(source.replace('\\', '/')).name
    name = re.sub(r'^[0-9a-f]{8}_', '', name)
    return _BADGE_BASENAMES.get(name)


def is_quickstart_banner(image: bytes | bytearray | memoryview | None,
                         redirect_url: str | None = None) -> bool:
    """Recognize audited image bytes, without depending on tracking query data."""
    if not isinstance(image, (bytes, bytearray, memoryview)):
        return False
    if hashlib.sha256(image).hexdigest() != QUICKSTART_IMAGE_SHA256:
        return False
    if redirect_url:
        if not isinstance(redirect_url, str):
            return False
        try:
            parts = urlsplit(redirect_url)
        except ValueError:
            return False
        if (parts.scheme != 'https' or parts.hostname not in {'anaconda.com', 'www.anaconda.com'}
                or parts.path.rstrip('/') != '/products/navigator/quick-start-environments'):
            return False
    return True


def _dimensions(size) -> tuple[int, int]:
    if hasattr(size, 'width') and hasattr(size, 'height'):
        width, height = size.width(), size.height()
    else:
        width, height = size
    width, height = int(width), int(height)
    if width <= 0 or height <= 0:
        raise ValueError('Display asset size must be positive')
    return width, height


@lru_cache(maxsize=16)
def _svg_bytes(name: str) -> bytes:
    return (ASSET_ROOT / name).read_bytes()


def _render(name: str, size):
    from PySide6 import QtCore, QtGui, QtSvg
    if QtGui.QGuiApplication.instance() is None:
        raise RuntimeError('Create the Qt application before rendering assets')
    width, height = _dimensions(size)
    renderer = QtSvg.QSvgRenderer(QtCore.QByteArray(_svg_bytes(name)))
    if not renderer.isValid():
        raise ValueError(f'Invalid localized SVG: {name}')
    pixmap = QtGui.QPixmap(width, height)
    pixmap.fill(QtCore.Qt.GlobalColor.transparent)
    painter = QtGui.QPainter(pixmap)
    try:
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        renderer.render(painter)
    finally:
        painter.end()
    return pixmap


def localized_badge(kind: str, size):
    """Render an explicitly selected Chinese category as QPixmap at logical size."""
    if kind not in BADGE_LABELS:
        raise ValueError(f'Unknown category: {kind}')
    return _render('badge_' + kind + '.svg', size)


def localized_sidebar(size):
    """Render the audited Quick Start message; caller preserves the original URL."""
    return _render('sidebar_quickstart.svg', size)
