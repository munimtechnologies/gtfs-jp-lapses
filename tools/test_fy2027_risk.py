# Tests for fy2027_risk.py on a made-up feed list and census (no network). Needs expiry_watch.py, gtfs_lapses.py
# and fy_cliff.py in the same folder.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import csv
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fy2027_risk as fr  # noqa: E402


def feed(fid, end='2027-03-31', disc=False, pref=6):
    return {'organization_id': 'org', 'organization_name': 'org バス', 'feed_id': fid, 'feed_name': f'路線 {fid}',
            'feed_pref_id': pref, 'feed_license': 'CC BY 4.0', 'last_published_at': '2026-04-10',
            'latest_feed_start_date': '2026-04-01', 'latest_feed_end_date': end, 'feed_is_discontinued': disc}


# p1, p2: lapsed on 2026-04-01 (prior). o1: lapsed on 2025-04-01 only (other). o2, o3: no lapse. new1: not in the
# census. x: ends later. dsc: discontinued. All but x and dsc end on 2027-03-31.
FEEDS = [feed('p1'), feed('p2'), feed('o1'), feed('o2'), feed('o3'), feed('new1'), feed('x', '2027-06-30'),
         feed('dsc', disc=True)]
CENSUS_FEEDS = [{'organization_id': 'org', 'feed_id': f} for f in ('p1', 'p2', 'o1', 'o2', 'o3', 'x', 'dsc')]
LAPSES = [{'organization_id': 'org', 'feed_id': 'p1', 'start': '2026-04-01'},
          {'organization_id': 'org', 'feed_id': 'p1', 'start': '2025-04-01'},
          {'organization_id': 'org', 'feed_id': 'p2', 'start': '2026-04-01'},
          {'organization_id': 'org', 'feed_id': 'o1', 'start': '2025-04-01'},
          {'organization_id': 'org', 'feed_id': 'o2', 'start': '2026-06-01'}]
REPEAT = [{'year': '2023', 'prior_at_risk': '0', 'lapsed_again': '0', 'others_at_risk': '99', 'others_lapsed': '9'},
          {'year': '2024', 'prior_at_risk': '5', 'lapsed_again': '2', 'others_at_risk': '100', 'others_lapsed': '10'},
          {'year': '2025', 'prior_at_risk': '5', 'lapsed_again': '0', 'others_at_risk': '100', 'others_lapsed': '10'},
          {'year': '2026', 'prior_at_risk': '10', 'lapsed_again': '4', 'others_at_risk': '100', 'others_lapsed': '20'}]
LATER = [{'organization_id': 'org', 'feed_id': 'p1', 'start': '2027-04-01'},
         {'organization_id': 'org', 'feed_id': 'o2', 'start': '2027-04-01'},
         {'organization_id': 'org', 'feed_id': 'o3', 'start': '2027-05-01'}]


def write(path, rows):
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


class Parts(unittest.TestCase):
    def test_cohort(self):
        keys = {(r['organization_id'], r['feed_id']) for r in CENSUS_FEEDS}
        rows = fr.cohort(FEEDS, LAPSES, keys)
        self.assertEqual([(r['feed_id'], r['group']) for r in rows],
                         [('p1', 'prior'), ('p2', 'prior'), ('new1', 'other'), ('o1', 'other'), ('o2', 'other'),
                          ('o3', 'other')])
        by = {r['feed_id']: r for r in rows}
        self.assertEqual((by['p1']['past_lapses'], by['p1']['past_april1_lapses']), (2, 2))
        self.assertEqual((by['o1']['past_april1_lapses'], by['o1']['lapsed_on_prior_day']), (1, 'false'))
        self.assertEqual(by['new1']['in_census'], 'false')
        self.assertEqual(by['p2']['pref_name'], '山形県')

    def test_rates(self):
        self.assertEqual(fr.rates(REPEAT, {2026}), (0.4, 0.2, 10, 100))
        rp, ro, pn, on = fr.rates(REPEAT, {2024, 2025, 2026})
        self.assertAlmostEqual(rp, 0.3)
        self.assertAlmostEqual(ro, 40 / 300)
        self.assertEqual((pn, on), (20, 300))
        with self.assertRaises(ValueError):
            fr.rates(REPEAT, {2023})

    def test_expect(self):
        m = fr.expect(2, 4, 0.4, 0.2)
        self.assertEqual((m['expected'], m['low90'], m['high90']), (1.6, 0, 4))
        self.assertEqual((m['expected_prior'], m['expected_other']), (0.8, 0.8))

    def test_fisher(self):
        self.assertAlmostEqual(fr.fisher_greater(2, 0, 1, 3), 0.2)
        self.assertAlmostEqual(fr.fisher_greater(1, 1, 1, 3), 0.6)
        self.assertAlmostEqual(fr.fisher_greater(0, 5, 5, 0), 1.0)

    def test_forecast(self):
        keys = {(r['organization_id'], r['feed_id']) for r in CENSUS_FEEDS}
        fc = fr.forecast(fr.cohort(FEEDS, LAPSES, keys), REPEAT)
        self.assertEqual((fc['cohort'], fc['prior'], fc['other']), (6, 2, 4))
        self.assertEqual(fc['models']['rates_2026']['expected'], 1.6)
        self.assertEqual(fc['models']['rates_2024_2026']['expected'], 1.1)
        self.assertEqual(fc['models']['flat_2026']['expected'], 1.3)
        self.assertEqual(fc['target_day'], '2027-04-01')


