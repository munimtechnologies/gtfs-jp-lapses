# Tests for gtfs_lapses.py on made-up feed histories (no network).
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import csv
import datetime as dt
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gtfs_lapses as gl  # noqa: E402

D = dt.date.fromisoformat


def f(rid, pub, start, end, kind='NEW'):
    return {'rid': rid, 'gtfs_file_uid': rid + '-uid', 'update_type': kind, 'published_at': pub,
            'from_date': start, 'to_date': end}


def detail(files, max_prev=None, disc=False, disc_date=''):
    prev = sum(1 for x in files if x['rid'].startswith('prev'))
    return {'code': 200, 'body': {'max_prev': prev if max_prev is None else max_prev, 'max_next': 0,
                                  'is_discontinued': disc, 'discontinued_date': disc_date, 'gtfs_files': files}}


# a: renewed on time every time. b: lapsed 2025-04-01..04-09 (renewal published late, back-dated to 04-01),
# and lapsed again from 2026-10-01 to today. c: an UPDATE file published after its start date.
# d: discontinued on 2026-06-01 with its data ending 2026-03-31 (end of a network, not a lapse). e: no files.
A = detail([f('current', '2026-03-20T10:00:00+09:00', '2026-04-01', '2027-03-31'),
            f('prev_1', '2025-03-25T10:00:00+09:00', '2025-04-01', '2026-03-31')])
B = detail([f('current', '2025-04-10T09:00:00+09:00', '2025-04-01', '2026-09-30'),
            f('prev_1', '2024-03-15T09:00:00+09:00', '2024-04-01', '2025-03-31')])
C = detail([f('current', '2025-06-10T09:00:00+09:00', '2025-06-01', '2027-05-31', 'UPDATE')])
DD = detail([f('current', '2025-03-01T09:00:00+09:00', '2025-04-01', '2026-03-31')], disc=True,
            disc_date='2026-06-01')
E = detail([])
FEEDS = ('# test\n# cols\n'
         'org|a|A町|Aバス|6|CC BY 4.0|2027-03-31|false\n'
         'org|b|B市|Bバス|6|CC BY 4.0|2026-09-30|false\n'
         'org|c|C村|Cバス|13|CC0 1.0|2027-05-31|false\n'
         'org|d|D町|Dバス|13|CC BY 4.0|2026-03-31|true\n'
         'org|e|E町|Eバス|2|CC BY 4.0||false\n')
# A feed that publishes daily: the API holds 3 earlier files but the first answer carries only 1.
DAILY = [f('current', '2026-10-03T04:05:00+09:00', '2026-10-01', '2027-01-17'),
         f('prev_1', '2026-10-02T04:05:00+09:00', '2026-10-01', '2027-01-16'),
         f('prev_2', '2026-10-01T04:05:00+09:00', '2026-10-01', '2027-01-15'),
         f('prev_3', '2026-09-30T04:05:00+09:00', '2026-04-01', '2026-12-31')]


