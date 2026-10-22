# Tests for holiday_check.py on five made-up feeds worked out by hand (no network).
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import csv
import datetime as dt
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import holiday_check as hc  # noqa: E402

D = dt.date.fromisoformat
WK, SU = '1,1,1,1,1,0,0', '0,0,0,0,0,1,1'
NEW_YEAR = ['20261229', '20261230', '20261231', '20270101', '20270102', '20270103']
HOLS = [d.replace('-', '') for d in hc.HOLIDAYS if d.replace('-', '') not in NEW_YEAR]


def cal(sid, days, start='20260401', end='20270331'):
    return dict(zip(['service_id'] + hc.WEEK + ['start_date', 'end_date'], [sid] + days.split(',') + [start, end]))


def trips(sid, n):
    return [{'route_id': 'r', 'service_id': sid, 'trip_id': f'{sid}{i}'} for i in range(n)]


# A: weekday and weekend services, no holidays in the file. B: the same with every holiday on the weekend service and
# no service at all over the New Year break. C: GTFS-JP standard service_ids, no holidays, files in a folder.
# D: the same service every day. E: weekdays only from 2026-10-01, with an extra service on 2026-11-23.
FEEDS = {
    'A': {'calendar.txt': [cal('wk', WK), cal('su', SU)], 'trips.txt': trips('wk', 10) + trips('su', 4)},
    'B': {'calendar.txt': [cal('wk', WK), cal('su', SU)], 'trips.txt': trips('wk', 10) + trips('su', 4),
          'calendar_dates.txt': [{'service_id': s, 'date': d, 'exception_type': t} for d in HOLS
                                 for s, t in (('wk', '2'), ('su', '1'))] +
          [{'service_id': s, 'date': d, 'exception_type': '2'} for d in NEW_YEAR for s in ('wk', 'su')],
          'feed_info.txt': [{'feed_publisher_name': 'B', 'feed_start_date': '20260401', 'feed_end_date': '20270331'}]},
    'C': {'gtfs/calendar.txt': [cal('平日(月〜金)', WK), cal('土曜・日曜・祝日', SU)],
          'gtfs/trips.txt': trips('平日(月〜金)', 8) + trips('土曜・日曜・祝日', 3)},
    'D': {'calendar.txt': [cal('all', '1,1,1,1,1,1,1')], 'trips.txt': trips('all', 5)},
    'E': {'calendar.txt': [cal('wk', WK, start='20261001')], 'trips.txt': trips('wk', 6) + trips('fest', 2),
          'calendar_dates.txt': [{'service_id': 'fest', 'date': '20261123', 'exception_type': '1'}],
          'feed_info.txt': [{'feed_publisher_name': 'E', 'feed_start_date': '20261001', 'feed_end_date': '20270331'}]},
}


