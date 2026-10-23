# calendar_next.py - for each feed whose current file ends before the end date the GTFS Data Repository lists for it
# (class file_ends_earlier in calgap/2026-10-22/feeds.csv, from calendar_gap.py), reads the feed's entry in the
# repository API once and checks whether a later file (one that starts after the file that was read) is already
# published and covers the days from the day after the read file's own last day through the listed end date. The
# listed date is the end of the latest file the repository holds, which can be a later file not yet in force, so a
# gap found by calendar_gap.py can be no gap at all. Only the files' from_date and to_date as the repository gives
# them are used; the later files' own calendars are not read. Standard library only.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import argparse
import csv
import datetime as dt
import json
import os
import re
import time
import urllib.parse
import urllib.request

API = 'https://api.gtfs-data.jp/v2'
UA = 'GTFS calendar-gap check - MV2 of Munim, Inc. (mv2@munimtech.com)'
BASE = ['organization_id', 'feed_id', 'organization_name', 'feed_name', 'pref_id', 'pref_name', 'license']
GAP = ['listed_end', 'file_start', 'file_end', 'gap_days', 'hidden', 'file_ended']
COLUMNS = BASE + GAP + ['status', 'class', 'later_files', 'later_from', 'covered_to', 'uncovered_from',
                        'uncovered_days', 'current_from', 'current_to', 'is_discontinued', 'discontinued_date',
                        'memo_ended', 'current_memo']
CLASSES = ['later_file_covers', 'later_file_partial', 'no_later_file', 'api_failed']
ENDED = re.compile('廃止|休止|運休|運行終了|運行を終了')
MEMO_CHARS = 80


def read_csv(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, columns):
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def day(v):
    try:
        return dt.date.fromisoformat((v or '').strip())
    except ValueError:
        return None


