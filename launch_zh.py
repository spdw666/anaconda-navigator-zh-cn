# -*- coding: utf-8 -*-
"""Anaconda Navigator 简体中文启动器

用法（桌面快捷方式里的命令行）：
    D:\\anaconda3\\pythonw.exe D:\\anaconda3\\cwp.py D:\\anaconda3 ^
        D:\\anaconda3\\pythonw.exe D:\\AnacondaHanhua\\launch_zh.py

本启动器在进程内包装 Qt 文本入口，不修改 anaconda_navigator 源码文件。
兼容性以 README 记录的实测版本和本仓库回归测试结果为准；
想取消汉化，只要让快捷方式指回官方的 anaconda-navigator-script.py。
"""

import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)


def _diagnostic(message):
    """Best-effort diagnostics, including pythonw's absent standard streams."""
    for stream in (getattr(sys, 'stderr', None), getattr(sys, '__stderr__', None)):
        if stream is None:
            continue
        try:
            stream.write(message + '\n')
            return
        except Exception:
            # Closed streams, encoding errors and GUI launchers must not stop main().
            continue


# 1) 先装汉化补丁（必须在任何 Qt 控件被创建之前）
try:
    import zhcn_boot
    zhcn_boot.apply()
except Exception as exc:  # 补丁失败后清理进程内包装，再进入官方入口。
    # apply() rolls back transactionally; uninstall() is an idempotent extra guard.
    if 'zhcn_boot' in globals():
        try:
            zhcn_boot.uninstall()
        except Exception as rollback_exc:
            _diagnostic('[zhcn] rollback failed: {!r}'.format(rollback_exc))
    _diagnostic('[zhcn] patch failed, falling back to English: {!r}'.format(exc))

# 2) 再走官方入口（与 anaconda-navigator-script.py 完全一致）
from anaconda_navigator.app.main import main  # noqa: E402

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(main())
