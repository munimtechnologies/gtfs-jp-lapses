# Tests for names_check.py on four made-up feeds worked out by hand (no network).
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
import names_check as nc  # noqa: E402


def S(sid, name, lt='', parent=''):
    return {'stop_id': sid, 'stop_name': name, 'location_type': lt, 'parent_station': parent}


def T(table, field, lang, tr, rid='', fv=''):
    return {'table_name': table, 'field_name': field, 'language': lang, 'translation': tr, 'record_id': rid,
            'record_sub_id': '', 'field_value': fv}


def J(text, lang, tr):
    return {'trans_id': text, 'lang': lang, 'translation': tr}


def TR(tid, headsign):
    return {'route_id': 'r', 'service_id': 'w', 'trip_id': tid, 'trip_headsign': headsign}


# A: GTFS-format translations. s1 by text; s2 by record_id, whose Japanese "English" beats the field_value row;
# s3's reading has kanji and only its parent p3 has English; s4 (entrance) and s5 (no name) are not counted.
A = {'stops.txt': [S('s1', '駅前'), S('s2', '市役所', '0'), S('p3', '病院', '1'), S('s3', '病院', '0', 'p3'),
                   S('s4', '入口', '2'), S('s5', '', '0')],
     'translations.txt': [T('stops', 'stop_name', 'ja-Hrkt', 'えきまえ', fv='駅前'),
                          T('stops', 'stop_name', 'en', 'Ekimae', fv='駅前'),
                          T('stops', 'stop_name', 'ja-Hrkt', 'しやくしょ', rid='s2'),
                          T('stops', 'stop_name', 'en', '市役所', rid='s2'),
                          T('stops', 'stop_name', 'EN', 'City Hall', fv='市役所'),
                          T('stops', 'stop_name', 'ja-Hrkt', '病院', fv='病院'),
                          T('stops', 'stop_name', 'en', 'Hospital', rid='p3'),
                          T('stops', 'stop_name', 'ko', '병원', rid='s3'),
                          T('stops', 'stop_name', 'ja', '病院', fv='病院'),
                          T('trips', 'trip_headsign', 'en', 'For Station', fv='駅前行'),
                          T('trips', 'trip_headsign', 'ja-Hrkt', 'びょういんゆき', rid='t2')],
     'trips.txt': [TR('t1', '駅前行'), TR('t2', '病院行'), TR('t3', '病院行'), TR('t4', '')]}
# B: the older GTFS-JP format, which translates every name with that text (two poles called 本町, and a headsign).
B = {'stops.txt': [S('b1', '本町', '0'), S('b2', '本町', '0'), S('b3', '東口', '0')],
     'translations.txt': [J('本町', 'ja', '本町'), J('本町', 'ja-Hrkt', 'ほんまち'), J('本町', 'en', 'Honmachi'),
                          J('東口', 'ja-Hrkt', 'ひがしぐち')],
     'trips.txt': [TR('t1', '本町')]}
# C: no translations.txt. D: a translations.txt with a header only.
C = {'stops.txt': [S('c1', 'X町')], 'trips.txt': [TR('t1', 'X町')]}
D = {'stops.txt': [S('d1', '西町')], 'translations.txt': [], 'trips.txt': []}
# Z: stations only, no poles.
Z = {'stops.txt': [S('z1', '駅', '1')]}

WANT = {
    'A': {'format': 'gtfs', 'stops': 3, 'stops_reading': 3, 'stops_en': 2, 'reading_parent_only': 0,
          'en_parent_only': 1, 'reading_kanji': 1, 'en_japanese': 1, 'en_copy': 1, 'other_languages': 'ko',
          'headsigns': 2, 'headsigns_reading': 1, 'headsigns_en': 1},
    'B': {'format': 'jp_v2', 'stops': 3, 'stops_reading': 3, 'stops_en': 2, 'reading_parent_only': 0,
          'en_parent_only': 0, 'reading_kanji': 0, 'en_japanese': 0, 'en_copy': 0, 'other_languages': '',
          'headsigns': 1, 'headsigns_reading': 1, 'headsigns_en': 1},
    'C': {'format': 'missing', 'stops': 1, 'stops_reading': 0, 'stops_en': 0, 'headsigns': 1, 'headsigns_en': 0},
    'D': {'format': 'empty', 'stops': 1, 'stops_reading': 0, 'stops_en': 0, 'headsigns': 0},
}


def reader(files):
    return lambda name: iter(files.get(name, []))


def feed(fid, pref, lic='CC BY 4.0', disc=False):
    return {'organization_id': 'o', 'feed_id': fid, 'organization_name': 'O', 'feed_name': fid, 'feed_pref_id': pref,
            'feed_license': lic, 'latest_feed_end_date': '2027-03-31', 'feed_is_discontinued': disc}


FEEDS = {'A': feed('A', 13), 'B': feed('B', 13, 'CC0 1.0'), 'C': feed('C', 1, 'CC BY 2.1 JP'), 'D': feed('D', '', 'PDL1.0')}


def results():
    out = []
    for key, files in (('A', A), ('B', B), ('C', C), ('D', D)):
        r = nc.check(reader(files), 'translations.txt' in files)
        r['feed'] = FEEDS[key]
        out.append(r)
    return out


