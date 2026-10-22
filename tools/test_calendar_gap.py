# Tests for calendar_gap.py on small CSV files built here; every expected value was worked out by hand
# (days from 2026-10-22: to 2026-10-31 is 9, to 2026-12-31 is 70, to 2027-03-31 is 160, to 2027-06-30 is 251).
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calendar_gap as cg  # noqa: E402

HEAD = 'organization_id,feed_id,organization_name,feed_name,pref_id,pref_name,license,end_date,end_date_source,expiry\r\n'
HEALTH = HEAD + ''.join(f'o,{f},事業者,路線{f},13,東京都,CC BY 4.0,{e},{s},{x}\r\n' for f, e, s, x in (
    ('A', '2027-03-31', 'census', 'ok'), ('B', '2027-03-27', 'census', 'ok'), ('B2', '2027-03-31', 'census', 'ok'),
    ('C', '2026-10-31', 'watch', 'flag'), ('D', '2027-06-30', 'census', 'ok'), ('E', '2026-12-31', 'census', 'ok'),
    ('F', '2027-03-31', 'census', 'ok'), ('G', '2027-03-31', 'census', 'ok'), ('H', '', '', 'ok')))
LASTBUS = ('organization_id,feed_id,status,cover_start,cover_end\r\n'
           'o,A,ok,2026-04-01,2027-03-31\r\n'
           'o,B,ok,2026-03-29,2026-10-24\r\n'
           'o,B2,ok,2026-04-01,2027-03-30\r\n'
           'o,C,ok,2025-11-01,2026-10-15\r\n'
           'o,D,ok,,\r\n'
           'o,E,ok,2026-01-01,2027-01-15\r\n'
           'o,G,failed,,\r\n'
           'o,H,ok,2026-04-01,2027-03-31\r\n')


def write(folder, name, text):
    path = os.path.join(folder, name)
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        f.write(text)
    return path


class CalendarGapTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        self.health, self.lastbus = write(d, 'health.csv', HEALTH), write(d, 'lastbus.csv', LASTBUS)
        self.out = os.path.join(d, 'out')
        self.rows = cg.build(cg.read_csv(self.health), cg.read_csv(self.lastbus), '2026-10-22')
        self.by = {r['feed_id']: r for r in self.rows}

    def tearDown(self):
        self.tmp.cleanup()

    def test_classes(self):
        self.assertEqual([r['feed_id'] for r in self.rows], ['A', 'B', 'B2', 'C', 'D', 'E', 'F', 'G', 'H'])
        want = {'A': 'same', 'B': 'file_ends_earlier', 'B2': 'file_ends_earlier', 'C': 'file_ends_earlier',
                'D': 'no_file_dates', 'E': 'file_ends_later', 'F': 'not_read', 'G': 'not_read', 'H': 'no_listed_date'}
        self.assertEqual({k: r['class'] for k, r in self.by.items()}, want)

    def test_gaps_and_days(self):
        self.assertEqual(self.by['A']['gap_days'], 0)
        self.assertEqual(self.by['A']['listed_days_left'], 160)
        self.assertEqual(self.by['A']['file_days_left'], 160)
        self.assertEqual(self.by['B']['gap_days'], 154)
        self.assertEqual(self.by['B']['listed_days_left'], 156)
        self.assertEqual(self.by['B']['file_days_left'], 2)
        self.assertEqual(self.by['B2']['gap_days'], 1)
        self.assertEqual(self.by['C']['gap_days'], 16)
        self.assertEqual(self.by['C']['file_days_left'], -7)
        self.assertEqual(self.by['D']['listed_days_left'], 251)
        self.assertEqual(self.by['D']['file_end'], '')
        self.assertEqual(self.by['E']['gap_days'], -15)
        self.assertEqual(self.by['E']['file_days_left'], 85)
        self.assertEqual(self.by['F']['listed_days_left'], 160)
        self.assertEqual(self.by['H']['listed_days_left'], '')
        self.assertEqual(self.by['H']['file_days_left'], 160)

    def test_hidden_and_ended(self):
        self.assertEqual({k for k, r in self.by.items() if r['hidden'] == 'yes'}, {'B'})
        self.assertEqual({k for k, r in self.by.items() if r['hidden'] == 'no'}, {'A', 'B2', 'C', 'E'})
        self.assertEqual({k for k, r in self.by.items() if r['file_ended'] == 'yes'}, {'C'})
        self.assertEqual(self.by['H']['file_ended'], 'no')
        self.assertEqual(self.by['D']['file_ended'], '')

    def test_median(self):
        self.assertEqual(cg.median([154, 1, 16]), 16)
        self.assertEqual(cg.median([4, 1]), 1)
        self.assertIsNone(cg.median([]))

    def test_summary(self):
        s = cg.summarise(self.rows, '2026-10-22')
        self.assertEqual(s['feeds'], 9)
        self.assertEqual(s['classes'], {'same': 1, 'file_ends_earlier': 3, 'file_ends_later': 1, 'no_file_dates': 1,
                                        'no_listed_date': 1, 'not_read': 2})
        self.assertEqual(s['earlier'], {'feeds': 3, 'over_7_days': 2, 'over_30_days': 1, 'median_gap_days': 16,
                                        'max_gap_days': 154})
        self.assertEqual(s['hidden'], 1)
        self.assertEqual(s['file_ended_while_listed_current'], 1)
        self.assertEqual(s['listed_sources'], {'': 1, 'census': 7, 'watch': 1})

    def test_main_writes_files(self):
        s = cg.main(['--health', self.health, '--lastbus', self.lastbus, '--as-of', '2026-10-22', '--out', self.out])
        self.assertEqual(sorted(os.listdir(self.out)), ['calendar_gap.md', 'feeds.csv', 'summary.json'])
        with open(os.path.join(self.out, 'summary.json'), encoding='utf-8') as f:
            self.assertEqual(json.load(f)['hidden'], s['hidden'])
        with open(os.path.join(self.out, 'calendar_gap.md'), encoding='utf-8') as f:
            md = f.read()
        self.assertIn('| 事業者 | 路線B | 東京都 | 2027-03-27 | 2026-10-24 | 154 | yes |', md)
        self.assertIn('| 事業者 | 路線C | 東京都 | 2026-10-31 | 2026-10-15 | 16 | no |', md)
        self.assertNotIn('路線B2 |', md)
        self.assertLess(md.index('路線B |'), md.index('路線C |'))
        rows = cg.read_csv(os.path.join(self.out, 'feeds.csv'))
        self.assertEqual(list(rows[0].keys()), cg.COLUMNS)
        self.assertEqual(rows[1]['gap_days'], '154')


if __name__ == '__main__':
    unittest.main()
