#!/usr/bin/env python3
# gtfs_jp_expiry.py - is a Japanese open bus timetable in the GTFS Data Repository (https://gtfs-data.jp/) still
# valid today, and when does it run out? Part of the gtfs-jp-expiry agent skill in
# https://github.com/munimtechnologies/gtfs-jp-lapses (skills/gtfs-jp-expiry/).
# MV2 of Munim, Inc. (mv2@munimtech.com) - Apache-2.0 license. Made with AI agents working in MV2's name.
"""Three ways to answer, from the cheapest:

  (default)            read the weekly watch list bundled next to this script (data/expiring-2026-11-08.csv):
                       feeds that had ended, or had 60 days or less left, on 2026-11-08. No network.
  --feeds-json PATH    read a saved copy of https://api.gtfs-data.jp/v2/feeds and rate every feed in it.
  --fetch              download that list once (one GET request) and rate every feed in it.

  --detail-json PATH / --fetch-feed ORG/FEED
                       read one feed's file list (organizations/{org}/feeds/{feed}) and say whether any published
                       file covers the day, until when, and whether a later file leaves days uncovered.

Standard library only. Exit code 0 = something matched, 1 = nothing matched, 2 = input could not be read.
"""
import argparse
import csv
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request

VERSION = '0.1.0'
SNAPSHOT_DATE = '2026-11-08'
HERE = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT = os.path.join(HERE, '..', 'data', 'expiring-2026-11-08.csv')
API = 'https://api.gtfs-data.jp/v2'
UA = 'gtfs-jp-expiry agent skill - MV2 of Munim, Inc. (mv2@munimtech.com)'
JST = dt.timezone(dt.timedelta(hours=9))
ONE = dt.timedelta(days=1)
PREFS = ['北海道', '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県', '茨城県', '栃木県', '群馬県',
         '埼玉県', '千葉県', '東京都', '神奈川県', '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県',
         '岐阜県', '静岡県', '愛知県', '三重県', '滋賀県', '京都府', '大阪府', '兵庫県', '奈良県', '和歌山県',
         '鳥取県', '島根県', '岡山県', '広島県', '山口県', '徳島県', '香川県', '愛媛県', '高知県', '福岡県',
         '佐賀県', '長崎県', '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県']
# Status names, from worst to best. 'later' = more than 60 days left.
ORDER = ['expired', 'ends_7', 'ends_30', 'ends_60', 'later', 'no_end_date', 'discontinued']
COLS = ['status', 'days_left', 'latest_feed_end_date', 'latest_feed_start_date', 'organization_id', 'feed_id',
        'organization_name', 'feed_name', 'pref_id', 'pref_name', 'license', 'last_published_at',
        'days_since_published', 'ends_on_fy_end', 'source']


def day(s):
    """'2026-05-25' or '2026-05-25T10:00:00+09:00' -> date; anything else -> None."""
    s = (s or '').strip() if isinstance(s, str) else ''
    try:
        return dt.date.fromisoformat(s[:10]) if len(s) >= 10 else None
    except ValueError:
        return None


def iso(d):
    return d.isoformat() if d else ''


def pref_name(pid):
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return ''
    return PREFS[pid - 1] if 1 <= pid <= len(PREFS) else 'その他・広域'


def fy_end(as_of):
    """The last day (March 31) of the Japanese fiscal year that contains as_of."""
    end = dt.date(as_of.year, 3, 31)
    return end if as_of <= end else dt.date(as_of.year + 1, 3, 31)


def band(days_left):
    """Days left = latest valid date - the day checked, so 0 means the day checked is the last valid day."""
    if days_left < 0:
        return 'expired'
    if days_left <= 7:
        return 'ends_7'
    if days_left <= 30:
        return 'ends_30'
    if days_left <= 60:
        return 'ends_60'
    return 'later'


