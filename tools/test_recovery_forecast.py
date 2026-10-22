# Tests for recovery_forecast.py on made-up lapses worked out by hand (no network).
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import csv
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recovery_forecast as rf  # noqa: E402

AS_OF = '2026-03-01'
# Ended: 10, 20 and 40 days. Open on 2026-03-01: d (10 days so far), g (15), f (91). e is marked ongoing but ended
# on 2026-02-15 when its feed was marked discontinued, so it is censored at 15 days and left out of the forecast.
# Kaplan-Meier over all seven: S = 6/7 from day 10, 4/7 from day 20, 2/7 from day 40.
LAPSES = [
    {'organization_id': 'P', 'feed_id': 'a', 'feed_name': 'A', 'pref_id': '1', 'start': '2025-01-01',
     'end': '2025-01-10', 'days': '10', 'ongoing': 'false', 'ended_by_file_published': '2025-01-11'},
    {'organization_id': 'P', 'feed_id': 'b', 'feed_name': 'B', 'pref_id': '1', 'start': '2025-01-01',
     'end': '2025-01-20', 'days': '20', 'ongoing': 'false', 'ended_by_file_published': '2025-01-21'},
    {'organization_id': 'P', 'feed_id': 'c', 'feed_name': 'C', 'pref_id': '1', 'start': '2025-01-01',
     'end': '2025-02-09', 'days': '40', 'ongoing': 'false', 'ended_by_file_published': '2025-02-10'},
    {'organization_id': 'Q', 'feed_id': 'd', 'feed_name': 'D', 'pref_id': '2', 'start': '2026-02-20',
     'end': '2026-03-01', 'days': '10', 'ongoing': 'true', 'ended_by_file_published': ''},
    {'organization_id': 'Q', 'feed_id': 'e', 'feed_name': 'E', 'pref_id': '2', 'start': '2026-02-01',
     'end': '2026-02-15', 'days': '15', 'ongoing': 'true', 'ended_by_file_published': ''},
    {'organization_id': 'R', 'feed_id': 'g', 'feed_name': 'G', 'pref_id': '3', 'start': '2026-02-15',
     'end': '2026-03-01', 'days': '15', 'ongoing': 'true', 'ended_by_file_published': ''},
    {'organization_id': 'R', 'feed_id': 'f', 'feed_name': 'F', 'pref_id': '3', 'start': '2025-12-01',
     'end': '2026-03-01', 'days': '91', 'ongoing': 'true', 'ended_by_file_published': ''},
]
LATER = [
    {'organization_id': 'Q', 'feed_id': 'd', 'start': '2026-02-20', 'end': '2026-03-05', 'days': '14',
     'ongoing': 'false', 'ended_by_file_published': '2026-03-10'},
    {'organization_id': 'R', 'feed_id': 'g', 'start': '2026-02-15', 'end': '2026-04-15', 'days': '60',
     'ongoing': 'true', 'ended_by_file_published': ''},
]


class Parts(unittest.TestCase):
    def test_open(self):
        self.assertEqual([r['feed_id'] for r in rf.open_lapses(LAPSES, AS_OF)], ['d', 'g', 'f'])

    def test_poisson_binomial(self):
        dist = rf.poisson_binomial([2 / 3, 2 / 3, 0])
        for got, want in zip(dist, [1 / 9, 4 / 9, 4 / 9, 0]):
            self.assertAlmostEqual(got, want)
        self.assertEqual((rf.quantile(dist, 0.05), rf.quantile(dist, 0.5), rf.quantile(dist, 0.95)), (0, 1, 2))
        self.assertEqual(rf.poisson_binomial([]), [1.0])


class Forecast(unittest.TestCase):
    def setUp(self):
        self.fc = rf.forecast(LAPSES, AS_OF, horizons=(5, 30))

    def test_probabilities(self):
        p = {x['feed_id']: (x['p_over_within_5d'], x['p_over_within_30d']) for x in self.fc['lapses']}
        self.assertEqual(p['d'], (0.0, 0.6667))  # 1 - (2/7)/(6/7)
        self.assertEqual(p['g'], (0.3333, 0.6667))  # 1 - (4/7)/(6/7); 1 - (2/7)/(6/7)
        self.assertEqual(p['f'], (0.0, 0.0))  # older than the longest ended lapse
        self.assertEqual(self.fc['excluded_discontinued'], 1)
        self.assertEqual([x['age_days'] for x in self.fc['lapses']], [10, 15, 91])

    def test_horizons(self):
        h5, h30 = self.fc['horizons']
        self.assertEqual((h5['last_lapse_day'], h5['open_lapses'], h5['expected_recoveries'], h5['median'],
                          h5['range_90']), ('2026-03-06', 3, 0.33, 0, [0, 1]))
        self.assertEqual((h30['last_lapse_day'], h30['expected_recoveries'], h30['median'], h30['range_90']),
                         ('2026-03-31', 1.33, 1, [0, 2]))

    def test_score(self):
        res = rf.score(self.fc, LATER, '2026-04-15')
        h5, h30 = res['horizons']
        self.assertEqual((h5['over'], h5['over_known_by_then'], h5['still_open'], h5['missing'], h5['within_range_90']),
                         (1, 0, 1, 1, True))
        self.assertEqual((h30['over'], h30['over_known_by_then'], h30['still_open'], h30['missing']), (1, 1, 1, 1))
        early = rf.score(self.fc, LATER, '2026-03-20')['horizons']
        self.assertEqual([h['status'] for h in early], ['scored', 'not_due'])


class Main(unittest.TestCase):
    def test_files(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, 'lapses.csv')
            with open(path, 'w', encoding='utf-8-sig', newline='') as f:
                w = csv.DictWriter(f, fieldnames=list(LAPSES[0]))
                w.writeheader()
                w.writerows(LAPSES)
            rf.main(['--lapses', path, '--as-of', AS_OF, '--out', d])
            out = os.path.join(d, 'forecast', 'recovery', AS_OF)
            with open(os.path.join(out, 'recovery.json'), encoding='utf-8') as f:
                fc = json.load(f)
            self.assertEqual([h['horizon_days'] for h in fc['horizons']], [30, 90])
            with open(os.path.join(out, 'recovery.md'), encoding='utf-8') as f:
                md = f.read()
            self.assertIn('| 30 d | 2026-03-31 | 3 | 1.33 | 1 | 0–2 |', md)
            self.assertIn('| Q | d | 2026-02-20 | 10 | no | 0.67 | 0.67 |', md)
            self.assertIn("Made by MV2 of Munim, Inc. with AI agents working in MV2's name.", md)
            with open(os.path.join(out, 'recovery.csv'), encoding='utf-8-sig') as f:
                self.assertEqual(len(list(csv.DictReader(f))), 3)
            later = os.path.join(d, 'later.csv')
            with open(later, 'w', encoding='utf-8-sig', newline='') as f:
                w = csv.DictWriter(f, fieldnames=list(LATER[0]))
                w.writeheader()
                w.writerows(LATER)
            rf.main(['--lapses', later, '--as-of', '2026-06-30', '--out', d, '--score', later,
                     '--forecast-json', os.path.join(out, 'recovery.json')])
            with open(os.path.join(out, 'score-2026-06-30', 'score.json'), encoding='utf-8') as f:
                sc = json.load(f)
            self.assertEqual([h['over'] for h in sc['horizons']], [1, 1])

    def test_header(self):
        with open(rf.__file__, encoding='utf-8') as f:
            head = f.read(1200)
        self.assertIn('Apache-2.0', head)
        self.assertIn("Made with AI agents working in MV2's name", head)


if __name__ == '__main__':
    unittest.main()
