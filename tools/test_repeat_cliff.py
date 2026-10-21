# Tests for repeat_cliff.py on a made-up census output (no network). Needs fy_cliff.py in the same folder.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import csv
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import repeat_cliff as rc  # noqa: E402


def feed(fid, org='org'):
    return {'organization_id': org, 'feed_id': fid, 'window_end': '2026-10-16'}


def ver(fid, start, end, org='org'):
    return {'organization_id': org, 'feed_id': fid, 'from_date': start, 'to_date': end}


def lap(fid, start, days, org='org'):
    return {'organization_id': org, 'feed_id': fid, 'start': start, 'days': str(days), 'ongoing': 'false'}


# a: lapsed on April 1 of 2025 and again of 2026. b: lapsed 2025, renewed in time for 2026. c: lapsed 2025, then
# moved its data to end in September, so it is not at risk in 2026. d: first April-1 lapse in 2026.
# e: renewed in time in 2026. f: at risk only in 2025, renewed. g: already in a lapse on 2026-03-31 (a file
# published later was back-dated to end that day), so not at risk in 2026.
FEEDS = [feed('a'), feed('b'), feed('c', 'org2'), feed('d'), feed('e'), feed('f'), feed('g')]
VERSIONS = [ver('a', '2024-04-01', '2025-03-31'), ver('a', '2025-05-01', '2026-03-31'),
            ver('b', '2024-04-01', '2025-03-31'), ver('b', '2025-04-10', '2026-03-31'),
            ver('b', '2026-04-01', '2027-03-31'),
            ver('c', '2024-04-01', '2025-03-31', 'org2'), ver('c', '2025-06-01', '2026-09-30', 'org2'),
            ver('d', '2025-04-01', '2026-03-31'),
            ver('e', '2025-04-01', '2026-03-31'), ver('e', '2026-04-01', '2027-03-31'),
            ver('f', '2024-04-01', '2025-03-31'), ver('f', '2025-04-01', '2026-09-30'),
            ver('g', '2025-04-01', '2026-01-31'), ver('g', '2025-04-01', '2026-03-31')]
LAPSES = [lap('a', '2025-04-01', 30), lap('a', '2026-04-01', 10), lap('b', '2025-04-01', 9),
          lap('c', '2025-04-01', 61, 'org2'), lap('d', '2026-04-01', 20), lap('g', '2026-02-01', 70)]


class Repeats(unittest.TestCase):
    def setUp(self):
        self.rows = rc.repeats(FEEDS, VERSIONS, LAPSES)

    def test_only_years_with_a_previous_april_lapse(self):
        # 2025 has no 2024 lapses; 2027 is not watched yet
        self.assertEqual([r['year'] for r in self.rows], [2026])

    def test_2026(self):
        r = self.rows[0]
        self.assertEqual((r['prior_lapsers'], r['prior_at_risk'], r['lapsed_again']), (3, 2, 1))
        self.assertEqual(r['lapsed_again_orgs'], 1)
        self.assertEqual(r['repeat_share'], 0.5)
        self.assertEqual((r['others_at_risk'], r['others_lapsed'], r['others_share']), (2, 1, 0.5))
        self.assertEqual(r['p_one_sided'], 0.75)

    def test_binom_tail(self):
        self.assertAlmostEqual(rc.binom_tail(1, 2, 0.5), 0.75)
        self.assertEqual(rc.binom_tail(0, 5, 0.1), 1.0)
        self.assertTrue(0.001 < rc.binom_tail(10, 21, 0.179) < 0.003)

    def test_main_writes_files(self):
        with tempfile.TemporaryDirectory() as d:
            for name, rows in (('feeds.csv', FEEDS), ('versions.csv', VERSIONS), ('lapses.csv', LAPSES)):
                with open(os.path.join(d, name), 'w', encoding='utf-8-sig', newline='') as f:
                    w = csv.DictWriter(f, fieldnames=list(rows[0]))
                    w.writeheader()
                    w.writerows(rows)
            rc.main([d])
            with open(os.path.join(d, 'repeat_cliff.csv'), encoding='utf-8-sig', newline='') as f:
                out = list(csv.DictReader(f))
            self.assertEqual([(r['year'], r['lapsed_again']) for r in out], [('2026', '1')])
            with open(os.path.join(d, 'repeat_cliff.md'), encoding='utf-8') as f:
                self.assertIn('| 2026 | 3 | 2 | 1 | 1 | 0.5 |', f.read())


if __name__ == '__main__':
    unittest.main()
