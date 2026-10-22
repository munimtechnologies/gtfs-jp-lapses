# last_bus.py - an all-Japan census of the first and last bus (始発・終バス) at every place, read from the current file
# of every feed in the stop-name census (names/2026-10-22/feeds.csv: the active, openly licensed feeds of the GTFS
# Data Repository). A place is a stop name within one feed (the poles of one stop share its name). For an ordinary
# Wednesday, Saturday and Sunday (2026-11-11, 11-14 and 11-15: no holiday, outside the New Year break) it finds, from
# calendar.txt and calendar_dates.txt, the bus trips (route_type 3, 200-299 or 700-799) that run that service day, and
# gives each place its first and last departure: a timed stop of the trip that is not its last stop and where riders may
# board (pickup_type is not 1). Times past 24:00 stay on the service day they belong to; trips in frequencies.txt run
# from the window's start to its last start. Six predictions (PREDICTIONS) were fixed before any file was read.
# Standard library only.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import argparse
import csv
import datetime as dt
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
UA = 'GTFS last-bus census - MV2 of Munim, Inc. (mv2@munimtech.com)'
H = 3600
DAYS = {'wed': '2026-11-11', 'sat': '2026-11-14', 'sun': '2026-11-15'}
WEEK = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')
csv.field_size_limit(1 << 24)
BASE = ['organization_id', 'feed_id', 'organization_name', 'feed_name', 'pref_id', 'pref_name', 'license']
COLUMNS = BASE + ['status', 'detail', 'cover_start', 'cover_end', 'covers_wed', 'covers_sat', 'covers_sun', 'trips',
                  'bus_trips', 'places', 'places_wed', 'places_sat', 'places_sun', 'first_wed_median',
                  'last_wed_median', 'last_wed_max', 'before_19_wed', 'no_sun']
PLACE_COLUMNS = ['organization_id', 'feed_id', 'pref_id', 'place', 'lat', 'lon', 'first_wed', 'last_wed', 'first_sat',
                 'last_sat', 'first_sun', 'last_sun']
PREF_COLUMNS = ['pref_id', 'pref_name', 'feeds', 'read', 'feeds_wed', 'places_wed', 'last_wed_p25', 'last_wed_median',
                'last_wed_p75', 'share_before_19', 'share_before_20', 'share_from_22', 'no_sunday_share']
