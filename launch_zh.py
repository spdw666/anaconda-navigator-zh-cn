# -*- coding: utf-8 -*-
"""Anaconda Navigator 简体中文启动器

用法（桌面快捷方式里的命令行）：
    D:\\anaconda3\\pythonw.exe D:\\anaconda3\\cwp.py D:\\anaconda3 ^
        D:\\anaconda3\\pythonw.exe D:\\AnacondaHanhua\\launch_zh.py

设计：**完全不修改 D:\\anaconda3 里的任何文件**（除了本文件所在目录）。
汉化靠 import 时给 Qt 类打补丁实现，conda 升级/重装都不会破坏程序本体；
想取消汉化，只要让快捷方式指回官方的 anaconda-navigator-script.py。
"""

import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# 1) 先装汉化补丁（必须在任何 Qt 控件被创建之前）
try:
    import zhcn_boot
    zhcn_boot.apply()
except Exception as exc:  # 汉化失败绝不能拖垮 Navigator 本体
    sys.stderr.write('[zhcn] patch failed, falling back to English: {!r}\n'.format(exc))

# 2) 再走官方入口（与 anaconda-navigator-script.py 完全一致）
from anaconda_navigator.app.main import main  # noqa: E402

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(main())
