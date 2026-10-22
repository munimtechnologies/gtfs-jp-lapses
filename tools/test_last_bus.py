# Tests for last_bus.py on small files built here; every expected value was worked out by hand.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import datetime as dt
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import last_bus as lb  # noqa: E402

DAYS = {'wed': dt.date(2026, 11, 11), 'sat': dt.date(2026, 11, 14), 'sun': dt.date(2026, 11, 15)}
# 駅前 has two poles (A1, A2); 終点 (C1) and 公園 (E1) are only ever the last stop of a bus trip.
STOPS_A = ('stop_id,stop_name,stop_lat,stop_lon,location_type,parent_station\r\n'
           'A1,駅前,35.000000,135.000000,0,\r\n'
           'A2,駅前,35.000200,135.000000,0,\r\n'
           'B1,本町,35.010000,135.000000,0,\r\n'
           'C1,終点,35.020000,135.000000,0,\r\n'
           'D1,団地,35.030000,135.000000,0,\r\n'
           'E1,公園,35.040000,135.000000,0,\r\n')
ROUTES_A = 'route_id,route_type\r\nR1,3\r\nR2,2\r\n'
CALENDAR_A = ('service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\r\n'
              'WD,1,1,1,1,1,0,0,20260401,20270331\r\n'
              'WE,0,0,0,0,0,1,1,20260401,20270331\r\n')
# Sunday 2026-11-15: the weekend service is replaced by a special one.
CALENDAR_DATES_A = 'service_id,date,exception_type\r\nWE,20261115,2\r\nSP,20261115,1\r\n'
TRIPS_A = ('route_id,service_id,trip_id\r\n'
           'R1,WD,T1\r\nR1,WD,T2\r\nR1,WD,T3\r\nR1,WE,T4\r\nR1,SP,T5\r\nR2,WD,T6\r\nR1,WD,T7\r\nR1,NONE,T8\r\n')
# T1, T2: weekday trips 駅前 -> 本町 -> 終点. T3: after midnight, listed out of order; 本町 is drop-off only.
# T4: Saturday 駅前 -> 本町. T5: Sunday 団地 -> 公園. T6: rail, not counted. T7: weekday 団地 -> 公園 every 30 minutes
# from 6:00 to before 8:00 (starts 6:00, 6:30, 7:00, 7:30). T8: a service with no calendar.
STOP_TIMES_A = ('trip_id,arrival_time,departure_time,stop_id,stop_sequence,pickup_type\r\n'
                'T1,07:00:00,07:00:00,A1,1,0\r\n'
                'T1,07:10:00,07:10:00,B1,2,0\r\n'
                'T1,07:20:00,07:20:00,C1,3,0\r\n'
                'T2,18:30:00,18:30:00,A2,1,\r\n'
                'T2,18:40:00,18:40:00,B1,2,\r\n'
                'T2,18:50:00,18:50:00,C1,3,\r\n'
                'T3,24:40:00,24:40:00,C1,3,0\r\n'
                'T3,24:20:00,24:20:00,A1,1,0\r\n'
                'T3,24:30:00,24:30:00,B1,2,1\r\n'
                'T4,09:00:00,09:00:00,A1,1,0\r\n'
                'T4,09:10:00,09:10:00,B1,2,0\r\n'
                'T5,10:00:00,10:00:00,D1,1,0\r\n'
                'T5,10:15:00,10:15:00,E1,2,0\r\n'
                'T6,23:00:00,23:00:00,E1,1,0\r\n'
                'T6,23:10:00,23:10:00,D1,2,0\r\n'
                'T7,06:00:00,06:00:00,D1,1,0\r\n'
                'T7,06:05:00,06:05:00,E1,2,0\r\n'
                'T8,12:00:00,12:00:00,D1,1,0\r\n'
                'T8,12:05:00,12:05:00,E1,2,0\r\n')
