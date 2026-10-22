# Tests for holiday_recheck.py on six made-up feeds worked out by hand (no network).
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import csv
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import holiday_recheck as hr  # noqa: E402

DAYS = [hr.BASE] + hr.LATER + hr.NEW_YEAR
COLS = ['organization_id', 'feed_id', 'organization_name', 'feed_name', 'pref_name'] + DAYS


def feed(fid, cls):
    r = {'organization_id': 'o', 'feed_id': fid, 'organization_name': 'O', 'feed_name': fid, 'pref_name': 'P'}
    r.update({d: 'outside' for d in DAYS})
    r.update(cls)
    return r


NY_F1 = {'2026-12-29': 'ordinary', '2026-12-30': 'ordinary', '2026-12-31': 'no_service', '2027-01-01': 'no_service',
         '2027-01-02': 'no_service'}
# f1: handles November, ordinary from 2027-01-11 (in the R1 cohort). f2: handles everything. f3: ordinary throughout.
# f4: handles November, standard-id ordinary on 2027-01-11 (in the cohort; gone at the re-check). f5: ordinary on
# 2026-11-23 only. f6: covers nothing.
BEFORE = [
    feed('f1', dict({'2026-11-03': 'sunday', '2026-11-23': 'sunday', '2027-01-11': 'ordinary', '2027-02-11': 'ordinary'},
                    **NY_F1)),
    feed('f2', dict({d: 'sunday' for d in [hr.BASE] + hr.LATER}, **{d: 'no_service' for d in hr.NEW_YEAR})),
    feed('f3', dict({d: 'ordinary' for d in [hr.BASE] + hr.LATER}, **{'2026-12-29': 'ordinary_std', '2026-12-30':
                                                                       'same_as_weekend'})),
    feed('f4', {'2026-11-03': 'no_service', '2026-11-23': 'special', '2027-01-11': 'ordinary_std'}),
    feed('f5', {'2026-11-03': 'sunday', '2026-11-23': 'ordinary', '2027-01-11': 'sunday', '2027-02-11': 'sunday'}),
    feed('f6', {}),
]
# At the re-check f1 handles 2027-01-11 and 2026-12-30, f4 and f6 are gone and f7 is new.
AFTER = [dict(BEFORE[0], **{'2027-01-11': 'sunday', '2026-12-30': 'no_service'}), BEFORE[1], BEFORE[2], BEFORE[4],
         feed('f7', {'2027-01-11': 'ordinary'})]


def keyed(rows):
    return {(r['organization_id'], r['feed_id']): r for r in rows}


class Test(unittest.TestCase):
    def test_sign_p(self):
        self.assertAlmostEqual(hr.sign_p(31, 1), 66 / 2 ** 32)
        self.assertIsNone(hr.sign_p(0, 0))
        self.assertEqual(hr.sign_p(2, 2), 1.0)
        self.assertEqual(hr.sign_p(0, 2), 0.5)

    def test_horizon(self):
        h = {x['date']: x for x in hr.horizon(keyed(BEFORE))}
        self.assertEqual([h['2026-11-23'][k] for k in ('feeds', 'both_handled', 'handled_then_shown',
                                                       'shown_then_handled', 'both_shown')], [5, 3, 1, 0, 1])
        self.assertEqual(h['2026-11-23']['sign_test_p'], 1.0)
        self.assertEqual([h['2027-01-11'][k] for k in ('feeds', 'both_handled', 'handled_then_shown',
                                                       'shown_then_handled', 'both_shown')], [5, 2, 2, 0, 1])
        self.assertEqual(h['2027-01-11']['sign_test_p'], 0.5)
        self.assertEqual([h['2027-02-11'][k] for k in ('feeds', 'both_handled', 'handled_then_shown', 'both_shown')],
                         [4, 2, 1, 1])
        self.assertEqual(h['2027-02-23']['feeds'], 2)
        self.assertIsNone(h['2027-02-23']['sign_test_p'])

    def test_cohort(self):
        self.assertEqual(hr.cohort_r1(keyed(BEFORE)), [('o', 'f1'), ('o', 'f4')])

    def test_predictions(self):
        p = hr.predictions(keyed(BEFORE), keyed(AFTER), '2026-12-15')
        self.assertEqual((p['R1']['cohort'], p['R1']['applicable_after'], p['R1']['handled_after']), (2, 1, 1))
        self.assertFalse(p['R1']['held'])
        # 1 of 3 pairs handled is 33%, not under 25%: R2 does not hold here (the first version of this test said it
        # did, which was the test's mistake; the rule in holiday_recheck.py is unchanged).
        self.assertEqual((p['R2']['pairs'], p['R2']['handled_after'], p['R2']['share']), (3, 1, 0.333))
        self.assertFalse(p['R2']['held'])
        self.assertEqual((p['R3']['shown'], p['R3']['applicable'], p['R3']['share'], p['R3']['share_2026_10_22']),
                         (2, 5, 0.4, 0.6))
        self.assertTrue(p['R3']['held'])
        self.assertTrue(all(x['in_window'] for x in p.values()))
        self.assertFalse(hr.predictions(keyed(BEFORE), keyed(AFTER), '2027-01-05')['R1']['in_window'])

    def test_predictions_unchanged_files(self):
        # Nothing changed: no pair is newly handled (R2 holds), and none of the cohort handles 2027-01-11 (R1 holds).
        p = hr.predictions(keyed(BEFORE), keyed(BEFORE), '2026-12-15')
        self.assertEqual((p['R1']['applicable_after'], p['R1']['handled_after']), (2, 0))
        self.assertTrue(p['R1']['held'])
        self.assertEqual((p['R2']['pairs'], p['R2']['handled_after']), (3, 0))
        self.assertTrue(p['R2']['held'])

    def test_changes(self):
        ch = hr.changes(keyed(BEFORE), keyed(AFTER))
        self.assertEqual([(c['feed_id'], c['date'], c['before'], c['after']) for c in ch],
                         [('f1', '2026-12-30', 'ordinary', 'no_service'), ('f1', '2027-01-11', 'ordinary', 'sunday')])

    def test_main(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = {}
            for name, rows in (('before', BEFORE), ('after', AFTER)):
                paths[name] = os.path.join(tmp, f'{name}.csv')
                with open(paths[name], 'w', encoding='utf-8-sig', newline='') as f:
                    w = csv.DictWriter(f, fieldnames=COLS)
                    w.writeheader()
                    w.writerows(rows)
            out = os.path.join(tmp, 'out')
            hr.main(['--before', paths['before'], '--after', paths['after'], '--as-of', '2026-12-15', '--out', out])
            with open(os.path.join(out, 'horizon.json'), encoding='utf-8') as f:
                self.assertEqual(json.load(f)['cohort_r1'], ['o/f1', 'o/f4'])
            with open(os.path.join(out, 'recheck.json'), encoding='utf-8') as f:
                res = json.load(f)
            self.assertEqual((res['removed'], res['added'], res['changed_pairs']), (['o/f4', 'o/f6'], ['o/f7'], 2))
            self.assertEqual(res['predictions']['R1']['held'], False)
            with open(os.path.join(out, 'changes.csv'), encoding='utf-8-sig', newline='') as f:
                self.assertEqual(len(list(csv.DictReader(f))), 2)
            for name in ('horizon.md', 'recheck.md'):
                self.assertTrue(os.path.getsize(os.path.join(out, name)) > 0)


if __name__ == '__main__':
    unittest.main()
