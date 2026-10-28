"""Set JupyterLab's translation-extension locale, preserving unrelated settings.

Use the Python interpreter that runs JupyterLab. Existing JSON/JSON5 settings are
backed up byte-for-byte before the first change; changed JSON5 is emitted as JSON.
"""
from __future__ import annotations

import argparse
from importlib import metadata
import json
import os
from pathlib import Path
import tempfile


def read_settings(path: Path) -> dict:
    if not path.exists():
        return {}
    source = path.read_text(encoding='utf-8-sig')
    try:
        result = json.loads(source)
    except json.JSONDecodeError:
        import json5  # supplied by JupyterLab; needed for commented user settings
        result = json5.loads(source, allow_duplicate_keys=False)
    if not isinstance(result, dict):
        raise ValueError(f'Settings must be a JSON object: {path}')
    return result


def atomic_write_settings(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = path.with_name(path.name + '.bak_zhcn')
    if path.is_file() and not backup.exists():
        with backup.open('xb') as handle:
            handle.write(path.read_bytes())
    fd, temporary = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def configure(settings_dir: Path, locale: str = 'zh_CN', *, dry_run: bool = False,
              legacy_config: Path | None = None) -> dict:
    """Update the actual plugin setting, optionally remove only legacy Language."""
    available = {'en', 'default'} | {
        point.name.replace('-', '_') for point in metadata.entry_points(group='jupyterlab.languagepack')
    }
    locale = locale.replace('-', '_')
    if locale not in available:
        raise ValueError(f'Language pack not installed for {locale!r}; available={sorted(available)}')
    target = settings_dir.resolve() / '@jupyterlab/translation-extension/plugin.jupyterlab-settings'
    current = read_settings(target)
    changed = current.get('locale') != locale
    legacy = read_settings(legacy_config) if legacy_config is not None else None
    legacy_changed = legacy is not None and 'Language' in legacy
    if changed and not dry_run:
        atomic_write_settings(target, dict(current, locale=locale))
    if legacy_changed and not dry_run:
        legacy.pop('Language')
        atomic_write_settings(legacy_config, legacy)
    return dict(settings_path=str(target), locale=locale, changed=changed,
                legacy_language_removed=legacy_changed, dry_run=dry_run)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--locale', default='zh_CN')
    parser.add_argument('--settings-dir', type=Path, help='JupyterLab user-settings root')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--clean-legacy-language', action='store_true',
                        help='Remove only the ignored top-level Language key from jupyter_config.json')
    parser.add_argument('--legacy-config', type=Path, help='Explicit legacy JSON path (requires --clean-legacy-language)')
    args = parser.parse_args(argv)
    if args.legacy_config and not args.clean_legacy_language:
        parser.error('--legacy-config requires --clean-legacy-language')
    from jupyterlab.commands import get_user_settings_dir
    from jupyter_core.paths import jupyter_config_dir
    settings = args.settings_dir if args.settings_dir is not None else Path(get_user_settings_dir())
    legacy = None
    if args.clean_legacy_language:
        legacy = args.legacy_config or Path(jupyter_config_dir()) / 'jupyter_config.json'
    result = configure(settings, args.locale, dry_run=args.dry_run, legacy_config=legacy)
    for key, value in result.items():
        print(f'{key.upper()}={value}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
