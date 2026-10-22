# verify_names.py - an independent recount of the stop-name census in names/2026-10-22/feeds.csv (names_check.py).
# For every feed listed there it downloads the current file again and counts, with code written separately from
# names_check.py, the stops (location_type 0 or empty) that have a kana reading (ja-Hrkt), an English name (en, en-*)
# and a romanised name (ja-Latn) in translations.txt, then lists every feed whose counts differ from the census. It also
# notes files that are not valid UTF-8 (the census reads them as UTF-8 with replacement characters; this reads them as
# Shift_JIS/cp932). A file updated since the census can differ for that reason alone. Standard library only.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import argparse
import csv
import io
import json
import os
import time
import urllib.parse
import urllib.request
import zipfile
from collections import Counter

API = 'https://api.gtfs-data.jp/v2'
UA = 'GTFS stop-name recount - MV2 of Munim, Inc. (mv2@munimtech.com)'
MOST = 0.9
KEYS = ['stops', 'reading', 'en', 'latn', 'en_or_latn']
# census column for each recount key that the census also has
CENSUS = {'stops': 'stops', 'reading': 'stops_reading', 'en': 'stops_en'}


def find(zf, name):
    """The shallowest member whose file name is `name` (any case), ignoring __MACOSX."""
    hits = [n for n in zf.namelist() if not n.startswith('__MACOSX') and n.split('/')[-1].lower() == name]
    hits.sort(key=lambda n: n.count('/'))
    return hits[0] if hits else None


def table(zf, name):
    """(rows, utf8). rows is None when the member is missing; keys and values are stripped."""
    n = find(zf, name)
    if n is None:
        return None, True
    raw = zf.read(n)
    try:
        text, utf8 = raw.decode('utf-8-sig'), True
    except UnicodeDecodeError:
        text, utf8 = raw.decode('cp932', errors='replace'), False
    rd = csv.reader(io.StringIO(text, newline=''))
    head = next(rd, None)
    if head is None:
        return [], utf8
    head = [h.strip().lstrip('﻿') for h in head]
    rows = [dict(zip(head, (c.strip() for c in row))) for row in rd if any(c.strip() for c in row)]
    return rows, utf8


def langkey(s):
    return (s or '').strip().lower().replace('_', '-')


def is_en(lang):
    return lang == 'en' or lang.startswith('en-')


def count(zf):
    """Counter of stops, reading, en, latn, en_or_latn for one file, plus utf8 (1 or 0) and format."""
    stops, ok_stops = table(zf, 'stops.txt')
    trans, ok_trans = table(zf, 'translations.txt')
    by_record, by_value, by_text = {}, {}, {}
    fmt = 'missing' if trans is None else 'empty' if not trans else \
        'gtfs' if 'table_name' in trans[0] else 'jp_v2' if 'trans_id' in trans[0] else 'unknown'
    for r in trans or []:
        lang, tr = langkey(r.get('language') or r.get('lang')), r.get('translation')
        if not lang or not tr:
            continue
        if fmt == 'jp_v2':
            if r.get('trans_id'):
                by_text.setdefault(r['trans_id'], set()).add(lang)
            continue
        tab = (r.get('table_name') or '').lower()
        if tab.endswith('.txt'):
            tab = tab[:-4]
        if tab != 'stops' or (r.get('field_name') or '').lower() != 'stop_name':
            continue
        if r.get('record_id'):
            by_record.setdefault(r['record_id'], set()).add(lang)
        elif r.get('field_value'):
            by_value.setdefault(r['field_value'], set()).add(lang)
    c = Counter()
    for s in stops or []:
        name = s.get('stop_name')
        if not name or (s.get('location_type') or '0') != '0':
            continue
        langs = by_record.get(s.get('stop_id') or '', set()) | by_value.get(name, set()) | by_text.get(name, set())
        en, latn = any(is_en(x) for x in langs), 'ja-latn' in langs
        c['stops'] += 1
        c['reading'] += 'ja-hrkt' in langs
        c['en'] += en
        c['latn'] += latn
        c['en_or_latn'] += en or latn
    c['utf8'] = int(ok_stops and ok_trans)
    return c, fmt


def compare(census, got):
    """Recount keys whose value differs from the census row."""
    return [k for k, col in CENSUS.items() if str(got.get(k, 0)) != str(census.get(col, '')).strip()]


def most(k, n):
    return bool(n) and k / n >= MOST


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
    out = []
    for i, f in enumerate(census_rows):
        if i and pause:
            time.sleep(pause)
        row = {'organization_id': f['organization_id'], 'feed_id': f['feed_id'], 'pref_id': f.get('pref_id', ''),
               'census_format': f.get('format', '')}
        for k, col in CENSUS.items():
            row['census_' + k] = f.get(col, '')
        try:
            with zipfile.ZipFile(io.BytesIO(get(f['organization_id'], f['feed_id']))) as zf:
                c, fmt = count(zf)
        except Exception as e:  # noqa: BLE001 - recorded, not fatal
            row.update(status='failed', detail=str(e)[:200])
            out.append(row)
            continue
        row.update({k: c[k] for k in KEYS}, format=fmt, utf8=c['utf8'])
        diff = compare(f, c)
        row.update(status='differ' if diff else 'match', detail=';'.join(diff))
        out.append(row)
        log(f"{row['status']} {f['organization_id']}/{f['feed_id']} {fmt} stops={c['stops']} reading={c['reading']} "
            f"en={c['en']} latn={c['latn']} {row['detail']}")
    return out