def feed_list(doc):
    """The API's /feeds answer ({'body': [...]}) or a bare list -> the feed dicts that have both ids."""
    body = doc.get('body') if isinstance(doc, dict) else doc
    return [f for f in body or [] if isinstance(f, dict) and f.get('organization_id') and f.get('feed_id')]


def rate(f, as_of, source):
    """One feed dict from the API list -> one output row."""
    end = day(f.get('latest_feed_end_date'))
    pub = day(f.get('last_published_at'))
    if f.get('feed_is_discontinued') in (True, 'true'):
        status, left = 'discontinued', ''
    elif not end:
        status, left = 'no_end_date', ''
    else:
        left = (end - as_of).days
        status = band(left)
    pid = f.get('feed_pref_id')
    return {'status': status, 'days_left': left, 'latest_feed_end_date': iso(end),
            'latest_feed_start_date': iso(day(f.get('latest_feed_start_date'))),
            'organization_id': f['organization_id'], 'feed_id': f['feed_id'],
            'organization_name': f.get('organization_name') or '', 'feed_name': f.get('feed_name') or '',
            'pref_id': pid if pid is not None else '', 'pref_name': pref_name(pid),
            'license': f.get('feed_license') or '', 'last_published_at': iso(pub),
            'days_since_published': (as_of - pub).days if pub else '',
            'ends_on_fy_end': bool(end and end == fy_end(as_of)), 'source': source}


def rate_all(feeds, as_of, source='api'):
    rows = [rate(f, as_of, source) for f in feeds]
    rows.sort(key=sort_key)
    return rows


def sort_key(r):
    left = r['days_left'] if isinstance(r['days_left'], int) else 10 ** 6
    return (ORDER.index(r['status']), left, r['organization_id'], r['feed_id'])


def snapshot_rows(path, as_of):
    """Rows of the bundled weekly watch list, with days left and status recomputed for as_of."""
    rows = []
    with open(path, encoding='utf-8-sig', newline='') as fh:
        for x in csv.DictReader(fh):
            end = day(x.get('latest_feed_end_date'))
            if not end or not x.get('organization_id') or not x.get('feed_id'):
                continue
            pub = day(x.get('last_published_at'))
            left = (end - as_of).days
            rows.append({'status': band(left), 'days_left': left, 'latest_feed_end_date': iso(end),
                         'latest_feed_start_date': x.get('latest_feed_start_date') or '',
                         'organization_id': x['organization_id'], 'feed_id': x['feed_id'],
                         'organization_name': x.get('organization_name') or '', 'feed_name': x.get('feed_name') or '',
                         'pref_id': x.get('pref_id') or '', 'pref_name': x.get('pref_name') or pref_name(x.get('pref_id')),
                         'license': x.get('license') or '', 'last_published_at': iso(pub),
                         'days_since_published': (as_of - pub).days if pub else '',
                         'ends_on_fy_end': end == fy_end(as_of), 'source': 'snapshot ' + SNAPSHOT_DATE,
                         'past_lapses': x.get('past_lapses', ''), 'past_april1_lapses': x.get('past_april1_lapses', '')})
    rows.sort(key=sort_key)
    return rows


def select(rows, org=None, feed=None, grep=None, pref=None, within=None, status=None):
    out = []
    g = grep.lower() if grep else None
    for r in rows:
        if org and r['organization_id'] != org:
            continue
        if feed and r['feed_id'] != feed:
            continue
        if g and not any(g in str(r[k]).lower() for k in ('organization_id', 'feed_id', 'organization_name',
                                                           'feed_name')):
            continue
        if pref and str(pref) not in (str(r['pref_id']), r['pref_name']) and not r['pref_name'].startswith(str(pref)):
            continue
        if within is not None and not (isinstance(r['days_left'], int) and r['days_left'] <= within):
            continue
        if status and r['status'] != status:
            continue
        out.append(r)
    return out


