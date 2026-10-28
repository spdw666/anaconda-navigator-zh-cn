# -*- coding: utf-8 -*-
"""Run this checkout's isolated regression suite (not another installed copy)."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['QT_API'] = 'pyside6'

import zhcn_boot  # noqa: E402


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    engine = Path(zhcn_boot.__file__).resolve()
    expected = (ROOT / 'zhcn_boot.py').resolve()
    if engine != expected:
        raise RuntimeError('Wrong engine loaded: {!s}; expected {!s}'.format(engine, expected))
    print('ENGINE_PATH=' + str(engine), flush=True)
    print('ENGINE_SHA256=' + hashlib.sha256(engine.read_bytes()).hexdigest(), flush=True)
    if argv == ['--engine-info']:
        return 0
    if argv:
        print('Usage: _verify_patch.py [--engine-info]', file=sys.stderr)
        return 2
    suite = unittest.defaultTestLoader.discover(
        str(ROOT / 'tests'), pattern='test_*.py', top_level_dir=str(ROOT),
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful() and result.skipped:
        print('=== INCOMPLETE: {} TESTS SKIPPED; install the full test dependencies ==='.format(
            len(result.skipped)), flush=True)
        return 1
    if result.wasSuccessful():
        print('=== ALL {} TESTS PASSED (skipped={}) ==='.format(
            result.testsRun, len(result.skipped)), flush=True)
        return 0
    print('=== TESTS FAILED ===', flush=True)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