def to_int(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0


def clean(text):
    """One line, no table-breaking bars."""
    return ' '.join(str(text or '').replace('|', '／').split())


def fetch_body(org, feed):
    """The body of the feed's API entry, or None."""
    q = lambda s: urllib.parse.quote(s, safe='')  # noqa: E731
    req = urllib.request.Request(f'{API}/organizations/{q(org)}/feeds/{q(feed)}', headers={'User-Agent': UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode('utf-8'))
    except Exception:  # noqa: BLE001 - recorded as api_failed
        return None
    return data.get('body') if isinstance(data, dict) and data.get('code') == 200 else None


def check(row, body):
    """One output row for one file_ends_earlier feed and its API body (None if the request failed)."""
    out = {x: row.get(x, '') for x in BASE + GAP}
    out.update({x: '' for x in COLUMNS if x not in out})
    if body is None:
        out.update({'status': 'api_failed', 'class': 'api_failed'})
        return out
    start, end, listed = day(row.get('file_start')), day(row.get('file_end')), day(row.get('listed_end'))
    files = [f for f in body.get('gtfs_files') or [] if day(f.get('from_date')) and day(f.get('to_date'))]
    cur = next((f for f in files if f.get('rid') == 'current'), None)
    later = sorted((f for f in files if start is None or day(f['from_date']) > start),
                   key=lambda f: (day(f['from_date']), day(f['to_date'])))
    covered = end
    for f in later:
        if day(f['from_date']) <= covered + dt.timedelta(days=1):
            covered = max(covered, day(f['to_date']))
    out.update({'status': 'ok', 'later_files': len(later), 'later_from': later[0]['from_date'] if later else '',
                'covered_to': covered.isoformat(), 'current_from': cur['from_date'] if cur else '',
                'current_to': cur['to_date'] if cur else '',
                'is_discontinued': 'yes' if body.get('is_discontinued') else 'no',
                'discontinued_date': body.get('discontinued_date') or '',
                'memo_ended': 'yes' if cur and ENDED.search(cur.get('memo') or '') else 'no',
                'current_memo': clean(cur.get('memo'))[:MEMO_CHARS] if cur else ''})
    if covered >= listed:
        out.update({'class': 'later_file_covers', 'uncovered_days': 0})
        return out
    first = covered + dt.timedelta(days=1)
    after = [day(f['from_date']) for f in later if day(f['from_date']) > first]
    last = min([listed] + [d - dt.timedelta(days=1) for d in after])
    out.update({'class': 'later_file_partial' if later else 'no_later_file', 'uncovered_from': first.isoformat(),
                'uncovered_days': (last - covered).days})
    return out


def summarise(rows, checked_on):
    def by_class(rs):
        return {c: sum(r['class'] == c for r in rs) for c in CLASSES}
    return {'checked_on': checked_on, 'feeds': len(rows), 'classes': by_class(rows),
            'hidden': by_class([r for r in rows if r['hidden'] == 'yes']),
            'over_7_days': by_class([r for r in rows if to_int(r['gap_days']) > 7]),
            'file_ended': by_class([r for r in rows if r['file_ended'] == 'yes']),
            'memo_ended': sum(r['memo_ended'] == 'yes' for r in rows),
            'marked_discontinued': sum(r['is_discontinued'] == 'yes' for r in rows),
            'no_later_file_memo_ended': sum(r['class'] == 'no_later_file' and r['memo_ended'] == 'yes' for r in rows),
            'generated_at': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'by': "MV2 of Munim, Inc. (made with AI agents working in MV2's name)"}


def report(rows, s):
    c, h = s['classes'], s['hidden']
    lines = [f'# 期限より早く終わるファイルに後続のファイルはあるか / Do the files that end early have a later file? '
             f'({s["checked_on"]})', '',
             '現行ファイルの最後の運行日が掲載上の期限より前のデータ（calendar_gap.py の file_ends_earlier）について、'
             'リポジトリのAPIで、読んだファイルより後に始まるファイルがすでに公開され、その翌日から掲載上の期限まで'
             'つながっているかを確かめました。掲載上の期限は、まだ有効になっていない後続のファイルの期限であることがあります。',
             'For each feed whose current file runs out before the end date the repository lists (class '
             'file_ends_earlier in calendar_gap.py), the repository API was read once to see whether a later file is '
             'already published and covers, without a break, the days from the day after the read file\'s own last day '
             'to the listed end date. The listed date can be the end of a later file that is not in force yet.', '',
             f'Feeds checked: {s["feeds"]}. A later file covers the rest: {c["later_file_covers"]}; a later file '
             f'leaves a break: {c["later_file_partial"]}; no later file: {c["no_later_file"]}; API request failed: '
             f'{c["api_failed"]}.', '',
             f'Of the {sum(h.values())} feeds called hidden by calendar_gap.py: {h["later_file_covers"]} covered by a '
             f'later file, {h["later_file_partial"]} with a break, {h["no_later_file"]} with no later file.', '',
             f'Current-file note (memo) mentions abolition or suspension (廃止・休止・運休・運行終了): {s["memo_ended"]} '
             f'feeds, {s["no_later_file_memo_ended"]} of them with no later file. Marked discontinued in the '
             f'repository: {s["marked_discontinued"]}.', '',
             '## 後続のファイルがない、またはつながらないデータ / No later file, or a break', '',
             '| organization | feed | pref | listed end | file end | uncovered from | days | later files | '
             'marked discontinued | memo |', '|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        if r['class'] in ('no_later_file', 'later_file_partial'):
            lines.append(f'| {r["organization_name"]} | {r["feed_name"]} | {r["pref_name"]} | {r["listed_end"]} | '
                         f'{r["file_end"]} | {r["uncovered_from"]} | {r["uncovered_days"]} | {r["later_files"]} | '
                         f'{r["is_discontinued"]} | {r["current_memo"]} |')
    lines += ['', '## 後続のファイルが残りを埋めるデータ / A later file covers the rest', '',
              '| organization | feed | pref | file end | later file from | covered to |', '|---|---|---|---|---|---|']
    for r in rows:
        if r['class'] == 'later_file_covers':
            lines.append(f'| {r["organization_name"]} | {r["feed_name"]} | {r["pref_name"]} | {r["file_end"]} | '
                         f'{r["later_from"]} | {r["covered_to"]} |')
    lines += ['', 'Limits: only the from_date and to_date the repository gives for each file are used; the later '
              'files\' own calendars are not read, so a later file may itself end early. A file counts as later when it '
              'starts after the first day of the file that was read. The API was read on the day above, after the '
              'files were read on 2026-10-22, so a later file published in between also counts. A day with no file in '
              'force is not proof that no bus runs (a route can be seasonal or have ended), and a note is the '
              'publisher\'s text, shown as given. Place names in the data are records of fact, not judgements.', '',
              f'Generated {s["generated_at"]}. Source: GTFS Data Repository (https://gtfs-data.jp/); each feed\'s '
              'publisher and licence are in feeds.csv. Made by MV2 of Munim, Inc. with AI agents working in MV2\'s '
              'name. Data CC BY 4.0.']
    return '\n'.join(lines) + '\n'


def main(argv=None):
    ap = argparse.ArgumentParser(description='Later files for feeds whose current file ends early.')
    ap.add_argument('--gaps', required=True, help='calgap/2026-10-22/feeds.csv')
    ap.add_argument('--checked-on', default=dt.datetime.now(dt.timezone.utc).date().isoformat())
    ap.add_argument('--pause', type=float, default=1.0)
    ap.add_argument('--out', required=True)
    a = ap.parse_args(argv)
    rows = []
    for i, g in enumerate(r for r in read_csv(a.gaps) if r.get('class') == 'file_ends_earlier'):
        if i and a.pause:
            time.sleep(a.pause)
        rows.append(check(g, fetch_body(g['organization_id'], g['feed_id'])))
    s = summarise(rows, a.checked_on)
    os.makedirs(a.out, exist_ok=True)
    write_csv(os.path.join(a.out, 'feeds.csv'), rows, COLUMNS)
    with open(os.path.join(a.out, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(s, f, ensure_ascii=False, indent=1)
    with open(os.path.join(a.out, 'next.md'), 'w', encoding='utf-8') as f:
        f.write(report(rows, s))
    print(json.dumps(s, ensure_ascii=False))
    return s


if __name__ == '__main__':
    main()
