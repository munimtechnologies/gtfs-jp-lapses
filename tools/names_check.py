# names_check.py - do the files of Japan's open bus timetables in the GTFS Data Repository (https://gtfs-data.jp/)
# give a reading and an English name for each stop and destination? GTFS-JP makes translations.txt and the kana
# reading (ja-Hrkt) of stop names required, and recommends English. For every active feed with an open licence it
# downloads the current file and counts, per stop (location_type 0) and per destination text (trip_headsign), whether
# translations.txt gives a reading and an English name, in either format in use: GTFS's rows (table_name, field_name,
# record_id or field_value) or the older GTFS-JP rows (trans_id, lang, translation), which translate any name with
# that text. Reads stops.txt, trips.txt and translations.txt only; nothing else is kept. Feed selection and downloads
# as in holiday_check.py. Standard library only.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import argparse
import datetime as dt
import io
import json
import os
import re
import sys
import time
import urllib.request
import zipfile
from collections import Counter

import holiday_check as hc

UA = 'GTFS stop-name check - MV2 of Munim, Inc. (mv2@munimtech.com)'
JA_SCRIPT = re.compile('[぀-ヿ㐀-䶿一-鿿豈-﫿]')
KANJI = re.compile('[㐀-䶿一-鿿豈-﫿]')
# A feed "gives" readings or English when at least this share of its stops have them.
MOST = 0.9
FORMATS = ['gtfs', 'jp_v2', 'unknown', 'empty', 'missing']
# Fixed on 2026-10-22, before any file was read (names/predictions-2026-10-22.md); scored by predictions().
PREDICTIONS = {
    'N1': 'At least 70% of the checked feeds give a kana reading (ja-Hrkt) for at least 90% of their stops.',
    'N2': 'Between 20% and 60% of the checked feeds give an English name for at least 90% of their stops.',
    'N3': 'Of all stops with an English name, at least 1% have kana or kanji in that English name.',
    'N4': 'Of the feeds whose translations.txt has rows, at least 10% use the older GTFS-JP format '
          '(trans_id, lang, translation).',
}


def lang_kind(s):
    """'reading' for ja-Hrkt, 'en' for English, else the lower-case language code (None when empty)."""
    s = (s or '').strip().lower().replace('_', '-')
    if s == 'ja-hrkt':
        return 'reading'
    if s == 'en' or s.startswith('en-'):
        return 'en'
    return s or None


def read_translations(rows):
    """(format, by_id, by_text). by_id[(table, field, record_id)] and by_text[(table, field, text)] are
    {kind: translation}; the older GTFS-JP rows go into by_text under ('*', '*', text). Format is 'none' when there
    are no rows."""
    fmt, by_id, by_text = 'none', {}, {}
    for r in rows:
        if fmt == 'none':
            fmt = 'gtfs' if 'table_name' in r else 'jp_v2' if 'trans_id' in r else 'unknown'
        if fmt == 'gtfs':
            kind, tr = lang_kind(r.get('language')), r.get('translation') or ''
            table, field = (r.get('table_name') or '').lower(), (r.get('field_name') or '').lower()
            if table.endswith('.txt'):
                table = table[:-4]
            if not kind or not tr:
                continue
            if r.get('record_id'):
                by_id.setdefault((table, field, r['record_id']), {}).setdefault(kind, tr)
            elif r.get('field_value'):
                by_text.setdefault((table, field, r['field_value']), {}).setdefault(kind, tr)
        elif fmt == 'jp_v2':
            kind, tr = lang_kind(r.get('lang')), r.get('translation') or ''
            if kind and tr and r.get('trans_id'):
                by_text.setdefault(('*', '*', r['trans_id']), {}).setdefault(kind, tr)
    return fmt, by_id, by_text


def lookup(tr, table, field, rid, text):
    """{kind: translation} for one value; a record_id row wins over a field_value row, which wins over the older
    text rows."""
    _fmt, by_id, by_text = tr
    out = {}
    for src in (by_text.get(('*', '*', text)), by_text.get((table, field, text)), by_id.get((table, field, rid))):
        if src:
            out.update(src)
    return out


