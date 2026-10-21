# expiry_watch.py - which of Japan's open bus timetables in the GTFS Data Repository (https://gtfs-data.jp/) run out
# within the next 60 days, or already have, each marked with its own record in the lapse census (lapses.csv): how
# many times it had no valid file before, and how many of those began on April 1. It reads only the API's feed
# list (one request), so it can be re-run on any day. The repository already e-mails each publisher 14 days before
# a file ends; this is the same signal in public, for the apps and route planners that read the feeds.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import argparse
import datetime as dt
import json
import os
import sys
import time

from fy_cliff import read_csv
from gtfs_lapses import API, FY_END, JST, day, fetch, pref_name, write_csv

FEEDS_URL = f'{API}/feeds'
CENSUS_LABEL = 'data/2026-10-16/lapses.csv'
CENSUS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', *CENSUS_LABEL.split('/'))
# (status, last day-count in the band). Days left = latest valid date - today, so 0 means today is the last day.
BANDS = [('ends_7', 7), ('ends_30', 30), ('ends_60', 60)]
LABELS = {'expired': ('期限切れ', 'expired'), 'ends_7': ('7日以内', '0-7 days'),
          'ends_30': ('8〜30日', '8-30 days'), 'ends_60': ('31〜60日', '31-60 days')}
COLS = ['status', 'days_left', 'latest_feed_end_date', 'organization_id', 'feed_id', 'organization_name',
        'feed_name', 'pref_id', 'pref_name', 'license', 'latest_feed_start_date', 'last_published_at',
        'days_since_published', 'past_lapses', 'past_april1_lapses', 'latest_lapse_start']


def iso(d):
    return d.isoformat() if d else ''


def band(days_left):
    """'expired' (no valid file today), 'ends_7', 'ends_30' or 'ends_60'; None for more than 60 days left."""
    if days_left < 0:
        return 'expired'
    for name, hi in BANDS:
        if days_left <= hi:
            return name
    return None


def feed_list(doc):
    """The API's /feeds answer ({'body': [...]}) or a bare list -> the feed dicts that have both ids."""
    body = doc.get('body') if isinstance(doc, dict) else doc
    return [f for f in body or [] if isinstance(f, dict) and f.get('organization_id') and f.get('feed_id')]


def history(lapse_rows):
    """{(org, feed): (lapses, how many began on April 1, start of the latest)} from the census's lapses.csv."""
    h = {}
    for x in lapse_rows:
        s = day(x.get('start'))
        if not s:
            continue
        k = (x['organization_id'], x['feed_id'])
        n, apr, last = h.get(k, (0, 0, None))
        h[k] = (n + 1, apr + (1 if (s.month, s.day) == (4, 1) else 0), max(last, s) if last else s)
    return h


def watch(feeds, hist, as_of):
    """(watch-list rows, counts). Discontinued feeds and feeds without an end date are counted, not listed.
    Rows are sorted by days left, then by the feed's past lapses (most first)."""
    counts = {'feeds_in_list': len(feeds), 'discontinued': 0, 'no_end_date': 0, 'active': 0,
              'expired': 0, 'ends_7': 0, 'ends_30': 0, 'ends_60': 0,
              'ending_on_fy_end': 0, 'ending_by_fy_end': 0, 'fy_end': FY_END.isoformat()}
    rows = []
    for f in feeds:
        if f.get('feed_is_discontinued') in (True, 'true'):
            counts['discontinued'] += 1
            continue
        end = day(f.get('latest_feed_end_date'))
        if not end:
            counts['no_end_date'] += 1
            continue
        counts['active'] += 1
        counts['ending_on_fy_end'] += 1 if end == FY_END else 0
        counts['ending_by_fy_end'] += 1 if end <= FY_END else 0
        left = (end - as_of).days
        status = band(left)
        if not status:
            continue
        counts[status] += 1
        n, apr, last = hist.get((f['organization_id'], f['feed_id']), (0, 0, None))
        pub = day(f.get('last_published_at'))
        try:
            pid = int(f.get('feed_pref_id') or 0)
        except (TypeError, ValueError):
            pid = 0
        rows.append({'status': status, 'days_left': left, 'latest_feed_end_date': iso(end),
                     'organization_id': f['organization_id'], 'feed_id': f['feed_id'],
                     'organization_name': f.get('organization_name') or '', 'feed_name': f.get('feed_name') or '',
                     'pref_id': pid, 'pref_name': pref_name(pid), 'license': f.get('feed_license') or '',
                     'latest_feed_start_date': iso(day(f.get('latest_feed_start_date'))),
                     'last_published_at': iso(pub), 'days_since_published': (as_of - pub).days if pub else '',
                     'past_lapses': n, 'past_april1_lapses': apr, 'latest_lapse_start': iso(last)})
    rows.sort(key=lambda r: (r['days_left'], -r['past_lapses'], r['organization_id'], r['feed_id']))
    return rows, counts