def summary(rows, as_of):
    c = {s: 0 for s in ORDER}
    for r in rows:
        c[r['status']] += 1
    fy = fy_end(as_of)
    dated = [r for r in rows if r['status'] not in ('discontinued', 'no_end_date')]
    return {'as_of': as_of.isoformat(), 'feeds': len(rows), 'by_status': c, 'fy_end': fy.isoformat(),
            'ending_on_fy_end': sum(1 for r in dated if r['ends_on_fy_end']),
            'ending_by_fy_end': sum(1 for r in dated if day(r['latest_feed_end_date']) <= fy)}


def files_of(detail):
    """One feed's API answer -> [(from, to, rid, published day)] for files with readable, ordered dates."""
    body = detail.get('body', detail) if isinstance(detail, dict) else {}
    out = []
    for f in (body or {}).get('gtfs_files') or []:
        a, b = day(f.get('from_date')), day(f.get('to_date'))
        if a and b and a <= b:
            out.append((a, b, str(f.get('rid', '')), day(f.get('published_at'))))
    out.sort()
    return out


def merge(files):
    """[(from, to, ...)] -> merged runs [[start, end]] of days covered by at least one file."""
    runs = []
    for f in files:
        a, b = f[0], f[1]
        if runs and a <= runs[-1][1] + ONE:
            runs[-1][1] = max(runs[-1][1], b)
        else:
            runs.append([a, b])
    return runs


def coverage(detail, as_of):
    """Does any published file cover as_of, until when, and which uncovered stretches follow?"""
    files = files_of(detail)
    runs = merge(files)
    now = next((r for r in runs if r[0] <= as_of <= r[1]), None)
    later = [r for r in runs if r[0] > as_of]
    gaps = []
    prev_end = now[1] if now else None
    for r in later:
        if prev_end is not None:
            gaps.append({'from': iso(prev_end + ONE), 'to': iso(r[0] - ONE), 'days': (r[0] - prev_end).days - 1})
        prev_end = r[1]
    last = runs[-1][1] if runs else None
    if now:
        status = 'covered'
        left = (now[1] - as_of).days
    elif later:
        status = 'gap_now'
        left = None
    elif runs:
        status = 'expired'
        left = (last - as_of).days
    else:
        status = 'no_files'
        left = None
    return {'as_of': as_of.isoformat(), 'status': status, 'files': len(files),
            'covered_until': iso(now[1]) if now else '', 'days_left': left,
            'next_covered_from': iso(later[0][0]) if (later and not now) else '',
            'gaps_ahead': gaps, 'last_covered_day': iso(last)}


def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode('utf-8'))


def detail_url(org, feed):
    q = lambda s: urllib.parse.quote(s, safe='')
    return f'{API}/organizations/{q(org)}/feeds/{q(feed)}?max_prev=1&max_next=100'


def show(rows):
    for r in rows:
        left = r['days_left'] if r['days_left'] != '' else '-'
        print(f"{r['status']}\t{left}\t{r['latest_feed_end_date'] or '-'}\t{r['organization_id']}/{r['feed_id']}\t"
              f"{r['organization_name']} {r['feed_name']}\t{r['pref_name']}\t{r['license']}")


