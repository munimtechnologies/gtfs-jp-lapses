# Tests for lapse_survival.py on made-up lapses worked out by hand (no network).
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import csv
import json
import math
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lapse_survival as ls  # noqa: E402

# April-1 lapses: 2 and 4 days (2025, ended), 4 days (2026, still open), 6 days (2026, ended).
# Other days: 1 day (2025-06-01) and 3 days (2026-01-01), both ended.
LAPSES = [
    {'organization_id': 'P', 'feed_id': 'a', 'start': '2025-04-01', 'days': '2', 'ongoing': 'false'},
    {'organization_id': 'P', 'feed_id': 'b', 'start': '2025-04-01', 'days': '4', 'ongoing': 'false'},
    {'organization_id': 'Q', 'feed_id': 'c', 'start': '2026-04-01', 'days': '4', 'ongoing': 'true'},
    {'organization_id': 'Q', 'feed_id': 'd', 'start': '2026-04-01', 'days': '6', 'ongoing': 'false'},
    {'organization_id': 'R', 'feed_id': 'e', 'start': '2025-06-01', 'days': '1', 'ongoing': 'false'},
    {'organization_id': 'R', 'feed_id': 'f', 'start': '2026-01-01', 'days': '3', 'ongoing': 'false'},
]
A = [(2, True), (4, True), (4, False), (6, True)]
B = [(1, True), (3, True)]


class Parts(unittest.TestCase):
    def test_km(self):
        steps = ls.km(A)
        self.assertEqual([(t, n, k) for t, n, k, _, _ in steps], [(2, 4, 1), (4, 3, 1), (6, 1, 1)])
        self.assertEqual([round(s, 4) for _, _, _, s, _ in steps], [0.75, 0.5, 0.0])
        self.assertAlmostEqual(steps[0][4], 0.75 * math.sqrt(1 / 12))
        self.assertAlmostEqual(steps[1][4], 0.25)  # 0.5 * sqrt(1/12 + 1/6)
        self.assertEqual(steps[2][4], 0.0)

    def test_reads(self):
        steps = ls.km(A)
        self.assertEqual([round(ls.surv_at(steps, t), 9) for t in (0, 3, 4, 7)], [1.0, 0.75, 0.5, 0.0])
        self.assertEqual(ls.km_median(steps), 4)
        self.assertEqual(ls.km_median(ls.km([(5, False), (2, True), (9, False)])), None)
        self.assertAlmostEqual(ls.rmst(steps, 5), 4.0)  # 2*1 + 2*0.75 + 1*0.5
        self.assertAlmostEqual(ls.rmst(steps), 4.5)
        self.assertEqual(ls.rmst([], 10), 10)

    def test_logrank(self):
        o, ex, chi2, p = ls.logrank(A, B)
        self.assertEqual(o, 3)
        self.assertAlmostEqual(ex, 2 / 3 + 0.8 + 0.75 + 2)
        self.assertAlmostEqual(chi2, (3 - ex) ** 2 / (2 / 9 + 0.16 + 0.1875))
        self.assertTrue(0.10 < p < 0.11)
        self.assertEqual(ls.logrank([(3, True)], [(3, True)])[2], 0.0)


class Analyse(unittest.TestCase):
    def test_groups(self):
        res = ls.analyse(LAPSES)
        g = {r['group']: r for r in res['groups']}
        self.assertEqual(sorted(g), ['all', 'april_1', 'other_days'])  # each year has fewer than MIN_GROUP
        a = g['april_1']
        self.assertEqual((a['lapses'], a['ended'], a['still_open'], a['followed_to_days']), (4, 3, 1, 6))
        self.assertEqual((a['km_median_days'], a['ended_only_median_days'], a['rmst_365_days']), (4, 4, 4.5))
        self.assertEqual(a['still_lapsed_30d'], None)  # nobody followed for 30 days
        al = g['all']
        self.assertEqual((al['km_median_days'], al['rmst_365_days']), (3, 3.7))  # 1 + 5/6 + 2/3 + 1/2 + 2/3

    def test_years_and_tests(self):
        old = ls.MIN_GROUP
        ls.MIN_GROUP = 2
        try:
            res = ls.analyse(LAPSES)
        finally:
            ls.MIN_GROUP = old
        self.assertEqual([r['group'] for r in res['groups']],
                         ['all', 'april_1', 'other_days', 'april_1_2025', 'april_1_2026'])
        t = {x['test']: x for x in res['tests']}
        self.assertEqual(sorted(t), ['april_1 vs other_days', 'april_1_2026 vs april_1 before 2026'])
        first = t['april_1 vs other_days']
        self.assertEqual((first['observed_ended_first'], first['expected_ended_first'], first['chi2'],
                          first['first_group_ends']), (3, 4.2, 2.598, 'later'))
        second = t['april_1_2026 vs april_1 before 2026']
        self.assertEqual((second['observed_ended_first'], second['expected_ended_first'], second['chi2']),
                         (1, 2.2, 2.882))  # (1 - 13/6)^2 / (1/4 + 2/9)

    def test_feed_days(self):
        exp = ls.expected_counts({'forecast': {'models': {'flat_2026': {'expected': 10.0}}}},
                                 {'forecast_2027': [{'model': 'persistence_2026', 'expected': 10.0},
                                                    {'model': 'trend_2022_2026', 'expected': 12.0}]})
        self.assertEqual(exp, {'flat_2026': 10.0, 'trend_2022_2026': 12.0})
        d = {x['model']: x for x in ls.analyse(LAPSES, exp)['forecast_2027_feed_days']}
        self.assertEqual((d['flat_2026']['expected_feed_days_365'], d['trend_2022_2026']['expected_feed_days_365']),
                         (45, 54))


class Main(unittest.TestCase):
    def test_files(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, 'lapses.csv')
            with open(path, 'w', encoding='utf-8-sig', newline='') as f:
                w = csv.DictWriter(f, fieldnames=list(LAPSES[0]))
                w.writeheader()
                w.writerows(LAPSES)
            fc = os.path.join(d, 'forecast.json')
            with open(fc, 'w', encoding='utf-8') as f:
                json.dump({'forecast': {'models': {'flat_2026': {'expected': 10.0}}}}, f)
            ls.main(['--lapses', path, '--as-of', '2026-10-16', '--forecast', fc, '--out', d])
            out = os.path.join(d, 'data', '2026-10-16')
            with open(os.path.join(out, 'lapse_survival.json'), encoding='utf-8') as f:
                res = json.load(f)
            self.assertEqual(res['as_of'], '2026-10-16')
            with open(os.path.join(out, 'lapse_survival.md'), encoding='utf-8') as f:
                md = f.read()
            self.assertIn('| april_1 | 4 | 3 | 1 | 6 | 4 | 4 | – | – | – | – | 4.5 |', md)
            self.assertIn('| flat_2026 | 10.0 | 4.5 | 45 |', md)
            self.assertIn("Made by MV2 of Munim, Inc. with AI agents working in MV2's name.", md)

    def test_header(self):
        with open(ls.__file__, encoding='utf-8') as f:
            head = f.read(1200)
        self.assertIn('Apache-2.0', head)
        self.assertIn("Made with AI agents working in MV2's name", head)


if __name__ == '__main__':
    unittest.main()
