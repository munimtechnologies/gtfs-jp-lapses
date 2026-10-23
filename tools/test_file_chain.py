# Tests for file_chain.py on a made-up feed list and API answers (no network).
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import csv
import datetime as dt
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import file_chain as fc  # noqa: E402

AS_OF = dt.date(2026, 10, 23)


def feed(fid, end, disc=False, pref=6):
    return {'organization_id': 'org', 'organization_name': 'org バス', 'feed_id': fid, 'feed_name': f'路線 {fid}',
            'feed_pref_id': pref, 'feed_license': 'CC BY 4.0', 'latest_feed_end_date': end,
            'feed_is_discontinued': disc}


def gf(rid, a, b, pub='2026-03-01T10:00:00+09:00', memo=''):
    return {'rid': rid, 'from_date': a, 'to_date': b, 'published_at': pub, 'memo': memo}


# a: current to 11-30, next from 12-01 (continuous; next published 10-20 JST, 42 days ahead).
# b: current to 10-31, next from 11-05 (break 11-01..11-04, 4 days; published 10-20 15:30 UTC = 10-21 JST, 15 days).
# c: current ended 10-20, next from 11-01 (nothing in force today; 9 days to 11-01; published 10-01, 31 days).
# d: listed end 10-01 (expired, never read). e: overlapping files like 2026-11-01..02 (continuous; 19 days).
# f: API request failed. g: the only file ends 2027-03-31 but the list says 2027-06-30 (list mismatch).
# h: one file to the listed end (continuous, no later file). i: discontinued. j: no end date. k: no files.
FEEDS = [feed('a', '2027-03-31'), feed('b', '2027-03-31'), feed('c', '2027-03-31'), feed('d', '2026-10-01'),
         feed('e', '2026-12-31'), feed('f', '2027-03-31'), feed('g', '2027-06-30'), feed('h', '2027-03-31'),
         feed('i', '2026-10-01', disc=True), feed('j', None), feed('k', '2027-03-31')]
BODIES = {
    'a': {'is_discontinued': False, 'gtfs_files': [
        gf('next_1', '2026-12-01', '2027-03-31', pub='2026-10-20T23:30:00+09:00'),
        gf('current', '2026-04-01', '2026-11-30', memo='R8.4.1改正')]},
    'b': {'is_discontinued': False, 'gtfs_files': [
        gf('current', '2026-04-01', '2026-10-31', memo='一部便運休'),
        gf('next_1', '2026-11-05', '2027-03-31', pub='2026-10-20T15:30:00Z')]},
    'c': {'is_discontinued': False, 'gtfs_files': [
        gf('current', '2026-04-01', '2026-10-20'),
        gf('next_1', '2026-11-01', '2027-03-31', pub='2026-10-01T09:00:00+09:00')]},
    'e': {'is_discontinued': False, 'gtfs_files': [
        gf('next_1', '2026-11-01', '2026-12-31', pub='2026-10-13T15:59:14.520716+09:00'),
        gf('current', '2025-11-01', '2026-11-02', memo='年末年始の対応')]},
    'f': None,
    'g': {'is_discontinued': False, 'gtfs_files': [gf('current', '2026-04-01', '2027-03-31')]},
    'h': {'is_discontinued': False, 'gtfs_files': [gf('current', '2026-04-01', '2027-03-31'),
                                                   {'rid': 'bad', 'from_date': '', 'to_date': None}]},
    'k': {'is_discontinued': False, 'gtfs_files': []},
}


class FakeFetch:
    def __init__(self):
        self.calls = []

    def __call__(self, org, fid):
        self.calls.append(fid)
        return BODIES[fid]


