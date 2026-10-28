# -*- coding: utf-8 -*-
"""把 PyCharm 的安装路径写进 Navigator 配置，修「已安装但显示未安装」。

Navigator 只在几个固定目录里找 JetBrains 产品：
    C:\\Program Files\\JetBrains
    C:\\Program Files (x86)\\JetBrains
    %LOCALAPPDATA%\\Programs
    %LOCALAPPDATA%\\JetBrains\\Toolbox\\apps
装在 D 盘或任意自定义目录时，它找不到，卡片就一直显示「安装」。
配置文件里的 [applications] 段可以手工指定路径，这个脚本负责发现并写入。

用法（必须用 Anaconda 自带的 python）：
    D:\\anaconda3\\python.exe fix_pycharm.py            # 自动发现并写入
    D:\\anaconda3\\python.exe fix_pycharm.py "路径"     # 指定安装目录
"""
from __future__ import annotations

import configparser
import json
import os
import pathlib
import sys

CONF = pathlib.Path(os.environ['APPDATA']) / '.anaconda' / 'navigator' / 'anaconda-navigator.ini'

# productCode -> 配置键（见 base_apps.yml：PY=专业版，PC=社区版，PE=教育版）
KEY_BY_CODE = {'PY': 'pycharm_pro_path', 'PC': 'pycharm_ce_path', 'PE': 'pycharm_ce_path'}


def find_pycharm(explicit: str | None = None) -> pathlib.Path:
    """定位 PyCharm 安装根目录（含 bin/pycharm64.exe 的那一层）。"""
    if explicit:
        return pathlib.Path(explicit)

    candidates: list[pathlib.Path] = []

    # 1) 桌面 / 开始菜单快捷方式（用户自己建的那个最准）
    for folder in (
        pathlib.Path.home() / 'Desktop',
        pathlib.Path(os.environ['APPDATA']) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs',
    ):
        for lnk in folder.glob('**/pycharm*.lnk'):
            candidates.append(lnk)

    # 2) 常见安装位置
    for drive in 'CDEFG':
        for name in ('PyCharm', 'PyCharm Community', 'JetBrains'):
            root = pathlib.Path(f'{drive}:/')
            if root.is_dir():
                candidates.extend(root.glob(f'{name}*'))
                candidates.extend(root.glob(f'Program Files/JetBrains/{name}*'))

    for item in candidates:
        root = _to_root(item)
        if root is not None:
            return root

    raise SystemExit('未找到 PyCharm，请把安装目录作为参数传进来。')


def _to_root(item: pathlib.Path) -> pathlib.Path | None:
    """把快捷方式或目录统一收敛到「含 product-info.json 的根目录」。"""
    if item.suffix.lower() == '.lnk':
        target = _read_lnk(item)
        if target is None:
            return None
        item = target.parent.parent if target.parent.name == 'bin' else target

    for probe in (item, item / 'bin' / '..'):
        probe = probe.resolve()
        if (probe / 'bin' / 'pycharm64.exe').is_file() and (probe / 'product-info.json').is_file():
            return probe
    return None


def _read_lnk(lnk: pathlib.Path) -> pathlib.Path | None:
    """取 .lnk 的目标路径。用 WScript.Shell，避免解析二进制格式。"""
    try:
        import win32com.client  # type: ignore[import-not-found]
    except ImportError:
        return None
    shell = win32com.client.Dispatch('WScript.Shell')
    target = shell.CreateShortCut(str(lnk)).TargetPath
    return pathlib.Path(target) if target else None


def read_product_code(root: pathlib.Path) -> str:
    """读 product-info.json 拿 productCode（PY / PC / PE）。"""
    data = json.loads((root / 'product-info.json').read_text(encoding='utf-8'))
    return data.get('productCode', 'PY')


def write_config(key: str, root: pathlib.Path) -> bool:
    """把 root 写进 [applications] 段的 key。逐行替换，保持文件其余部分一字不动。"""
    if not CONF.is_file():
        raise SystemExit(f'配置文件不存在：{CONF}\n请先启动一次 Anaconda Navigator。')

    # newline='' 保留原始 \r\n —— 默认的通用换行会把 CRLF 折成 \n，写回就毁了文件
    with CONF.open('r', encoding='utf-8', newline='') as stream:
        raw = stream.read()
    newline = '\r\n' if '\r\n' in raw else '\n'
    lines = raw.split(newline)
    wanted = f'{key} = {root}'
    hits = 0

    for index, line in enumerate(lines):
        if line.split(' = ')[0].strip() == key:
            if line == wanted:
                print(f'已是目标值，无需修改：{line}')
                return False
            print(f'替换：{line!r}\n  ->  {wanted!r}')
            lines[index] = wanted
            hits += 1

    if hits != 1:
        raise SystemExit(f'[applications] 段里没有找到唯一的 {key}，中止（命中 {hits} 处）')

    backup = CONF.with_suffix('.ini.bak_fix_pycharm')
    if not backup.exists():
        backup.write_bytes(CONF.read_bytes())
        print(f'已备份：{backup}')

    with CONF.open('w', encoding='utf-8', newline='') as stream:
        stream.write(newline.join(lines))
    return True


def main() -> None:
    root = find_pycharm(sys.argv[1] if len(sys.argv) > 1 else None)
    code = read_product_code(root)
    key = KEY_BY_CODE.get(code)
    if key is None:
        raise SystemExit(f'未知的 productCode {code!r}（{root}）')

    print(f'安装目录：{root}')
    print(f'版本    ：{json.loads((root / "product-info.json").read_text(encoding="utf-8"))["version"]}')
    print(f'productCode = {code} -> 写 {key}\n')

    if write_config(key, root):
        print('\n完成。重启 Anaconda Navigator 即可看到「启动」按钮。')


if __name__ == '__main__':
    main()
