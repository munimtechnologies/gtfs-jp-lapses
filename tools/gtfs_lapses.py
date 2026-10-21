# gtfs_lapses.py - how often Japan's open bus timetables in the GTFS Data Repository (https://gtfs-data.jp/)
# run out before a replacement is published. For every feed it reads the version history the repository's
# API keeps (when each file was published and which dates it covers) and counts the days on which no
# published file was valid, i.e. days when apps and route planners reading the repository had no timetable.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import argparse
import csv
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = 'https://api.gtfs-data.jp/v2'
FEEDS_TXT = 'https://raw.githubusercontent.com/munimtechnologies/kaerimichi/main/feeds.txt'
UA = 'GTFS lapse census - MV2 of Munim, Inc. (mv2@munimtech.com)'
JST = dt.timezone(dt.timedelta(hours=9))
ONE = dt.timedelta(days=1)
FY_END = dt.date(2027, 3, 31)
LAPSE_BINS = [(1, 7), (8, 30), (31, 90), (91, 365), (366, None)]
PREFS = ['北海道', '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県', '茨城県', '栃木県', '群馬県',
         '埼玉県', '千葉県', '東京都', '神奈川県', '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県',
         '岐阜県', '静岡県', '愛知県', '三重県', '滋賀県', '京都府', '大阪府', '兵庫県', '奈良県', '和歌山県',
         '鳥取県', '島根県', '岡山県', '広島県', '山口県', '徳島県', '香川県', '愛媛県', '高知県', '福岡県',
         '佐賀県', '長崎県', '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県']


def pref_name(pid):
    return PREFS[pid - 1] if 1 <= pid <= len(PREFS) else 'その他・広域'


def day(s):
    """'2026-05-25' -> date; anything else -> None."""
    s = (s or '').strip()
    try:
        return dt.date.fromisoformat(s[:10]) if len(s) >= 10 else None
    except ValueError:
        return None


def jst_day(ts):
    """An ISO timestamp ('2026-09-15T10:26:36.57+09:00') -> its calendar day in Japan."""
    s = (ts or '').strip()
    if not s:
        return None
    try:
        t = dt.datetime.fromisoformat(s.replace('Z', '+00:00'))
    except ValueError:
        return day(s)
    return t.date() if t.tzinfo is None else t.astimezone(JST).date()


def parse_feeds_txt(text):
    """feeds.txt as written by Kaerimichi's daily job: two '#' lines, then one '|'-separated line per feed."""
    cols = ['organization_id', 'feed_id', 'organization_name', 'feed_name', 'feed_pref_id', 'feed_license',
            'latest_feed_end_date', 'feed_is_discontinued']
    out = []
    for line in text.lstrip('﻿').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        parts = line.split('|')
        if len(parts) == len(cols):
            out.append(dict(zip(cols, parts)))
    return out


def versions(detail):
    """The files of one feed, as dicts with pub (Japan day it was published), from, to, rid, uid, type.
    Files without a publication time, or with unreadable or inverted dates, go to the second list."""
    body = detail.get('body', detail) if isinstance(detail, dict) else {}
    good, bad = [], []
    for f in body.get('gtfs_files') or []:
        v = {'rid': f.get('rid', ''), 'uid': f.get('gtfs_file_uid', ''), 'type': f.get('update_type') or '',
             'pub': jst_day(f.get('published_at')), 'from': day(f.get('from_date')), 'to': day(f.get('to_date'))}
        (good if v['pub'] and v['from'] and v['to'] and v['from'] <= v['to'] else bad).append(v)
    good.sort(key=lambda v: (v['pub'], v['from']))
    return good, bad


def covers_from(v, strict):
    """First day a file was usable: its first valid date, or its publication day if that came later.
    Not strict: an UPDATE replaced an earlier upload of the same timetable whose own publication time the
    API no longer shows, so count it from its first valid date (this keeps the lapse count a lower bound)."""
    if not strict and v['type'] == 'UPDATE':
        return v['from']
    return max(v['from'], v['pub'])