FREQUENCIES_A = 'trip_id,start_time,end_time,headway_secs\r\nT7,06:00:00,08:00:00,1800\r\n'
# A Shift_JIS file in a folder whose calendar runs to 2027 but whose feed_info ends on 2026-10-31: no day is covered.
STOPS_B = 'stop_id,stop_name,stop_lat,stop_lon\r\n本町,本町,35.000000,135.000000\r\n新町,新町,35.018000,135.000000\r\n'
ROUTES_B = 'route_id,route_type\r\nQ,3\r\n'
CALENDAR_B = ('service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\r\n'
              '平日,1,1,1,1,1,1,1,20250401,20270331\r\n')
FEED_INFO_B = ('feed_publisher_name,feed_publisher_url,feed_lang,feed_start_date,feed_end_date\r\n'
               'O,https://example.jp/,ja,20250401,20261031\r\n')
TRIPS_B = 'route_id,service_id,trip_id\r\nQ,平日,U1\r\n'
STOP_TIMES_B = ('trip_id,arrival_time,departure_time,stop_id,stop_sequence\r\n'
                'U1,7:00:00,7:00:00,本町,1\r\nU1,7:06:00,7:06:00,新町,2\r\n')


def make_zip(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        for name, data in files:
            zf.writestr(name, data)
    return buf.getvalue()


ZIP_A = make_zip([('stops.txt', STOPS_A.encode('utf-8')), ('routes.txt', ROUTES_A.encode('utf-8')),
                  ('calendar.txt', CALENDAR_A.encode('utf-8')),
                  ('calendar_dates.txt', CALENDAR_DATES_A.encode('utf-8')),
                  ('trips.txt', TRIPS_A.encode('utf-8')), ('stop_times.txt', STOP_TIMES_A.encode('utf-8')),
                  ('frequencies.txt', FREQUENCIES_A.encode('utf-8'))])
ZIP_B = make_zip([('feed/stops.txt', STOPS_B.encode('cp932')), ('feed/routes.txt', ROUTES_B.encode('cp932')),
                  ('feed/calendar.txt', CALENDAR_B.encode('cp932')), ('feed/feed_info.txt', FEED_INFO_B.encode('cp932')),
                  ('feed/trips.txt', TRIPS_B.encode('cp932')), ('feed/stop_times.txt', STOP_TIMES_B.encode('cp932')),
                  ('__MACOSX/feed/stops.txt', b'\x00junk')])

CENSUS = [{'organization_id': 'o', 'feed_id': 'a', 'organization_name': 'O', 'feed_name': 'A', 'pref_id': '1',
           'pref_name': '北海道', 'license': 'CC BY 4.0'},
          {'organization_id': 'o', 'feed_id': 'b', 'organization_name': 'O', 'feed_name': 'B', 'pref_id': '1',
           'pref_name': '北海道', 'license': 'CC0 1.0'},
          {'organization_id': 'o', 'feed_id': 'bad', 'organization_name': 'O', 'feed_name': 'X', 'pref_id': '1',
           'pref_name': '北海道', 'license': 'CC BY 4.0'}]


def get(org, feed):
    if feed == 'bad':
        raise OSError('HTTP Error 404')
    return {'a': ZIP_A, 'b': ZIP_B}[feed]


def check(data):
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        return lb.check(zf, DAYS)


class HelperTest(unittest.TestCase):
    def test_times_and_dates(self):
        self.assertEqual(lb.secs('24:20:00'), 87600)
        self.assertEqual(lb.secs(' 7:00:00'), 25200)
        self.assertIsNone(lb.secs(''))
        self.assertEqual(lb.fmt(88800), '24:40')
        self.assertEqual(lb.fmt(27000), '7:30')
        self.assertEqual(lb.fmt(None), '')
        self.assertEqual(lb.gdate('20261111'), dt.date(2026, 11, 11))
        self.assertIsNone(lb.gdate('2026-11-11'))
        self.assertEqual([d.weekday() for d in DAYS.values()], [2, 5, 6])
        self.assertEqual([lb.is_bus(x) for x in (3, 715, 200, 4, 2, -1)], [True, True, True, False, False, False])

    def test_quantile(self):
        self.assertEqual(lb.quantile([27000, 88800, 67200], 0.5), 67200)
        self.assertEqual(lb.quantile([27000, 88800, 67200], 0.25), 27000)
        self.assertEqual(lb.quantile([27000, 88800, 67200], 0.75), 88800)
        self.assertEqual(lb.quantile([10, 20], 0.5), 10)
        self.assertIsNone(lb.quantile([], 0.5))


class CheckTest(unittest.TestCase):
    def test_file_a(self):
        c, places = check(ZIP_A)
        self.assertEqual((c['trips'], c['bus_trips'], c['places']), (8, 7, 3))
        self.assertEqual((c['places_wed'], c['places_sat'], c['places_sun']), (3, 1, 1))
        self.assertEqual((c['covers_wed'], c['covers_sat'], c['covers_sun']), (True, True, True))
        self.assertEqual((c['cover_start'], c['cover_end']), ('2026-04-01', '2027-03-31'))
        got = {p['place']: tuple(lb.fmt(p[k]) for k in ('first_wed', 'last_wed', 'first_sat', 'last_sat',
                                                          'first_sun', 'last_sun')) for p in places}
        self.assertEqual(got, {'駅前': ('7:00', '24:20', '9:00', '9:00', '', ''),
                               '本町': ('7:10', '18:40', '', '', '', ''),
                               '団地': ('6:00', '7:30', '', '', '10:00', '10:00')})
        self.assertEqual([p['place'] for p in places], sorted(got))
        ekimae = [p for p in places if p['place'] == '駅前'][0]
        self.assertAlmostEqual(ekimae['lat'], 35.0001, places=6)
        self.assertAlmostEqual(ekimae['lon'], 135.0, places=6)

    def test_file_b_not_covered(self):
        c, places = check(ZIP_B)
        self.assertEqual((c['trips'], c['bus_trips'], c['places'], c['places_wed']), (1, 1, 0, 0))
        self.assertEqual((c['covers_wed'], c['covers_sun']), (False, False))
        self.assertEqual((c['cover_start'], c['cover_end']), ('2025-04-01', '2026-10-31'))
        self.assertEqual(places, [])


class RunTest(unittest.TestCase):
    def test_run_summary_and_tables(self):
        rows = lb.run(CENSUS, get, DAYS, pause=0, log=lambda s: None)
        self.assertEqual([r['status'] for r in rows], ['ok', 'ok', 'failed'])
        a, b = rows[0], rows[1]
        self.assertEqual({k: a[k] for k in ('covers_sun', 'places', 'places_wed', 'first_wed_median', 'last_wed_median',
                                            'last_wed_max', 'before_19_wed', 'no_sun')},
                         {'covers_sun': 'yes', 'places': 3, 'places_wed': 3, 'first_wed_median': '7:00',
                          'last_wed_median': '18:40', 'last_wed_max': '24:20', 'before_19_wed': 2, 'no_sun': 2})
        self.assertEqual({k: b[k] for k in ('covers_wed', 'places_wed', 'last_wed_median', 'before_19_wed', 'no_sun')},
                         {'covers_wed': 'no', 'places_wed': 0, 'last_wed_median': '', 'before_19_wed': 0, 'no_sun': ''})
        s = lb.summarise(rows, '2026-10-22', DAYS)
        self.assertEqual((s['feeds'], s['read'], s['failed']), (3, 2, 1))
        self.assertEqual(s['days'], {'wed': '2026-11-11', 'sat': '2026-11-14', 'sun': '2026-11-15'})
        self.assertEqual(s['feeds_covering'], {'wed': 1, 'sat': 1, 'sun': 1})
        self.assertEqual(s['feeds_with_departures'], {'wed': 1, 'sat': 1, 'sun': 1})
        self.assertEqual(s['places'], {'wed': 3, 'sat': 1, 'sun': 1})
        self.assertEqual(s['last_wed'], {'p10': '7:30', 'p25': '7:30', 'p50': '18:40', 'p75': '24:20', 'p90': '24:20'})
        self.assertEqual(s['first_wed_median'], '7:00')
        self.assertEqual(s['share_last_wed'], {'before_18:00': 0.333, 'before_19:00': 0.667, 'before_20:00': 0.667,
                                               'before_21:00': 0.667, 'before_22:00': 0.667, 'from_23:00': 0.333})
        self.assertEqual(s['last_wed_by_hour'], {'07': 1, '18': 1, '24': 1})
        self.assertEqual(s['no_sunday'], {'places': 3, 'without': 2, 'share': 0.667})
        self.assertEqual(s['no_saturday'], {'places': 3, 'without': 2, 'share': 0.667})
        self.assertEqual(s['sunday_earlier'], {'places': 1, 'earlier': 0, 'share': 0.0, 'median_minutes_earlier': -150})
        self.assertEqual(s['feeds_median_before_18'], {'feeds': 1, 'count': 0, 'share': 0.0})
        p = s['predictions']
        self.assertEqual({k: p[k]['held'] for k in p},
                         {'L1': False, 'L2': True, 'L3': True, 'L4': False, 'L5': False, 'L6': False})
        self.assertEqual([p[k]['value'] for k in ('L1', 'L2', 'L5')], ['18:40', 0.667, 0.333])
        pref = lb.prefectures(rows)
        self.assertEqual(pref, [{'pref_id': 1, 'pref_name': '北海道', 'feeds': 3, 'read': 2, 'feeds_wed': 1,
                                 'places_wed': 3, 'last_wed_p25': '7:30', 'last_wed_median': '18:40',
                                 'last_wed_p75': '24:20', 'share_before_19': 0.667, 'share_before_20': 0.667,
                                 'share_from_22': 0.333, 'no_sunday_share': 0.667}])
        md = lb.report(s)
        self.assertIn('did not hold', md)
        self.assertIn('median 18:40', md)
        self.assertIn('| before 19:00 | 66.7% |', md)

    def test_main_writes_files(self):
        old = lb.get_zip
        lb.get_zip = get
        try:
            with tempfile.TemporaryDirectory() as tmp:
                feeds = os.path.join(tmp, 'feeds.csv')
                with open(feeds, 'w', encoding='utf-8-sig', newline='') as f:
                    f.write(','.join(lb.BASE) + '\r\n')
                    for r in CENSUS:
                        f.write(','.join(r[k] for k in lb.BASE) + '\r\n')
                lb.main(['--feeds', feeds, '--out', tmp, '--as-of', '2026-10-22', '--pause', '0'])
                out = os.path.join(tmp, 'lastbus', '2026-10-22')
                self.assertEqual(sorted(os.listdir(out)),
                                 ['feeds.csv', 'lastbus.md', 'places.csv', 'prefectures.csv', 'summary.json'])
                with open(os.path.join(out, 'places.csv'), encoding='utf-8-sig') as f:
                    lines = f.read().strip().splitlines()
                self.assertEqual(lines[0], ','.join(lb.PLACE_COLUMNS))
                self.assertEqual(len(lines), 4)
                self.assertIn('o,a,1,駅前,35.0001,135.0,7:00,24:20,9:00,9:00,,', lines)
                with open(os.path.join(out, 'summary.json'), encoding='utf-8') as f:
                    self.assertEqual(json.load(f)['places'], {'wed': 3, 'sat': 1, 'sun': 1})
        finally:
            lb.get_zip = old


if __name__ == '__main__':
    unittest.main()
