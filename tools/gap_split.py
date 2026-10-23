# gap_split.py - from a leads.csv of tools/lead_history.py, splits the new-period files that start in a date range
# into those that start on one day of the year (April 1, the first day of Japan's fiscal year, by default) and the
# rest, and counts for each how many were published after their start date ('late') and how many of those left no
# valid file on the start date ('gap': no earlier file still covered it) rather than the old timetable ('stale').
# The 2026-10-16 census (leads/2026-10-16/) found April-1 files late less often than others but, when late, usually
# with no valid file, because the file before them mostly ended on March 31. This tool reproduces those counts and
# scores the predictions for 2027-04-01 in PREDICTIONS (leads/predictions-2027-04-01.md) on a later census.
# p-values are kept to 6 significant figures and shown to 3, so a very small p is not printed as 0.
# No network; standard library only.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import argparse
import csv
import datetime as dt
import json
import math
import os

# Fixed on 2026-10-23, before any file starting on 2027-04-01 exists. Scored with
# --start 2026-10-01 --end 2027-04-01 --day 04-01 --predictions on a census taken on or after 2027-07-01.
PREDICTIONS = {
    'G1': 'Of the new-period files starting on 2027-04-01, between 6% and 18% left no valid file on that day (gap).',
    'G2': 'That share is higher than for the new-period files starting on other days from 2026-10-01 to 2027-03-31 '
          '(one-sided Fisher exact test, p < 0.05).',
    'G3': 'Of the files starting on 2027-04-01 that were published after their start date, at least 40% left no valid '
          'file on that day.',
}
GAP_COLUMNS = ['group', 'organization_id', 'feed_id', 'published_date', 'from_date', 'lead_days']


def day(v):
    try:
        return dt.date.fromisoformat((v or '').strip()[:10])
    except ValueError:
        return None


