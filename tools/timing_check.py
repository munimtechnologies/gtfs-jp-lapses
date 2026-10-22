# timing_check.py - an all-Japan census of timing and stop-position errors in the current file of every feed in the
# stop-name census (names/2026-10-22/feeds.csv: the active, openly licensed feeds of the GTFS Data Repository), and of
# how fast the buses are scheduled to run. For each file it counts: poles (location_type 0 or empty) with missing or
# zero coordinates, or outside Japan; "stacks", two or more differently named poles at exactly the same coordinates;
# steps between two consecutive timed stops of a trip where the vehicle would go faster than the limit for its
# route_type (the limits of MobilityData's fast_travel_between_consecutive_stops; a step under one minute counts as one
# minute, because times in these files are given to the minute); "time travel", a step where a trip arrives before it
# left the stop before; and timed stop_times that point to a stop that is not in stops.txt. For bus trips (route_type
# 3, 200-299 or 700-799) it also gives the scheduled speed: the straight-line distance through the timed stops over the
# time from the first departure to the last arrival. Six predictions (PREDICTIONS) were fixed before any file was
# read. Standard library only.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import argparse
import csv
import io
import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from collections import Counter, defaultdict

API = 'https://api.gtfs-data.jp/v2'
UA = 'GTFS timing census - MV2 of Munim, Inc. (mv2@munimtech.com)'
R_KM = 6371.0
# lat min, lat max, lon min, lon max: Japan with its outlying islands (Okinotorishima 20.4N, Yonaguni 122.9E,
# Minamitorishima 154.0E, Cape Soya 45.5N)
JAPAN = (20.0, 46.0, 122.0, 154.0)
# km/h, MobilityData's limits by basic route_type
LIMITS = {0: 100, 1: 150, 2: 500, 3: 150, 4: 80, 5: 30, 6: 50, 7: 50, 11: 150, 12: 150}
EXAMPLES = 20  # per feed, in fast_steps.csv, time_travel.csv and stacks.csv
csv.field_size_limit(1 << 24)
BASE = ['organization_id', 'feed_id', 'organization_name', 'feed_name', 'pref_id', 'pref_name', 'license']
COUNTS = ['stops', 'stops_bad_coords', 'stops_outside_japan', 'stacked_stops', 'largest_stack', 'trips', 'steps',
          'fast_steps', 'fast_steps_0min', 'fast_trips', 'time_travel_steps', 'time_travel_trips', 'missing_stop_refs']
COLUMNS = BASE + ['status', 'detail'] + COUNTS + ['max_kmh', 'bus_trips_timed', 'bus_kmh_median', 'timing']
# Fixed on 2026-10-22, before any file was read by this tool.
PREDICTIONS = {
    'T1': 'Between 5% and 30% of the files read have at least one step faster than the limit for its route_type.',
    'T2': 'Fewer than 5% of the files read have at least one step where a trip arrives before it left the stop '
          'before.',
    'T3': 'Fewer than 3% of the files read have a pole with missing, zero or outside-Japan coordinates.',
    'T4': 'The median scheduled straight-line speed of bus trips, over all bus trips in all files read, is between 12 '
          'and 25 km/h.',
    'T5': 'At least half of all too-fast steps are scheduled at under one minute (0 minutes in a timetable given to '
          'the minute).',
    'T6': 'At least 10% of the files read have a stack: two or more differently named poles at exactly the same '
          'coordinates.',
}


def find(zf, name):
    """The shallowest member whose file name is `name` (any case), ignoring __MACOSX."""
    hits = [n for n in zf.namelist() if not n.startswith('__MACOSX') and n.split('/')[-1].lower() == name]
    hits.sort(key=lambda n: n.count('/'))
    return hits[0] if hits else None


def encoding(zf):
    """utf-8-sig if stops.txt is valid UTF-8, else cp932 (Shift_JIS); used for every table of the file."""
    n = find(zf, 'stops.txt')
    if n is None:
        return 'utf-8-sig'
    try:
        zf.read(n).decode('utf-8-sig')
        return 'utf-8-sig'
    except UnicodeDecodeError:
        return 'cp932'