def main(argv=None):
    ap = argparse.ArgumentParser(description='Expiry of Japanese GTFS feeds in the GTFS Data Repository.')
    src = ap.add_mutually_exclusive_group()
    src.add_argument('--feeds-json', help='a saved copy of https://api.gtfs-data.jp/v2/feeds')
    src.add_argument('--fetch', action='store_true', help='download the feed list once (network)')
    src.add_argument('--detail-json', help="a saved copy of one feed's organizations/{org}/feeds/{feed} answer")
    src.add_argument('--fetch-feed', metavar='ORG/FEED', help="download one feed's file list once (network)")
    ap.add_argument('--snapshot', default=SNAPSHOT, help='the bundled watch list (default mode)')
    ap.add_argument('--as-of', help='the day to check, YYYY-MM-DD (default: today in Japan)')
    ap.add_argument('--org', help='organization_id, exact')
    ap.add_argument('--feed', help='feed_id, exact')
    ap.add_argument('--grep', help='substring of the ids or the Japanese names')
    ap.add_argument('--pref', help='prefecture number (1-47) or name, e.g. 39 or 高知県')
    ap.add_argument('--within', type=int, help='only feeds with this many days left or fewer (expired included)')
    ap.add_argument('--status', choices=ORDER)
    ap.add_argument('--summary', action='store_true', help='counts by status instead of rows')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--version', action='version', version=f'gtfs_jp_expiry {VERSION} (snapshot {SNAPSHOT_DATE})')
    a = ap.parse_args(argv)
    as_of = day(a.as_of) if a.as_of else dt.datetime.now(JST).date()
    if not as_of:
        print('--as-of must be YYYY-MM-DD', file=sys.stderr)
        return 2

    if a.detail_json or a.fetch_feed:
        try:
            if a.detail_json:
                with open(a.detail_json, encoding='utf-8') as fh:
                    detail = json.load(fh)
            else:
                org, _, feed = a.fetch_feed.partition('/')
                if not org or not feed:
                    print('--fetch-feed needs ORG/FEED', file=sys.stderr)
                    return 2
                detail = fetch_json(detail_url(org, feed))
        except (OSError, ValueError) as e:
            print(f'could not read the feed detail: {e}', file=sys.stderr)
            return 2
        res = coverage(detail, as_of)
        if a.json:
            print(json.dumps(res, ensure_ascii=False, indent=1))
        else:
            print(f"{res['status']}: {res['files']} files; covered until {res['covered_until'] or '-'}; "
                  f"next covered from {res['next_covered_from'] or '-'}; last covered day {res['last_covered_day'] or '-'}")
            for g in res['gaps_ahead']:
                if g['days'] > 0:
                    print(f"gap ahead: {g['from']} .. {g['to']} ({g['days']} days with no published file)")
        return 0 if res['files'] else 1

    try:
        if a.feeds_json or a.fetch:
            if a.feeds_json:
                with open(a.feeds_json, encoding='utf-8') as fh:
                    doc = json.load(fh)
                source = 'saved list'
            else:
                doc = fetch_json(f'{API}/feeds')
                source = f'{API}/feeds read {dt.datetime.now(JST).date().isoformat()}'
            rows = rate_all(feed_list(doc), as_of, source)
            if not rows:
                print('the feed list is empty', file=sys.stderr)
                return 2
        else:
            rows = snapshot_rows(a.snapshot, as_of)
            age = (as_of - day(SNAPSHOT_DATE)).days
            if age > 7:
                print(f'note: the bundled list is from {SNAPSHOT_DATE} ({age} days before {as_of}); feeds that had '
                      'more than 60 days left then are not in it. Use --fetch or --feeds-json for current data.',
                      file=sys.stderr)
    except (OSError, ValueError) as e:
        print(f'could not read the feed list: {e}', file=sys.stderr)
        return 2

    lookup = bool(a.org or a.feed or a.grep)
    within = a.within if a.within is not None else (None if (lookup or a.summary or a.status or a.pref) else 60)
    picked = select(rows, a.org, a.feed, a.grep, a.pref, within, a.status)
    if a.summary:
        res = summary(picked, as_of)
        print(json.dumps(res, ensure_ascii=False, indent=None if not a.json else 1))
        return 0 if picked else 1
    if a.json:
        print(json.dumps(picked, ensure_ascii=False, indent=1))
    else:
        show(picked)
    if not picked and lookup and not (a.feeds_json or a.fetch):
        print(f'not on the {SNAPSHOT_DATE} watch list: on that day it had more than 60 days left, was '
              'discontinued, or is not in the repository. Use --fetch or --feeds-json to check the current list.',
              file=sys.stderr)
    return 0 if picked else 1


if __name__ == '__main__':
    sys.exit(main())
