# Tests for trend_band.py on a made-up census and cohort (no network). Needs cluster_band.py, repeat_cliff.py and
# fy_cliff.py in the same folder.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import csv
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trend_band as tb  # noqa: E402

# Publisher P (prefecture 1): f0-f4. Q (prefecture 2): f5-f9. Every feed has files ending March 31 of 2023-2026, so all
# 10 are at risk each year. April-1 lapses: 2023 f0; 2024 f0, f1; 2025 f0-f2; 2026 f0-f2 and f5 (shares 0.1-0.4).
FEEDS = [{'organization_id': 'P' if i < 5 else 'Q', 'feed_id': f'f{i}', 'pref_id': '1' if i < 5 else '2',
          'window_end': '2026-10-16'} for i in range(10)]
VERSIONS = [{'organization_id': r['organization_id'], 'feed_id': r['feed_id'], 'to_date': f'{y}-03-31'}
            for r in FEEDS for y in range(2023, 2027)]
HITS = {2023: [0], 2024: [0, 1], 2025: [0, 1, 2], 2026: [0, 1, 2, 5]}
LAPSES = [{'organization_id': 'P' if i < 5 else 'Q', 'feed_id': f'f{i}', 'start': f'{y}-04-01', 'days': '10'}
          for y, ids in HITS.items() for i in ids]
COHORT = [{'group': 'other', 'organization_id': 'P', 'feed_id': f'f{i}', 'pref_id': '1'} for i in range(5)]


def write(path, rows):
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


class Parts(unittest.TestCase):
    def test_line(self):
        predict, fit_var = tb.line([(2023, 10, 1), (2024, 10, 2), (2025, 10, 3), (2026, 10, 4)])
        self.assertAlmostEqual(predict(2027), 0.5)
        self.assertAlmostEqual(fit_var(2027, 0.5), 0.0375)  # 0.25 * (1/40 + 2.5^2/50)
        self.assertEqual(tb.line([(2026, 10, 4)]), None)
        self.assertEqual(tb.line([]), None)
        predict, _ = tb.line([(2025, 10, 0), (2026, 10, 10)])
        self.assertEqual(predict(2027), 1.0)  # clipped
        self.assertEqual(predict(2023), 0.0)

    def test_band(self):
        self.assertEqual(tb.band(50, 25, 100), (41, 59))
        self.assertEqual(tb.band(4, 24, 10), (0, 10))


class Analyse(unittest.TestCase):
    def setUp(self):
        self.res = tb.analyse(FEEDS, VERSIONS, LAPSES, COHORT, min_at_risk=1)

    def test_shares(self):
        self.assertEqual([(r['year'], r['at_risk'], r['lapsed']) for r in self.res['shares']],
                         [(2023, 10, 1), (2024, 10, 2), (2025, 10, 3), (2026, 10, 4)])

    def test_backtest(self):
        bt = {(r['year'], r['model']): r for r in self.res['backtest']}
        self.assertEqual(sorted(bt), [(2024, 'persistence'), (2025, 'persistence'), (2025, 'trend_all'),
                                      (2026, 'persistence'), (2026, 'trend_all')])
        p = bt[(2026, 'persistence')]
        self.assertEqual((p['expected'], p['observed'], p['error']), (3.0, 4, 1.0))
        t = bt[(2026, 'trend_all')]
        self.assertEqual((t['fit_years'], t['expected'], t['error'], t['publisher_deff']), ('2023-2025', 4.0, 0.0, 3.0))
        self.assertEqual((t['independent_low90'], t['independent_high90'], t['independent_covered']), (1, 7, True))
        self.assertEqual((t['publisher_low90'], t['publisher_high90']), (0, 9))
        self.assertEqual((t['publisher_fit_low90'], t['publisher_fit_high90']), (0, 10))

    def test_scores(self):
        self.assertEqual(self.res['scores'], [{'model': 'trend_all', 'years': [2025, 2026], 'mean_error': 0.0,
                                               'mean_abs_error': 0.0, 'persistence_mean_error': 1.0,
                                               'persistence_mean_abs_error': 1.0}])

    def test_forecast_2027(self):
        f = {r['model']: r for r in self.res['forecast_2027']}
        self.assertEqual(sorted(f), ['persistence_2026', 'trend_2023_2026', 'trend_2024_2026'])
        self.assertEqual(f['persistence_2026']['expected'], 2.0)
        self.assertEqual(f['trend_2023_2026']['expected'], 2.5)
        self.assertEqual(f['trend_2024_2026']['expected'], 2.5)
        self.assertEqual(f['trend_2023_2026']['publisher_fit_high90'], 5)  # capped at the cohort size
        c = self.res['cohort_2027']
        self.assertEqual((c['feeds'], c['publisher_weighted_size'], c['publisher_deff']), (5, 5.0, 1.429))


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
                json.dump({'forecast': {'models': {'rates_2026': {'expected': 9.9}, 'flat_2026': {'expected': 2.0}}}}, f)
            old = tb.MIN_AT_RISK
            tb.MIN_AT_RISK = 1
            try:
                tb.main(['--census', census, '--cohort', cohort, '--forecast', fc, '--out', d])
            finally:
                tb.MIN_AT_RISK = old
            out = os.path.join(d, 'forecast', '2027-04-01')
            with open(os.path.join(out, 'trend_band.json'), encoding='utf-8') as f:
                res = json.load(f)
            self.assertTrue(res['matches_forecast'])
            with open(os.path.join(out, 'trend_band.md'), encoding='utf-8') as f:
                md = f.read()
            self.assertIn('| 2026 | trend_all | 2023-2025 | 4.0 | 4 | 0.0 | 1–7 ✓ | 0–9 ✓ | 0–10 ✓ |', md)
            self.assertIn("Made by MV2 of Munim, Inc. with AI agents working in MV2's name.", md)

    def test_header(self):
        with open(tb.__file__, encoding='utf-8') as f:
            head = f.read(1200)
        self.assertIn('Apache-2.0', head)
        self.assertIn("Made with AI agents working in MV2's name", head)


if __name__ == '__main__':
    unittest.main()
