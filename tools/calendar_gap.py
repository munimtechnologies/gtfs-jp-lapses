# calendar_gap.py - compares, for each feed, the end date the GTFS Data Repository lists for it (the end_date column of
# health/2026-10-22/feeds.csv: the expiry list of 2026-10-22, else the lapse census of 2026-10-16) with the last day its
# current file itself covers (cover_end in lastbus/2026-10-22/feeds.csv: the span of calendar.txt and
# calendar_dates.txt, narrowed to feed_info's dates where given). A file whose own dates end before the listed date
# has no service after its own end, while an expiry warning that reads the listed date sees nothing wrong ("hidden").
# No new downloads. Descriptive only: no predictions were recorded, and some of these files had already been seen in
# the last-bus census. Standard library only.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import argparse
import csv
import datetime as dt
import json
import os
from collections import Counter

WARN_DAYS = 60
BASE = ['organization_id', 'feed_id', 'organization_name', 'feed_name', 'pref_id', 'pref_name', 'license']
COLUMNS = BASE + ['listed_end', 'listed_source', 'file_start', 'file_end', 'gap_days', 'class', 'listed_days_left',
                  'file_days_left', 'file_ended', 'hidden']
CLASSES = ['same', 'file_ends_earlier', 'file_ends_later', 'no_file_dates', 'no_listed_date', 'not_read']


def read_csv(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, columns):
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def key(r):
    return (r['organization_id'], r['feed_id'])


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


def build(health, lastbus, as_of):
    """One row per feed of the health table, in its order."""
    lb = {key(r): r for r in lastbus}
    today = day(as_of)
    rows = []
    for h in health:
        row = {x: h.get(x, '') for x in BASE}
        listed, l = day(h.get('end_date')), lb.get(key(h))
        row.update({'listed_end': listed.isoformat() if listed else '', 'listed_source': h.get('end_date_source', ''),
                    'file_start': '', 'file_end': '', 'gap_days': '', 'listed_days_left': '', 'file_days_left': '',
                    'file_ended': '', 'hidden': ''})
        if listed:
            row['listed_days_left'] = (listed - today).days
        if not l or l.get('status') != 'ok':
            row['class'] = 'not_read'
            rows.append(row)
            continue
        start, end = day(l.get('cover_start')), day(l.get('cover_end'))
        row['file_start'] = start.isoformat() if start else ''
        if not end:
            row['class'] = 'no_file_dates'
            rows.append(row)
            continue
        row['file_end'] = end.isoformat()
        row['file_days_left'] = (end - today).days
        row['file_ended'] = 'yes' if end < today else 'no'
        if not listed:
            row['class'] = 'no_listed_date'
            rows.append(row)
            continue
        gap = (listed - end).days
        row['gap_days'] = gap
        row['class'] = 'same' if gap == 0 else ('file_ends_earlier' if gap > 0 else 'file_ends_later')
        hidden = gap > 0 and row['listed_days_left'] > WARN_DAYS and row['file_days_left'] <= WARN_DAYS
        row['hidden'] = 'yes' if hidden else 'no'
        rows.append(row)
    return rows