def rows(zf, name, enc):
    """Rows of one table as dicts (lower-case keys, stripped values); nothing if the table is missing."""
    n = find(zf, name)
    if n is None:
        return
    with zf.open(n) as raw:
        rd = csv.reader(io.TextIOWrapper(raw, encoding=enc, errors='replace', newline=''))
        head = next(rd, None)
        if head is None:
            return
        head = [h.strip().lstrip('﻿').lower() for h in head]
        for row in rd:
            if any(c.strip() for c in row):
                yield dict(zip(head, (c.strip() for c in row)))


def secs(s):
    p = (s or '').strip().split(':')
    if len(p) != 3:
        return None
    try:
        h, m, x = (int(v) for v in p)
    except ValueError:
        return None
    return h * 3600 + m * 60 + x


def hms(t):
    return f'{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}'


def km(a, b):
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R_KM * math.asin(min(1.0, math.sqrt(h)))


def coord(s):
    """('ok', (lat, lon)), ('bad', None) for missing, unreadable or zero, ('outside', None) outside Japan."""
    try:
        lat, lon = float(s.get('stop_lat') or ''), float(s.get('stop_lon') or '')
    except ValueError:
        return 'bad', None
    if not (math.isfinite(lat) and math.isfinite(lon)) or (lat == 0 and lon == 0):
        return 'bad', None
    if not (JAPAN[0] <= lat <= JAPAN[1] and JAPAN[2] <= lon <= JAPAN[3]):
        return 'outside', None
    return 'ok', (lat, lon)


def limit(rt):
    if rt in LIMITS:
        return LIMITS[rt]
    if 100 <= rt < 200:
        return 500
    if 900 <= rt < 1000:
        return 100
    if 1000 <= rt < 1100:
        return 80
    if 1300 <= rt < 1400:
        return 50
    return 150


def is_bus(rt):
    return rt == 3 or 200 <= rt < 300 or 700 <= rt < 800


def to_int(v, default=-1):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


