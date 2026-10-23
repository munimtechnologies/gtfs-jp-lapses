# Tests for gap_split.py on a made-up leads.csv (no network). Every expected value is worked by hand below.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import csv
import datetime as dt
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gap_split as gs  # noqa: E402

COLS = ['organization_id', 'feed_id', 'published_date', 'from_date', 'lead_days', 'late_kind']


def r(org, feed, a, lead, kind=''):
    return {'organization_id': org, 'feed_id': feed, 'published_date': '', 'from_date': a, 'lead_days': str(lead),
            'late_kind': kind}


# Range 2024-01-01 to 2025-12-31 keeps rows 1-9; row 10 starts before it and row 11 after it.
# April 1 (rows 1, 2, 3, 4, 7): 5 files, late 4 (1, 2, 3, 7), gap 3 (1, 2, 7), stale 1 (3); gap share 3/5 = 0.6,
#   late share 0.8, gap of late 3/4 = 0.75; gap feeds o1/f1, o1/f2, o4/f1 = 3, publishers o1, o4 = 2.
# Other days (rows 5, 6, 8, 9): 4 files, late 2 (5, 8), gap 1 (8), stale 1 (5); gap share 0.25, late share 0.5,
#   gap of late 0.5; 1 feed, 1 publisher.
# Gap share greater: a=3, b=2, c=1, d=3; n1=5, n2=4, k=4, C(9,4)=126; x=3: C(5,3)C(4,1)=40, x=4: C(5,4)C(4,0)=5;
#   p = 45/126 = 0.357143 (shown 0.357).
# Late share smaller: fisher_greater(2, 2, 4, 1): n1=4, n2=5, k=6, C(9,6)=84; x=2: C(4,2)C(5,4)=30, x=3: C(4,3)C(5,3)
#   =40, x=4: C(4,4)C(5,2)=10; p = 80/84 = 0.952381 (shown 0.952).
# By year: 2024 April rows 1-4 (n 4, gap 2, 0.5), other rows 5, 6 (n 2, gap 0, 0.0); 2025 April row 7 (n 1, gap 1,
#   1.0), other rows 8, 9 (n 2, gap 1, 0.5).
# Predictions: G1 0.6 is outside 6-18% (no); G2 p 0.357143 (no); G3 0.75 >= 0.40 (yes).
ROWS = [r('o1', 'f1', '2024-04-01', -3, 'gap'),
        r('o1', 'f2', '2024-04-01', -10, 'gap'),
        r('o2', 'f1', '2024-04-01', -5, 'stale'),
        r('o3', 'f1', '2024-04-01', 7),
        r('o2', 'f1', '2024-10-01', -2, 'stale'),
        r('o3', 'f1', '2024-07-01', 0),
        r('o4', 'f1', '2025-04-01', -1, 'gap'),
        r('o4', 'f1', '2025-01-06', -4, 'gap'),
        r('o5', 'f1', '2025-06-01', 14),
        r('o5', 'f1', '2023-04-01', 3),
        r('o1', 'f1', '2026-04-01', -1, 'stale')]
START, END = dt.date(2024, 1, 1), dt.date(2025, 12, 31)


class TestFisher(unittest.TestCase):
    def test_classic(self):
        self.assertEqual(gs.fisher_greater(3, 0, 0, 3), 0.05)

    def test_empty_group(self):
        self.assertIsNone(gs.fisher_greater(0, 0, 1, 2))

    def test_small_p_is_not_rounded_to_zero(self):
        # 10/10 against 0/10: only x = 10 counts, C(10,10)C(10,0) = 1 of C(20,10) = 184756, p = 5.41254e-06.
        p = gs.fisher_greater(10, 0, 0, 10)
        self.assertGreater(p, 0)
        self.assertAlmostEqual(p * 184756, 1.0, places=4)
        self.assertEqual(gs.pval(p), '5.41e-06')

    def test_pval(self):
        self.assertEqual(gs.pval(None), '')
        self.assertEqual(gs.pval(0.357143), '0.357')
        self.assertEqual(gs.pval(0.05), '0.05')


