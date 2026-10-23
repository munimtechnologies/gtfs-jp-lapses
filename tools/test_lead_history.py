# Tests for lead_history.py on a made-up version history (no network). Every expected value is worked by hand below.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import csv
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lead_history as lh  # noqa: E402

COLS = ['organization_id', 'feed_id', 'rid', 'gtfs_file_uid', 'update_type', 'published_date', 'from_date', 'to_date',
        'lead_days']


def v(feed, rid, typ, pub, a, b):
    return {'organization_id': 'o', 'feed_id': feed, 'rid': rid, 'gtfs_file_uid': f'{feed}-{rid}', 'update_type': typ,
            'published_date': pub, 'from_date': a, 'to_date': b, 'lead_days': ''}


# Feed a: r0 and r1 are published on its first day (2023-03-20), so no lead. r2 starts 2024-04-01, published 03-25:
#   lead 7, April 1, in the cohort. r3 re-issues 2024-04-01 (not later than r2): a correction. r4 starts 2025-04-01,
#   published 04-03: lead -2; the latest end before it is 2025-03-31, so no file covered 04-01: 'gap'.
# Feed b: s1 first day. s2 starts 2023-07-01, published 06-01: lead 30. s3 (UPDATE) starts 2023-11-01, published
#   11-10: lead -9; s2 runs to 2024-06-30, so the old file was still valid: 'stale'. s5 and s4 are both published
#   2026-10-01; sorted by start, s5 (10-01, lead 0) comes first, then s4 (10-15, lead 14); both start after the cohort.
# Feed c: one file on its first day and one unreadable row.
ROWS = [v('a', 'r1', 'NEW', '2023-03-20', '2023-04-01', '2024-03-31'),
        v('a', 'r0', 'NEW', '2023-03-20', '2022-04-01', '2023-03-31'),
        v('a', 'r2', 'NEW', '2024-03-25', '2024-04-01', '2025-03-31'),
        v('a', 'r3', 'UPDATE', '2024-05-10', '2024-04-01', '2025-03-31'),
        v('a', 'r4', 'NEW', '2025-04-03', '2025-04-01', '2026-03-31'),
        v('b', 's1', 'NEW', '2022-12-01', '2022-12-01', '2023-11-30'),
        v('b', 's2', 'NEW', '2023-06-01', '2023-07-01', '2024-06-30'),
        v('b', 's3', 'UPDATE', '2023-11-10', '2023-11-01', '2024-10-31'),
        v('b', 's4', 'NEW', '2026-10-01', '2026-10-15', '2027-03-31'),
        v('b', 's5', 'NEW', '2026-10-01', '2026-10-01', '2026-10-14'),
        v('c', 'c1', 'NEW', '2024-01-01', '2024-01-01', '2024-12-31'),
        v('c', 'bad', 'NEW', '2024-02-01', '', '2024-12-31')]


class Parts(unittest.TestCase):
    def test_bucket(self):
        self.assertEqual([lh.bucket(x) for x in (-1, 0, 1, 6, 7, 13, 14, 20, 21, 27, 28, 113)],
                         ['late', 'same_day', '1-6', '1-6', '7-13', '7-13', '14-20', '14-20', '21-27', '21-27', '28+',
                          '28+'])

    def test_fisher(self):
        # 3 of 3 against 0 of 3: only the observed table is as extreme, 1 / C(6,3) = 1/20.
        self.assertEqual(lh.fisher_greater(3, 0, 0, 3), 0.05)
        # 1 of 2 against 1 of 2: tables with x = 1 (4 ways) and x = 2 (1 way) of C(4,2) = 6.
        self.assertEqual(lh.fisher_greater(1, 1, 1, 1), round(5 / 6, 6))
        self.assertIsNone(lh.fisher_greater(0, 0, 1, 1))

    def test_new_periods(self):
        periods, counts = lh.new_periods(ROWS)
        self.assertEqual(counts, {'feeds': 3, 'files': 11, 'unreadable': 1, 'first_day': 4, 'reissue': 1,
                                  'new_period': 6})
        got = {p['rid']: (p['lead_days'], p['bucket'], p['april_1'], p['in_cohort'], p['late_kind']) for p in periods}
        self.assertEqual(got, {'r2': (7, '7-13', 'yes', 'yes', ''), 'r4': (-2, 'late', 'yes', 'yes', 'gap'),
                               's2': (30, '28+', 'no', 'yes', ''), 's3': (-9, 'late', 'no', 'yes', 'stale'),
                               's5': (0, 'same_day', 'no', 'no', ''), 's4': (14, '14-20', 'no', 'no', '')})
        self.assertEqual([p['rid'] for p in periods if p['feed_id'] == 'b'], ['s2', 's3', 's5', 's4'])
        s3 = next(p for p in periods if p['rid'] == 's3')
        self.assertEqual((s3['before_from'], s3['before_to']), ('2023-07-01', '2024-06-30'))


