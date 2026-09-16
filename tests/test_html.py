import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from review_workbench import prepare
from render_report import render


class HtmlTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.run, self.src, self.analysis, self.out = [self.root / p for p in ('run', 'reviews.jsonl', 'analysis.json', 'report.html')]
        self.src.write_text(json.dumps(dict(id='S1', title='<script>alert(1)</script>', content='A specific scenario.',
                                           date='2026-01-01', skus=[], verified=None, vine=None, images=[])))
        prepare(self.src, self.run, 'DEMO', 'US')
        self.data = dict(author='waytoaic', completion='complete', reviewed_ids=['S1'], findings=[dict(
            id='P1', problem='Uncertain <img onerror=alert(1)>', people='unknown', scene='a scenario', need='inferred',
            solution='current product', confidence_reason='synthetic only', next_test='reproduce', support_ids=['S1'],
            counter_ids=[], quotes=[dict(review_id='S1', text='A specific scenario.')], gaps=['real data'],
            status='hypothesis', applicability='unknown')], actions=[dict(type=t, finding_ids=['P1'], status='hypothesis',
            proposal='possible action', verification='test first', acceptance='proposed criterion', gaps=['input'])
            for t in ['new_product','product_iteration','listing','search_terms','asin_targeting']])

    def run_render(self):
        self.analysis.write_text(json.dumps(self.data))
        render(self.run, self.analysis, self.out)
        return self.out.read_text()

    def test_five_dynamic_panels_and_no_external_resources(self):
        page = self.run_render()
        self.assertEqual(page.count('role="tabpanel"'), 5)
        self.assertNotIn('<script src=', page)
        self.assertNotIn('<link ', page)
        self.assertIn('显示 1 / 1 条', page)

    def test_untrusted_text_is_escaped_and_unknown_flags_stay_unknown(self):
        page = self.run_render()
        self.assertNotIn('<img onerror=', page)
        self.assertNotIn('<script>alert(1)', page)
        self.assertIn('&lt;script&gt;', page)
        self.assertIn('Vine 未知', page)
        self.assertIn('VP 未知', page)

    def test_invalid_evidence_refuses_output(self):
        self.data['findings'][0]['support_ids']=['invented']
        with self.assertRaises(ValueError): self.run_render()
        self.assertFalse(self.out.exists())

    def test_empty_analysis_does_not_invent_cards(self):
        self.data.update(findings=[],actions=[],reviewed_ids=[],completion='partial')
        page=self.run_render()
        self.assertNotIn('role="tabpanel"',page)
        self.assertIn('显示 0 / 0 条',page)


if __name__=='__main__': unittest.main()