class TestSummary(unittest.TestCase):
    def setUp(self):
        self.s, self.on, self.off = gs.summarise(ROWS, START, END, '04-01', predictions=True)

    def test_split(self):
        self.assertEqual(len(self.on), 5)
        self.assertEqual(len(self.off), 4)

    def test_day_group(self):
        self.assertEqual(self.s['groups']['day'], {'n': 5, 'late': 4, 'gap': 3, 'stale': 1, 'late_share': 0.8,
                                                   'gap_share': 0.6, 'gap_of_late': 0.75, 'gap_feeds': 3,
                                                   'gap_publishers': 2})

    def test_other_group(self):
        self.assertEqual(self.s['groups']['other'], {'n': 4, 'late': 2, 'gap': 1, 'stale': 1, 'late_share': 0.5,
                                                     'gap_share': 0.25, 'gap_of_late': 0.5, 'gap_feeds': 1,
                                                     'gap_publishers': 1})

    def test_tests(self):
        self.assertEqual(self.s['tests'], {'gap_p_greater': 0.357143, 'late_p_less': 0.952381})

    def test_by_year(self):
        y = self.s['by_start_year']
        self.assertEqual(sorted(y), ['2024', '2025'])
        self.assertEqual((y['2024']['day']['n'], y['2024']['day']['gap'], y['2024']['day']['gap_share']), (4, 2, 0.5))
        self.assertEqual((y['2024']['other']['n'], y['2024']['other']['gap'], y['2024']['other']['gap_share']),
                         (2, 0, 0.0))
        self.assertEqual((y['2025']['day']['n'], y['2025']['day']['gap'], y['2025']['day']['gap_share']), (1, 1, 1.0))
        self.assertEqual((y['2025']['other']['n'], y['2025']['other']['gap'], y['2025']['other']['gap_share']),
                         (2, 1, 0.5))

    def test_predictions(self):
        p = self.s['predictions']
        self.assertEqual((p['G1']['value'], p['G1']['held']), (0.6, False))
        self.assertEqual((p['G2']['value'], p['G2']['held']), (0.357143, False))
        self.assertEqual((p['G3']['value'], p['G3']['held']), (0.75, True))

    def test_no_predictions_unless_asked(self):
        s, _, _ = gs.summarise(ROWS, START, END, '04-01')
        self.assertNotIn('predictions', s)

    def test_empty_range(self):
        s, on, off = gs.summarise(ROWS, dt.date(2030, 1, 1), dt.date(2030, 12, 31), '04-01', predictions=True)
        self.assertEqual((on, off), ([], []))
        self.assertIsNone(s['groups']['day']['gap_share'])
        self.assertIsNone(s['tests']['gap_p_greater'])
        self.assertFalse(s['predictions']['G1']['held'])


class TestMain(unittest.TestCase):
    def test_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'leads.csv')
            with open(path, 'w', encoding='utf-8-sig', newline='') as f:
                w = csv.DictWriter(f, fieldnames=COLS)
                w.writeheader()
                w.writerows(ROWS)
            out = os.path.join(tmp, 'out')
            gs.main(['--leads', path, '--start', '2024-01-01', '--end', '2025-12-31', '--predictions', '--out', out])
            with open(os.path.join(out, 'gaps.csv'), encoding='utf-8-sig', newline='') as f:
                gaps = list(csv.DictReader(f))
            self.assertEqual([(g['group'], g['organization_id'], g['feed_id'], g['from_date']) for g in gaps],
                             [('day', 'o1', 'f1', '2024-04-01'), ('day', 'o1', 'f2', '2024-04-01'),
                              ('day', 'o4', 'f1', '2025-04-01'), ('other', 'o4', 'f1', '2025-01-06')])
            with open(os.path.join(out, 'gaps.json'), encoding='utf-8') as f:
                s = json.load(f)
            self.assertEqual(s['range'], ['2024-01-01', '2025-12-31'])
            with open(os.path.join(out, 'gaps.md'), encoding='utf-8') as f:
                md = f.read()
            self.assertIn('| day | 5 | 4 | 3 | 1 | 80.0% | 60.0% | 75.0% | 3 | 2 |', md)
            self.assertIn('| other | 4 | 2 | 1 | 1 | 50.0% | 25.0% | 50.0% | 1 | 1 |', md)
            self.assertIn('| 2024 | 4 | 2 | 50.0% | 2 | 0 | 0.0% |', md)
            self.assertIn('gap share of 04-01 greater: 0.357\n', md)
            self.assertIn('late share of 04-01 smaller: 0.952\n', md)
            self.assertIn('G2: ', md)
            self.assertIn('Result: p = 0.357, did not hold.', md)
            self.assertIn('G3:', md)


if __name__ == '__main__':
    unittest.main()