def check(read, present):
    """Counts for one file. read(name) yields the rows of stops.txt, trips.txt and translations.txt as dicts;
    present says whether the file has a translations.txt."""
    tr = read_translations(read('translations.txt'))
    fmt = 'missing' if not present else 'empty' if tr[0] == 'none' else tr[0]
    rows = [r for r in read('stops.txt') if r.get('stop_name')]
    parents = {r.get('stop_id', ''): lookup(tr, 'stops', 'stop_name', r.get('stop_id', ''), r['stop_name'])
               for r in rows if r.get('location_type') == '1'}
    st, langs = Counter(), set()
    for r in rows:
        if (r.get('location_type') or '0') != '0':
            continue
        name = r['stop_name']
        t = lookup(tr, 'stops', 'stop_name', r.get('stop_id', ''), name)
        p = parents.get(r.get('parent_station') or '', {})
        st['stops'] += 1
        for kind in ('reading', 'en'):
            if t.get(kind):
                st['stops_' + kind] += 1
            elif p.get(kind):
                st[kind + '_parent_only'] += 1
        if t.get('reading') and KANJI.search(t['reading']):
            st['reading_kanji'] += 1
        if t.get('en') and JA_SCRIPT.search(t['en']):
            st['en_japanese'] += 1
            st['en_copy'] += t['en'] == name
        langs.update(k for k in t if k not in ('reading', 'en', 'ja'))
    hs = {}
    for r in read('trips.txt'):
        h = r.get('trip_headsign')
        if not h:
            continue
        t = lookup(tr, 'trips', 'trip_headsign', r.get('trip_id', ''), h)
        hs.setdefault(h, set()).update(k for k in ('reading', 'en') if t.get(k))
    out = {'format': fmt, 'other_languages': ';'.join(sorted(langs)), 'headsigns': len(hs),
           'headsigns_reading': sum('reading' in v for v in hs.values()),
           'headsigns_en': sum('en' in v for v in hs.values())}
    for k in ('stops', 'stops_reading', 'stops_en', 'reading_parent_only', 'en_parent_only', 'reading_kanji',
              'en_japanese', 'en_copy'):
        out[k] = st[k]
    return out


def band(k, n):
    if not n:
        return ''
    return 'none' if k == 0 else 'most' if k / n >= MOST else 'some'


def run(feeds, as_of, get_zip, pause=2.0, limit=None, budget_s=None, log=print):
    """(results, skipped). get_zip(feed) returns the bytes of the feed's current zip."""
    results, skipped, tried, started = [], [], 0, time.time()
    for f in feeds:
        why = hc.skip_reason(f, as_of)
        if why:
            skipped.append(hc.skip_row(f, why))
            continue
        if (limit is not None and tried >= limit) or (budget_s is not None and time.time() - started > budget_s):
            skipped.append(hc.skip_row(f, 'not_reached'))
            continue
        if tried and pause:
            time.sleep(pause)
        tried += 1
        try:
            data = get_zip(f)
        except Exception as e:  # noqa: BLE001 - any failed download is recorded and skipped
            skipped.append(hc.skip_row(f, 'download_failed', e))
            continue
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                res = check(lambda name: hc.zip_rows(zf, name), hc.member(zf, 'translations.txt') is not None)
        except Exception as e:  # noqa: BLE001 - a broken file is recorded and skipped
            skipped.append(hc.skip_row(f, 'bad_zip', e))
            continue
        if not res['stops']:
            skipped.append(hc.skip_row(f, 'no_stops'))
            continue
        res['feed'] = f
        results.append(res)
        log(f"ok {f['organization_id']}/{f['feed_id']} {res['format']} stops={res['stops']} "
            f"reading={res['stops_reading']} en={res['stops_en']}")
    return results, skipped