def markdown(rows, counts, as_of, census, limit=120):
    c = counts
    lines = [f'# 期限切れ・期限間近のGTFSデータ / Expiring GTFS feeds in Japan ({as_of})', '',
             'GTFSデータリポジトリ（https://gtfs-data.jp/ ）の一覧で、最新データの有効期限が過ぎた、または60日以内に切れるデータです。'
             '「過去の空白」は2026年10月16日までの空白調査（' + census + '）での回数です。',
             'Feeds in the GTFS Data Repository list whose latest file has already ended or ends within 60 days. '
             f'"Past lapses" are the feed\'s lapses in the census to 2026-10-16 ({census}).', '',
             f'- 一覧 / in the list: {c["feeds_in_list"]}; 運行終了 / discontinued: {c["discontinued"]}; '
             f'期限なし / no end date: {c["no_end_date"]}; 有効 / active: {c["active"]}',
             f'- 期限切れ / expired: {c["expired"]}; 0〜7日 / 0-7 days: {c["ends_7"]}; '
             f'8〜30日 / 8-30 days: {c["ends_30"]}; 31〜60日 / 31-60 days: {c["ends_60"]}',
             f'- {c["fy_end"]} に切れる / ending exactly on {c["fy_end"]}: {c["ending_on_fy_end"]} '
             f'(それまでに切れる / ending by then: {c["ending_by_fy_end"]})', '',
             '| 状態 / status | 残り日数 / days left | 期限 / ends | 提供者 / operator | データ / feed | 都道府県 | '
             '過去の空白（うち4月1日） / past lapses (Apr 1) | 最終公開 / last published |',
             '|---|---|---|---|---|---|---|---|']
    for r in rows[:limit]:
        ja, en = LABELS[r['status']]
        lines.append(f'| {ja} / {en} | {r["days_left"]} | {r["latest_feed_end_date"]} | {r["organization_name"]} | '
                     f'{r["feed_name"]} | {r["pref_name"]} | {r["past_lapses"]} ({r["past_april1_lapses"]}) | '
                     f'{r["last_published_at"]} |')
    if len(rows) > limit:
        lines.append(f'| … | | | {len(rows) - limit} more in expiring.csv | | | | |')
    lines += ['', '期限は一覧の latest_feed_end_date です。公開済みの次のデータが期限の後から始まる場合など、一覧だけでは見えない空白もあります。'
              '地域名は事実の記録であり、評価ではありません。',
              'The end date is the list\'s latest_feed_end_date. Gaps the list alone cannot show (for example a newer '
              'file that starts some days after the old one ends) are not caught. Place names are records of fact, '
              'not judgements.', '',
              'Source: GTFS Data Repository API v2 (https://gtfs-data.jp/); each feed\'s publisher and licence are in '
              'expiring.csv. Made by MV2 of Munim, Inc. with AI agents working in MV2\'s name. Data CC BY 4.0.', '']
    return '\n'.join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--as-of', help='the day to check (YYYY-MM-DD); default: today in Japan')
    ap.add_argument('--feeds-json', help='a saved copy of the API\'s /feeds answer (default: fetch it)')
    ap.add_argument('--lapses', default=CENSUS, help='the census lapses.csv that gives each feed\'s record')
    ap.add_argument('--min-feeds', type=int, default=400, help='stop if the list has fewer feeds than this')
    ap.add_argument('--out', default='/out')
    a = ap.parse_args(argv)
    as_of = day(a.as_of) if a.as_of else dt.datetime.now(JST).date()
    if a.feeds_json:
        with open(a.feeds_json, encoding='utf-8') as f:
            text = f.read()
    else:
        text = fetch(FEEDS_URL)
    feeds = feed_list(json.loads(text))
    if len(feeds) < a.min_feeds:
        sys.exit(f'the feed list has {len(feeds)} feeds, fewer than {a.min_feeds}')
    census = CENSUS_LABEL if a.lapses == CENSUS else a.lapses
    hist = history(read_csv(a.lapses)) if os.path.exists(a.lapses) else {}
    rows, counts = watch(feeds, hist, as_of)
    out = os.path.join(a.out, 'watch', as_of.isoformat())
    os.makedirs(out, exist_ok=True)
    write_csv(os.path.join(out, 'expiring.csv'), COLS, rows)
    summary = {'as_of': as_of.isoformat(), 'source': FEEDS_URL + (' (saved copy)' if a.feeds_json else ''),
               'census': census if hist else '', 'counts': counts, 'listed': len(rows),
               'listed_with_past_lapse': sum(1 for r in rows if r['past_lapses']),
               'listed_with_past_april1_lapse': sum(1 for r in rows if r['past_april1_lapses']),
               'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
               'by': 'MV2 of Munim, Inc. (made with AI agents working in MV2\'s name)'}
    with open(os.path.join(out, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    with open(os.path.join(out, 'watch.md'), 'w', encoding='utf-8') as f:
        f.write(markdown(rows, counts, as_of, census))
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
