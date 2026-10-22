# Tests for timing_check.py on small files built here; every expected count was worked out by hand.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import io
import os
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timing_check as tc  # noqa: E402

# S2 is 0.009 degrees north of S1 (1.00075 km), S3 0.045 degrees (5.00377 km); S4 sits exactly on S3 with another
# name (a stack); S5 is at 0,0 and S6 south of Japan; P is a parent station and is not a pole.
STOPS_A = ('stop_id,stop_name,stop_lat,stop_lon,location_type\r\n'
           'P,駅,35.000000,135.000000,1\r\n'
           'S1,A,35.000000,135.000000,0\r\n'
           'S2,B,35.009000,135.000000,0\r\n'
           'S3,C,35.045000,135.000000,\r\n'
           'S4,D,35.045000,135.000000,0\r\n'
           'S5,E,0,0,0\r\n'
           'S6,F,10.0,135.0,0\r\n')
ROUTES_A = 'route_id,route_type\r\nR1,3\r\nR2,4\r\n'
TRIPS_A = 'route_id,service_id,trip_id\r\nR1,W,T1\r\nR1,W,T2\r\nR1,W,T3\r\nR2,W,T4\r\nR1,W,T5\r\n'
# T1: S1 -> S2 in 4 min (15 km/h), S2 -> S3 in 0 min (4.003 km, counted as 1 min: 240.2 km/h, too fast for a bus).
#     Trip: 5.0038 km in 4 min = 75.1 km/h.
# T2: after midnight; S1 -> S2 in 6 min = 10.0 km/h.
# T3: listed out of order; by stop_sequence it leaves S1 at 9:10 and reaches S2 at 9:05 (time travel), then goes to
#     ZZ, which is not in stops.txt.
# T4: a ferry (limit 80 km/h): S1 -> S3 in 2 min = 150.1 km/h, too fast, not under one minute.
# T5: only one timed stop, so it is not a trip here.
STOP_TIMES_A = ('trip_id,arrival_time,departure_time,stop_id,stop_sequence\r\n'
                'T1,08:00:00,08:00:00,S1,1\r\n'
                'T1,,08:04:00,S2,2\r\n'
                'T1,08:04:00,08:04:00,S3,3\r\n'
                'T2,25:00:00,25:00:00,S1,1\r\n'
                'T2,25:06:00,25:06:00,S2,2\r\n'
                'T3,09:05:00,09:05:00,S2,2\r\n'
                'T3,09:10:00,09:10:00,S1,1\r\n'
                'T3,09:20:00,09:20:00,ZZ,3\r\n'
                'T4,10:00:00,10:00:00,S1,1\r\n'
                'T4,10:02:00,10:02:00,S3,2\r\n'
                'T5,11:00:00,11:00:00,S1,1\r\n'
                'T5,,,S2,2\r\n')
# A clean file in Shift_JIS with Japanese stop_ids: 本町 -> 新町 is 0.018 degrees (2.0015 km) in 6 min = 20.0 km/h.
STOPS_B = 'stop_id,stop_name,stop_lat,stop_lon\r\n本町,本町,35.000000,135.000000\r\n新町,新町,35.018000,135.000000\r\n'
ROUTES_B = 'route_id,route_type\r\nQ,3\r\n'
TRIPS_B = 'route_id,service_id,trip_id\r\nQ,W,U1\r\n'
STOP_TIMES_B = ('trip_id,arrival_time,departure_time,stop_id,stop_sequence\r\n'
                'U1,7:00:00,7:00:00,本町,1\r\nU1,7:06:00,7:06:00,新町,2\r\n')