BANDS = [('before_18:00', 18), ('before_19:00', 19), ('before_20:00', 20), ('before_21:00', 21), ('before_22:00', 22)]
# Fixed on 2026-10-22, before any file was read by this tool.
PREDICTIONS = {
    'L1': 'Over all places with a bus departure on the Wednesday, the median last departure is between 19:00 and '
          '21:00.',
    'L2': 'At least 25% of the places with a bus departure on the Wednesday have their last departure before 19:00.',
    'L3': 'At least 15% of the places with a bus departure on the Wednesday, in files that cover the Sunday, have no '
          'bus departure on the Sunday.',
    'L4': 'At least 30% of the feeds with a bus departure on the Wednesday have a median last departure (over their '
          'places) before 18:00.',
    'L5': 'Fewer than 10% of the places with a bus departure on the Wednesday have their last departure at 23:00 or '
          'later.',
    'L6': 'Of the places with a bus departure on both the Wednesday and the Sunday, at least 40% have an earlier last '
          'departure on the Sunday.',
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


def fmt(t):
    """Seconds after the service day's midnight as H:MM (hours past 24 kept); '' for None."""
    return '' if t is None else f'{t // H}:{t % H // 60:02d}'


def gdate(s):
    """'20261111' -> date; anything else -> None."""
    s = (s or '').strip()
    if len(s) == 8 and s.isdigit():
        try:
            return dt.date(int(s[:4]), int(s[4:6]), int(s[6:]))
        except ValueError:
            return None
    return None


def num(s):
    try:
        v = float(s or '')
    except ValueError:
        return None
    return v if math.isfinite(v) else None


def to_int(v, default=-1):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


def is_bus(rt):
    return rt == 3 or 200 <= rt < 300 or 700 <= rt < 800


def calendar(zf, enc):
    """(cal, add, rem, cover): weekly services, services added and removed by date, and the days the file covers
    (the span of calendar.txt and calendar_dates.txt, narrowed to feed_info's dates where given) or None."""
    cal, add, rem = {}, defaultdict(set), defaultdict(set)
    lo = hi = None
    for r in rows(zf, 'calendar.txt', enc):
        sid, s, e = r.get('service_id', ''), gdate(r.get('start_date')), gdate(r.get('end_date'))
        if not sid or not s or not e:
            continue
        cal[sid] = (tuple(r.get(w, '0') == '1' for w in WEEK), s, e)
        lo, hi = min(lo or s, s), max(hi or e, e)
    for r in rows(zf, 'calendar_dates.txt', enc):
        sid, d, t = r.get('service_id', ''), gdate(r.get('date')), r.get('exception_type', '')
        if not sid or not d or t not in ('1', '2'):
            continue
        (add if t == '1' else rem)[d].add(sid)
        lo, hi = min(lo or d, d), max(hi or d, d)
    cover = (lo, hi) if lo else None
    for r in list(rows(zf, 'feed_info.txt', enc))[:1]:
        fs, fe = gdate(r.get('feed_start_date')), gdate(r.get('feed_end_date'))
        if cover and fs and fe and fs <= fe:
            a, b = max(fs, lo), min(fe, hi)
            cover = (a, b) if a <= b else None
    return cal, add, rem, cover


def services(cal, add, rem, d):
    """The service_ids that run on day d."""
    on = {sid for sid, (wk, s, e) in cal.items() if s <= d <= e and wk[d.weekday()]}
    return (on | add.get(d, set())) - rem.get(d, set())


def check(zf, days):
    """(counts, places) for one GTFS zip. days maps a label ('wed', 'sat', 'sun') to a date. places: one dict per
    place with a bus departure on at least one of the days (place, lat, lon, first_<label>, last_<label> in seconds or
    None), sorted by name."""
    enc = encoding(zf)
    place, where = {}, defaultdict(list)
    for s in rows(zf, 'stops.txt', enc):
        sid = s.get('stop_id', '')
        nm = s.get('stop_name', '') or sid
        place[sid] = nm
        lat, lon = num(s.get('stop_lat')), num(s.get('stop_lon'))
        if lat is not None and lon is not None and not (lat == 0 and lon == 0):
            where[nm].append((lat, lon))
    cal, add, rem, cover = calendar(zf, enc)
    covers = {k: cover is not None and cover[0] <= d <= cover[1] for k, d in days.items()}
    on = {k: services(cal, add, rem, d) if covers[k] else set() for k, d in days.items()}
    rtype = {r.get('route_id', ''): to_int(r.get('route_type')) for r in rows(zf, 'routes.txt', enc)}
    c = Counter()
    run_on = {}
    for t in rows(zf, 'trips.txt', enc):
        c['trips'] += 1
        if not is_bus(rtype.get(t.get('route_id', ''), -1)):
            continue
        c['bus_trips'] += 1
        labels = tuple(k for k in days if t.get('service_id', '') in on[k])
        if labels:
            run_on[sys.intern(t.get('trip_id', ''))] = labels
    stops = defaultdict(list)
    for i, r in enumerate(rows(zf, 'stop_times.txt', enc)):
        tid = r.get('trip_id', '')
        if tid not in run_on:
            continue
        dep = secs(r.get('departure_time'))
        if dep is None:
            dep = secs(r.get('arrival_time'))
        try:
            seq = float(r.get('stop_sequence') or '')
        except ValueError:
            seq = math.inf
        stops[tid].append((seq, i, dep, sys.intern(r.get('stop_id', '')), (r.get('pickup_type') or '0') == '1'))
    freq = defaultdict(list)
    for r in rows(zf, 'frequencies.txt', enc):
        tid = r.get('trip_id', '')
        s, e, h = secs(r.get('start_time')), secs(r.get('end_time')), to_int(r.get('headway_secs'), 0)
        if tid in run_on and s is not None and e is not None and h > 0 and e > s:
            freq[tid].append((s, s + (e - s - 1) // h * h))
    first = {k: {} for k in days}
    last = {k: {} for k in days}
    for tid, st in stops.items():
        st.sort()
        timed = [x for x in st if x[2] is not None]
        if not timed:
            continue
        base = timed[0][2]
        windows = freq.get(tid) or [(base, base)]
        early, late = min(w[0] for w in windows) - base, max(w[1] for w in windows) - base
        for seq, i, dep, sid, no_pickup in st[:-1]:
            if dep is None or no_pickup:
                continue
            nm = place.get(sid, sid)
            for k in run_on[tid]:
                if nm not in first[k] or dep + early < first[k][nm]:
                    first[k][nm] = dep + early
                if nm not in last[k] or dep + late > last[k][nm]:
                    last[k][nm] = dep + late
    names = sorted(set().union(*(set(first[k]) for k in days)))
    out = []
    for nm in names:
        pts = where.get(nm, [])
        p = {'place': nm, 'lat': round(sum(x[0] for x in pts) / len(pts), 6) if pts else None,
             'lon': round(sum(x[1] for x in pts) / len(pts), 6) if pts else None}
        for k in days:
            p[f'first_{k}'], p[f'last_{k}'] = first[k].get(nm), last[k].get(nm)
        out.append(p)
    c['places'] = len(out)
    for k in days:
        c[f'places_{k}'] = len(last[k])
        c[f'covers_{k}'] = covers[k]
    c['cover_start'] = cover[0].isoformat() if cover else ''
    c['cover_end'] = cover[1].isoformat() if cover else ''
    return c, out


def quantile(values, q):
    """The smallest value with at least a share q of the values at or below it (a lower median for q = 0.5)."""
    v = sorted(values)
    if not v:
        return None
    return v[max(0, math.ceil(q * len(v)) - 1)]


def share(k, n):
    return round(k / n, 3) if n else None


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


def run(census_rows, get, days, pause=2.0, log=print):
    """One row per feed; its places are kept in the row's _places."""
    out = []
    for i, f in enumerate(census_rows):
        if i and pause:
            time.sleep(pause)
        row = {k: f.get(k, '') for k in BASE}
        row['_places'] = []
        try:
            with zipfile.ZipFile(io.BytesIO(get(f['organization_id'], f['feed_id']))) as zf:
                c, places = check(zf, days)
        except Exception as e:  # noqa: BLE001 - recorded, not fatal
            row.update({k: '' for k in COLUMNS[len(BASE):]})
            row.update(status='failed', detail=str(e)[:200])
            out.append(row)
            log(f"failed {f['organization_id']}/{f['feed_id']} {row['detail']}")
            continue
        wed = [p['last_wed'] for p in places if p['last_wed'] is not None]
        row.update(status='ok', detail='', cover_start=c['cover_start'], cover_end=c['cover_end'],
                   trips=c['trips'], bus_trips=c['bus_trips'], places=c['places'])
        for k in days:
            row[f'covers_{k}'] = 'yes' if c[f'covers_{k}'] else 'no'
            row[f'places_{k}'] = c[f'places_{k}']
        row.update(first_wed_median=fmt(quantile([p['first_wed'] for p in places if p['first_wed'] is not None], 0.5)),
                   last_wed_median=fmt(quantile(wed, 0.5)), last_wed_max=fmt(max(wed) if wed else None),
                   before_19_wed=sum(t < 19 * H for t in wed),
                   no_sun=(sum(p['last_wed'] is not None and p['last_sun'] is None for p in places)
                           if row['covers_sun'] == 'yes' else ''))
        ids = {'organization_id': f['organization_id'], 'feed_id': f['feed_id'], 'pref_id': f.get('pref_id', '')}
        row['_places'] = [{**ids, **p} for p in places]
        out.append(row)
        log(f"ok {f['organization_id']}/{f['feed_id']} places={c['places']} wed={c['places_wed']} "
            f"sat={c['places_sat']} sun={c['places_sun']} last_wed_median={row['last_wed_median']}")
    return out


def score(v):
    med, b19, nosun, f18, late, earlier = (v['median'], v['before_19'], v['no_sunday'], v['feeds_before_18'],
                                           v['from_23'], v['sunday_earlier'])
    held = {'L1': med is not None and 19 * H <= med <= 21 * H,
            'L2': b19 is not None and b19 >= 0.25,
            'L3': nosun is not None and nosun >= 0.15,
            'L4': f18 is not None and f18 >= 0.30,
            'L5': late is not None and late < 0.10,
            'L6': earlier is not None and earlier >= 0.40}
    value = {'L1': fmt(med), 'L2': b19, 'L3': nosun, 'L4': f18, 'L5': late, 'L6': earlier}
    return {k: {'statement': PREDICTIONS[k], 'value': value[k], 'held': held[k]} for k in PREDICTIONS}


def summarise(rows_, as_of, days):
    ok = [r for r in rows_ if r['status'] == 'ok']
    places = [p for r in ok for p in r['_places']]
    wed = [p['last_wed'] for p in places if p['last_wed'] is not None]
    first = [p['first_wed'] for p in places if p['first_wed'] is not None]
    cov_sun = [p for r in ok if r['covers_sun'] == 'yes' for p in r['_places'] if p['last_wed'] is not None]
    cov_sat = [p for r in ok if r['covers_sat'] == 'yes' for p in r['_places'] if p['last_wed'] is not None]
    both = [p for p in places if p['last_wed'] is not None and p['last_sun'] is not None]
    feed_medians = [quantile([p['last_wed'] for p in r['_places'] if p['last_wed'] is not None], 0.5)
                    for r in ok if r['places_wed']]
    hours = Counter(t // H for t in wed)
    s = {'as_of': as_of, 'days': {k: d.isoformat() for k, d in days.items()}, 'feeds': len(rows_), 'read': len(ok),
         'failed': len(rows_) - len(ok),
         'feeds_covering': {k: sum(r[f'covers_{k}'] == 'yes' for r in ok) for k in days},
         'feeds_with_departures': {k: sum(r[f'places_{k}'] > 0 for r in ok) for k in days},
         'places': {k: sum(p[f'last_{k}'] is not None for p in places) for k in days},
         'last_wed': {f'p{int(q * 100)}': fmt(quantile(wed, q)) for q in (0.1, 0.25, 0.5, 0.75, 0.9)},
         'first_wed_median': fmt(quantile(first, 0.5)),
         'share_last_wed': {**{k: share(sum(t < h * H for t in wed), len(wed)) for k, h in BANDS},
                            'from_23:00': share(sum(t >= 23 * H for t in wed), len(wed))},
         'last_wed_by_hour': {f'{h:02d}': hours[h] for h in sorted(hours)},
         'no_sunday': {'places': len(cov_sun), 'without': sum(p['last_sun'] is None for p in cov_sun),
                       'share': share(sum(p['last_sun'] is None for p in cov_sun), len(cov_sun))},
         'no_saturday': {'places': len(cov_sat), 'without': sum(p['last_sat'] is None for p in cov_sat),
                         'share': share(sum(p['last_sat'] is None for p in cov_sat), len(cov_sat))},
         'sunday_earlier': {'places': len(both), 'earlier': sum(p['last_sun'] < p['last_wed'] for p in both),
                            'share': share(sum(p['last_sun'] < p['last_wed'] for p in both), len(both)),
                            'median_minutes_earlier': quantile([int(round((p['last_wed'] - p['last_sun']) / 60))
                                                                for p in both], 0.5)},
         'feeds_median_before_18': {'feeds': len(feed_medians), 'count': sum(t < 18 * H for t in feed_medians),
                                    'share': share(sum(t < 18 * H for t in feed_medians), len(feed_medians))}}
    s['predictions'] = score({'median': quantile(wed, 0.5), 'before_19': s['share_last_wed']['before_19:00'],
                              'no_sunday': s['no_sunday']['share'], 'feeds_before_18': s['feeds_median_before_18']['share'],
                              'from_23': s['share_last_wed']['from_23:00'], 'sunday_earlier': s['sunday_earlier']['share']})
    s['generated_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    s['by'] = "MV2 of Munim, Inc. (made with AI agents working in MV2's name)"
    return s


def prefectures(rows_):
    by = defaultdict(list)
    for r in rows_:
        by[(to_int(r['pref_id'], 0), r['pref_name'])].append(r)
    out = []
    for (pid, pname), rs in sorted(by.items()):
        ok = [r for r in rs if r['status'] == 'ok']
        w = [p['last_wed'] for r in ok for p in r['_places'] if p['last_wed'] is not None]
        cov = [p for r in ok if r['covers_sun'] == 'yes' for p in r['_places'] if p['last_wed'] is not None]
        out.append({'pref_id': pid, 'pref_name': pname, 'feeds': len(rs), 'read': len(ok),
                    'feeds_wed': sum(r['places_wed'] > 0 for r in ok), 'places_wed': len(w),
                    'last_wed_p25': fmt(quantile(w, 0.25)), 'last_wed_median': fmt(quantile(w, 0.5)),
                    'last_wed_p75': fmt(quantile(w, 0.75)),
                    'share_before_19': share(sum(t < 19 * H for t in w), len(w)),
                    'share_before_20': share(sum(t < 20 * H for t in w), len(w)),
                    'share_from_22': share(sum(t >= 22 * H for t in w), len(w)),
                    'no_sunday_share': share(sum(p['last_sun'] is None for p in cov), len(cov))})
    return out


def report(s):
    d, w, b = s['days'], s['last_wed'], s['share_last_wed']
    pct = lambda x: '' if x is None else f'{x * 100:.1f}%'  # noqa: E731
    lines = [f'# 始発と終バス：全国の停留所 / First and last buses at every place in Japan ({s["as_of"]})', '',
             f'停留所名の調査（names/2026-10-22）と同じデータの現行ファイルを読み、平日（水曜 {d["wed"]}）・土曜（{d["sat"]}）・'
             f'日曜（{d["sun"]}）に、それぞれの停留所（同じ事業者データ内の同じ名前の標柱をまとめたもの）からバスが出る最初と'
             '最後の時刻を求めました。',
             f'The current file of every feed in the stop-name census was read. For an ordinary Wednesday ({d["wed"]}), '
             f'Saturday ({d["sat"]}) and Sunday ({d["sun"]}), each place (a stop name within one feed) gets its first and '
             'last scheduled bus departure where riders may board.', '',
             f'Feeds: {s["feeds"]}; read {s["read"]}; failed {s["failed"]}. Files covering the Wednesday '
             f'{s["feeds_covering"]["wed"]}; with a bus departure that day {s["feeds_with_departures"]["wed"]}.', '',
             f'Places with a bus departure: Wednesday {s["places"]["wed"]}, Saturday {s["places"]["sat"]}, Sunday '
             f'{s["places"]["sun"]}.', '',
             f'Weekday last departure: 10% of places by {w["p10"]}, 25% by {w["p25"]}, median {w["p50"]}, 75% by '
             f'{w["p75"]}, 90% by {w["p90"]}. Median first departure {s["first_wed_median"]}.', '',
             '| last weekday bus | share of places |', '|---|---|']
    lines += [f'| {k.replace("_", " ")} | {pct(v)} |' for k, v in b.items()]
    ns, ne = s['no_sunday'], s['sunday_earlier']
    lines += ['', f'No bus on the Sunday: {ns["without"]} of {ns["places"]} weekday places in files covering the Sunday '
              f'({pct(ns["share"])}). Saturday: {s["no_saturday"]["without"]} of {s["no_saturday"]["places"]} '
              f'({pct(s["no_saturday"]["share"])}).',
              f'Earlier last bus on the Sunday: {ne["earlier"]} of {ne["places"]} places served both days '
              f'({pct(ne["share"])}); median difference {ne["median_minutes_earlier"]} minutes.',
              f'Feeds whose median last weekday departure is before 18:00: {s["feeds_median_before_18"]["count"]} of '
              f'{s["feeds_median_before_18"]["feeds"]} ({pct(s["feeds_median_before_18"]["share"])}).', '',
              '## Predictions recorded before any file was read', '']
    for k, p in s['predictions'].items():
        lines.append(f'- {k}: {p["statement"]} Result: {p["value"]}: ' + ('held.' if p['held'] else 'did not hold.'))
    lines += ['', 'Limits: timetable files only, not real-time running. A place is a stop name within one feed, so two '
              'different stops with the same name in one feed are merged, and a stop served by two operators appears '
              'once per feed. Only bus trips are counted (route_type 3, 200-299 or 700-799); demand-responsive trips '
              'that are in the files are counted like any other. The last departure from a place can be in any '
              'direction, so it is the latest time a bus leaves there, not the last bus home. Stops with no time in '
              'stop_times are not counted. Only the current file of each feed is read, on the day of the run; a file '
              'that does not cover a day has no departures that day.', '',
              f'Generated {s["generated_at"]}. Source: GTFS Data Repository API v2 (https://gtfs-data.jp/); each feed\'s '
              'publisher and licence are in feeds.csv. Made by MV2 of Munim, Inc. with AI agents working in MV2\'s name. '
              'Data CC BY 4.0.']
    return '\n'.join(lines) + '\n'


def write_csv(path, rows_, columns):
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows_)


def place_rows(rows_):
    for r in rows_:
        for p in r['_places']:
            yield {k: (fmt(v) if k.startswith(('first_', 'last_')) else ('' if v is None else v)) for k, v in p.items()}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--feeds', required=True, help='names/2026-10-22/feeds.csv')
    ap.add_argument('--out', required=True, help='results go to <out>/lastbus/<as-of>/')
    ap.add_argument('--as-of', default=time.strftime('%Y-%m-%d', time.gmtime()))
    ap.add_argument('--wed', default=DAYS['wed'])
    ap.add_argument('--sat', default=DAYS['sat'])
    ap.add_argument('--sun', default=DAYS['sun'])
    ap.add_argument('--pause', type=float, default=2.0)
    ap.add_argument('--limit', type=int)
    a = ap.parse_args(argv)
    days = {'wed': dt.date.fromisoformat(a.wed), 'sat': dt.date.fromisoformat(a.sat),
            'sun': dt.date.fromisoformat(a.sun)}
    with open(a.feeds, encoding='utf-8-sig', newline='') as f:
        census = list(csv.DictReader(f))
    if a.limit is not None:
        census = census[:a.limit]
    print(f'feeds: {len(census)}', flush=True)
    rows_ = run(census, get_zip, days, a.pause, log=lambda x: print(x, flush=True))
    out = os.path.join(a.out, 'lastbus', a.as_of)
    os.makedirs(out, exist_ok=True)
    s = summarise(rows_, a.as_of, days)
    write_csv(os.path.join(out, 'feeds.csv'), rows_, COLUMNS)
    write_csv(os.path.join(out, 'prefectures.csv'), prefectures(rows_), PREF_COLUMNS)
    write_csv(os.path.join(out, 'places.csv'), place_rows(rows_), PLACE_COLUMNS)
    with open(os.path.join(out, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(s, f, ensure_ascii=False, indent=1)
    with open(os.path.join(out, 'lastbus.md'), 'w', encoding='utf-8') as f:
        f.write(report(s))
    print(json.dumps(s, ensure_ascii=False))
    return s


if __name__ == '__main__':
    main()