class Lapses(unittest.TestCase):
    def test_days(self):
        self.assertEqual(gl.jst_day('2026-03-31T23:30:00+09:00'), D('2026-03-31'))
        self.assertEqual(gl.jst_day('2026-03-31T15:30:00Z'), D('2026-04-01'))  # 00:30 next day in Japan
        self.assertIsNone(gl.day('2026/03/31'))
        self.assertIsNone(gl.jst_day(None))

    def test_parse_feeds(self):
        rows = gl.parse_feeds_txt('﻿' + FEEDS)
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[3]['feed_is_discontinued'], 'true')

    def test_coverage_merges_adjacent(self):
        vs, bad = gl.versions(A)
        self.assertEqual(bad, [])
        self.assertEqual(gl.coverage(vs), [[D('2025-04-01'), D('2027-03-31')]])
        self.assertEqual(gl.lapses(gl.coverage(vs), D('2026-10-15')), [])

    def test_late_renewal_and_open_lapse(self):
        vs, _ = gl.versions(B)
        res = gl.analyse_feed(vs, D('2026-10-15'))
        self.assertEqual(res['first_covered'], D('2024-04-01'))
        self.assertEqual(res['lapses'], [(D('2025-04-01'), D('2025-04-09'), False),
                                         (D('2026-10-01'), D('2026-10-15'), True)])
        self.assertEqual(res['lapsed_days'], 9 + 15)
        self.assertEqual(res['years'][2025], (365, 9))
        self.assertEqual(res['years'][2024], (275, 0))  # 2024-04-01..12-31
        self.assertEqual(res['years'][2026][1], 15)
        self.assertEqual(gl.lead_days(vs[1]), -9)  # published 9 days after its first valid date

    def test_update_counted_from_first_valid_date_unless_strict(self):
        vs, _ = gl.versions(C)
        self.assertEqual(gl.analyse_feed(vs, D('2026-10-15'))['first_covered'], D('2025-06-01'))
        self.assertEqual(gl.analyse_feed(vs, D('2026-10-15'), strict=True)['first_covered'], D('2025-06-10'))

    def test_unusable_files(self):
        vs, bad = gl.versions(detail([f('current', None, '2026-01-01', '2026-12-31'),
                                      f('prev_1', '2025-01-01T00:00:00+09:00', '2025-12-31', '2025-01-01')]))
        self.assertEqual(vs, [])
        self.assertEqual(len(bad), 2)

    def fetch_with(self, short, full):
        urls = []

        def fake(url, tries=3):
            urls.append(url)
            return json.dumps(short if 'max_prev=100&' in url else full)
        old = gl.fetch
        gl.fetch = fake
        try:
            return gl.load_detail('org', 'daily bus', None, 0), urls
        finally:
            gl.fetch = old

    def test_asks_again_for_the_full_history(self):
        got, urls = self.fetch_with(detail(DAILY[:2], max_prev=3), detail(DAILY))
        self.assertEqual(len(urls), 2)
        self.assertIn('/feeds/daily%20bus?max_prev=100&', urls[0])
        self.assertIn('?max_prev=3&max_next=100', urls[1])
        self.assertEqual(gl.prev_count(got), 3)
        res = gl.analyse_feed(gl.versions(got)[0], D('2026-10-16'))
        self.assertEqual(res['first_covered'], D('2026-09-30'))  # prev_3 is NEW, so it counts from publication

    def test_complete_history_is_fetched_once(self):
        got, urls = self.fetch_with(detail(DAILY), detail([]))
        self.assertEqual(len(urls), 1)
        self.assertEqual(gl.prev_count(got), 3)

    def test_main_offline(self):
        with tempfile.TemporaryDirectory() as tmp:
            det = os.path.join(tmp, 'details')
            os.makedirs(det)
            for name, d in (('a', A), ('b', B), ('c', C), ('d', DD), ('e', E)):
                with open(os.path.join(det, f'org__{name}.json'), 'w', encoding='utf-8') as fh:
                    json.dump(d, fh)
            feeds = os.path.join(tmp, 'feeds.txt')
            with open(feeds, 'w', encoding='utf-8') as fh:
                fh.write(FEEDS)
            out = os.path.join(tmp, 'out')
            gl.main(['--as-of', '2026-10-15', '--feeds', feeds, '--details', det, '--pause', '0', '--out', out])
            o = os.path.join(out, 'lapses', '2026-10-15')
            self.assertEqual(sorted(os.listdir(o)), ['errors.json', 'feeds.csv', 'findings.md', 'lapses.csv',
                                                     'prefectures.csv', 'summary.json', 'versions.csv', 'years.csv'])
            with open(os.path.join(o, 'summary.json'), encoding='utf-8') as fh:
                s = json.load(fh)
            self.assertEqual(s['lapses'], 2)
            self.assertEqual(s['active_lapsed_now'], 1)  # b; d is discontinued, not lapsed
            self.assertEqual(s['feeds_with_lapse'], 1)
            self.assertTrue(s['checks']['all_read_or_error'])
            self.assertEqual(s['checks']['latest_to_matches_list_end'], 4)  # e has no files and no date
            self.assertEqual(s['checks']['feeds_fewer_prev_files_than_api_max_prev'], 0)
            self.assertEqual(s['expiry']['expired'], 1)
            self.assertEqual(s['expiry']['ending_exactly_fy_end'], 1)
            with open(os.path.join(o, 'feeds.csv'), 'rb') as fh:
                raw = fh.read()
            self.assertTrue(raw.startswith(b'\xef\xbb\xbf'))
            rows = {r['feed_id']: r for r in csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))}
            self.assertEqual(rows['d']['window_end'], '2026-03-31')  # data ended before it was discontinued
            self.assertEqual(rows['d']['lapsed_days'], '0')
            self.assertEqual(rows['b']['lapsed_now_days'], '15')
            self.assertEqual(rows['c']['lapsed_days_strict'], '0')  # strict starts at 06-10: still no gap after
            self.assertEqual(rows['e']['observed_days'], '0')
            with open(os.path.join(o, 'findings.md'), encoding='utf-8') as fh:
                self.assertIn('| Bバス |', fh.read())


if __name__ == '__main__':
    unittest.main()