class Main(unittest.TestCase):
    def setup_dir(self, d):
        census = os.path.join(d, 'census')
        os.makedirs(census)
        write(os.path.join(census, 'feeds.csv'), CENSUS_FEEDS)
        write(os.path.join(census, 'lapses.csv'), LAPSES)
        write(os.path.join(census, 'repeat_cliff.csv'), REPEAT)
        feeds = os.path.join(d, 'feeds.json')
        with open(feeds, 'w', encoding='utf-8') as f:
            json.dump({'code': 200, 'body': FEEDS}, f, ensure_ascii=False)
        return census, feeds

    def test_forecast_files(self):
        with tempfile.TemporaryDirectory() as d:
            census, feeds = self.setup_dir(d)
            fr.main(['--feeds-json', feeds, '--census', census, '--as-of', '2026-10-22', '--min-feeds', '5',
                     '--out', d])
            out = os.path.join(d, 'forecast', '2027-04-01')
            with open(os.path.join(out, 'cohort.csv'), 'rb') as f:
                raw = f.read()
            self.assertTrue(raw.startswith('﻿'.encode('utf-8')))
            self.assertIn(b'\r\n', raw)
            with open(os.path.join(out, 'cohort.csv'), encoding='utf-8-sig', newline='') as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(list(rows[0]), fr.COLS)
            self.assertEqual(len(rows), 6)
            with open(os.path.join(out, 'forecast.json'), encoding='utf-8') as f:
                s = json.load(f)
            self.assertEqual(s['recorded'], '2026-10-22')
            self.assertIsNone(s['result'])
            with open(os.path.join(out, 'forecast.md'), encoding='utf-8') as f:
                md = f.read()
            self.assertIn('| 2026年の割合 / 2026 rates | 40.0% | 20.0% | 1.6 (0.8 + 0.8) | 0–4 |', md)
            self.assertIn("Made by MV2 of Munim, Inc. with AI agents working in MV2's name.", md)

            # Score against a later census, from the cohort recorded before the day.
            later = os.path.join(d, 'later.csv')
            write(later, LATER)
            fr.main(['--census', census, '--as-of', '2027-04-08', '--score', later,
                     '--cohort', os.path.join(out, 'cohort.csv'), '--out', d])
            with open(os.path.join(out, 'score.json'), encoding='utf-8') as f:
                r = json.load(f)['result']
            self.assertEqual((r['prior_lapsed'], r['prior_not'], r['other_lapsed'], r['other_not']), (1, 1, 1, 3))
            self.assertEqual(r['p_one_sided'], 0.6)
            with open(os.path.join(out, 'scored.csv'), encoding='utf-8-sig', newline='') as f:
                scored = {x['feed_id']: x['lapsed_on_target_day'] for x in csv.DictReader(f)}
            self.assertEqual(scored, {'p1': 'true', 'p2': 'false', 'new1': 'false', 'o1': 'false', 'o2': 'true',
                                      'o3': 'false'})

    def test_too_few_feeds(self):
        with tempfile.TemporaryDirectory() as d:
            census, feeds = self.setup_dir(d)
            with self.assertRaises(SystemExit):
                fr.main(['--feeds-json', feeds, '--census', census, '--out', d])

    def test_header(self):
        with open(fr.__file__, encoding='utf-8') as f:
            head = f.read(1200)
        self.assertIn('Apache-2.0', head)
        self.assertIn("Made with AI agents working in MV2's name", head)


if __name__ == '__main__':
    unittest.main()