def check(zf):
    """(Counter of COUNTS, details) for one GTFS zip. details: max_kmh, speeds (bus trips, km/h rounded to 0.1),
    fast, back and stacks (example rows, at most EXAMPLES each)."""
    enc = encoding(zf)
    c = Counter()
    pos, name, known = {}, {}, set()
    at = defaultdict(list)
    for s in rows(zf, 'stops.txt', enc):
        sid = s.get('stop_id', '')
        known.add(sid)
        name[sid] = s.get('stop_name', '')
        state, p = coord(s)
        if p:
            pos[sid] = p
        if (s.get('location_type') or '0') != '0':
            continue
        c['stops'] += 1
        if state == 'bad':
            c['stops_bad_coords'] += 1
        elif state == 'outside':
            c['stops_outside_japan'] += 1
        else:
            at[(round(p[0], 6), round(p[1], 6))].append(name[sid])
    stacks = []
    for (lat, lon), names in sorted(at.items()):
        distinct = sorted(set(names))
        if len(distinct) >= 2:
            c['stacked_stops'] += len(names)
            c['largest_stack'] = max(c['largest_stack'], len(distinct))
            if len(stacks) < EXAMPLES:
                stacks.append({'lat': lat, 'lon': lon, 'poles': len(names), 'names': '／'.join(distinct)})
    rtype = {r.get('route_id', ''): to_int(r.get('route_type')) for r in rows(zf, 'routes.txt', enc)}
    route = {r.get('trip_id', ''): r.get('route_id', '') for r in rows(zf, 'trips.txt', enc)}
    trips = defaultdict(list)
    for i, r in enumerate(rows(zf, 'stop_times.txt', enc)):
        arr, dep = secs(r.get('arrival_time')), secs(r.get('departure_time'))
        if arr is None and dep is None:
            continue
        sid = sys.intern(r.get('stop_id', ''))
        if sid not in known:
            c['missing_stop_refs'] += 1
        try:
            seq = float(r.get('stop_sequence') or '')
        except ValueError:
            seq = math.inf
        trips[sys.intern(r.get('trip_id', ''))].append(
            (seq, i, arr if arr is not None else dep, dep if dep is not None else arr, sid))
    top, speeds, fast_rows, back_rows = 0.0, [], [], []
    for tid, st in trips.items():
        if len(st) < 2:
            continue
        st.sort()
        c['trips'] += 1
        rt = rtype.get(route.get(tid), -1)
        lim = limit(rt)
        dist, whole, fast, back = 0.0, True, False, False
        for p, q in zip(st, st[1:]):
            dt = q[2] - p[3]
            if dt < 0:
                c['time_travel_steps'] += 1
                back, whole = True, False
                if len(back_rows) < EXAMPLES:
                    back_rows.append({'trip_id': tid, 'from_stop_id': p[4], 'from_stop_name': name.get(p[4], ''),
                                      'departure': hms(p[3]), 'to_stop_id': q[4], 'to_stop_name': name.get(q[4], ''),
                                      'arrival': hms(q[2])})
                continue
            a, b = pos.get(p[4]), pos.get(q[4])
            if a is None or b is None:
                whole = False
                continue
            d = km(a, b)
            dist += d
            v = d / max(dt, 60) * 3600
            c['steps'] += 1
            top = max(top, v)
            if v > lim:
                c['fast_steps'] += 1
                c['fast_steps_0min'] += dt < 60
                fast = True
                if len(fast_rows) < EXAMPLES:
                    fast_rows.append({'trip_id': tid, 'route_type': rt, 'from_stop_id': p[4],
                                      'from_stop_name': name.get(p[4], ''), 'to_stop_id': q[4],
                                      'to_stop_name': name.get(q[4], ''), 'km': round(d, 3),
                                      'minutes': round(dt / 60, 1), 'kmh': round(v, 1), 'limit_kmh': lim})
        c['fast_trips'] += fast
        c['time_travel_trips'] += back
        if whole and is_bus(rt):
            dur = st[-1][2] - st[0][3]
            if dur >= 60 and dist > 0:
                speeds.append(round(dist / dur * 3600, 1))
    return c, {'max_kmh': round(top, 1), 'speeds': speeds, 'fast': fast_rows, 'back': back_rows, 'stacks': stacks}


def quantile(values, q):
    """The smallest value with at least a share q of the values at or below it (a lower median for q = 0.5)."""
    v = sorted(values)
    if not v:
        return None
    return v[max(0, math.ceil(q * len(v)) - 1)]


def timing_check(row):
    if row['status'] != 'ok' or not row['trips']:
        return 'n/a'
    bad = ('fast_steps', 'time_travel_steps', 'stops_bad_coords', 'stops_outside_japan', 'missing_stop_refs')
    return 'flag' if any(row[k] for k in bad) else 'ok'


def zip_url(org, feed):
    q = lambda s: urllib.parse.quote(s, safe='')  # noqa: E731
    return f'{API}/organizations/{q(org)}/feeds/{q(feed)}/files/feed.zip?rid=current'


def fetch(url, timeout=180):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def get_zip(org, feed):
    try:
        return fetch(zip_url(org, feed))
    except Exception:  # noqa: BLE001 - one retry
        time.sleep(5)
        return fetch(zip_url(org, feed))


