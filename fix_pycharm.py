# -*- coding: utf-8 -*-
"""为 Navigator 配置 PyCharm；用法：python fix_pycharm.py [安装目录] [--config INI]。

显式目录与自动发现执行相同校验；完整校验 INI 后只改 applications 段。
缺段/键时补齐，保留已有换行/BOM，首次备份，并在同目录原子替换。
"""
from __future__ import annotations

import argparse
import codecs
import configparser
import ctypes
import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile

CONF = pathlib.Path(os.environ.get('APPDATA', pathlib.Path.home() / 'AppData' / 'Roaming')) / '.anaconda' / 'navigator' / 'anaconda-navigator.ini'
KEY_BY_CODE = {'PY': 'pycharm_pro_path', 'PC': 'pycharm_ce_path', 'PE': 'pycharm_ce_path'}


def _known_folder(csidl: int) -> pathlib.Path | None:
    """读取系统已知文件夹，跟随桌面/开始菜单重定向。"""
    if os.name != 'nt':
        return None
    buffer = ctypes.create_unicode_buffer(32768)
    if ctypes.windll.shell32.SHGetFolderPathW(None, csidl, None, 0, buffer) != 0:
        return None
    return pathlib.Path(buffer.value) if buffer.value else None


def _read_lnk(lnk: pathlib.Path) -> pathlib.Path | None:
    """使用系统 PowerShell/COM，不要求额外 Python 模块。"""
    env = os.environ.copy()
    env['ANACONDA_ZH_SHORTCUT_PROBE'] = str(lnk)
    command = "[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false); $s=New-Object -ComObject WScript.Shell; $s.CreateShortcut($env:ANACONDA_ZH_SHORTCUT_PROBE).TargetPath | ConvertTo-Json -Compress"
    try:
        result = subprocess.run(
            ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command],
            env=env, capture_output=True, encoding='utf-8', timeout=15,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )
        target = json.loads(result.stdout) if result.returncode == 0 else None
        return pathlib.Path(target) if isinstance(target, str) and target else None
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def _product_info(root: pathlib.Path) -> dict:
    data = json.loads((root / 'product-info.json').read_text(encoding='utf-8-sig'))
    if not isinstance(data, dict) or data.get('productCode') not in KEY_BY_CODE:
        raise ValueError('product-info.json 缺少受支持的 productCode（PY/PC/PE）')
    if not isinstance(data.get('version'), str) or not data['version'].strip():
        raise ValueError('product-info.json 缺少有效 version')
    return data


def _to_root(item: pathlib.Path) -> pathlib.Path | None:
    """返回包含 executable 和有效元数据的绝对安装根目录。"""
    try:
        if item.suffix.lower() == '.lnk':
            target = _read_lnk(item)
            if target is None:
                return None
            item = target.parent.parent if target.parent.name.lower() == 'bin' else target
        root = item.expanduser().resolve(strict=True)
        if not (root / 'bin' / 'pycharm64.exe').is_file():
            return None
        _product_info(root)
        return root
    except (OSError, ValueError):
        return None


def find_pycharm(explicit: str | None = None) -> pathlib.Path:
    if explicit:
        root = _to_root(pathlib.Path(explicit))
        if root is None:
            raise SystemExit(f'无效的 PyCharm 安装目录：{explicit}（需 bin/pycharm64.exe 和有效 product-info.json）')
        return root
    candidates: list[pathlib.Path] = []
    for folder in (_known_folder(0x10), _known_folder(0x02)):
        if folder is not None and folder.is_dir():
            candidates.extend(folder.glob('**/pycharm*.lnk'))
    for drive in 'CDEFG':
        root = pathlib.Path(f'{drive}:/')
        if root.is_dir():
            for pattern in ('PyCharm*', 'PyCharm Community*', 'Program Files/JetBrains/PyCharm*'):
                candidates.extend(root.glob(pattern))
    for candidate in candidates:
        root = _to_root(candidate)
        if root is not None:
            return root
    raise SystemExit('未找到有效 PyCharm 安装目录；可将安装根目录作为参数传入。')


def read_product_code(root: pathlib.Path) -> str:
    return _product_info(root)['productCode']


def _parse_ini(raw: str) -> configparser.ConfigParser:
    parser = configparser.ConfigParser(interpolation=None, strict=True)
    parser.read_string(raw)
    return parser


