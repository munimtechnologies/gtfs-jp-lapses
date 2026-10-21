# Tests for fy_cliff.py on a made-up census output (no network).
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import csv
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fy_cliff as fc  # noqa: E402


def feed(fid, end):
    return {'organization_id': 'org', 'feed_id': fid, 'window_end': end}


def ver(fid, start, end):
    return {'organization_id': 'org', 'feed_id': fid, 'from_date': start, 'to_date': end}


def lap(fid, start, days, ongoing=False):
    return {'organization_id': 'org', 'feed_id': fid, 'start': start, 'days': str(days),
            'ongoing': 'true' if ongoing else 'false'}


# a: renewed in time twice. b: lapsed 2025-04-01 for 9 days. c: lapsed 2025-04-01 and still open (200 days).
# d: its data ended 2025-03-31 and it was discontinued then (not at risk). e: a lapse that began in October.
FEEDS = [feed('a', '2026-10-16'), feed('b', '2026-10-16'), feed('c', '2026-10-16'), feed('d', '2025-03-31'),
         feed('e', '2026-10-16')]
VERSIONS = [ver('a', '2024-04-01', '2025-03-31'), ver('a', '2025-04-01', '2026-03-31'),
            ver('a', '2026-04-01', '2027-03-31'), ver('b', '2024-04-01', '2025-03-31'),
            ver('b', '2025-04-01', '2027-03-31'), ver('c', '2024-04-01', '2025-03-31'),
            ver('d', '2024-04-01', '2025-03-31'), ver('e', '2025-01-01', '2025-09-30')]
LAPSES = [lap('b', '2025-04-01', 9), lap('c', '2025-04-01', 200, True), lap('e', '2025-10-01', 30)]


class Cliff(unittest.TestCase):
    def setUp(self):
        self.rows = {r['year']: r for r in fc.cliff(FEEDS, VERSIONS, LAPSES)}

    def test_years(self):
        self.assertEqual(sorted(self.rows), [2025, 2026, 2027])

    def test_2025(self):
        r = self.rows[2025]
        self.assertEqual(r['feeds_ending_mar31'], 3)  # a, b, c; d was discontinued
        self.assertEqual(r['renewed_in_time'], 1)
        self.assertEqual(r['lapsed_apr1'], 2)
        self.assertEqual(r['lapsed_share'], 0.6667)
        self.assertEqual(r['still_open'], 1)
        self.assertEqual(r['median_days_ended'], 9)
        self.assertEqual(r['feed_days_lost'], 209)
        self.assertEqual(r['lapses_started'], 3)
        self.assertEqual(r['apr1_share_of_lapses'], 0.6667)

    def test_2026_no_lapse(self):
        r = self.rows[2026]
        self.assertEqual((r['feeds_ending_mar31'], r['lapsed_apr1'], r['lapses_started']), (1, 0, 0))
        self.assertEqual(r['apr1_share_of_lapses'], '')

    def test_future_year_not_watched(self):
        # files valid until 2027-03-31 exist, but no feed is watched past 2027-04-01 yet
        self.assertEqual(self.rows[2027]['feeds_ending_mar31'], 0)
        self.assertEqual(self.rows[2027]['lapsed_share'], '')

    def test_main_writes_files(self):
        with tempfile.TemporaryDirectory() as d:
            for name, rows in (('feeds.csv', FEEDS), ('versions.csv', VERSIONS), ('lapses.csv', LAPSES)):
                with open(os.path.join(d, name), 'w', encoding='utf-8-sig', newline='') as f:
                    w = csv.DictWriter(f, fieldnames=list(rows[0]))
                    w.writeheader()
                    w.writerows(rows)
            fc.main([d])
            with open(os.path.join(d, 'fy_cliff.csv'), encoding='utf-8-sig', newline='') as f:
                out = list(csv.DictReader(f))
            self.assertEqual([r['year'] for r in out], ['2025', '2026', '2027'])
            self.assertEqual(out[0]['lapsed_apr1'], '2')
            with open(os.path.join(d, 'fy_cliff.md'), encoding='utf-8') as f:
                self.assertIn('| 2025 | 3 | 1 | 2 | 0.6667 |', f.read())


if __name__ == '__main__':
    unittest.main()