def run(census_rows, get, pause=2.0, log=print):
    """One row per feed; examples are collected in each row's _fast, _back and _stacks, bus speeds in _speeds."""
    out = []
    for i, f in enumerate(census_rows):
        if i and pause:
            time.sleep(pause)
        row = {k: f.get(k, '') for k in BASE}
        row.update({'_speeds': [], '_fast': [], '_back': [], '_stacks': []})
        try:
            with zipfile.ZipFile(io.BytesIO(get(f['organization_id'], f['feed_id']))) as zf:
                c, d = check(zf)
        except Exception as e:  # noqa: BLE001 - recorded, not fatal
            row.update({k: '' for k in COUNTS + ['max_kmh', 'bus_trips_timed', 'bus_kmh_median']})
            row.update(status='failed', detail=str(e)[:200], timing='n/a')
            out.append(row)
            log(f"failed {f['organization_id']}/{f['feed_id']} {row['detail']}")
            continue
        row.update({k: c[k] for k in COUNTS})
        med = quantile(d['speeds'], 0.5)
        row.update(status='ok', detail='', max_kmh=d['max_kmh'], bus_trips_timed=len(d['speeds']),
                   bus_kmh_median='' if med is None else med)
        row['timing'] = timing_check(row)
        ids = {'organization_id': f['organization_id'], 'feed_id': f['feed_id']}
        row.update({'_speeds': d['speeds'], '_fast': [{**ids, **x} for x in d['fast']],
                    '_back': [{**ids, **x} for x in d['back']], '_stacks': [{**ids, **x} for x in d['stacks']]})
        out.append(row)
        log(f"{row['timing']} {f['organization_id']}/{f['feed_id']} trips={c['trips']} fast={c['fast_steps']} "
            f"back={c['time_travel_steps']} coords={c['stops_bad_coords'] + c['stops_outside_japan']} "
            f"stacked={c['stacked_stops']} bus_kmh={row['bus_kmh_median']}")
    return out


def share(k, n):
    return round(k / n, 3) if n else None


def score(s):
    n, w = s['read'], s['feeds_with']
    fast_share, back_share = share(w['fast'], n), share(w['time_travel'], n)
    coord_share, stack_share = share(w['bad_or_outside_coords'], n), share(w['stack'], n)
    med = s['bus_speed']['median_kmh']
    zero = share(s['fast_steps_0min'], s['fast_steps'])
    held = {'T1': fast_share is not None and 0.05 <= fast_share <= 0.30,
            'T2': back_share is not None and back_share < 0.05,
            'T3': coord_share is not None and coord_share < 0.03,
            'T4': med is not None and 12 <= med <= 25,
            'T5': zero is not None and zero >= 0.5,
            'T6': stack_share is not None and stack_share >= 0.10}
    value = {'T1': fast_share, 'T2': back_share, 'T3': coord_share, 'T4': med, 'T5': zero, 'T6': stack_share}
    return {k: {'statement': PREDICTIONS[k], 'value': value[k], 'held': held[k]} for k in PREDICTIONS}


def summarise(rows, as_of):
    ok = [r for r in rows if r['status'] == 'ok']
    speeds = [v for r in ok for v in r['_speeds']]
    medians = [r['bus_kmh_median'] for r in ok if r['bus_kmh_median'] != '']
    s = {'as_of': as_of, 'feeds': len(rows), 'read': len(ok), 'failed': len(rows) - len(ok),
         'feeds_with': {'fast': sum(r['fast_steps'] > 0 for r in ok),
                        'time_travel': sum(r['time_travel_steps'] > 0 for r in ok),
                        'bad_or_outside_coords': sum(r['stops_bad_coords'] + r['stops_outside_japan'] > 0 for r in ok),
                        'stack': sum(r['stacked_stops'] > 0 for r in ok),
                        'missing_stop_refs': sum(r['missing_stop_refs'] > 0 for r in ok)}}
    s.update({k: sum(r[k] for r in ok) for k in ('stops', 'stops_bad_coords', 'stops_outside_japan', 'stacked_stops',
                                                   'trips', 'steps', 'fast_steps', 'fast_steps_0min',
                                                   'time_travel_steps', 'missing_stop_refs')})
    s['timing'] = dict(sorted(Counter(r['timing'] for r in rows).items()))
    s['bus_speed'] = {'trips': len(speeds), 'p25_kmh': quantile(speeds, 0.25), 'median_kmh': quantile(speeds, 0.5),
                      'p75_kmh': quantile(speeds, 0.75), 'feeds': len(medians),
                      'median_of_feed_medians_kmh': quantile(medians, 0.5)}
    s['predictions'] = score(s)
    s['generated_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    s['by'] = "MV2 of Munim, Inc. (made with AI agents working in MV2's name)"
    return s


