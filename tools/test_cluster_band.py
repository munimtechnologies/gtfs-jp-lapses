# Tests for cluster_band.py on a made-up census and cohort (no network). Needs repeat_cliff.py and fy_cliff.py in the
# same folder.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import csv
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cluster_band as cb  # noqa: E402

# Publisher A (prefecture 25): a1, a2, a3. B (prefecture 6): b1. C (prefecture 6): c1, c2. Every feed has files
# ending 2025-03-31 and 2026-03-31. All of A lapsed on 2025-04-01; a1, a2 and c1 lapsed on 2026-04-01.
FEEDS = [{'organization_id': o, 'feed_id': f, 'pref_id': p, 'window_end': '2026-10-16'}
         for o, f, p in (('A', 'a1', '25'), ('A', 'a2', '25'), ('A', 'a3', '25'), ('B', 'b1', '6'), ('C', 'c1', '6'),
                         ('C', 'c2', '6'))]
VERSIONS = [{'organization_id': r['organization_id'], 'feed_id': r['feed_id'], 'to_date': d}
            for r in FEEDS for d in ('2025-03-31', '2026-03-31')]
LAPSES = ([{'organization_id': 'A', 'feed_id': f, 'start': '2025-04-01', 'days': '10'} for f in ('a1', 'a2', 'a3')] +
          [{'organization_id': o, 'feed_id': f, 'start': '2026-04-01', 'days': '5'}
           for o, f in (('A', 'a1'), ('A', 'a2'), ('C', 'c1'))])
# The 2027 cohort: a1, a2 lapsed on 2026-04-01 (prior); b1, c2 and a feed new since the census (D, prefecture 13).
COHORT = [{'group': g, 'organization_id': o, 'feed_id': f, 'pref_id': p}
          for g, o, f, p in (('prior', 'A', 'a1', '25'), ('prior', 'A', 'a2', '25'), ('other', 'B', 'b1', '6'),
                             ('other', 'C', 'c2', '6'), ('other', 'D', 'new1', '13'))]


def write(path, rows):
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


class Parts(unittest.TestCase):
    def test_icc(self):
        self.assertAlmostEqual(cb.icc([(2, 2), (2, 0), (2, 2), (2, 0)]), 1.0)
        self.assertAlmostEqual(cb.icc([(2, 1), (2, 1), (2, 1), (2, 1)]), -1.0)
        self.assertEqual(cb.icc([(1, 1), (1, 0), (1, 0)]), 0.0)
        self.assertEqual(cb.icc([(5, 2)]), 0.0)

    def test_deff_and_band(self):
        self.assertEqual(cb.deff(2.0, -1.0), 1.0)
        self.assertAlmostEqual(cb.deff(3.0, 0.25), 1.5)
        self.assertEqual(cb.band(50, 25), (41, 59))
        self.assertEqual(cb.band(50, 25, 4), (33, 67))
        self.assertEqual(cb.band(1, 4), (0, 5))

    def test_weighted_size(self):
        self.assertAlmostEqual(cb.weighted_size([('A', 1), ('A', 2), ('A', 3), ('B', 1)], lambda k: k[0]), 2.5)
        self.assertEqual(cb.weighted_size([], lambda k: k[0]), 0.0)


class Analyse(unittest.TestCase):
    def setUp(self):
        self.res = cb.analyse(FEEDS, VERSIONS, LAPSES, COHORT)

    def test_icc_by_year(self):
        by = {r['year']: r for r in self.res['icc_by_year']}
        self.assertEqual((by[2025]['at_risk'], by[2025]['lapsed']), (6, 3))
        self.assertEqual(by[2025]['publisher_icc'], 1.0)
        self.assertEqual(by[2025]['prefecture_icc'], 1.0)
        self.assertEqual((by[2026]['publisher_clusters'], by[2026]['publisher_clusters_lapsed']), (3, 2))
        self.assertLess(by[2026]['publisher_icc'], 0)

    def test_backtest(self):
        self.assertEqual(len(self.res['backtest']), 1)  # 2026 from 2025; no prior group in 2025, so flat only
        r = self.res['backtest'][0]
        self.assertEqual((r['year'], r['model'], r['expected'], r['observed']), (2026, 'flat', 3.0, 3))
        self.assertEqual((r['independent_low90'], r['independent_high90'], r['independent_covered']), (0, 6, True))
        self.assertEqual(r['publisher_deff'], 2.333)
        self.assertEqual((r['publisher_low90'], r['publisher_high90']), (0, 7))
        self.assertEqual(r['prefecture_deff'], 3.0)
        self.assertEqual((r['prefecture_low90'], r['prefecture_high90']), (0, 7))

    def test_forecast_2027(self):
        f = {r['model']: r for r in self.res['forecast_2027']}
        self.assertEqual(f['rates_2026']['expected'], 2.3)
        self.assertEqual(f['rates_2024_2026']['expected'], 2.7)
        self.assertEqual(f['flat_2026']['expected'], 2.5)
        self.assertEqual(f['flat_2026']['independent_deff'], 1.0)
        self.assertEqual(f['flat_2026']['publisher_icc_2026_deff'], 1.0)  # negative ICC in 2026 floors at 1
        c = self.res['cohort_2027']
        self.assertEqual((c['feeds'], c['prior'], c['publishers'], c['prefectures']), (5, 2, 4, 3))
        self.assertEqual((c['largest_publisher_feeds'], c['largest_prefecture_feeds']), (2, 2))
        self.assertAlmostEqual(c['publisher_weighted_size'], 1.4)


class Main(unittest.TestCase):
    def test_files(self):
        with tempfile.TemporaryDirectory() as d:
            census = os.path.join(d, 'census')
            os.makedirs(census)
            write(os.path.join(census, 'feeds.csv'), FEEDS)
            write(os.path.join(census, 'versions.csv'), VERSIONS)
            write(os.path.join(census, 'lapses.csv'), LAPSES)
            cohort = os.path.join(d, 'cohort.csv')
            write(cohort, COHORT)
            fc = os.path.join(d, 'forecast.json')
            with open(fc, 'w', encoding='utf-8') as f:
                json.dump({'forecast': {'models': {'rates_2026': {'expected': 2.3}, 'rates_2024_2026': {'expected': 2.7},
                                                   'flat_2026': {'expected': 2.5}}}}, f)
            cb.main(['--census', census, '--cohort', cohort, '--forecast', fc, '--out', d])
            out = os.path.join(d, 'forecast', '2027-04-01')
            with open(os.path.join(out, 'cluster_band.json'), encoding='utf-8') as f:
                res = json.load(f)
            self.assertTrue(res['matches_forecast'])
            with open(os.path.join(out, 'cluster_band.md'), encoding='utf-8') as f:
                md = f.read()
            self.assertIn('| 2026 | flat | 3.0 | 3 | 0–6 ✓ (deff 1.0) |', md)
            self.assertIn("Made by MV2 of Munim, Inc. with AI agents working in MV2's name.", md)

    def test_header(self):
        with open(cb.__file__, encoding='utf-8') as f:
            head = f.read(1200)
        self.assertIn('Apache-2.0', head)
        self.assertIn("Made with AI agents working in MV2's name", head)


if __name__ == '__main__':
    unittest.main()