def summarise(rows):
    ok = [r for r in rows if r['status'] != 'failed']
    t = {k: sum(r[k] for r in ok) for k in KEYS}
    s = {'feeds': len(rows), 'status': dict(Counter(r['status'] for r in rows)),
         'not_utf8': sum(1 for r in ok if not r['utf8']),
         'format_differs': sum(1 for r in ok if r['format'] != r['census_format']),
         'totals': t,
         'share_reading': round(t['reading'] / t['stops'], 3) if t['stops'] else None,
         'share_en': round(t['en'] / t['stops'], 3) if t['stops'] else None,
         'share_en_or_latn': round(t['en_or_latn'] / t['stops'], 3) if t['stops'] else None,
         'feeds_with_latn': sum(1 for r in ok if r['latn']),
         'feeds_most_reading': sum(most(r['reading'], r['stops']) for r in ok),
         'feeds_most_en': sum(most(r['en'], r['stops']) for r in ok),
         'feeds_most_en_or_latn': sum(most(r['en_or_latn'], r['stops']) for r in ok),
         'feeds_latn_without_en': sum(1 for r in ok if most(r['en_or_latn'], r['stops']) and not most(r['en'], r['stops']))}
    return s


COLS = ['organization_id', 'feed_id', 'pref_id', 'status', 'detail', 'census_format', 'format', 'utf8', 'census_stops',
        'stops', 'census_reading', 'reading', 'census_en', 'en', 'latn', 'en_or_latn']


def markdown(s, rows, generated_at):
    lines = ['# 停留所名の再集計 / Independent recount of the stop-name census (names/2026-10-22)', '',
             'names_check.py とは別に書いたコードで、同じフィードの現行ファイルをもう一度ダウンロードし、停留所（標柱）ごとのよみがな・'
             '英語の数を数え直しました。ローマ字（ja-Latn）も数えています（事前登録の予測には含まれません）。',
             'Code written separately from names_check.py downloaded the current file of every feed in the census again and '
             'recounted the stops (poles) with a reading and an English name. It also counts romanised names (ja-Latn), '
             'which were not part of the predictions recorded before the census.', '',
             f'Feeds: {s["feeds"]}; ' + ', '.join(f'{k} {v}' for k, v in sorted(s['status'].items())) +
             f'; files not valid UTF-8: {s["not_utf8"]}; translations format read differently: {s["format_differs"]}.', '',
             f'Stops {s["totals"]["stops"]}: reading {s["share_reading"]}, English {s["share_en"]}, '
             f'English or ja-Latn {s["share_en_or_latn"]}. Feeds with any ja-Latn: {s["feeds_with_latn"]}.',
             f'Feeds giving it for at least 90% of their stops: reading {s["feeds_most_reading"]}, English '
             f'{s["feeds_most_en"]}, English or ja-Latn {s["feeds_most_en_or_latn"]} '
             f'({s["feeds_latn_without_en"]} only through ja-Latn).', '']
    diff = [r for r in rows if r['status'] != 'match']
    if diff:
        lines += ['| feed | status | census stops/reading/English | recount | utf8 | detail |', '|---|---|---|---|---|---|']
        for r in diff:
            lines.append(f"| {r['organization_id']}/{r['feed_id']} | {r['status']} | {r['census_stops']}/"
                         f"{r['census_reading']}/{r['census_en']} | {r.get('stops', '')}/{r.get('reading', '')}/"
                         f"{r.get('en', '')} | {r.get('utf8', '')} | {r['detail']} |")
        lines.append('')
    lines += ['A file updated after the census (2026-10-22 ~10:17 UTC) can differ for that reason alone. '
              f'Generated {generated_at}. Source: GTFS Data Repository API v2 (https://gtfs-data.jp/). '
              "Made by MV2 of Munim, Inc. with AI agents working in MV2's name. Data CC BY 4.0.", '']
    return '\n'.join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--feeds', required=True, help="the census's feeds.csv")
    ap.add_argument('--out', required=True)
    ap.add_argument('--pause', type=float, default=2.0)
    ap.add_argument('--limit', type=int)
    a = ap.parse_args(argv)
    with open(a.feeds, encoding='utf-8-sig', newline='') as f:
        census = list(csv.DictReader(f))
    if a.limit is not None:
        census = census[:a.limit]
    print(f'census feeds: {len(census)}', flush=True)
    rows = run(census, get_zip, a.pause, log=lambda x: print(x, flush=True))
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, 'recount.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)
    s = summarise(rows)
    s['generated_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    s['by'] = "MV2 of Munim, Inc. (made with AI agents working in MV2's name)"
    with open(os.path.join(a.out, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(s, f, ensure_ascii=False, indent=1)
    with open(os.path.join(a.out, 'recount.md'), 'w', encoding='utf-8') as f:
        f.write(markdown(s, rows, s['generated_at']))
    print(json.dumps(s, ensure_ascii=False))


if __name__ == '__main__':
    main()