def coverage(vs, strict=False):
    """Merged inclusive [start, end] date ranges on which at least one published file was valid."""
    iv = sorted((covers_from(v, strict), v['to']) for v in vs if covers_from(v, strict) <= v['to'])
    merged = []
    for a, b in iv:
        if merged and a <= merged[-1][1] + ONE:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return merged


def lapses(merged, last_day):
    """Uncovered runs between the first covered day and last_day (inclusive), as (start, end, ongoing)."""
    out = []
    if not merged or merged[0][0] > last_day:
        return out
    bounds = [(b + ONE, a2 - ONE) for (_, b), (a2, _) in zip(merged, merged[1:])]
    bounds.append((merged[-1][1] + ONE, None))
    for g0, g1 in bounds:
        if g0 > last_day:
            break
        ongoing = g1 is None or g1 >= last_day
        out.append((g0, last_day if ongoing else g1, ongoing))
    return out


def overlap(a0, a1, b0, b1):
    """Days in both inclusive ranges."""
    lo, hi = max(a0, b0), min(a1, b1)
    return (hi - lo).days + 1 if lo <= hi else 0


def analyse_feed(vs, last_day, strict=False):
    """Observation window, lapse runs and per-year day counts for one feed's files."""
    merged = coverage(vs, strict)
    if not merged or merged[0][0] > last_day:
        return {'first_covered': None, 'observed_days': 0, 'lapsed_days': 0, 'lapses': [], 'years': {}}
    first = merged[0][0]
    runs = lapses(merged, last_day)
    years = {}
    for y in range(first.year, last_day.year + 1):
        y0, y1 = dt.date(y, 1, 1), dt.date(y, 12, 31)
        obs = overlap(first, last_day, y0, y1)
        lap = sum(overlap(g0, g1, y0, y1) for g0, g1, _ in runs)
        years[y] = (obs, lap)
    return {'first_covered': first, 'observed_days': (last_day - first).days + 1,
            'lapsed_days': sum((g1 - g0).days + 1 for g0, g1, _ in runs), 'lapses': runs, 'years': years}


def lead_days(v):
    """Days between publication and the first valid date: positive = published ahead, negative = back-dated."""
    return (v['from'] - v['pub']).days