class Parts(unittest.TestCase):
    def test_jst_day(self):
        self.assertEqual(fc.jst_day('2026-10-20T15:30:00Z'), dt.date(2026, 10, 21))
        self.assertEqual(fc.jst_day('2026-10-13T15:59:14.520716+09:00'), dt.date(2026, 10, 13))
        self.assertEqual(fc.jst_day('2026-10-13'), dt.date(2026, 10, 13))
        self.assertIsNone(fc.jst_day(''))

    def test_pref(self):
        self.assertEqual(fc.pref(6), (6, '山形県'))
        self.assertEqual(fc.pref('47'), (47, '沖縄県'))
        self.assertEqual(fc.pref(None), (0, ''))

    def test_quartiles(self):
        q = fc.quartiles([42, 15, 31, 19])
        self.assertEqual((q['n'], q['min'], q['median'], q['max']), (4, 15, 25, 42))
        self.assertEqual(fc.quartiles([]), {'n': 0})
        self.assertEqual(fc.quartiles([7])['median'], 7)


class Chain(unittest.TestCase):
    def row(self, fid):
        f = next(x for x in FEEDS if x['feed_id'] == fid)
        return fc.chain(f, BODIES[fid], AS_OF)

    def test_continuous(self):
        r = self.row('a')
        self.assertEqual((r['class'], r['in_force_from'], r['in_force_to'], r['in_force_days_left']),
                         ('continuous', '2026-04-01', '2026-11-30', 38))
        self.assertEqual((r['later_files'], r['next_from'], r['next_published'], r['next_lead_days']),
                         (1, '2026-12-01', '2026-10-20', 42))
        self.assertEqual((r['covered_to'], r['continued'], r['break_from'], r['break_within_60'], r['memo_ended']),
                         ('2027-03-31', 'yes', '', '', 'no'))

    def test_break(self):
        r = self.row('b')
        self.assertEqual((r['class'], r['break_from'], r['break_days'], r['resume_from'], r['break_within_60']),
                         ('break', '2026-11-01', 4, '2026-11-05', 'yes'))
        self.assertEqual((r['in_force_to'], r['in_force_days_left'], r['continued'], r['covered_to']),
                         ('2026-10-31', 8, 'no', '2026-10-31'))
        self.assertEqual((r['next_published'], r['next_lead_days'], r['memo_ended'], r['in_force_memo']),
                         ('2026-10-21', 15, 'yes', '一部便運休'))

    def test_not_in_force(self):
        r = self.row('c')
        self.assertEqual((r['class'], r['break_from'], r['break_days'], r['resume_from'], r['break_within_60']),
                         ('not_in_force', '2026-10-23', 9, '2026-11-01', 'yes'))
        self.assertEqual((r['in_force_to'], r['in_force_days_left'], r['continued'], r['next_lead_days']),
                         ('', '', '', 31))
        self.assertEqual(r['covered_to'], '')

    def test_overlap(self):
        r = self.row('e')
        self.assertEqual((r['class'], r['in_force_to'], r['in_force_days_left'], r['covered_to'], r['continued']),
                         ('continuous', '2026-11-02', 10, '2026-12-31', 'yes'))
        self.assertEqual((r['next_from'], r['next_published'], r['next_lead_days']), ('2026-11-01', '2026-10-13', 19))

    def test_others(self):
        self.assertEqual(self.row('f')['class'], 'api_failed')
        g = self.row('g')
        self.assertEqual((g['class'], g['in_force_days_left'], g['continued'], g['later_files']),
                         ('list_mismatch', 159, 'no', 0))
        h = self.row('h')
        self.assertEqual((h['class'], h['in_force_days_left'], h['later_files'], h['next_lead_days']),
                         ('continuous', 159, 0, ''))
        self.assertEqual(self.row('k')['class'], 'no_files')