def predictions(results):
    """The four predictions above, scored on this run's files."""
    n, out = len(results), {}
    rd = sum(band(r['stops_reading'], r['stops']) == 'most' for r in results)
    en = sum(band(r['stops_en'], r['stops']) == 'most' for r in results)
    out['N1'] = {'feeds': n, 'most_reading': rd, 'share': hc.ratio(rd, n), 'held': (rd >= 0.7 * n) if n else None}
    out['N2'] = {'feeds': n, 'most_en': en, 'share': hc.ratio(en, n),
                 'held': (0.2 * n <= en <= 0.6 * n) if n else None}
    m, k = sum(r['stops_en'] for r in results), sum(r['en_japanese'] for r in results)
    out['N3'] = {'stops_en': m, 'en_japanese': k, 'share': hc.ratio(k, m), 'held': (k >= 0.01 * m) if m else None}
    fm = Counter(r['format'] for r in results)
    t = fm['gtfs'] + fm['jp_v2'] + fm['unknown']
    out['N4'] = {'with_rows': t, 'jp_v2': fm['jp_v2'], 'share': hc.ratio(fm['jp_v2'], t),
                 'held': (fm['jp_v2'] >= 0.1 * t) if t else None}
    for key, text in PREDICTIONS.items():
        out[key]['text'] = text
    return out


def pref_rows(results):
    g = {}
    for r in results:
        b = hc.feed_base(r)
        x = g.setdefault((b['pref_id'], b['pref_name']), Counter())
        x['feeds'] += 1
        for k in ('stops', 'stops_reading', 'stops_en'):
            x[k] += r[k]
        x['feeds_most_reading'] += band(r['stops_reading'], r['stops']) == 'most'
        x['feeds_most_en'] += band(r['stops_en'], r['stops']) == 'most'
    return [{'pref_id': pid, 'pref_name': name, 'feeds': x['feeds'], 'stops': x['stops'],
             'share_reading': hc.ratio(x['stops_reading'], x['stops']), 'share_en': hc.ratio(x['stops_en'], x['stops']),
             'feeds_most_reading': x['feeds_most_reading'], 'feeds_most_en': x['feeds_most_en']}
            for (pid, name), x in sorted(g.items())]


COUNTS = ['format', 'stops', 'stops_reading', 'stops_en', 'reading_parent_only', 'en_parent_only', 'reading_kanji',
          'en_japanese', 'en_copy', 'other_languages', 'headsigns', 'headsigns_reading', 'headsigns_en']


def feed_rows(results):
    rows = []
    for r in sorted(results, key=lambda r: (hc.feed_base(r)['pref_id'], r['feed']['organization_id'],
                                            r['feed']['feed_id'])):
        row = hc.feed_base(r)
        row.update({k: r[k] for k in COUNTS})
        row.update(share_reading=hc.ratio(r['stops_reading'], r['stops']), share_en=hc.ratio(r['stops_en'], r['stops']),
                   band_reading=band(r['stops_reading'], r['stops']), band_en=band(r['stops_en'], r['stops']))
        rows.append(row)
    return rows


def totals(results):
    t = {k: sum(r[k] for r in results) for k in COUNTS if k not in ('format', 'other_languages')}
    t['share_reading'] = hc.ratio(t['stops_reading'], t['stops'])
    t['share_en'] = hc.ratio(t['stops_en'], t['stops'])
    t['share_headsigns_reading'] = hc.ratio(t['headsigns_reading'], t['headsigns'])
    t['share_headsigns_en'] = hc.ratio(t['headsigns_en'], t['headsigns'])
    return t