def prefectures(rows):
    by = defaultdict(list)
    for r in rows:
        by[(to_int(r['pref_id'], 0), r['pref_name'])].append(r)
    out = []
    for (pid, pname), rs in sorted(by.items()):
        ok = [r for r in rs if r['status'] == 'ok']
        sp = [v for r in ok for v in r['_speeds']]
        out.append({'pref_id': pid, 'pref_name': pname, 'feeds': len(rs), 'read': len(ok),
                    'fast_feeds': sum(r['fast_steps'] > 0 for r in ok),
                    'time_travel_feeds': sum(r['time_travel_steps'] > 0 for r in ok),
                    'coord_feeds': sum(r['stops_bad_coords'] + r['stops_outside_japan'] > 0 for r in ok),
                    'stack_feeds': sum(r['stacked_stops'] > 0 for r in ok),
                    'timing_flag': sum(r['timing'] == 'flag' for r in rs), 'bus_trips': len(sp),
                    'bus_kmh_p25': quantile(sp, 0.25), 'bus_kmh_median': quantile(sp, 0.5),
                    'bus_kmh_p75': quantile(sp, 0.75)})
    return out


PREF_COLUMNS = ['pref_id', 'pref_name', 'feeds', 'read', 'fast_feeds', 'time_travel_feeds', 'coord_feeds',
                'stack_feeds', 'timing_flag', 'bus_trips', 'bus_kmh_p25', 'bus_kmh_median', 'bus_kmh_p75']
FAST_COLUMNS = ['organization_id', 'feed_id', 'trip_id', 'route_type', 'from_stop_id', 'from_stop_name', 'to_stop_id',
                'to_stop_name', 'km', 'minutes', 'kmh', 'limit_kmh']
BACK_COLUMNS = ['organization_id', 'feed_id', 'trip_id', 'from_stop_id', 'from_stop_name', 'departure', 'to_stop_id',
                'to_stop_name', 'arrival']
STACK_COLUMNS = ['organization_id', 'feed_id', 'lat', 'lon', 'poles', 'names']


