"""Native SVG render, source identity, and text-layout regressions."""
import os
from pathlib import Path
import unittest
from xml.etree import ElementTree as ET
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6 import QtCore, QtGui, QtSvg
import nav_assets


class LocalizedAssetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtGui.QGuiApplication.instance() or QtGui.QGuiApplication([])

    def test_category_matching_is_explicit(self):
        prefix = 'https://anaconda.com/api/navigator/static/community/'
        self.assertEqual(nav_assets.badge_kind(prefix + 'anaconda-course.37528.svg'), 'course')
        self.assertEqual(nav_assets.badge_kind(prefix + 'anaconda-learning-path.b7525.svg?ignored=1'), 'learning_path')
        self.assertEqual(nav_assets.badge_kind('6634f6a6_anaconda-certification.aed3f.svg'), 'certification')
        self.assertIsNone(nav_assets.badge_kind('https://example.com/api/navigator/static/community/anaconda-course.37528.svg'))
        self.assertIsNone(nav_assets.badge_kind(prefix + 'python.28c36.png'))
        self.assertIsNone(nav_assets.badge_kind(prefix + 'anaconda-course.unknown.svg'))

    def test_unknown_advertisement_is_never_replaced(self):
        self.assertFalse(nav_assets.is_quickstart_banner(b'unknown'))
        self.assertFalse(nav_assets.is_quickstart_banner(None))
        self.assertFalse(nav_assets.is_quickstart_banner('not bytes'))
        self.assertEqual(len(nav_assets.QUICKSTART_IMAGE_SHA256), 64)

    def test_known_image_keeps_redirect_semantics_and_bad_urls_are_ignored(self):
        with patch.object(nav_assets.hashlib, 'sha256') as digest:
            digest.return_value.hexdigest.return_value = nav_assets.QUICKSTART_IMAGE_SHA256
            self.assertTrue(nav_assets.is_quickstart_banner(b'known', 'https://anaconda.com/products/navigator/quick-start-environments?preserved=1'))
            self.assertFalse(nav_assets.is_quickstart_banner(b'known', 'https://example.com/products/navigator/quick-start-environments'))
            self.assertFalse(nav_assets.is_quickstart_banner(b'known', 'https://[broken'))
            self.assertFalse(nav_assets.is_quickstart_banner(b'known', 123))
        self.assertIsNone(nav_assets.badge_kind('https://[broken'))

    def test_every_category_has_visible_chinese_native_asset(self):
        for kind, title in nav_assets.BADGE_LABELS.items():
            with self.subTest(kind=kind):
                path = nav_assets.ASSET_ROOT / ('badge_' + kind + '.svg')
                root = ET.fromstring(path.read_text(encoding='utf-8'))
                labels = [x.attrib['aria-label'] for x in root.iter() if 'aria-label' in x.attrib]
                self.assertIn(title, labels)
                self.assertNotIn('COURSE', labels)
                self.assertNotIn('LEARNING PATH', labels)
                renderer = QtSvg.QSvgRenderer(str(path))
                self.assertTrue(renderer.isValid())
                bounds = renderer.boundsOnElement('category-text')
                self.assertGreater(bounds.width(), 0)
                self.assertGreater(bounds.height(), 0)
                self.assertGreaterEqual(bounds.left(), 0)
                self.assertLessEqual(bounds.right(), 480)
                self.assertLessEqual(bounds.bottom(), 270)
                for size in [(150, 85), QtCore.QSize(220, 124), (480, 270)]:
                    pixmap = nav_assets.localized_badge(kind, size)
                    self.assertFalse(pixmap.isNull())
                    self.assertEqual((pixmap.width(), pixmap.height()), nav_assets._dimensions(size))

    def test_sidebar_contains_complete_translated_message(self):
        path = nav_assets.ASSET_ROOT / 'sidebar_quickstart.svg'
        root = ET.fromstring(path.read_text(encoding='utf-8'))
        labels = [x.attrib['aria-label'] for x in root.iter() if 'aria-label' in x.attrib]
        for expected in ['Anaconda', '快速起步环境', '按项目或行业', '选用预配置环境', '理清依赖，快速开发', '启动环境']:
            self.assertIn(expected, labels)
        renderer = QtSvg.QSvgRenderer(str(path))
        self.assertTrue(renderer.isValid())
        for node in root.iter():
            if 'aria-label' in node.attrib:
                box = renderer.boundsOnElement(node.attrib['id'])
                self.assertGreaterEqual(box.left(), 0)
                self.assertLessEqual(box.right(), 243)
                self.assertGreaterEqual(box.top(), 0)
                self.assertLessEqual(box.bottom(), 243)
        for size in [(150, 150), (190, 190), (243, 243)]:
            self.assertFalse(nav_assets.localized_sidebar(size).isNull())

    def test_unknown_kinds_and_empty_sizes_are_explicit_errors(self):
        with self.assertRaises(ValueError):
            nav_assets.localized_badge('arbitrary-photo', (150, 85))
        with self.assertRaises(ValueError):
            nav_assets.localized_badge('course', (0, 0))


if __name__ == '__main__':
    unittest.main()
