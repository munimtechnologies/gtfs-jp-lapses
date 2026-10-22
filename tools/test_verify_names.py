# Tests for verify_names.py on small files built here; every expected count was worked out by hand.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import io
import os
import sys
import unittest
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify_names as vn  # noqa: E402

STOPS_A = 'stop_id,stop_name,location_type,parent_station\r\nP,駅,1,\r\nA,駅,0,P\r\nB,市役所,0,\r\nC,病院,,\r\nD,,0,\r\n'
TRANS_A = ('table_name,field_name,language,translation,record_id,record_sub_id,field_value\r\n'
           'stops,stop_name,ja-Hrkt,えき,,,駅\r\n'
           'stops,stop_name,en,Station,,,駅\r\n'
           'stops.txt,stop_name,ja-Hrkt,しやくしょ,B,,\r\n'
           'stops,stop_name,ja_Latn,Shiyakusho,B,,\r\n'
           'stops,stop_name,EN-us,City Hall,B,,\r\n'
           'stops,stop_name,ja-Hrkt,,C,,\r\n'
           'trips,trip_headsign,en,Hospital,,,病院\r\n')
STOPS_B = 'stop_id,stop_name\r\nX,本町\r\nY,新町\r\n'
TRANS_B = 'trans_id,lang,translation\r\n本町,ja-Hrkt,ほんまち\r\n本町,en,Honmachi\r\n新町,ja-Latn,Shinmachi\r\n'


def make_zip(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        for name, data in files:
            zf.writestr(name, data)
    return buf.getvalue()


ZIP_A = make_zip([('stops.txt', STOPS_A.encode('utf-8')), ('translations.txt', TRANS_A.encode('utf-8'))])
ZIP_B = make_zip([('stops.txt', STOPS_B.encode('cp932')), ('translations.txt', TRANS_B.encode('cp932'))])
ZIP_C = make_zip([('__MACOSX/stops.txt', b'\x00\x01junk'),
                  ('gtfs/stops.txt', '﻿stop_id,stop_name\nS1,駅前\n'.encode('utf-8'))])


def count(data):
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        return vn.count(zf)


class CountTest(unittest.TestCase):
    def test_gtfs_rows(self):
        c, fmt = count(ZIP_A)
        self.assertEqual(fmt, 'gtfs')
        # A by field_value (reading, en); B by record_id (reading, ja-Latn, en-US); C's only row is empty; P is a
        # parent station and D has no name, so neither is counted.
        self.assertEqual({k: c[k] for k in vn.KEYS}, {'stops': 3, 'reading': 2, 'en': 2, 'latn': 1, 'en_or_latn': 2})
        self.assertEqual(c['utf8'], 1)

    def test_old_format_in_shift_jis(self):
        c, fmt = count(ZIP_B)
        self.assertEqual(fmt, 'jp_v2')
        self.assertEqual({k: c[k] for k in vn.KEYS}, {'stops': 2, 'reading': 1, 'en': 1, 'latn': 1, 'en_or_latn': 2})
        self.assertEqual(c['utf8'], 0)

    def test_folder_bom_and_no_translations(self):
        c, fmt = count(ZIP_C)
        self.assertEqual(fmt, 'missing')
        self.assertEqual({k: c[k] for k in vn.KEYS}, {'stops': 1, 'reading': 0, 'en': 0, 'latn': 0, 'en_or_latn': 0})
        self.assertEqual(c['utf8'], 1)


class CompareTest(unittest.TestCase):
    def test_compare(self):
        census = {'stops': '3', 'stops_reading': '2', 'stops_en': '1'}
        self.assertEqual(vn.compare(census, {'stops': 3, 'reading': 2, 'en': 2}), ['en'])
        self.assertEqual(vn.compare(census, {'stops': 3, 'reading': 2, 'en': 1}), [])

    def test_run_and_summary(self):
        census = [{'organization_id': 'o', 'feed_id': 'a', 'pref_id': '1', 'format': 'gtfs', 'stops': '3',
                   'stops_reading': '2', 'stops_en': '2'},
                  {'organization_id': 'o', 'feed_id': 'bad', 'pref_id': '1', 'format': 'gtfs', 'stops': '1',
                   'stops_reading': '1', 'stops_en': '1'}]

        def get(org, feed):
            if feed == 'bad':
                raise OSError('HTTP Error 404')
            return ZIP_A

        rows = vn.run(census, get, pause=0, log=lambda s: None)
        self.assertEqual([r['status'] for r in rows], ['match', 'failed'])
        s = vn.summarise(rows)
        self.assertEqual(s['status'], {'match': 1, 'failed': 1})
        self.assertEqual(s['totals'], {'stops': 3, 'reading': 2, 'en': 2, 'latn': 1, 'en_or_latn': 2})
        # 2 of 3 stops is under 90%, so no feed counts as giving readings or English for most stops.
        self.assertEqual((s['feeds_most_reading'], s['feeds_most_en'], s['feeds_most_en_or_latn']), (0, 0, 0))
        self.assertEqual((s['not_utf8'], s['format_differs'], s['feeds_with_latn']), (0, 0, 1))
        md = vn.markdown(s, rows, 'now')
        self.assertIn('o/bad | failed', md)


if __name__ == '__main__':
    unittest.main()