def fetch(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
            # Full histories of feeds that publish daily are a few MB, so allow two minutes.
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            if e.code == 404 or i == tries - 1:
                raise
        except urllib.error.URLError:
            if i == tries - 1:
                raise
        time.sleep(5)


def detail_url(org, feed, max_prev=100):
    q = lambda s: urllib.parse.quote(s, safe='')  # noqa: E731
    return f'{API}/organizations/{q(org)}/feeds/{q(feed)}?max_prev={max_prev}&max_next=100'


def prev_count(detail):
    body = detail.get('body', detail) if isinstance(detail, dict) else {}
    return sum(1 for f in body.get('gtfs_files') or [] if str(f.get('rid', '')).startswith('prev'))


def load_detail(org, feed, details_dir, pause):
    """The feed's JSON from the API, or from details_dir/<org>__<feed>.json when testing offline."""
    if details_dir:
        with open(os.path.join(details_dir, f'{org}__{feed}.json'), encoding='utf-8') as f:
            return json.load(f)
    time.sleep(pause)
    detail = json.loads(fetch(detail_url(org, feed)))
    # Feeds that publish daily have more than 100 earlier files (v1 read only the newest 100 of up to 707);
    # the API returns all of them when asked, so ask once more.
    want = detail.get('body', detail).get('max_prev')
    if isinstance(want, int) and want > prev_count(detail):
        time.sleep(pause)
        detail = json.loads(fetch(detail_url(org, feed, want)))
    return detail


def median(xs):
    if not xs:
        return None
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def share(n, d):
    return round(n / d, 4) if d else None


def iso(d):
    return d.isoformat() if d else ''


def bin_label(lo, hi):
    return f'{lo}+' if hi is None else f'{lo}-{hi}'


def run(feed_list, last_day, details_dir=None, pause=1.0, log=print):
    """Fetch and analyse every feed. Returns (feed_rows, version_rows, lapse_rows, errors)."""
    feed_rows, version_rows, lapse_rows, errors = [], [], [], []
    for i, m in enumerate(feed_list):
        org, fid = m['organization_id'], m['feed_id']
        try:
            detail = load_detail(org, fid, details_dir, pause)
        except Exception as e:  # noqa: BLE001 - one bad feed must not stop the census
            errors.append({'organization_id': org, 'feed_id': fid, 'error': f'{type(e).__name__}: {e}'[:200]})
            continue
        body = detail.get('body', detail)
        vs, bad = versions(detail)
        disc = bool(body.get('is_discontinued')) or m.get('feed_is_discontinued') == 'true'
        disc_day = day(body.get('discontinued_date'))
        # A discontinued feed is watched only until its last valid date (or the day before it was discontinued,
        # if earlier), so the end of a network is never counted as a lapse.
        end = last_day
        if disc:
            ends = [x for x in (max((v['to'] for v in vs), default=None), disc_day - ONE if disc_day else None) if x]
            end = min([last_day] + ends)
        res = analyse_feed(vs, end)
        strict = analyse_feed(vs, end, strict=True)
        try:
            pid = int(m.get('feed_pref_id') or body.get('feed_pref_id') or 0)
        except ValueError:
            pid = 0
        prevs = sum(1 for v in vs + bad if str(v['rid']).startswith('prev'))
        latest_to = max((v['to'] for v in vs), default=None)
        runs = res['lapses']
        leads = [lead_days(v) for v in vs]
        feed_rows.append({
            'organization_id': org, 'feed_id': fid, 'organization_name': m.get('organization_name', ''),
            'feed_name': m.get('feed_name', ''), 'pref_id': pid, 'license': m.get('feed_license', ''),
            'discontinued': 'true' if disc else 'false', 'discontinued_date': iso(disc_day),
            'files': len(vs), 'files_unusable': len(bad), 'prev_files': prevs,
            'api_max_prev': body.get('max_prev', ''), 'first_covered': iso(res['first_covered']),
            'window_end': iso(end), 'observed_days': res['observed_days'], 'lapsed_days': res['lapsed_days'],
            'lapse_share': share(res['lapsed_days'], res['observed_days']), 'lapses': len(runs),
            'longest_lapse_days': max(((g1 - g0).days + 1 for g0, g1, _ in runs), default=0),
            'lapsed_now_days': next(((g1 - g0).days + 1 for g0, g1, on in runs if on), 0) if not disc else 0,
            'lapsed_days_strict': strict['lapsed_days'], 'latest_to_date': iso(latest_to),
            'list_end_date': m.get('latest_feed_end_date', ''),
            'days_left': (latest_to - last_day).days if latest_to else '',
            'backdated_files': sum(1 for x in leads if x < 0),
            'median_lead_days': median(leads), '_years': res['years'], '_leads': leads, '_vs': vs})
        for v in vs:
            version_rows.append({'organization_id': org, 'feed_id': fid, 'rid': v['rid'], 'gtfs_file_uid': v['uid'],
                                 'update_type': v['type'], 'published_date': iso(v['pub']),
                                 'from_date': iso(v['from']), 'to_date': iso(v['to']), 'lead_days': lead_days(v)})
        for g0, g1, on in runs:
            nxt = next((v['pub'] for v in vs if covers_from(v, False) == g1 + ONE), None) if not on else None
            lapse_rows.append({'organization_id': org, 'feed_id': fid, 'feed_name': m.get('feed_name', ''),
                               'pref_id': pid, 'start': iso(g0), 'end': iso(g1), 'days': (g1 - g0).days + 1,
                               'ongoing': 'true' if on else 'false', 'ended_by_file_published': iso(nxt)})
        if log and (i + 1) % 50 == 0:
            log(f'{i + 1}/{len(feed_list)} feeds')
    return feed_rows, version_rows, lapse_rows, errors


def tables(feed_rows, lapse_rows, last_day):
    """Year table, lapse-length bins, expiry calendar and prefecture table."""
    years = {}
    for r in feed_rows:
        for y, (obs, lap) in r['_years'].items():
            t = years.setdefault(y, {'year': y, 'feeds_observed': 0, 'feed_days': 0, 'lapsed_feed_days': 0,
                                     'feeds_with_lapse': 0, 'files_published': 0, 'backdated_files': 0,
                                     '_leads': []})
            if obs:
                t['feeds_observed'] += 1
                t['feed_days'] += obs
                t['lapsed_feed_days'] += lap
                t['feeds_with_lapse'] += 1 if lap else 0
        for v in r['_vs']:
            t = years.get(v['pub'].year)
            if t is not None:
                t['files_published'] += 1
                t['backdated_files'] += 1 if lead_days(v) < 0 else 0
                t['_leads'].append(lead_days(v))
    year_rows = []
    for y in sorted(years):
        t = years[y]
        t['lapsed_share'] = share(t['lapsed_feed_days'], t['feed_days'])
        t['median_lead_days'] = median(t.pop('_leads'))
        t['backdated_share'] = share(t['backdated_files'], t['files_published'])
        t['lapses_started'] = sum(1 for x in lapse_rows if day(x['start']).year == y)
        year_rows.append(t)
    bins = []
    ended = [x['days'] for x in lapse_rows if x['ongoing'] == 'false']
    ongoing = [x['days'] for x in lapse_rows if x['ongoing'] == 'true']
    for lo, hi in LAPSE_BINS:
        inb = lambda d: d >= lo and (hi is None or d <= hi)  # noqa: E731
        bins.append({'days': bin_label(lo, hi), 'ended': sum(map(inb, ended)), 'ongoing': sum(map(inb, ongoing))})
    active = [r for r in feed_rows if r['discontinued'] == 'false' and r['latest_to_date']]
    left = [r['days_left'] for r in active]
    expiry = {'active_feeds': len(active), 'expired': sum(1 for d in left if d < 0),
              'expiring_7_days': sum(1 for d in left if 0 <= d <= 7),
              'expiring_30_days': sum(1 for d in left if 0 <= d <= 30),
              'ending_by_fy_end': sum(1 for r in active if day(r['latest_to_date']) <= FY_END),
              'ending_exactly_fy_end': sum(1 for r in active if day(r['latest_to_date']) == FY_END),
              'fy_end': FY_END.isoformat(), 'as_of': last_day.isoformat()}
    prefs = {}
    for r in active:
        p = prefs.setdefault(r['pref_id'], {'pref_id': r['pref_id'], 'pref_name': pref_name(r['pref_id']),
                                            'active_feeds': 0, 'lapsed_now': 0, 'feed_days': 0,
                                            'lapsed_feed_days': 0})
        p['active_feeds'] += 1
        p['lapsed_now'] += 1 if r['lapsed_now_days'] else 0
        p['feed_days'] += r['observed_days']
        p['lapsed_feed_days'] += r['lapsed_days']
    pref_rows = []
    for pid in sorted(prefs):
        p = prefs[pid]
        p['lapsed_share'] = share(p['lapsed_feed_days'], p['feed_days'])
        pref_rows.append(p)
    return year_rows, bins, expiry, pref_rows


def write_csv(path, columns, rows):
    # UTF-8 with a BOM (Excel in Japan) and CRLF, like Kaerimichi's other data.
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore', lineterminator='\r\n')
        w.writeheader()
        w.writerows(rows)


def pct(x):
    return '–' if x is None else f'{x * 100:.1f}%'


def findings(feed_rows, lapse_rows, year_rows, bins, expiry, errors, checks, last_day):
    observed = [r for r in feed_rows if r['observed_days']]
    fd = sum(r['observed_days'] for r in observed)
    ld = sum(r['lapsed_days'] for r in observed)
    lds = sum(r['lapsed_days_strict'] for r in observed)
    now = sorted((r for r in feed_rows if r['lapsed_now_days']), key=lambda r: -r['lapsed_now_days'])
    lines = [f'# GTFS Data Repository lapse census, as of {last_day} (Japan): findings', '',
             f'Feeds in the list: {len(feed_rows) + len(errors)}; read: {len(feed_rows)}; errors: {len(errors)}; '
             f'with at least one usable file: {len(observed)}.', '',
             f'Across {fd:,} feed-days observed, {ld:,} ({pct(share(ld, fd))}) had no published valid file '
             f'(strict count, which also dates UPDATE files from their publication: {lds:,}, {pct(share(lds, fd))}).',
             f'{sum(1 for r in observed if r["lapses"])} feeds had at least one lapse; {len(lapse_rows)} lapses in all.',
             '', '## By calendar year', '',
             '| year | feeds | feed-days | lapsed | share | feeds with a lapse | lapses started | files published | '
             'back-dated | median lead (days) |', '|---|---|---|---|---|---|---|---|---|---|']
    lines += [f'| {t["year"]} | {t["feeds_observed"]} | {t["feed_days"]:,} | {t["lapsed_feed_days"]:,} | '
              f'{pct(t["lapsed_share"])} | {t["feeds_with_lapse"]} | {t["lapses_started"]} | {t["files_published"]} | '
              f'{t["backdated_files"]} ({pct(t["backdated_share"])}) | {t["median_lead_days"]} |' for t in year_rows]
    lines += ['', '## Lapse lengths (days)', '', '| days | ended | still open |', '|---|---|---|']
    lines += [f'| {b["days"]} | {b["ended"]} | {b["ongoing"]} |' for b in bins]
    lines += ['', '## Expiry calendar (active feeds, latest valid date of any published file)', '',
              '```', json.dumps(expiry, ensure_ascii=False, indent=1), '```', '',
              f'## Active feeds with no valid file today: {len(now)}', '',
              '| operator | feed | pref | days without a valid file | latest valid date |', '|---|---|---|---|---|']
    lines += [f'| {r["organization_name"]} | {r["feed_name"]} | {pref_name(r["pref_id"])} | {r["lapsed_now_days"]} | '
              f'{r["latest_to_date"]} |' for r in now[:60]]
    longest = sorted((x for x in lapse_rows if x['ongoing'] == 'false'), key=lambda x: -x['days'])[:20]
    lines += ['', '## Longest lapses that ended', '', '| feed | pref | from | to | days |', '|---|---|---|---|---|']
    lines += [f'| {x["feed_name"]} | {pref_name(x["pref_id"])} | {x["start"]} | {x["end"]} | {x["days"]} |'
              for x in longest]
    lines += ['', '## Checks', '', '```', json.dumps(checks, ensure_ascii=False, indent=1), '```', '']
    if errors:
        lines += ['## Errors', ''] + [f'- {e["organization_id"]}/{e["feed_id"]}: {e["error"]}' for e in errors] + ['']
    return '\n'.join(lines)


FEED_COLS = ['organization_id', 'feed_id', 'organization_name', 'feed_name', 'pref_id', 'license', 'discontinued',
             'discontinued_date', 'files', 'files_unusable', 'prev_files', 'api_max_prev', 'first_covered',
             'window_end', 'observed_days', 'lapsed_days', 'lapse_share', 'lapses', 'longest_lapse_days',
             'lapsed_now_days', 'lapsed_days_strict', 'latest_to_date', 'list_end_date', 'days_left',
             'backdated_files', 'median_lead_days']
VERSION_COLS = ['organization_id', 'feed_id', 'rid', 'gtfs_file_uid', 'update_type', 'published_date', 'from_date',
                'to_date', 'lead_days']
LAPSE_COLS = ['organization_id', 'feed_id', 'feed_name', 'pref_id', 'start', 'end', 'days', 'ongoing',
              'ended_by_file_published']
YEAR_COLS = ['year', 'feeds_observed', 'feed_days', 'lapsed_feed_days', 'lapsed_share', 'feeds_with_lapse',
             'lapses_started', 'files_published', 'backdated_files', 'backdated_share', 'median_lead_days']
PREF_COLS = ['pref_id', 'pref_name', 'active_feeds', 'lapsed_now', 'feed_days', 'lapsed_feed_days', 'lapsed_share']


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--as-of', help='last day counted (YYYY-MM-DD); default: today in Japan')
    ap.add_argument('--feeds', help='a local feeds.txt (default: Kaerimichi main on GitHub)')
    ap.add_argument('--details', help='a folder of <org>__<feed>.json files instead of the API (tests)')
    ap.add_argument('--pause', type=float, default=1.0, help='seconds between API requests')
    ap.add_argument('--out', default='/out')
    a = ap.parse_args(argv)
    last_day = day(a.as_of) if a.as_of else dt.datetime.now(JST).date()
    if a.feeds:
        with open(a.feeds, encoding='utf-8') as f:
            text = f.read()
    else:
        text = fetch(FEEDS_TXT)
    feed_list = parse_feeds_txt(text)
    feed_rows, version_rows, lapse_rows, errors = run(feed_list, last_day, a.details, a.pause)
    year_rows, bins, expiry, pref_rows = tables(feed_rows, lapse_rows, last_day)
    checks = {'feeds_in_list': len(feed_list), 'feeds_read': len(feed_rows), 'errors': len(errors),
              'all_read_or_error': len(feed_rows) + len(errors) == len(feed_list),
              'error_share_below_5pct': len(errors) <= 0.05 * max(1, len(feed_list)),
              'feeds_with_files': sum(1 for r in feed_rows if r['files']),
              'feeds_fewer_prev_files_than_api_max_prev': sum(
                  1 for r in feed_rows if isinstance(r['api_max_prev'], int) and r['prev_files'] < r['api_max_prev']),
              'latest_to_matches_list_end': sum(1 for r in feed_rows
                                                if r['latest_to_date'] and r['latest_to_date'] == r['list_end_date']),
              'files_unusable': sum(r['files_unusable'] for r in feed_rows),
              'update_files': sum(1 for v in version_rows if v['update_type'] == 'UPDATE'),
              'files': len(version_rows)}
    out = os.path.join(a.out, 'lapses', last_day.isoformat())
    os.makedirs(out, exist_ok=True)
    write_csv(os.path.join(out, 'feeds.csv'), FEED_COLS, feed_rows)
    write_csv(os.path.join(out, 'versions.csv'), VERSION_COLS, version_rows)
    write_csv(os.path.join(out, 'lapses.csv'), LAPSE_COLS, lapse_rows)
    write_csv(os.path.join(out, 'years.csv'), YEAR_COLS, year_rows)
    write_csv(os.path.join(out, 'prefectures.csv'), PREF_COLS, pref_rows)
    observed = [r for r in feed_rows if r['observed_days']]
    fd = sum(r['observed_days'] for r in observed)
    ld = sum(r['lapsed_days'] for r in observed)
    summary = {'as_of': last_day.isoformat(), 'source': f'{API} (GTFS Data Repository) + {FEEDS_TXT}',
               'feed_days': fd, 'lapsed_feed_days': ld, 'lapsed_share': share(ld, fd),
               'lapsed_feed_days_strict': sum(r['lapsed_days_strict'] for r in observed),
               'feeds_with_lapse': sum(1 for r in observed if r['lapses']), 'lapses': len(lapse_rows),
               'active_lapsed_now': sum(1 for r in feed_rows if r['lapsed_now_days']),
               'expiry': expiry, 'lapse_lengths': bins, 'years': year_rows, 'checks': checks,
               'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    with open(os.path.join(out, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    with open(os.path.join(out, 'findings.md'), 'w', encoding='utf-8') as f:
        f.write(findings(feed_rows, lapse_rows, year_rows, bins, expiry, errors, checks, last_day))
    with open(os.path.join(out, 'errors.json'), 'w', encoding='utf-8') as f:
        json.dump(errors, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: summary[k] for k in ('feed_days', 'lapsed_feed_days', 'lapsed_share', 'feeds_with_lapse',
                                              'lapses', 'active_lapsed_now', 'expiry', 'checks')}, ensure_ascii=False))
    if not (checks['all_read_or_error'] and checks['error_share_below_5pct']):
        sys.exit('too many feeds could not be read: see errors.json')


if __name__ == '__main__':
    main()