class Summary(unittest.TestCase):
    def setUp(self):
        periods, counts = lh.new_periods(ROWS)
        self.s = lh.summarise(periods, counts, lh.day('2026-10-16'))

    def test_cohort(self):
        c = self.s['cohort_stats']
        # Cohort leads -9, -2, 7, 30: median 2.5; inclusive quartiles -3.75 and 12.75.
        self.assertEqual((c['n'], c['late'], c['late_share']), (4, 2, 0.5))
        self.assertEqual(c['lead_days'], {'n': 4, 'min': -9, 'q1': -3.75, 'median': 2.5, 'q3': 12.75, 'max': 30})
        self.assertEqual((c['share_at_least_7'], c['share_at_least_14'], c['share_at_least_21']), (0.5, 0.25, 0.25))
        self.assertEqual(c['buckets'], {'late': 2, 'same_day': 0, '1-6': 0, '7-13': 1, '14-20': 0, '21-27': 0,
                                        '28+': 1})
        self.assertEqual(self.s['late_kind'], {'stale': 1, 'gap': 1})
        self.assertEqual(self.s['all_new_periods'], 6)

    def test_years_april_types_feeds(self):
        y = self.s['by_start_year']
        self.assertEqual(sorted(y), ['2023', '2024', '2025', '2026'])
        self.assertEqual((y['2023']['n'], y['2023']['late']), (2, 1))
        self.assertEqual((y['2026']['n'], y['2026']['late'], y['2026']['lead_days']['median']), (2, 0, 7.0))
        a = self.s['april_1_vs_other']
        self.assertEqual((a['april_1']['n'], a['april_1']['late'], a['other']['n'], a['other']['late']), (2, 1, 2, 1))
        self.assertEqual(a['april_1']['median'], 2.5)
        self.assertEqual(a['fisher_p_greater'], round(5 / 6, 6))
        self.assertEqual(self.s['by_update_type'], {'NEW': {'n': 3, 'late': 1, 'late_share': 0.3333},
                                                    'UPDATE': {'n': 1, 'late': 1, 'late_share': 1.0}})
        f = self.s['per_feed']
        # Feed a: 7 and -2 (median 2.5); feed b: 30 and -9 (median 10.5).
        self.assertEqual((f['feeds'], f['median_of_feed_medians'], f['feeds_any_late'], f['feeds_median_at_least_14']),
                         (2, 6.5, 2, 0))
        self.assertEqual(f['top'], [{'organization_id': 'o', 'feed_id': 'a', 'files': 2},
                                    {'organization_id': 'o', 'feed_id': 'b', 'files': 2}])
        self.assertEqual(f['without_top']['n'], 0)

    def test_predictions(self):
        p = self.s['predictions']
        self.assertEqual(sorted(p), ['P1', 'P2', 'P3', 'P4'])
        self.assertEqual((p['P1']['value'], p['P1']['held']), (0.5, False))
        self.assertEqual((p['P2']['value'], p['P2']['held']), (2.5, True))
        self.assertEqual((p['P3']['value'], p['P3']['held']), (0.25, True))
        self.assertEqual(p['P4']['held'], False)


class EndToEnd(unittest.TestCase):
    def test_main(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, 'versions.csv')
            with open(src, 'w', encoding='utf-8-sig', newline='') as f:
                w = csv.DictWriter(f, fieldnames=COLS)
                w.writeheader()
                w.writerows(ROWS)
            s = lh.main(['--versions', src, '--as-of', '2026-10-16', '--out', os.path.join(d, 'out')])
            out = os.path.join(d, 'out', '2026-10-16')
            self.assertEqual(sorted(os.listdir(out)), ['leads.csv', 'leads.md', 'summary.json'])
            with open(os.path.join(out, 'leads.csv'), encoding='utf-8-sig', newline='') as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 6)
            self.assertEqual(list(rows[0]), lh.COLUMNS)
            with open(os.path.join(out, 'summary.json'), encoding='utf-8') as f:
                self.assertEqual(json.load(f)['cohort_stats']['n'], s['cohort_stats']['n'])
            with open(os.path.join(out, 'leads.md'), encoding='utf-8') as f:
                md = f.read()
            self.assertIn('P2: The median lead', md)
            self.assertIn('Result: 2.5 days, held.', md)
            self.assertIn('| late | 2 | 50.0% |', md)


if __name__ == '__main__':
    unittest.main()
