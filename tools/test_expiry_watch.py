# Tests for expiry_watch.py on a made-up feed list and lapse census (no network). Needs gtfs_lapses.py and
# fy_cliff.py in the same folder.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import csv
import datetime as dt
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import expiry_watch as ew  # noqa: E402

AS_OF = dt.date(2026, 10, 21)


def feed(fid, end, org='org', disc=False, pref=6, pub='2026-04-01'):
    return {'organization_id': org, 'organization_name': f'{org} バス', 'feed_id': fid, 'feed_name': f'路線 {fid}',
            'feed_pref_id': pref, 'feed_license': 'CC BY 4.0', 'last_published_at': pub,
            'latest_feed_start_date': '2026-04-01', 'latest_feed_end_date': end, 'feed_is_discontinued': disc,
            'feed_discontinued_date': ''}


# a: ended yesterday. b: today is its last day. c, c2: 7 days left (c2 lapsed before, so it comes first).
# d: 8 days. e: 30 days. f: 60 days. g: 61 days (not listed). h: ends exactly 2027-03-31. k: ends later.
# i: discontinued. j: no end date.
FEEDS = [feed('a', '2026-10-20', pub='2025-10-01'), feed('b', '2026-10-21'), feed('c', '2026-10-28'),
         feed('c2', '2026-10-28'), feed('d', '2026-10-29'), feed('e', '2026-11-20'), feed('f', '2026-12-20'),
         feed('g', '2026-12-21'), feed('h', '2027-03-31'), feed('k', '2027-09-30'),
         feed('i', '2026-10-01', disc=True), feed('j', None)]
LAPSES = [{'organization_id': 'org', 'feed_id': 'a', 'start': '2025-04-01'},
          {'organization_id': 'org', 'feed_id': 'a', 'start': '2026-05-03'},
          {'organization_id': 'org', 'feed_id': 'c2', 'start': '2024-04-01'},
          {'organization_id': 'org', 'feed_id': 'z', 'start': ''}]


class Parts(unittest.TestCase):
    def test_band(self):
        self.assertEqual([ew.band(d) for d in (-30, -1, 0, 7, 8, 30, 31, 60)],
                         ['expired', 'expired', 'ends_7', 'ends_7', 'ends_30', 'ends_30', 'ends_60', 'ends_60'])
        self.assertIsNone(ew.band(61))

    def test_feed_list(self):
        self.assertEqual(len(ew.feed_list({'code': 200, 'body': FEEDS})), 12)
        self.assertEqual(len(ew.feed_list(FEEDS + [{'feed_id': 'x'}, 'junk'])), 12)
        self.assertEqual(ew.feed_list({'code': 500}), [])

    def test_history(self):
        h = ew.history(LAPSES)
        self.assertEqual(h[('org', 'a')], (2, 1, dt.date(2026, 5, 3)))
        self.assertEqual(h[('org', 'c2')], (1, 1, dt.date(2024, 4, 1)))
        self.assertNotIn(('org', 'z'), h)


class Watch(unittest.TestCase):
    def setUp(self):
        self.rows, self.counts = ew.watch(FEEDS, ew.history(LAPSES), AS_OF)

    def test_order_and_status(self):
        self.assertEqual([(r['feed_id'], r['days_left'], r['status']) for r in self.rows],
                         [('a', -1, 'expired'), ('b', 0, 'ends_7'), ('c2', 7, 'ends_7'), ('c', 7, 'ends_7'),
                          ('d', 8, 'ends_30'), ('e', 30, 'ends_30'), ('f', 60, 'ends_60')])

    def test_counts(self):
        c = self.counts
        self.assertEqual((c['feeds_in_list'], c['discontinued'], c['no_end_date'], c['active']), (12, 1, 1, 10))
        self.assertEqual((c['expired'], c['ends_7'], c['ends_30'], c['ends_60']), (1, 3, 2, 1))
        self.assertEqual((c['ending_on_fy_end'], c['ending_by_fy_end']), (1, 9))

    def test_row_fields(self):
        a = self.rows[0]
        self.assertEqual((a['past_lapses'], a['past_april1_lapses'], a['latest_lapse_start']), (2, 1, '2026-05-03'))
        self.assertEqual((a['pref_name'], a['days_since_published'], a['last_published_at']), ('山形県', 385, '2025-10-01'))
        self.assertEqual(self.rows[1]['past_lapses'], 0)
        self.assertEqual(self.rows[1]['latest_lapse_start'], '')


class Main(unittest.TestCase):
    def run_main(self, d, *extra):
        feeds = os.path.join(d, 'feeds.json')
        with open(feeds, 'w', encoding='utf-8') as f:
            json.dump({'code': 200, 'message': 'ok', 'body': FEEDS}, f, ensure_ascii=False)
        lapses = os.path.join(d, 'lapses.csv')
        with open(lapses, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['organization_id', 'feed_id', 'start'])
            w.writeheader()
            w.writerows(LAPSES)
        ew.main(['--as-of', '2026-10-21', '--feeds-json', feeds, '--lapses', lapses, '--out', d] + list(extra))
        return os.path.join(d, 'watch', '2026-10-21')

    def test_files(self):
        with tempfile.TemporaryDirectory() as d:
            out = self.run_main(d, '--min-feeds', '5')
            with open(os.path.join(out, 'expiring.csv'), 'rb') as f:
                raw = f.read()
            self.assertTrue(raw.startswith('﻿'.encode('utf-8')))
            self.assertIn(b'\r\n', raw)
            with open(os.path.join(out, 'expiring.csv'), encoding='utf-8-sig', newline='') as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(list(rows[0]), ew.COLS)
            self.assertEqual([r['feed_id'] for r in rows], ['a', 'b', 'c2', 'c', 'd', 'e', 'f'])
            with open(os.path.join(out, 'summary.json'), encoding='utf-8') as f:
                s = json.load(f)
            self.assertEqual((s['listed'], s['listed_with_past_lapse'], s['listed_with_past_april1_lapse']), (7, 2, 2))
            self.assertEqual(s['counts']['ending_on_fy_end'], 1)
            self.assertTrue(s['source'].endswith('(saved copy)'))
            with open(os.path.join(out, 'watch.md'), encoding='utf-8') as f:
                md = f.read()
            self.assertIn('| 期限切れ / expired | -1 | 2026-10-20 | org バス | 路線 a | 山形県 | 2 (1) | 2025-10-01 |', md)
            self.assertIn("Made by MV2 of Munim, Inc. with AI agents working in MV2's name.", md)

    def test_too_few_feeds(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SystemExit):
                self.run_main(d)

    def test_header(self):
        with open(ew.__file__, encoding='utf-8') as f:
            head = f.read(1200)
        self.assertIn('Apache-2.0', head)
        self.assertIn("Made with AI agents working in MV2's name", head)


if __name__ == '__main__':
    unittest.main()
