# Tests for calendar_next.py on a small gap table built here and API bodies given in the test (no network); every
# expected value was worked out by hand (2026-09-30 to 2026-10-31 is 31 days; 2026-11-30 to 2026-12-31 is 31).
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calendar_next as cn  # noqa: E402

HEAD = ('organization_id,feed_id,organization_name,feed_name,pref_id,pref_name,license,listed_end,listed_source,'
        'file_start,file_end,gap_days,class,listed_days_left,file_days_left,file_ended,hidden\r\n')
GAPS = HEAD + ''.join(f'o,{f},事業者,路線{f},13,東京都,CC BY 4.0,{le},census,{fs},{fe},{g},{c},1,1,{x},{h}\r\n'
                      for f, le, fs, fe, g, c, x, h in (
    ('A', '2027-03-31', '2026-04-01', '2027-03-31', 0, 'same', 'no', 'no'),
    ('B', '2027-03-27', '2026-03-29', '2026-10-24', 154, 'file_ends_earlier', 'no', 'yes'),
    ('M', '2026-12-31', '2025-11-01', '2026-11-02', 59, 'file_ends_earlier', 'no', 'yes'),
    ('U', '2027-03-31', '2026-09-01', '2026-11-30', 121, 'file_ends_earlier', 'no', 'yes'),
    ('N', '2026-10-31', '2023-04-01', '2026-09-30', 31, 'file_ends_earlier', 'yes', 'no'),
    ('P', '2027-03-31', '2026-04-01', '2026-11-30', 121, 'file_ends_earlier', 'no', 'yes'),
    ('F', '2027-03-31', '2026-04-01', '2027-03-22', 9, 'file_ends_earlier', 'no', 'no')))


def f(rid, a, b, memo=''):
    return {'rid': rid, 'from_date': a, 'to_date': b, 'memo': memo}


BODIES = {
    'B': {'is_discontinued': False, 'discontinued_date': '',
          'gtfs_files': [f('next_1', '2026-10-25', '2027-03-27'), f('current', '2026-03-29', '2026-10-24')]},
    'M': {'is_discontinued': False, 'discontinued_date': '',
          'gtfs_files': [f('next_1', '2026-11-01', '2026-12-31'), f('current', '2025-11-01', '2026-11-02')]},
    'U': {'is_discontinued': False, 'discontinued_date': '',
          'gtfs_files': [f('next_2', '2027-03-20', '2027-03-31'), f('next_1', '2026-12-01', '2027-03-19'),
                         f('current', '2026-09-01', '2026-11-30')]},
    'N': {'is_discontinued': False, 'discontinued_date': '',
          'gtfs_files': [f('current', '2023-04-01', '2026-10-31', 'R8.10.1よりデマンド化に伴い、路線廃止')]},
    'P': {'is_discontinued': True, 'discontinued_date': '2027-04-01',
          'gtfs_files': [f('current', '2026-04-01', '2027-03-31', 'ダイヤ改正|臨時\n便'),
                         f('next_1', '2027-01-01', '2027-03-31')]},
}


class CalendarNextTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.gaps = os.path.join(self.tmp.name, 'gaps.csv')
        with open(self.gaps, 'w', encoding='utf-8-sig', newline='') as fh:
            fh.write(GAPS)
        self.out = os.path.join(self.tmp.name, 'out')
        self.rows = {r['feed_id']: r for r in cn.read_csv(self.gaps)}
        self.calls = []
        self.saved = cn.fetch_body
        cn.fetch_body = lambda org, feed: self.calls.append(feed) or BODIES.get(feed)

    def tearDown(self):
        cn.fetch_body = self.saved
        self.tmp.cleanup()

    def one(self, k):
        return cn.check(self.rows[k], BODIES.get(k))

    def test_later_file_covers(self):
        b = self.one('B')
        self.assertEqual((b['class'], b['later_files'], b['later_from'], b['covered_to'], b['uncovered_from'],
                          b['uncovered_days']), ('later_file_covers', 1, '2026-10-25', '2027-03-27', '', 0))
        self.assertEqual((b['current_from'], b['current_to'], b['memo_ended']), ('2026-03-29', '2026-10-24', 'no'))
        m = self.one('M')
        self.assertEqual((m['class'], m['covered_to']), ('later_file_covers', '2026-12-31'))
        u = self.one('U')
        self.assertEqual((u['class'], u['later_files'], u['later_from'], u['covered_to']),
                         ('later_file_covers', 2, '2026-12-01', '2027-03-31'))

    def test_no_later_file(self):
        n = self.one('N')
        self.assertEqual((n['class'], n['later_files'], n['covered_to'], n['uncovered_from'], n['uncovered_days']),
                         ('no_later_file', 0, '2026-09-30', '2026-10-01', 31))
        self.assertEqual((n['memo_ended'], n['is_discontinued'], n['current_to']), ('yes', 'no', '2026-10-31'))

    def test_partial_and_failed(self):
        p = self.one('P')
        self.assertEqual((p['class'], p['later_files'], p['later_from'], p['covered_to'], p['uncovered_from'],
                          p['uncovered_days']), ('later_file_partial', 1, '2027-01-01', '2026-11-30', '2026-12-01', 31))
        self.assertEqual((p['is_discontinued'], p['discontinued_date'], p['memo_ended'], p['current_memo']),
                         ('yes', '2027-04-01', 'no', 'ダイヤ改正／臨時 便'))
        x = self.one('F')
        self.assertEqual((x['status'], x['class'], x['covered_to']), ('api_failed', 'api_failed', ''))

    def test_clean(self):
        self.assertEqual(cn.clean('a|b\n c'), 'a／b c')
        self.assertEqual(cn.clean(None), '')

    def test_main(self):
        s = cn.main(['--gaps', self.gaps, '--checked-on', '2026-10-23', '--pause', '0', '--out', self.out])
        self.assertEqual(self.calls, ['B', 'M', 'U', 'N', 'P', 'F'])
        self.assertEqual(s['feeds'], 6)
        self.assertEqual(s['classes'], {'later_file_covers': 3, 'later_file_partial': 1, 'no_later_file': 1,
                                        'api_failed': 1})
        self.assertEqual(s['hidden'], {'later_file_covers': 3, 'later_file_partial': 1, 'no_later_file': 0,
                                       'api_failed': 0})
        self.assertEqual(s['over_7_days'], {'later_file_covers': 3, 'later_file_partial': 1, 'no_later_file': 1,
                                            'api_failed': 1})
        self.assertEqual(s['file_ended'], {'later_file_covers': 0, 'later_file_partial': 0, 'no_later_file': 1,
                                           'api_failed': 0})
        self.assertEqual((s['memo_ended'], s['marked_discontinued'], s['no_later_file_memo_ended']), (1, 1, 1))
        self.assertEqual(sorted(os.listdir(self.out)), ['feeds.csv', 'next.md', 'summary.json'])
        with open(os.path.join(self.out, 'summary.json'), encoding='utf-8') as fh:
            self.assertEqual(json.load(fh)['classes'], s['classes'])
        with open(os.path.join(self.out, 'next.md'), encoding='utf-8') as fh:
            md = fh.read()
        self.assertIn('Feeds checked: 6. A later file covers the rest: 3; a later file leaves a break: 1; no later '
                      'file: 1; API request failed: 1.', md)
        self.assertIn('Of the 4 feeds called hidden by calendar_gap.py: 3 covered by a later file, 1 with a break, 0 '
                      'with no later file.', md)
        self.assertIn('| 事業者 | 路線N | 東京都 | 2026-10-31 | 2026-09-30 | 2026-10-01 | 31 | 0 | no | '
                      'R8.10.1よりデマンド化に伴い、路線廃止 |', md)
        self.assertIn('| 事業者 | 路線P | 東京都 | 2027-03-31 | 2026-11-30 | 2026-12-01 | 31 | 1 | yes | '
                      'ダイヤ改正／臨時 便 |', md)
        self.assertIn('| 事業者 | 路線B | 東京都 | 2026-10-24 | 2026-10-25 | 2027-03-27 |', md)
        self.assertIn('| 事業者 | 路線U | 東京都 | 2026-11-30 | 2026-12-01 | 2027-03-31 |', md)
        self.assertNotIn('路線A', md)
        rows = cn.read_csv(os.path.join(self.out, 'feeds.csv'))
        self.assertEqual(list(rows[0].keys()), cn.COLUMNS)
        self.assertEqual([r['feed_id'] for r in rows], ['B', 'M', 'U', 'N', 'P', 'F'])
        self.assertEqual(rows[3]['uncovered_days'], '31')


if __name__ == '__main__':
    unittest.main()