def zip_bytes(tables):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        for name, rows in tables.items():
            s = io.StringIO()
            w = csv.DictWriter(s, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
            zf.writestr(name, '﻿' + s.getvalue())
    return buf.getvalue()


def model(key):
    with zipfile.ZipFile(io.BytesIO(zip_bytes(FEEDS[key]))) as zf:
        return hc.build(lambda name: hc.zip_rows(zf, name))


def listed(key, **kw):
    f = {'organization_id': f'org{key}', 'feed_id': f'feed{key}', 'organization_name': f'Org {key}',
         'feed_name': f'Feed {key}', 'feed_pref_id': 13, 'feed_license': 'CC BY 4.0',
         'latest_feed_end_date': '2027-03-31', 'feed_is_discontinued': False}
    f.update(kw)
    return f


class Parts(unittest.TestCase):
    def test_standard_ids(self):
        self.assertTrue(hc.is_standard('平日(月〜金)'))
        self.assertTrue(hc.is_standard('土曜・日曜・祝日'))
        self.assertFalse(hc.is_standard('平日'))

    def test_checks(self):
        days = [d.isoformat() for d, *_ in hc.CHECKS]
        self.assertNotIn('2026-05-03', days)  # Sunday
        self.assertNotIn('2027-01-03', days)
        self.assertIn('2027-01-02', days)
        self.assertIn('2026-09-22', days)
        self.assertEqual(len(days), 21)

    def test_nearest(self):
        a = model('A')
        self.assertEqual(a['cover'], (D('2026-04-01'), D('2027-03-31')))
        self.assertEqual(hc.nearest(a, D('2026-05-06'), 2), D('2026-05-13'))  # 04-29 is a holiday
        self.assertEqual(hc.nearest(a, D('2027-01-11'), 0), D('2027-01-18'))  # 01-04 is in the New Year break
        self.assertEqual(hc.nearest(a, D('2026-11-03'), 6), D('2026-11-01'))
        self.assertEqual(hc.nearest(a, D('2027-03-22'), 6), D('2027-03-28'))  # 03-21 is a holiday

    def test_classes(self):
        # 2027-01-02 is a Saturday: where Saturday and Sunday run the same services there is nothing to tell apart.
        want = {'A': ('ordinary', 'ordinary', 'ordinary', 'same_as_weekend'),
                'B': ('sunday', 'sunday', 'no_service', 'no_service'),
                'C': ('ordinary_std', 'ordinary_std', 'ordinary_std', 'same_as_weekend'),
                'D': ('same_as_weekend', 'same_as_weekend', 'same_as_weekend', 'same_as_weekend'),
                'E': ('ordinary', 'special', 'ordinary', 'no_ordinary_service')}
        for key, classes in want.items():
            m = model(key)
            got = tuple(hc.classify(m, D(d))[0] for d in ('2026-11-03', '2026-11-23', '2026-12-30', '2027-01-02'))
            self.assertEqual(got, classes, key)
        e = model('E')
        self.assertEqual(hc.classify(e, D('2026-09-22')), ('outside', None))
        self.assertEqual(e['cover_from'], 'feed_info')
        self.assertEqual((e['services'], e['standard_services'], e['calendar_dates_rows']), (2, 0, 1))
        self.assertEqual(model('C')['standard_services'], 2)


class Run(unittest.TestCase):
    def setUp(self):
        feeds = [listed(k) for k in 'ABCDE'] + [
            listed('X', feed_license='その他'), listed('Y', latest_feed_end_date='2026-09-30'),
            listed('Z', feed_is_discontinued=True), listed('W')]

        def get(f):
            key = f['feed_id'][-1]
            if key == 'W':
                raise OSError('HTTP 404')
            return zip_bytes(FEEDS[key])
        self.results, self.skipped = hc.run(feeds, D('2026-10-22'), get, pause=0, log=lambda s: None)

    def test_skips(self):
        self.assertEqual(len(self.results), 5)
        self.assertEqual(sorted(s['reason'] for s in self.skipped),
                         ['discontinued', 'download_failed', 'ended', 'license'])

    def test_predictions(self):
        p = hc.predictions(self.results)
        self.assertEqual((p['P1']['shown'], p['P1']['applicable'], p['P1']['held']), (3, 4, False))
        self.assertEqual((p['P2']['feeds'], p['P2']['held']), (3, False))
        self.assertEqual(p['P2']['shown'], {'2026-09-21': 2, '2026-09-22': 2, '2026-09-23': 2})
        self.assertEqual((p['P3']['feeds'], p['P3']['consistent'], p['P3']['held']), (4, 3, False))
        self.assertEqual((p['P4']['share'], p['P4']['difference'], p['P4']['held']), (0.75, 0.0, False))

    def test_files(self):
        with tempfile.TemporaryDirectory() as d:
            s = hc.write_outputs(d, D('2026-10-22'), self.results, self.skipped, 9, '2026-10-22T00:00:00Z')
            out = os.path.join(d, 'holidays', '2026-10-22')
            self.assertEqual(s['feeds_checked'], 5)
            self.assertEqual(s['feeds_with_calendar_dates'], 2)
            self.assertEqual(s['feeds_all_standard_ids'], 1)
            self.assertEqual(s['feeds_upcoming_shown'], 3)  # A, C and E
            with open(os.path.join(out, 'dates.csv'), encoding='utf-8-sig') as f:
                rows = {r['date']: r for r in csv.DictReader(f)}
            r = rows['2026-11-03']
            self.assertEqual((r['covered'], r['applicable'], r['ordinary'], r['ordinary_std'], r['sunday'],
                              r['same_as_weekend'], r['share_shown']), ('5', '4', '2', '1', '1', '1', '0.75'))
            self.assertEqual((rows['2026-09-22']['covered'], rows['2026-09-22']['applicable']), ('4', '3'))
            with open(os.path.join(out, 'upcoming.csv'), encoding='utf-8-sig') as f:
                up = list(csv.DictReader(f))
            self.assertEqual([u['feed_id'] for u in up], ['feedA', 'feedC', 'feedE'])
            # Seven weekday holidays still to come (New Year's Day included); New Year: 12-29 to 01-02 less the Saturday.
            self.assertEqual((up[0]['holidays_shown'], up[0]['holidays_applicable'], up[0]['new_year_shown'],
                              up[0]['new_year_applicable']), ('7', '7', '4', '4'))
            self.assertEqual((up[2]['holidays_shown'], up[2]['holidays_applicable'], up[2]['new_year_shown']),
                             ('6', '7', '4'))
            with open(os.path.join(out, 'holidays.md'), encoding='utf-8') as f:
                md = f.read()
            self.assertIn('| 2026-11-03 | Tue | 文化の日 / Culture Day | 5 | 4 | 3 (1) | 0 | 1 | 0 | 0 | 1 | 75.0% |', md)
            self.assertIn("Made by MV2 of Munim, Inc. with AI agents working in MV2's name.", md)
            with open(os.path.join(out, 'summary.json'), encoding='utf-8') as f:
                self.assertIs(json.load(f)['predictions']['P1']['held'], False)

    def test_header(self):
        with open(hc.__file__, encoding='utf-8') as f:
            head = f.read(1200)
        self.assertIn('Apache-2.0', head)
        self.assertIn("Made with AI agents working in MV2's name", head)


if __name__ == '__main__':
    unittest.main()