def make_zip(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        for name, rows in files.items():
            s = io.StringIO()
            w = csv.DictWriter(s, fieldnames=list(rows[0]) if rows else ['table_name', 'field_name', 'language',
                                                                        'translation'])
            w.writeheader()
            w.writerows(rows)
            zf.writestr(name, '﻿' + s.getvalue())
    return buf.getvalue()


class Test(unittest.TestCase):
    def test_lang_kind(self):
        self.assertEqual([nc.lang_kind(x) for x in ('ja-Hrkt', 'JA_HRKT', 'en', 'en-US', 'EN', 'zh-Hans', '', None)],
                         ['reading', 'reading', 'en', 'en', 'en', 'zh-hans', None, None])

    def test_check(self):
        for key, files in (('A', A), ('B', B), ('C', C), ('D', D)):
            r = nc.check(reader(files), 'translations.txt' in files)
            for k, v in WANT[key].items():
                self.assertEqual(r[k], v, f'{key} {k}')

    def test_band(self):
        self.assertEqual([nc.band(0, 3), nc.band(2, 3), nc.band(9, 10), nc.band(3, 3), nc.band(0, 0)],
                         ['none', 'some', 'most', 'most', ''])

    def test_predictions(self):
        p = nc.predictions(results())
        self.assertEqual((p['N1']['feeds'], p['N1']['most_reading'], p['N1']['share']), (4, 2, 0.5))
        self.assertFalse(p['N1']['held'])
        self.assertEqual(p['N2']['most_en'], 0)
        self.assertFalse(p['N2']['held'])
        self.assertEqual((p['N3']['stops_en'], p['N3']['en_japanese'], p['N3']['share']), (4, 1, 0.25))
        self.assertTrue(p['N3']['held'])
        self.assertEqual((p['N4']['with_rows'], p['N4']['jp_v2'], p['N4']['share']), (2, 1, 0.5))
        self.assertTrue(p['N4']['held'])

    def test_prefs(self):
        rows = nc.pref_rows(results())
        self.assertEqual([(r['pref_id'], r['feeds']) for r in rows], [(0, 1), (1, 1), (13, 2)])
        self.assertEqual(rows[2], {'pref_id': 13, 'pref_name': '東京都', 'feeds': 2, 'stops': 6, 'share_reading': 1.0,
                                   'share_en': 0.667, 'feeds_most_reading': 2, 'feeds_most_en': 0})

    def test_run_and_outputs(self):
        zips = {'A': make_zip(A), 'B': make_zip(B), 'C': make_zip(C), 'D': make_zip(D), 'Z': make_zip(Z)}

        def get_zip(f):
            if f['feed_id'] == 'Y':
                raise OSError('down')
            return zips[f['feed_id']]

        feeds = [FEEDS['A'], FEEDS['B'], FEEDS['C'], FEEDS['D'], feed('X', 1, 'その他'), feed('Y', 1),
                 feed('E', 1, disc=True), feed('Z', 1)]
        res, skipped = nc.run(feeds, dt.date(2026, 10, 22), get_zip, pause=0, log=lambda s: None)
        self.assertEqual(sorted((s['feed_id'], s['reason']) for s in skipped),
                         [('E', 'discontinued'), ('X', 'license'), ('Y', 'download_failed'), ('Z', 'no_stops')])
        got = {r['feed']['feed_id']: r for r in res}
        for key in 'ABCD':
            for k, v in WANT[key].items():
                self.assertEqual(got[key][k], v, f'zip {key} {k}')
        with tempfile.TemporaryDirectory() as tmp:
            s = nc.write_outputs(tmp, dt.date(2026, 10, 22), res, skipped, len(feeds), 'T')
            self.assertEqual((s['feeds_checked'], s['totals']['stops'], s['totals']['stops_reading'],
                              s['totals']['stops_en'], s['totals']['share_en']), (4, 8, 6, 4, 0.5))
            self.assertEqual(s['formats'], {'gtfs': 1, 'jp_v2': 1, 'empty': 1, 'missing': 1})
            self.assertEqual(s['bands'], {'reading': {'none': 2, 'some': 0, 'most': 2},
                                          'en': {'none': 2, 'some': 2, 'most': 0}})
            self.assertEqual(s['other_languages'], {'ko': 1})
            out = os.path.join(tmp, 'names', '2026-10-22')
            for name, n in (('feeds.csv', 4), ('prefectures.csv', 3), ('skipped.csv', 4)):
                with open(os.path.join(out, name), encoding='utf-8-sig', newline='') as f:
                    self.assertEqual(len(list(csv.DictReader(f))), n, name)
            with open(os.path.join(out, 'summary.json'), encoding='utf-8') as f:
                self.assertEqual(json.load(f)['predictions']['N3']['en_japanese'], 1)
            with open(os.path.join(out, 'names.md'), encoding='utf-8') as f:
                self.assertIn('| 東京都 | 2 | 6 | 100.0% | 66.7% | 2 | 0 |', f.read())


if __name__ == '__main__':
    unittest.main()