def write_config(key: str, root: pathlib.Path) -> bool:
    """section 限定、全文件重复检查、保留换行、首次备份、原子写入。"""
    valid = _to_root(root)
    if valid is None:
        raise SystemExit(f'无效的 PyCharm 安装目录：{root}')
    root = valid
    if key != KEY_BY_CODE[read_product_code(root)]:
        raise SystemExit('配置键与 PyCharm productCode 不匹配')
    if not CONF.is_file():
        raise SystemExit(f'配置文件不存在：{CONF}\n请先启动一次 Anaconda Navigator。')
    original = CONF.read_bytes()
    raw = original.decode('utf-8-sig')
    try:
        parser = _parse_ini(raw)
    except configparser.Error as error:
        raise SystemExit(f'配置格式校验失败，原文件未改：{error}') from error
    previous = parser.get('applications', key, raw=True, fallback=None)
    match = re.search(r'\r\n|\n|\r', raw)
    newline = match.group() if match else os.linesep
    lines = raw.splitlines(keepends=True)
    section = None
    section_start = section_end = matched = None
    for index, line in enumerate(lines):
        header = re.match(r'^\s*\[([^\]]+)\]', line)
        if header:
            if section == 'applications' and section_end is None:
                section_end = index
            section = header.group(1)
            if section == 'applications':
                section_start = index
            continue
        option = re.match(r'^[ \t]*([^#;\s][^:=]*?)[ \t]*[=:]', line)
        if section == 'applications' and option and option.group(1).strip().lower() == key.lower():
            matched = index
    # Only local options count: ConfigParser.get() also inherits [DEFAULT].
    if matched is not None and previous is not None and ('\r' in previous or '\n' in previous):
        raise SystemExit(f'[applications] 的 {key} 是多行值，原文件未改')
    # strict 解析已完成，重复键不会因第一项已等于目标值而漏检。
    if matched is not None and previous == str(root):
        print(f'已是目标值，无需修改：{key} = {root}')
        return False
    wanted = f'{key} = {root}'
    if matched is not None:
        suffix = re.search(r'(\r\n|\n|\r)$', lines[matched])
        lines[matched] = wanted + (suffix.group() if suffix else '')
    elif section_start is not None:
        insert_at = section_end if section_end is not None else len(lines)
        if insert_at and not lines[insert_at - 1].endswith(('\r', '\n')):
            lines[insert_at - 1] += newline
        lines.insert(insert_at, wanted + newline)
    else:
        if lines and not lines[-1].endswith(('\r', '\n')):
            lines[-1] += newline
        lines.extend(['[applications]' + newline, wanted + newline])
    changed = ''.join(lines)
    if _parse_ini(changed).get('applications', key, raw=True) != str(root):
        raise SystemExit('配置写入前读回校验失败，原文件未改')
    payload = (codecs.BOM_UTF8 if original.startswith(codecs.BOM_UTF8) else b'') + changed.encode('utf-8')
    backup = CONF.with_suffix('.ini.bak_fix_pycharm')
    try:
        with backup.open('xb') as stream:
            stream.write(original)
            stream.flush()
            os.fsync(stream.fileno())
        print(f'已备份：{backup}')
    except FileExistsError:
        pass
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=CONF.parent, prefix=CONF.name + '.', suffix='.tmp', delete=False) as stream:
            temporary = pathlib.Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        shutil.copymode(CONF, temporary)
        if CONF.read_bytes() != original:
            raise SystemExit('配置已被其它进程更新，写入已中止；请关闭 Navigator 后重试')
        os.replace(temporary, CONF)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    if CONF.read_bytes() != payload:
        raise SystemExit('配置保存后字节校验失败')
    print(f'已更新 [applications]：{wanted}')
    return True


def main() -> None:
    global CONF
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', nargs='?', help='PyCharm 安装根目录（支持相对路径）')
    parser.add_argument('--config', type=pathlib.Path, help='Navigator INI 路径')
    args = parser.parse_args()
    if args.config:
        CONF = args.config.expanduser().resolve()
    root = find_pycharm(args.path)
    info = _product_info(root)
    key = KEY_BY_CODE[info['productCode']]
    print(f'安装目录：{root}\n版本：{info["version"]}\nproductCode = {info["productCode"]} -> {key}')
    if write_config(key, root):
        print('配置已验证保存；重启 Anaconda Navigator 后重新探测。')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError) as error:
        raise SystemExit(f'错误：{error}') from error