def markdown(summary, prefs):
    p, t = summary['predictions'], summary['totals']
    held = {True: 'held', False: 'did not hold', None: 'not scorable'}
    pct = hc.pct
    b = summary['bands']
    lines = [f'# 停留所名のよみがな・英語 / Readings and English names in Japan\'s GTFS files ({summary["as_of"]})', '',
             'GTFSデータリポジトリの有効なデータ（オープンライセンス）の現行ファイルについて、停留所（標柱、location_type 0）と行先'
             '（trip_headsign）ごとに、translations.txt によみがな（ja-Hrkt、GTFS-JPで必須）と英語（推奨）があるかを数えました。',
             'For the current file of every active, openly licensed feed in the GTFS Data Repository, each stop (location_type 0) '
             'and each destination text (trip_headsign) was checked for a kana reading (ja-Hrkt, required by GTFS-JP) and an '
             'English name (recommended) in translations.txt.', '',
             f'Feeds checked: {summary["feeds_checked"]}; skipped: ' +
             (', '.join(f'{k} {v}' for k, v in summary['skipped_by_reason'].items()) or 'none') + '.', '',
             '| | stops | with reading | with English | destinations | with reading | with English |',
             '|---|---|---|---|---|---|---|',
             f'| all feeds | {t["stops"]} | {pct(t["share_reading"])} | {pct(t["share_en"])} | {t["headsigns"]} | '
             f'{pct(t["share_headsigns_reading"])} | {pct(t["share_headsigns_en"])} |', '',
             '| feeds giving it for | none of their stops | some | at least 90% |', '|---|---|---|---|',
             f'| reading | {b["reading"]["none"]} | {b["reading"]["some"]} | {b["reading"]["most"]} |',
             f'| English | {b["en"]["none"]} | {b["en"]["some"]} | {b["en"]["most"]} |', '',
             'translations.txt: ' + ', '.join(f'{k} {v}' for k, v in summary['formats'].items()) +
             ' (gtfs = table_name/field_name rows; jp_v2 = trans_id, lang, translation).', '',
             f'Checks: readings containing kanji {t["reading_kanji"]}; English names containing kana or kanji '
             f'{t["en_japanese"]} (of which a copy of the Japanese name {t["en_copy"]}); stops without their own reading '
             f'or English whose parent station has one: {t["reading_parent_only"]} / {t["en_parent_only"]}. '
             'Other languages (feeds): ' + (', '.join(f'{k} {v}' for k, v in summary['other_languages'].items()) or 'none')
             + '.', '',
             '## 都道府県別 / By prefecture', '',
             '| 都道府県 | feeds | stops | with reading | with English | feeds ≥90% reading | feeds ≥90% English |',
             '|---|---|---|---|---|---|---|']
    for r in prefs:
        lines.append(f'| {r["pref_name"]} | {r["feeds"]} | {r["stops"]} | {pct(r["share_reading"])} | '
                     f'{pct(r["share_en"])} | {r["feeds_most_reading"]} | {r["feeds_most_en"]} |')
    lines += ['', '## 事前に記録した予測 / Predictions recorded before the run (2026-10-22)', '',
              '| | prediction | result | |', '|---|---|---|---|']
    for key in ('N1', 'N2', 'N3', 'N4'):
        x = p[key]
        res = {k: v for k, v in x.items() if k not in ('text', 'held')}
        lines.append(f'| {key} | {x["text"]} | {json.dumps(res, ensure_ascii=False)} | {held[x["held"]]} |')
    lines += ['', '限界: 停留所はレコード（標柱）単位で数えます。record_idで親の停留所（location_type 1）だけに訳を付けたデータは、'
              '標柱では「なし」になります（その数は上の parent station の値）。行先は trips.txt の trip_headsign だけで、'
              'stop_times.txt の stop_headsign は見ていません。英語の内容が正しいかは確かめていません（かな・漢字が入っているかだけ）。',
              'Limits: stops are counted per record (pole). A file that translates only the parent station (location_type 1) '
              'by record_id shows "none" on its poles (counted above as parent station). Destinations are trip_headsign in '
              'trips.txt only, not stop_headsign. Whether an English name is right is not checked, only whether it has kana '
              'or kanji in it. Names are records of fact, not judgements.', '',
              'Source: GTFS Data Repository API v2 (https://gtfs-data.jp/); each feed\'s publisher and licence are in '
              'feeds.csv. Made by MV2 of Munim, Inc. with AI agents working in MV2\'s name. Data CC BY 4.0.', '']
    return '\n'.join(lines)


