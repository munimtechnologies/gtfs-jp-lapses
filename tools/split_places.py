# split_places.py - split the last-bus census's per-place table (lastbus/<as-of>/places.csv, one row per place, too
# large for one file in the repository) into one file per prefecture: places/<pref_id two digits>.csv, with a further
# split into <pp>-1.csv, <pp>-2.csv ... only if one prefecture would pass the size limit. The table comes from a re-read
# of the same feeds by tools/last_bus.py; a feed is kept only if its per-feed row in the re-read is identical, in every
# column, to its row in the published census (lastbus/<as-of>/feeds.csv), so the split matches the published figures.
# Feeds whose row changed are left out and listed in changed.csv. Standard library only.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import argparse
import csv
import io
import json
import os
import time

csv.field_size_limit(1 << 24)
LIMIT = 1_900_000  # bytes per file; the repository's publish step refuses files over 2,000,000
KEY = ('organization_id', 'feed_id')
INDEX_COLUMNS = ['pref_id', 'file', 'feeds', 'rows', 'bytes']
CHANGED_COLUMNS = ['organization_id', 'feed_id', 'organization_name', 'feed_name', 'pref_id', 'reason', 'columns']


def read_csv(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def key(r):
    return tuple(r.get(k, '') for k in KEY)


def compare(published, rerun):
    """Return (kept feed keys, changed rows) comparing every column the two per-feed tables share."""
    new = {key(r): r for r in rerun}
    kept, changed = set(), []
    for p in published:
        r = new.get(key(p))
        base = {k: p.get(k, '') for k in CHANGED_COLUMNS[:5]}
        if r is None:
            changed.append({**base, 'reason': 'missing_in_rerun', 'columns': ''})
            continue
        diff = [c for c in p if c in r and p[c] != r[c]]
        if diff:
            changed.append({**base, 'reason': 'row_differs', 'columns': ' '.join(diff)})
        elif p.get('status') != 'ok':
            changed.append({**base, 'reason': 'not_read', 'columns': ''})
        else:
            kept.add(key(p))
    return kept, changed


def pref_code(v):
    try:
        return f'{int(v):02d}'
    except (TypeError, ValueError):
        return '00'


def to_csv(columns, rows_):
    buf = io.StringIO(newline='')
    w = csv.DictWriter(buf, fieldnames=columns, extrasaction='ignore', lineterminator='\r\n')
    w.writeheader()
    w.writerows(rows_)
    return '﻿' + buf.getvalue()


def chunks(columns, rows_, limit):
    """Split rows into consecutive parts whose CSV text (with header and BOM) stays under limit bytes."""
    parts, cur, size = [], [], len(to_csv(columns, []).encode('utf-8'))
    head = size
    for r in rows_:
        n = len(to_csv(columns, [r]).encode('utf-8')) - head
        if cur and size + n > limit:
            parts.append(cur)
            cur, size = [], head
        cur.append(r)
        size += n
    if cur or not parts:
        parts.append(cur)
    return parts


def split(places, columns, kept, limit=LIMIT):
    """Return {file name: rows} and index rows, one prefecture (or part) per file, in table order."""
    by = {}
    for r in places:
        if key(r) in kept:
            by.setdefault(pref_code(r.get('pref_id')), []).append(r)
    files, index = {}, []
    for code in sorted(by):
        parts = chunks(columns, by[code], limit)
        for i, part in enumerate(parts, 1):
            name = f'{code}.csv' if len(parts) == 1 else f'{code}-{i}.csv'
            files[name] = part
            index.append({'pref_id': code, 'file': name, 'feeds': len({key(r) for r in part}), 'rows': len(part),
                          'bytes': len(to_csv(columns, part).encode('utf-8'))})
    return files, index


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--places', required=True, help='places.csv from the re-read')
    ap.add_argument('--rerun-feeds', required=True, help='feeds.csv from the re-read')
    ap.add_argument('--published-feeds', required=True, help='the published lastbus/<as-of>/feeds.csv')
    ap.add_argument('--out', required=True, help='folder for <pp>.csv, index.csv, changed.csv, split.json')
    ap.add_argument('--limit', type=int, default=LIMIT)
    a = ap.parse_args(argv)
    with open(a.places, encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        columns, places = reader.fieldnames, list(reader)
    published = read_csv(a.published_feeds)
    kept, changed = compare(published, read_csv(a.rerun_feeds))
    files, index = split(places, columns, kept, a.limit)
    os.makedirs(a.out, exist_ok=True)
    for name, part in files.items():
        with open(os.path.join(a.out, name), 'w', encoding='utf-8', newline='') as f:
            f.write(to_csv(columns, part))
    with open(os.path.join(a.out, 'index.csv'), 'w', encoding='utf-8', newline='') as f:
        f.write(to_csv(INDEX_COLUMNS, index))
    with open(os.path.join(a.out, 'changed.csv'), 'w', encoding='utf-8', newline='') as f:
        f.write(to_csv(CHANGED_COLUMNS, changed))
    s = {'published_feeds': len(published), 'kept_feeds': len(kept), 'changed_feeds': len(changed),
         'changed_by_reason': {}, 'rows_in': len(places), 'rows_out': sum(len(p) for p in files.values()),
         'files': len(files), 'largest_bytes': max((i['bytes'] for i in index), default=0), 'limit': a.limit,
         'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
         'by': "MV2 of Munim, Inc. (made with AI agents working in MV2's name)"}
    for c in changed:
        s['changed_by_reason'][c['reason']] = s['changed_by_reason'].get(c['reason'], 0) + 1
    with open(os.path.join(a.out, 'split.json'), 'w', encoding='utf-8') as f:
        json.dump(s, f, ensure_ascii=False, indent=1)
    print(json.dumps(s, ensure_ascii=False))
    return s


if __name__ == '__main__':
    main()