def report(s):
    w, b = s['feeds_with'], s['bus_speed']
    lines = [f'# 時刻と停留所位置の確かめ・バスの表定速度 / Timing and stop-position census, scheduled bus speeds ({s["as_of"]})',
             '',
             '停留所名の調査（names/2026-10-22）と同じデータの現行ファイルを読み、速すぎる区間・前の停留所を出る前に着く区間・'
             '座標のない停留所や国外の停留所・同じ座標に名前の違う停留所が重なるもの・stops.txt にない停留所への参照を数え、'
             'バスの便ごとの表定速度（停留所間の直線距離の合計 ÷ 始発から終着までの時間）を求めました。',
             'The current file of every feed in the stop-name census was read again. Counted: steps faster than the limit '
             'for the route_type, steps that arrive before the previous stop was left, poles with missing, zero or '
             'outside-Japan coordinates, stacks of differently named poles at exactly the same coordinates, and stop_times '
             'pointing to stops that are not in stops.txt; and, per bus trip, the scheduled straight-line speed.', '',
             f'Feeds: {s["feeds"]}; read {s["read"]}; failed {s["failed"]}. Trips {s["trips"]}; steps checked for speed '
             f'{s["steps"]}; poles {s["stops"]}.', '',
             '| check | feeds | count |', '|---|---|---|',
             f'| too fast for its route_type (under one minute counted as one) | {w["fast"]} | {s["fast_steps"]} steps '
             f'({s["fast_steps_0min"]} under one minute) |',
             f'| arrives before it left the stop before | {w["time_travel"]} | {s["time_travel_steps"]} steps |',
             f'| pole with missing, zero or outside-Japan coordinates | {w["bad_or_outside_coords"]} | '
             f'{s["stops_bad_coords"]} missing or zero, {s["stops_outside_japan"]} outside |',
             f'| stack: differently named poles at the same coordinates | {w["stack"]} | {s["stacked_stops"]} poles |',
             f'| stop_times pointing to a stop not in stops.txt | {w["missing_stop_refs"]} | {s["missing_stop_refs"]} rows |',
             '', 'Timing check per feed (flag = any of the rows above except stacks): '
             + ', '.join(f'{k} {v}' for k, v in s['timing'].items()) + '.', '',
             f'Scheduled bus speed (straight line through the timed stops): {b["trips"]} bus trips, median '
             f'{b["median_kmh"]} km/h (quartiles {b["p25_kmh"]} and {b["p75_kmh"]}); median of the {b["feeds"]} feeds\' '
             f'medians {b["median_of_feed_medians_kmh"]} km/h.', '',
             '## Predictions recorded before any file was read', '']
    for k, p in s['predictions'].items():
        lines.append(f'- {k}: {p["statement"]} Result: {p["value"]}: ' + ('held.' if p['held'] else 'did not hold.'))
    lines += ['', 'Limits: straight lines between stops are shorter than the road, so the speeds run low, and a '
              'too-fast step can come from a wrong time or a wrong position; the census does not say which. Times are '
              'mostly given to the minute, so short steps are coarse. Only the current file of each feed is read, on the '
              'day of the run. A flag is a sign to check, not proof of a mistake. Place names in the data are records of '
              'fact, not judgements.', '',
              f'Generated {s["generated_at"]}. Source: GTFS Data Repository API v2 (https://gtfs-data.jp/); each feed\'s '
              'publisher and licence are in feeds.csv. Made by MV2 of Munim, Inc. with AI agents working in MV2\'s name. '
              'Data CC BY 4.0.']
    return '\n'.join(lines) + '\n'


def write_csv(path, rows_, columns):
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows_)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--feeds', required=True, help='names/2026-10-22/feeds.csv')
    ap.add_argument('--out', required=True, help='results go to <out>/timing/<as-of>/')
    ap.add_argument('--as-of', default=time.strftime('%Y-%m-%d', time.gmtime()))
    ap.add_argument('--pause', type=float, default=2.0)
    ap.add_argument('--limit', type=int)
    a = ap.parse_args(argv)
    with open(a.feeds, encoding='utf-8-sig', newline='') as f:
        census = list(csv.DictReader(f))
    if a.limit is not None:
        census = census[:a.limit]
    print(f'feeds: {len(census)}', flush=True)
    rows_ = run(census, get_zip, a.pause, log=lambda x: print(x, flush=True))
    out = os.path.join(a.out, 'timing', a.as_of)
    os.makedirs(out, exist_ok=True)
    s = summarise(rows_, a.as_of)
    write_csv(os.path.join(out, 'feeds.csv'), rows_, COLUMNS)
    write_csv(os.path.join(out, 'prefectures.csv'), prefectures(rows_), PREF_COLUMNS)
    write_csv(os.path.join(out, 'fast_steps.csv'), [x for r in rows_ for x in r['_fast']], FAST_COLUMNS)
    write_csv(os.path.join(out, 'time_travel.csv'), [x for r in rows_ for x in r['_back']], BACK_COLUMNS)
    write_csv(os.path.join(out, 'stacks.csv'), [x for r in rows_ for x in r['_stacks']], STACK_COLUMNS)
    with open(os.path.join(out, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(s, f, ensure_ascii=False, indent=1)
    with open(os.path.join(out, 'timing.md'), 'w', encoding='utf-8') as f:
        f.write(report(s))
    print(json.dumps(s, ensure_ascii=False))
    return s


if __name__ == '__main__':
    main()
