"""Every Qt replacement stage must roll back, not just one sample stage."""
import unittest
from unittest.mock import patch

from PySide6 import QtWidgets
import zhcn_boot as engine


class TransactionMatrixTests(unittest.TestCase):
    def test_failure_before_and_after_every_replacement(self):
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        engine.uninstall()
        engine.apply()
        classes = {entry[0] for entry in engine._PATCHES}
        stages = len(engine._PATCHES)
        engine.uninstall()
        baseline = {cls: dict(vars(cls)) for cls in classes}
        original = engine._patch
        for after in (False, True):
            for fault_at in range(1, stages + 1):
                with self.subTest(after=after, fault_at=fault_at):
                    calls = 0

                    def fail(cls, name, value):
                        nonlocal calls
                        calls += 1
                        if calls == fault_at and not after:
                            raise RuntimeError('stage fault before assignment')
                        original(cls, name, value)
                        if calls == fault_at and after:
                            raise RuntimeError('stage fault after assignment')

                    try:
                        with patch.object(engine, '_patch', fail):
                            with self.assertRaises(RuntimeError):
                                engine.apply()
                        self.assertFalse(engine._APPLIED)
                        self.assertEqual(engine._PATCHES, [])
                        for cls in classes:
                            self.assertEqual(dict(vars(cls)), baseline[cls], cls.__name__)
                        label = QtWidgets.QLabel('Home')
                        self.assertEqual(label.text(), 'Home')
                    finally:
                        engine.uninstall()
        print(f'FAULT_MATRIX={stages} stages x 2 boundaries; all restored')


if __name__ == '__main__':
    unittest.main()