def read_csv(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def share(a, b):
    return round(a / b, 4) if b else None


def fisher_greater(a, b, c, d):
    """One-sided Fisher exact p that a/(a+b) is greater than c/(c+d), to 6 significant figures."""
    n1, n2, k = a + b, c + d, a + c
    if not n1 or not n2:
        return None
    lo, hi = max(0, k - n2), min(k, n1)
    num = sum(math.comb(n1, x) * math.comb(n2, k - x) for x in range(max(a, lo), hi + 1))
    return float(f'{num / math.comb(n1 + n2, k):.6g}')


def pval(x):
    return '' if x is None else f'{x:.3g}'


def group_stats(rows):
    n = len(rows)
    late = [r for r in rows if int(r['lead_days']) < 0]
    gaps = [r for r in late if r.get('late_kind') == 'gap']
    return {'n': n, 'late': len(late), 'gap': len(gaps), 'stale': len(late) - len(gaps),
            'late_share': share(len(late), n), 'gap_share': share(len(gaps), n),
            'gap_of_late': share(len(gaps), len(late)),
            'gap_feeds': len({(r['organization_id'], r['feed_id']) for r in gaps}),
            'gap_publishers': len({r['organization_id'] for r in gaps})}


def tests(d, o):
    return {'gap_p_greater': fisher_greater(d['gap'], d['n'] - d['gap'], o['gap'], o['n'] - o['gap']),
            'late_p_less': fisher_greater(o['late'], o['n'] - o['late'], d['late'], d['n'] - d['late'])}


def split(rows, start, end, md):
    """leads.csv rows -> (rows in range starting on the day md, the other rows in range)."""
    on, off = [], []
    for r in rows:
        a = day(r.get('from_date'))
        if a is None or not (start <= a <= end):
            continue
        (on if a.strftime('%m-%d') == md else off).append(r)
    return on, off


def summarise(rows, start, end, md, predictions=False):
    on, off = split(rows, start, end, md)
    d, o = group_stats(on), group_stats(off)
    years = {}
    for i, rs in enumerate((on, off)):
        for r in rs:
            years.setdefault(r['from_date'][:4], ([], []))[i].append(r)
    by_year = {y: {'day': group_stats(a), 'other': group_stats(b)} for y, (a, b) in sorted(years.items())}
    s = {'range': [start.isoformat(), end.isoformat()], 'day': md, 'groups': {'day': d, 'other': o},
         'tests': tests(d, o), 'by_start_year': by_year}
    if predictions:
        p = s['tests']['gap_p_greater']
        vals = {'G1': (d['gap_share'], d['gap_share'] is not None and 0.06 <= d['gap_share'] <= 0.18),
                'G2': (p, p is not None and p < 0.05),
                'G3': (d['gap_of_late'], d['gap_of_late'] is not None and d['gap_of_late'] >= 0.40)}
        s['predictions'] = {k: {'text': PREDICTIONS[k], 'value': v, 'held': h} for k, (v, h) in vals.items()}
    s['generated_at'] = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    s['by'] = "MV2 of Munim, Inc. (made with AI agents working in MV2's name)"
    return s, on, off


def pct(x):
    return '' if x is None else f'{100 * x:.1f}%'


def report(s, source):
    d, o, t = s['groups']['day'], s['groups']['other'], s['tests']
    lines = [f'# 開始日が{s["day"]}のファイルとそれ以外 / Files starting on {s["day"]} against other days '
             f'({s["range"][0]} to {s["range"][1]})', '',
             f'Source: `{source}` (tools/lead_history.py). A file is late when it was published after its start date; '
             'a late file is a gap when no earlier file still covered its start date (no valid file that day), and '
             'stale when one did (the old timetable stayed in force).', '',
             '| group | files | late | gap | stale | late share | gap share | gap of late | feeds with a gap | '
             'publishers with a gap |', '|---|---|---|---|---|---|---|---|---|---|']
    for name, g in (('day', d), ('other', o)):
        lines.append(f'| {name} | {g["n"]} | {g["late"]} | {g["gap"]} | {g["stale"]} | {pct(g["late_share"])} | '
                     f'{pct(g["gap_share"])} | {pct(g["gap_of_late"])} | {g["gap_feeds"]} | {g["gap_publishers"]} |')
    lines += ['', f'- one-sided Fisher exact p, gap share of {s["day"]} greater: {pval(t["gap_p_greater"])}',
              f'- one-sided Fisher exact p, late share of {s["day"]} smaller: {pval(t["late_p_less"])}', '',
              '## 開始年ごと / By start year', '',
              '| year | day files | day gap | day gap share | other files | other gap | other gap share |',
              '|---|---|---|---|---|---|---|']
    for y, v in s['by_start_year'].items():
        a, b = v['day'], v['other']
        lines.append(f'| {y} | {a["n"]} | {a["gap"]} | {pct(a["gap_share"])} | {b["n"]} | {b["gap"]} | '
                     f'{pct(b["gap_share"])} |')
    if 'predictions' in s:
        lines += ['', '## 事前に記録した予測 / Predictions recorded in advance', '']
        for k, p in s['predictions'].items():
            v = p['value']
            shown = '' if v is None else (f'p = {pval(v)}' if k == 'G2' else pct(v))
            lines.append(f'- {k}: {p["text"]} Result: {shown}, {"held" if p["held"] else "did not hold"}.')
    lines += ['', 'Limits: files are not independent (one publisher often publishes several feeds together), so the '
              'p-values are, if anything, too small. Only files that were eventually published are counted: a feed '
              'whose next file never came is a lapse in the census but has no row here. Publication dates are the '
              'repository\'s. Lead times are the publishers\' and are reported as facts, not judgements.', '',
              f'Generated {s["generated_at"]}. Source: GTFS Data Repository API v2 (https://gtfs-data.jp/). Made by MV2 '
              'of Munim, Inc. with AI agents working in MV2\'s name. Data CC BY 4.0.']
    return '\n'.join(lines) + '\n'


def main(argv=None):
    ap = argparse.ArgumentParser(description='Late and gap shares of files starting on one day of the year.')
    ap.add_argument('--leads', required=True, help='leads.csv of tools/lead_history.py')
    ap.add_argument('--start', required=True, help='first from_date in range (YYYY-MM-DD)')
    ap.add_argument('--end', required=True, help='last from_date in range (YYYY-MM-DD)')
    ap.add_argument('--day', default='04-01', help='the day of the year to split on (MM-DD)')
    ap.add_argument('--predictions', action='store_true', help='score G1-G3 (for the 2027-04-01 range)')
    ap.add_argument('--out', required=True)
    a = ap.parse_args(argv)
    start, end = day(a.start), day(a.end)
    if not (start and end):
        ap.error('--start and --end must be YYYY-MM-DD')
    s, on, off = summarise(read_csv(a.leads), start, end, a.day, a.predictions)
    os.makedirs(a.out, exist_ok=True)
    gap_rows = [dict(r, group=g) for g, rs in (('day', on), ('other', off)) for r in rs
                if int(r['lead_days']) < 0 and r.get('late_kind') == 'gap']
    with open(os.path.join(a.out, 'gaps.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=GAP_COLUMNS, extrasaction='ignore')
        w.writeheader()
        w.writerows(gap_rows)
    with open(os.path.join(a.out, 'gaps.json'), 'w', encoding='utf-8') as f:
        json.dump(s, f, ensure_ascii=False, indent=1)
    with open(os.path.join(a.out, 'gaps.md'), 'w', encoding='utf-8') as f:
        f.write(report(s, os.path.basename(a.leads)))
    print(json.dumps(s, ensure_ascii=False))
    return s


if __name__ == '__main__':
    main()