def write_outputs(out_root, as_of, results, skipped, feeds_listed, generated_at):
    out = os.path.join(out_root, 'names', as_of.isoformat())
    os.makedirs(out, exist_ok=True)
    frows = feed_rows(results)
    hc.write_csv(os.path.join(out, 'feeds.csv'),
                 ['organization_id', 'feed_id', 'organization_name', 'feed_name', 'pref_id', 'pref_name', 'license'] +
                 COUNTS + ['share_reading', 'share_en', 'band_reading', 'band_en'], frows)
    prefs = pref_rows(results)
    hc.write_csv(os.path.join(out, 'prefectures.csv'), ['pref_id', 'pref_name', 'feeds', 'stops', 'share_reading',
                                                        'share_en', 'feeds_most_reading', 'feeds_most_en'], prefs)
    hc.write_csv(os.path.join(out, 'skipped.csv'), ['organization_id', 'feed_id', 'feed_name', 'reason', 'detail'],
                 skipped)
    langs = Counter(x for r in results for x in r['other_languages'].split(';') if x)
    summary = {'as_of': as_of.isoformat(), 'feeds_listed': feeds_listed, 'feeds_checked': len(results),
               'skipped_by_reason': dict(Counter(s['reason'] for s in skipped)),
               'formats': {k: v for k, v in ((k, sum(r['format'] == k for r in results)) for k in FORMATS) if v},
               'bands': {kind: {x: sum(r['band_' + kind] == x for r in frows) for x in ('none', 'some', 'most')}
                         for kind in ('reading', 'en')},
               'totals': totals(results), 'other_languages': dict(langs.most_common()),
               'predictions': predictions(results), 'most_threshold': MOST,
               'source': hc.API + '/feeds and each feed\'s files/feed.zip?rid=current',
               'generated_at': generated_at, 'by': 'MV2 of Munim, Inc. (made with AI agents working in MV2\'s name)'}
    with open(os.path.join(out, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    with open(os.path.join(out, 'names.md'), 'w', encoding='utf-8') as f:
        f.write(markdown(summary, prefs))
    return summary


def fetch(url, timeout=180):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def get_zip(f):
    try:
        return fetch(hc.zip_url(f))
    except Exception:  # noqa: BLE001 - one retry
        time.sleep(5)
        return fetch(hc.zip_url(f))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--as-of', help='YYYY-MM-DD; default: today in Japan')
    ap.add_argument('--feeds-json', help='a saved copy of the API\'s /feeds answer (default: fetch it)')
    ap.add_argument('--out', default='/out')
    ap.add_argument('--pause', type=float, default=2.0, help='seconds between downloads')
    ap.add_argument('--limit', type=int, help='download at most this many files')
    ap.add_argument('--budget-min', type=float, default=150)
    ap.add_argument('--min-feeds', type=int, default=400)
    a = ap.parse_args(argv)
    as_of = hc.iso_day(a.as_of) if a.as_of else dt.datetime.now(hc.JST).date()
    if a.feeds_json:
        with open(a.feeds_json, encoding='utf-8') as f:
            doc = json.load(f)
    else:
        doc = json.loads(fetch(hc.API + '/feeds').decode('utf-8'))
    body = doc.get('body') if isinstance(doc, dict) else doc
    feeds = [f for f in body or [] if isinstance(f, dict) and f.get('organization_id') and f.get('feed_id')]
    if len(feeds) < a.min_feeds:
        sys.exit(f'the feed list has {len(feeds)} feeds, fewer than {a.min_feeds}')
    print(f'feeds listed: {len(feeds)}', flush=True)
    results, skipped = run(feeds, as_of, get_zip, a.pause, a.limit, a.budget_min * 60,
                           log=lambda s: print(s, flush=True))
    summary = write_outputs(a.out, as_of, results, skipped, len(feeds),
                            time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
