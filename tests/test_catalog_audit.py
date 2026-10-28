"""Coverage must be tested against independent inputs, and fail on new English."""
import json
from pathlib import Path
import tempfile
import unittest
import coverage_audit


class CatalogAuditTests(unittest.TestCase):
    def test_independent_catalog_has_no_missing_human_fields(self):
        result = coverage_audit.audit()
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['missing'], [])
        self.assertGreaterEqual(result['inventoried_fields'], 500)
        self.assertEqual(result['sources']['unique_titles'], 104)
        self.assertEqual(result['sources']['current_cards'], 99)

    def test_unseen_english_card_makes_coverage_fail(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'content.json'
            text = 'A new unknown English course title which needs translation'
            path.write_text(json.dumps([{'title': text, 'uri': 'https://example.com/unmodified'}]))
            result = coverage_audit.audit(live_content=[path])
            self.assertEqual(result['status'], 'FAIL')
            self.assertEqual([row['text'] for row in result['missing']], [text])

    def test_known_live_card_and_existing_chinese_remain_covered(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'content.json'
            path.write_text(json.dumps([{'title': 'Git Fundamentals', 'button': 'Get Access'},
                                       {'title': '已经是中文的课程'}]))
            result = coverage_audit.audit(live_content=[path])
            self.assertEqual(result['status'], 'PASS')


if __name__ == '__main__':
    unittest.main()
