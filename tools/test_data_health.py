# Tests for data_health.py on small CSV files built here; every expected value was worked out by hand.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data_health as dh  # noqa: E402

LAPSES = ('organization_id,feed_id,lapses,lapsed_days,longest_lapse_days,list_end_date\r\n'
          'o,F1,2,40,30,2027-03-31\r\no,F2,0,0,0,2026-11-10\r\no,F4,1,5,5,2026-12-31\r\no,F5,0,0,0,2027-09-30\r\n')
WATCH = ('status,days_left,latest_feed_end_date,organization_id,feed_id\r\n'
         '8-30,19,2026-11-10,o,F2\r\nexpired,-10,2026-10-12,o,F9\r\n')
HOLIDAYS = ('organization_id,feed_id,organization_name,feed_name,pref_id,pref_name,license,cover_from,'
            '2026-09-22,2026-11-03,2027-01-01\r\n'
            'o,F1,事業者,路線1,1,北海道,CC BY 4.0,feed_info,ordinary,ordinary,sunday\r\n'
            'o,F2,事業者,路線2,13,東京都,CC BY 4.0,feed_info,sunday,sunday,no_service\r\n'
            'o,F3,事業者,路線3,13,東京都,CC BY 4.0,calendar,ordinary,outside,outside\r\n'
            'o,F5,事業者,路線5,13,東京都,CC0 1.0,feed_info,sunday,sunday,sunday\r\n')
NAMES = ('organization_id,feed_id,organization_name,feed_name,pref_id,pref_name,license,stops,stops_reading,stops_en\r\n'
         'o,F1,事業者,路線1,1,北海道,CC BY 4.0,10,9,9\r\n'
         'o,F2,事業者,路線2,13,東京都,CC BY 4.0,10,10,0\r\n'
         'o,F4,事業者,路線4,1,北海道,CC BY 4.0,0,0,0\r\n'
         'o,F5,事業者,路線5,13,東京都,CC0 1.0,20,20,20\r\n')


def write(folder, name, text):
    path = os.path.join(folder, name)
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        f.write(text)
    return path


class DataHealthTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        self.paths = {n: write(d, f'{n}.csv', t) for n, t in
                      (('lapses', LAPSES), ('watch', WATCH), ('holidays', HOLIDAYS), ('names', NAMES))}
        self.out = os.path.join(d, 'out')
        self.rows = dh.build(dh.read_csv(self.paths['lapses']), dh.read_csv(self.paths['watch']),
                             dh.read_csv(self.paths['holidays']), dh.read_csv(self.paths['names']), '2026-10-22')
        self.by = {r['feed_id']: r for r in self.rows}

    def tearDown(self):
        self.tmp.cleanup()

    def test_fisher(self):
        self.assertAlmostEqual(dh.fisher_greater(3, 0, 0, 3), 0.05)
        self.assertAlmostEqual(dh.fisher_greater(2, 1, 1, 2), 0.5)
        self.assertAlmostEqual(dh.fisher_greater(0, 3, 3, 0), 1.0)
        self.assertIsNone(dh.fisher_greater(0, 0, 1, 1))
        self.assertIsNone(dh.fisher_greater(1, 1, 0, 0))

    def test_universe_and_order(self):
        # holidays or names census only (F9 is only on the expiry list), by prefecture then feed
        self.assertEqual([r['feed_id'] for r in self.rows], ['F1', 'F4', 'F2', 'F3', 'F5'])
        self.assertEqual(self.by['F4']['pref_name'], '北海道')
        self.assertEqual(self.by['F3']['pref_name'], '東京都')

    def test_expiry(self):
        f1, f2, f3, f4 = self.by['F1'], self.by['F2'], self.by['F3'], self.by['F4']
        self.assertEqual((f1['end_date'], f1['end_date_source'], f1['days_left'], f1['expiry']),
                         ('2027-03-31', 'census', 160, 'ok'))
        self.assertEqual((f2['end_date'], f2['end_date_source'], f2['days_left'], f2['expiry'], f2['expiry_status']),
                         ('2026-11-10', 'watch', 19, 'flag', '8-30'))
        self.assertEqual((f3['end_date'], f3['end_date_source'], f3['days_left'], f3['expiry']), ('', '', '', 'ok'))
        self.assertEqual(f4['days_left'], 70)

    def test_lapses(self):
        self.assertEqual((self.by['F1']['past_lapses'], self.by['F1']['lapsed_days'],
                          self.by['F1']['longest_lapse_days']), (2, 40, 30))
        self.assertEqual(self.by['F2']['past_lapses'], 0)
        self.assertEqual(self.by['F3']['past_lapses'], '')

    def test_holidays(self):
        # 2026-09-22 is before as-of and is not counted
        self.assertEqual((self.by['F1']['upcoming_ordinary'], self.by['F1']['upcoming_applicable'],
                          self.by['F1']['holidays']), (1, 2, 'flag'))
        self.assertEqual((self.by['F2']['upcoming_ordinary'], self.by['F2']['upcoming_applicable'],
                          self.by['F2']['holidays']), (0, 2, 'ok'))
        self.assertEqual((self.by['F3']['upcoming_ordinary'], self.by['F3']['upcoming_applicable'],
                          self.by['F3']['holidays']), (0, 0, 'n/a'))
        self.assertEqual((self.by['F4']['upcoming_applicable'], self.by['F4']['holidays']), ('', 'n/a'))

    def test_names(self):
        # 9 of 10 is exactly 90%, which is ok
        self.assertEqual((self.by['F1']['readings'], self.by['F1']['english']), ('ok', 'ok'))
        self.assertEqual((self.by['F2']['readings'], self.by['F2']['english']), ('ok', 'flag'))
        self.assertEqual((self.by['F4']['readings'], self.by['F4']['english']), ('n/a', 'n/a'))
        self.assertEqual((self.by['F3']['stops'], self.by['F3']['readings']), ('', 'n/a'))

    def test_flags(self):
        self.assertEqual({f: (r['flags_required'], r['all_ok']) for f, r in self.by.items()},
                         {'F1': (1, 'no'), 'F2': (1, 'no'), 'F3': (0, 'no'), 'F4': (0, 'no'), 'F5': (0, 'yes')})

    def test_summary_and_predictions(self):
        s = dh.summarise(self.rows, dh.read_csv(self.paths['watch']), '2026-10-22')
        self.assertEqual(s['feeds'], 5)
        self.assertEqual(s['checks']['expiry'], {'flag': 1, 'ok': 4})
        self.assertEqual(s['checks']['holidays'], {'flag': 1, 'n/a': 2, 'ok': 2})
        self.assertEqual(s['checks']['readings'], {'n/a': 2, 'ok': 3})
        self.assertEqual(s['checks']['english'], {'flag': 1, 'n/a': 2, 'ok': 2})
        self.assertEqual(s['flags_required'], {'0': 3, '1': 2})
        self.assertEqual((s['any_required_flag'], s['all_ok']), (2, 1))
        self.assertEqual(s['watch_outside'], {'expired': 1})
        d1, d2 = s['predictions']['D1'], s['predictions']['D2']
        # D1: past lapse F1 (flag) against F2, F5 (ok); F4 has no holiday check
        self.assertEqual((d1['first'], d1['rest'], d1['p'], d1['held']), ([1, 1], [0, 2], 0.333333, False))
        # D2: English flagged F2 (ok) against F1 (flag), F5 (ok)
        self.assertEqual((d2['first'], d2['rest'], d2['p'], d2['held']), ([0, 1], [1, 2], 1.0, False))
        e = s['expiry_by_past_lapses']
        self.assertEqual((e['first'], e['rest'], e['p']), ([0, 2], [1, 2], 1.0))
        self.assertNotIn('held', e)

    def test_prefectures(self):
        p = {r['pref_id']: r for r in dh.prefectures(self.rows)}
        self.assertEqual((p[1]['feeds'], p[1]['any_required_flag'], p[1]['all_ok'], p[1]['holidays_flag']),
                         (2, 1, 0, 1))
        self.assertEqual((p[13]['feeds'], p[13]['any_required_flag'], p[13]['all_ok'], p[13]['expiry_flag'],
                          p[13]['english_flag']), (3, 1, 1, 1, 1))

    def test_main_writes_files(self):
        s = dh.main(['--lapses', self.paths['lapses'], '--watch', self.paths['watch'], '--holidays',
                     self.paths['holidays'], '--names', self.paths['names'], '--out', self.out])
        for name in ('feeds.csv', 'prefectures.csv', 'summary.json', 'health.md'):
            self.assertTrue(os.path.exists(os.path.join(self.out, name)), name)
        with open(os.path.join(self.out, 'summary.json'), encoding='utf-8') as f:
            self.assertEqual(json.load(f)['feeds'], s['feeds'])
        rows = dh.read_csv(os.path.join(self.out, 'feeds.csv'))
        self.assertEqual(list(rows[0].keys()), dh.COLUMNS)
        self.assertEqual(rows[2]['feed_id'], 'F2')
        with open(os.path.join(self.out, 'health.md'), encoding='utf-8') as f:
            md = f.read()
        self.assertIn('D1:', md)
        self.assertIn('did not hold.', md)


if __name__ == '__main__':
    unittest.main()