def make_zip(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        for name, data in files:
            zf.writestr(name, data)
    return buf.getvalue()


ZIP_A = make_zip([('stops.txt', STOPS_A.encode('utf-8')), ('routes.txt', ROUTES_A.encode('utf-8')),
                  ('trips.txt', TRIPS_A.encode('utf-8')), ('stop_times.txt', STOP_TIMES_A.encode('utf-8'))])
ZIP_B = make_zip([('feed/stops.txt', STOPS_B.encode('cp932')), ('feed/routes.txt', ROUTES_B.encode('cp932')),
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
        return tc.check(zf)


class HelperTest(unittest.TestCase):
    def test_secs(self):
        self.assertEqual(tc.secs('25:06:00'), 90360)
        self.assertEqual(tc.secs(' 7:00:00'), 25200)
        self.assertIsNone(tc.secs(''))
        self.assertIsNone(tc.secs('08:00'))
        self.assertEqual(tc.hms(90360), '25:06:00')

    def test_km(self):
        self.assertAlmostEqual(tc.km((35.0, 135.0), (35.009, 135.0)), 1.00075, places=4)
        self.assertAlmostEqual(tc.km((35.0, 135.0), (35.045, 135.0)), 5.00377, places=4)

    def test_limits(self):
        self.assertEqual([tc.limit(x) for x in (3, 4, 715, 109, -1, 2)], [150, 80, 150, 500, 150, 500])
        self.assertEqual([tc.is_bus(x) for x in (3, 715, 200, 4, -1)], [True, True, True, False, False])

    def test_quantile(self):
        self.assertEqual(tc.quantile([75.1, 10.0], 0.5), 10.0)
        self.assertEqual(tc.quantile([10.0, 75.1, 20.0], 0.5), 20.0)
        self.assertEqual(tc.quantile([10.0, 75.1, 20.0], 0.25), 10.0)
        self.assertEqual(tc.quantile([10.0, 75.1, 20.0], 0.75), 75.1)
        self.assertIsNone(tc.quantile([], 0.5))


class CheckTest(unittest.TestCase):
    def test_file_a(self):
        c, d = check(ZIP_A)
        self.assertEqual({k: c[k] for k in tc.COUNTS},
                         {'stops': 6, 'stops_bad_coords': 1, 'stops_outside_japan': 1, 'stacked_stops': 2,
                          'largest_stack': 2, 'trips': 4, 'steps': 4, 'fast_steps': 2, 'fast_steps_0min': 1,
                          'fast_trips': 2, 'time_travel_steps': 1, 'time_travel_trips': 1, 'missing_stop_refs': 1})
        self.assertEqual(d['max_kmh'], 240.2)
        self.assertEqual(sorted(d['speeds']), [10.0, 75.1])
        self.assertEqual(sorted((x['trip_id'], x['kmh'], x['limit_kmh']) for x in d['fast']),
                         [('T1', 240.2, 150), ('T4', 150.1, 80)])
        self.assertEqual([(x['trip_id'], x['departure'], x['arrival']) for x in d['back']],
                         [('T3', '9:10:00', '9:05:00')])
        self.assertEqual(d['stacks'], [{'lat': 35.045, 'lon': 135.0, 'poles': 2, 'names': 'C／D'}])

    def test_file_b_shift_jis(self):
        c, d = check(ZIP_B)
        self.assertEqual((c['stops'], c['trips'], c['steps'], c['fast_steps'], c['missing_stop_refs']), (2, 1, 1, 0, 0))
        self.assertEqual(d['speeds'], [20.0])


class RunTest(unittest.TestCase):
    def test_run_summary_and_files(self):
        rows = tc.run(CENSUS, get, pause=0, log=lambda s: None)
        self.assertEqual([(r['status'], r['timing']) for r in rows], [('ok', 'flag'), ('ok', 'ok'), ('failed', 'n/a')])
        self.assertEqual([r['bus_kmh_median'] for r in rows], [10.0, 20.0, ''])
        s = tc.summarise(rows, '2026-10-22')
        self.assertEqual((s['feeds'], s['read'], s['failed']), (3, 2, 1))
        self.assertEqual(s['feeds_with'], {'fast': 1, 'time_travel': 1, 'bad_or_outside_coords': 1, 'stack': 1,
                                           'missing_stop_refs': 1})
        self.assertEqual((s['stops'], s['trips'], s['steps'], s['fast_steps'], s['fast_steps_0min']), (8, 5, 5, 2, 1))
        self.assertEqual(s['timing'], {'flag': 1, 'n/a': 1, 'ok': 1})
        self.assertEqual(s['bus_speed'], {'trips': 3, 'p25_kmh': 10.0, 'median_kmh': 20.0, 'p75_kmh': 75.1,
                                          'feeds': 2, 'median_of_feed_medians_kmh': 10.0})
        p = s['predictions']
        self.assertEqual({k: p[k]['held'] for k in p},
                         {'T1': False, 'T2': False, 'T3': False, 'T4': True, 'T5': True, 'T6': True})
        self.assertEqual([p[k]['value'] for k in ('T1', 'T4', 'T5')], [0.5, 20.0, 0.5])
        pref = tc.prefectures(rows)
        self.assertEqual(len(pref), 1)
        self.assertEqual({k: pref[0][k] for k in ('feeds', 'read', 'fast_feeds', 'timing_flag', 'bus_trips',
                                                   'bus_kmh_median')},
                         {'feeds': 3, 'read': 2, 'fast_feeds': 1, 'timing_flag': 1, 'bus_trips': 3,
                          'bus_kmh_median': 20.0})
        md = tc.report(s)
        self.assertIn('did not hold', md)
        self.assertIn('median 20.0 km/h', md)

    def test_main_writes_files(self):
        old = tc.get_zip
        tc.get_zip = get
        try:
            with tempfile.TemporaryDirectory() as tmp:
                feeds = os.path.join(tmp, 'feeds.csv')
                with open(feeds, 'w', encoding='utf-8-sig', newline='') as f:
                    f.write(','.join(tc.BASE) + '\r\n')
                    for r in CENSUS:
                        f.write(','.join(r[k] for k in tc.BASE) + '\r\n')
                tc.main(['--feeds', feeds, '--out', tmp, '--as-of', '2026-10-22', '--pause', '0'])
                out = os.path.join(tmp, 'timing', '2026-10-22')
                self.assertEqual(sorted(os.listdir(out)),
                                 ['fast_steps.csv', 'feeds.csv', 'prefectures.csv', 'stacks.csv', 'summary.json',
                                  'time_travel.csv', 'timing.md'])
                with open(os.path.join(out, 'fast_steps.csv'), encoding='utf-8-sig') as f:
                    self.assertEqual(len(f.read().strip().splitlines()), 3)
        finally:
            tc.get_zip = old


if __name__ == '__main__':
    unittest.main()