class Run(unittest.TestCase):
    def setUp(self):
        self.fetch = FakeFetch()
        self.rows, self.counts = fc.run(FEEDS, AS_OF, self.fetch, pause=0)
        self.s = fc.summarise(self.rows, self.counts, AS_OF)

    def test_order_and_calls(self):
        self.assertEqual([r['feed_id'] for r in self.rows], ['a', 'e', 'h', 'b', 'c', 'g', 'k', 'f', 'd'])
        self.assertNotIn('d', self.fetch.calls)
        self.assertEqual(sorted(self.fetch.calls), ['a', 'b', 'c', 'e', 'f', 'g', 'h', 'k'])

    def test_counts(self):
        self.assertEqual(self.counts, {'feeds_in_list': 11, 'discontinued': 1, 'no_end_date': 1, 'active': 9})
        self.assertEqual(self.s['classes'], {'continuous': 3, 'break': 1, 'not_in_force': 1, 'list_mismatch': 1,
                                             'no_files': 1, 'api_failed': 1, 'expired': 1})

    def test_summary(self):
        s = self.s
        self.assertEqual((s['checked_ok'], s['breaks'], s['break_within_60'], s['with_later_file']), (6, 2, 2, 4))
        self.assertEqual((s['in_force_ends_within_60'], s['in_force_ends_within_60_continued'],
                          s['in_force_ends_within_60_listed_later']), (3, 2, 3))
        self.assertEqual((s['memo_ended'], s['lead_days']['n'], s['lead_days']['median'], s['lead_days_under_7']),
                         (1, 4, 25, 0))

    def test_predictions(self):
        p = self.s['predictions']
        self.assertEqual(list(p), ['C1', 'C2', 'C3', 'C4'])
        self.assertEqual((p['C1']['value'], p['C1']['held']), (0.3333, False))
        self.assertEqual((p['C2']['value'], p['C2']['held']), (0.6667, False))
        self.assertEqual((p['C3']['value'], p['C3']['held']), (0.6667, False))
        self.assertEqual((p['C4']['value'], p['C4']['held']), (25, True))


class Main(unittest.TestCase):
    def test_files(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, 'feeds.json')
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({'code': 200, 'message': 'ok', 'body': FEEDS}, f, ensure_ascii=False)
            fc.main(['--as-of', '2026-10-23', '--feeds-json', path, '--min-feeds', '5', '--pause', '0',
                     '--out', d], fetch=FakeFetch())
            out = os.path.join(d, '2026-10-23')
            with open(os.path.join(out, 'chain.csv'), 'rb') as f:
                raw = f.read()
            self.assertTrue(raw.startswith('﻿'.encode('utf-8')))
            self.assertIn(b'\r\n', raw)
            with open(os.path.join(out, 'chain.csv'), encoding='utf-8-sig', newline='') as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(list(rows[0]), fc.COLUMNS)
            self.assertEqual(len(rows), 9)
            self.assertNotIn('organization_email', rows[0])
            with open(os.path.join(out, 'summary.json'), encoding='utf-8') as f:
                s = json.load(f)
            self.assertEqual(s['as_of'], '2026-10-23')
            with open(os.path.join(out, 'chain.md'), encoding='utf-8') as f:
                md = f.read()
            self.assertIn('| org バス | 路線 b | 山形県 | 2027-03-31 | break | 2026-10-31 | 2026-11-01 | 4 | 2026-11-05 | '
                          '一部便運休 |', md)
            self.assertIn('| org バス | 路線 b | 山形県 | 2026-10-31 | 8 | 2026-11-05 | 2026-10-21 | no | 2027-03-31 |', md)
            self.assertIn('- C4: ', md)
            self.assertIn("Made by MV2 of Munim, Inc. with AI agents working in MV2's name.", md)

    def test_too_few_feeds(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, 'feeds.json')
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({'body': FEEDS}, f)
            with self.assertRaises(SystemExit):
                fc.main(['--feeds-json', path, '--out', d], fetch=FakeFetch())

    def test_header(self):
        with open(fc.__file__, encoding='utf-8') as f:
            head = f.read(2000)
        self.assertIn('Apache-2.0', head)
        self.assertIn("Made with AI agents working in MV2's name", head)


if __name__ == '__main__':
    unittest.main()
