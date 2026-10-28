"""Audit a dated public-content/UI inventory, not just the dictionary's own keys."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import re

from nav_content import CONTENT_ZH, UI_ZH, DISPLAY_NAMES, tr_content, qt_catalog
from zhcn_boot import tr


def audit(path: Path | None = None, live_content: list[Path] | None = None) -> dict:
    path = path or Path(__file__).resolve().with_name('coverage_catalog.json')
    catalog = json.loads(path.read_text(encoding='utf-8'))
    for live in live_content or []:
        data = json.loads(live.read_text(encoding='utf-8-sig'))
        if not isinstance(data, list):
            raise ValueError('Live content must be a list of public card records')
        for item in data:
            for field in ('title', 'subtitle', 'summary', 'description', 'button'):
                value = item.get(field)
                if isinstance(value, str) and value:
                    catalog['rows'].append(dict(kind='content', source=live.name, field=field, text=value))
    preserved = set(catalog['preserve_product_names'])
    counts = Counter()
    missing = []
    for row in catalog['rows']:
        original = row['text']
        if row['kind'] == 'ui':
            translated = tr(original)
        elif row['field'] == 'display_name':
            translated = DISPLAY_NAMES.get(original, tr_content(original))
        else:
            translated = tr_content(original)
        if translated != original:
            counts['translated'] += 1
        elif original in preserved:
            counts['retained_product_names'] += 1
        elif re.search(r'[\u3400-\u9fff]', original) or not re.search('[A-Za-z]', original):
            counts['already_chinese_or_nonlinguistic'] += 1
        else:
            missing.append(row)
    return dict(snapshot_date=catalog['snapshot_date'], sources=catalog['sources'],
                inventoried_fields=len(catalog['rows']), categories=dict(counts),
                content_entries=len(CONTENT_ZH), extra_static_entries=len(UI_ZH),
                qt_native_entries=len(qt_catalog()), missing=missing,
                status='PASS' if not missing else 'FAIL')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--live-content', type=Path, action='append', help='Also audit a current public content.json cache')
    args = parser.parse_args(argv)
    result = audit(args.catalog, args.live_content)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding='utf-8')
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