def median(xs):
    """The lower median (the smaller middle value for an even count)."""
    xs = sorted(xs)
    return xs[(len(xs) - 1) // 2] if xs else None


def summarise(rows, as_of):
    early = [r for r in rows if r['class'] == 'file_ends_earlier']
    gaps = [r['gap_days'] for r in early]
    return {'as_of': as_of, 'warn_days': WARN_DAYS, 'feeds': len(rows),
            'classes': {c: sum(r['class'] == c for r in rows) for c in CLASSES},
            'earlier': {'feeds': len(early), 'over_7_days': sum(g > 7 for g in gaps),
                        'over_30_days': sum(g > 30 for g in gaps), 'median_gap_days': median(gaps),
                        'max_gap_days': max(gaps) if gaps else None},
            'hidden': sum(r['hidden'] == 'yes' for r in rows),
            'file_ended_while_listed_current': sum(r['file_ended'] == 'yes' and r['listed_days_left'] != ''
                                                   and r['listed_days_left'] >= 0 for r in rows),
            'listed_sources': dict(sorted(Counter(r['listed_source'] for r in rows).items())),
            'generated_at': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'by': "MV2 of Munim, Inc. (made with AI agents working in MV2's name)"}


def report(rows, s):
    c, e = s['classes'], s['earlier']
    lines = [f'# 掲載上の期限とファイル自体の期限 / Listed end date against the file\'s own dates ({s["as_of"]})', '',
             'GTFSデータリポジトリが各データについて示す期限（掲載上の期限）と、現行ファイルの calendar.txt・calendar_dates.txt '
             '（feed_info.txt があればその期間で絞ったもの）が実際に含む最後の日を比べました。新しいダウンロードはしていません。',
             'For each feed, the end date the GTFS Data Repository lists is compared with the last day the current file '
             'itself covers (calendar.txt and calendar_dates.txt, narrowed to feed_info.txt where given). No new '
             'downloads.', '',
             f'Feeds: {s["feeds"]}. Same end: {c["same"]}; file ends earlier: {c["file_ends_earlier"]}; file ends '
             f'later: {c["file_ends_later"]}; no readable file dates: {c["no_file_dates"]}; no listed date: '
             f'{c["no_listed_date"]}; not read: {c["not_read"]}.', '',
             f'File ends earlier than listed: {e["feeds"]} feeds; by more than 7 days {e["over_7_days"]}, by more than 30 '
             f'days {e["over_30_days"]}; median gap {e["median_gap_days"]} days, largest {e["max_gap_days"]}.', '',
             f'Hidden (the listed date is more than {s["warn_days"]} days away, but the file\'s own dates end within '
             f'{s["warn_days"]} days or have already ended): {s["hidden"]}. Files whose own dates had already ended on '
             f'{s["as_of"]} while the listed date had not: {s["file_ended_while_listed_current"]}.', '',
             '## Feeds whose file ends more than 7 days before the listed date', '',
             '| organization | feed | pref | listed end | file end | gap (days) | hidden |', '|---|---|---|---|---|---|---|']
    for r in sorted((r for r in rows if r['class'] == 'file_ends_earlier' and r['gap_days'] > 7),
                    key=lambda r: (-r['gap_days'], r['organization_id'], r['feed_id'])):
        lines.append(f'| {r["organization_name"]} | {r["feed_name"]} | {r["pref_name"]} | {r["listed_end"]} | '
                     f'{r["file_end"]} | {r["gap_days"]} | {r["hidden"]} |')
    lines += ['', 'Limits: descriptive only; no predictions were recorded, and some of these files had already been '
              'seen in the last-bus census. The listed date comes from the expiry list of 2026-10-22 where the feed is on '
              'it, else from the lapse census of 2026-10-16, and the file was read on 2026-10-22. "No readable file '
              'dates" can mean dates in an unexpected format rather than a missing calendar. A gap is a sign to check, '
              'not proof of a mistake. Place names in the data are records of fact, not judgements.', '',
              f'Generated {s["generated_at"]}. Source: GTFS Data Repository (https://gtfs-data.jp/); each feed\'s '
              'publisher and licence are in feeds.csv. Made by MV2 of Munim, Inc. with AI agents working in MV2\'s '
              'name. Data CC BY 4.0.']
    return '\n'.join(lines) + '\n'


def main(argv=None):
    ap = argparse.ArgumentParser(description='Listed end date against the file\'s own dates.')
    ap.add_argument('--health', required=True, help='health/2026-10-22/feeds.csv')
    ap.add_argument('--lastbus', required=True, help='lastbus/2026-10-22/feeds.csv')
    ap.add_argument('--as-of', default='2026-10-22')
    ap.add_argument('--out', required=True)
    a = ap.parse_args(argv)
    rows = build(read_csv(a.health), read_csv(a.lastbus), a.as_of)
    s = summarise(rows, a.as_of)
    os.makedirs(a.out, exist_ok=True)
    write_csv(os.path.join(a.out, 'feeds.csv'), rows, COLUMNS)
    with open(os.path.join(a.out, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(s, f, ensure_ascii=False, indent=1)
    with open(os.path.join(a.out, 'calendar_gap.md'), 'w', encoding='utf-8') as f:
        f.write(report(rows, s))
    print(json.dumps(s, ensure_ascii=False))
    return s


if __name__ == '__main__':
    main()
