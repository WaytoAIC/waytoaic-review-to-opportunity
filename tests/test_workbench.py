"""Regression tests using synthetic records; author: waytoaic."""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('workbench', Path(__file__).resolve().parents[1] / 'scripts/review_workbench.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source, self.run = self.root / 'input.jsonl', self.root / 'run'
        self.rows = [dict(id='R1', title='Hard to clean', content='The vacuum lifts the edge.', date='2026-01-01',
                         skus=['Color: Green', "Size: 3‘ x 7‘"], verified=True, vine=False, images=[]),
                     dict(id='R2', title='Works well', content='Easy to vacuum.', date='2026-01-02',
                         skus=['Color: Blue', "Size: 3'x7'"], verified=None, vine=True, images=[])]

    def prepare(self):
        self.source.write_text('\n'.join(json.dumps(r) for r in self.rows))
        return w.prepare(self.source, self.run, 'TEST', 'US', 'Green', "3'x7'")

    def analysis(self):
        return dict(author='waytoaic', completion='complete', reviewed_ids=['R1', 'R2'], findings=[dict(
            id='P1', problem='Difficult cleaning', support_ids=['R1'], counter_ids=['R2'],
            quotes=[dict(review_id='R1', text='vacuum lifts the edge')], applicability='target', status='hypothesis',
            people='unknown', scene='vacuuming', need='easy cleaning', solution='rug',
            confidence_reason='specific edge report; counterexample differs in color', gaps=['duration'], next_test='test exact variant')],
            actions=[dict(type='product_iteration', finding_ids=['P1'], status='hypothesis', proposal='test edge stability',
                          verification='compare same tool and floor', acceptance='proposed: no extra edge holding', gaps=['actual sample'])])

    def check(self, data):
        path = self.root / 'analysis.json'
        path.write_text(json.dumps(data))
        return w.check(self.run, path)

    def test_realistic_flow_and_variant_normalization(self):
        stats = self.prepare()
        self.assertEqual(stats['exact_target'], 1)
        self.assertEqual(self.check(self.analysis())['structural_check'], 'passed')

    def test_duplicate_merges_images_and_does_not_count_people(self):
        duplicate = copy.deepcopy(self.rows[0]); duplicate.update(id='R3', images=['https://example.org/review.jpg'])
        self.rows.append(duplicate)
        stats = self.prepare()
        self.assertEqual(stats['record_count'], 2)
        self.assertEqual(stats['images_available'], 1)
        self.assertIsNone(stats['independent_people'])
        self.assertEqual(stats['aliases']['R3'], 'R1')

    def test_conflicting_ids_rejected_before_write(self):
        self.rows[1]['id'] = 'R1'
        with self.assertRaisesRegex(ValueError, 'conflicting id'): self.prepare()
        self.assertFalse(self.run.exists())

    def test_string_false_rejected(self):
        self.rows[0]['vine'] = 'false'
        with self.assertRaisesRegex(ValueError, 'boolean'): self.prepare()

    def test_missing_body_is_not_invented(self):
        self.rows[0]['content'] = None
        stats = self.prepare()
        self.assertEqual(stats['missing_body'], 1)

    def test_reentry_checks_input_and_artifacts(self):
        first = self.prepare()
        self.assertEqual(self.prepare(), first)
        self.rows[0]['content'] += ' changed'
        with self.assertRaisesRegex(ValueError, 'different input'): self.prepare()

    def test_artifact_corruption_detected(self):
        self.prepare()
        (self.run / 'reviews.jsonl').write_text('{}\n')
        with self.assertRaisesRegex(ValueError, 'changed/missing'): self.check(self.analysis())

    def test_unknown_reference_rejected(self):
        self.prepare(); data = self.analysis(); data['findings'][0]['support_ids'] = ['invented']
        with self.assertRaisesRegex(ValueError, 'unknown id'): self.check(data)

    def test_fake_quote_rejected(self):
        self.prepare(); data = self.analysis(); data['findings'][0]['quotes'][0]['text'] = 'machine washable forever'
        with self.assertRaisesRegex(ValueError, 'not found'): self.check(data)

    def test_partial_cannot_claim_complete(self):
        self.prepare(); data = self.analysis(); data['reviewed_ids'] = ['R1']
        with self.assertRaisesRegex(ValueError, 'every record'): self.check(data)

    def test_other_variant_cannot_claim_target(self):
        self.prepare(); data = self.analysis(); f = data['findings'][0]
        f.update(support_ids=['R2'], counter_ids=[], quotes=[])
        with self.assertRaisesRegex(ValueError, 'exact variant'): self.check(data)

    def test_business_confirmation_requires_record(self):
        self.prepare(); data = self.analysis(); data['findings'][0]['status'] = 'business_confirmed'
        with self.assertRaisesRegex(ValueError, 'human_confirmation'): self.check(data)

    def test_action_requires_success_criterion(self):
        self.prepare(); data = self.analysis(); del data['actions'][0]['acceptance']
        with self.assertRaisesRegex(ValueError, 'acceptance'): self.check(data)

    def test_duplicate_boolean_conflict_not_silently_merged(self):
        dupe = copy.deepcopy(self.rows[0]); dupe.update(id='R3', vine=True); self.rows.append(dupe)
        with self.assertRaisesRegex(ValueError, 'conflicting vine'): self.prepare()


if __name__ == '__main__':
    unittest.main()
