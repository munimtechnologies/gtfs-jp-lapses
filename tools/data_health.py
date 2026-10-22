# data_health.py - one row per feed that joins the censuses already published in this repository, with no new
# downloads: the expiry list (watch/<date>/expiring.csv), the lapse census (data/2026-10-16/feeds.csv), the holiday
# census (holidays/2026-10-22/feeds.csv) and the stop-name census (names/2026-10-22/feeds.csv). Each feed gets four
# checks, each ok / flag / n/a: expiry (on the expiry list, i.e. expired or ending within 60 days), holidays (the
# ordinary timetable on at least one holiday or New Year day still to come), readings (a kana reading for under 90% of
# its stops) and English (an English name for under 90% of its stops; GTFS-JP v4.0 recommends English, it does not
# require it). The feeds are those whose current file the holiday or the stop-name census read on 2026-10-22 (active,
# openly licensed). Two predictions (PREDICTIONS) were fixed before the joined table was first made; they are scored
# in summary.json. Standard library only.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import argparse
import csv
import datetime as dt
import json
import math
import os
import re
from collections import Counter, defaultdict

MOST = 0.9
# The classes of holiday_check.py that say what a reader of the file sees on a day; 'shown' = the ordinary timetable.
GROUPS = {'ordinary': 'shown', 'ordinary_std': 'shown', 'no_service': 'encoded', 'sunday': 'encoded',
          'saturday': 'encoded', 'special': 'encoded'}
DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
CHECKS = ['expiry', 'holidays', 'readings', 'english']
REQUIRED = ['expiry', 'holidays', 'readings']
BASE = ['organization_id', 'feed_id', 'organization_name', 'feed_name', 'pref_id', 'pref_name', 'license']
COLUMNS = BASE + ['end_date', 'end_date_source', 'days_left', 'expiry', 'expiry_status', 'past_lapses', 'lapsed_days',
                  'longest_lapse_days', 'upcoming_ordinary', 'upcoming_applicable', 'holidays', 'stops',
                  'stops_reading', 'readings', 'stops_en', 'english', 'flags_required', 'all_ok']
# Fixed on 2026-10-22, before the joined table was first made (each census had only been read on its own).
PREDICTIONS = {
    'D1': 'Among feeds with a lapse-census row and a holiday check, feeds with at least one past lapse have a holiday '
          'flag more often than feeds with none (one-sided Fisher exact test, p < 0.05).',
    'D2': 'Among feeds with a holiday check and an English check, feeds whose English check is flagged have a holiday '
          'flag more often than feeds whose English check is ok (one-sided Fisher exact test, p < 0.05).',
}


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


def to_int(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0


def ratio(k, n):
    return round(k / n, 3) if n else None


def fisher_greater(a, b, c, d):
    """One-sided Fisher exact p that the first row (a flagged of a + b) has the higher flagged share than c of c + d."""
    n1, k, n = a + b, a + c, a + b + c + d
    if not n1 or n1 == n:
        return None
    hits = sum(math.comb(k, x) * math.comb(n - k, n1 - x) for x in range(a, min(k, n1) + 1))
    return hits / math.comb(n, n1)


def holiday_counts(row, as_of):
    """(days showing the ordinary timetable, applicable days) among the holiday and New Year days from as_of on."""
    days = [c for c in row if c and DATE.match(c) and c >= as_of]
    return sum(GROUPS.get(row[c]) == 'shown' for c in days), sum(row[c] in GROUPS for c in days)


def share_check(k, n):
    if not n:
        return 'n/a'
    return 'ok' if k / n >= MOST else 'flag'


def build(lapses, watch, holidays, names, as_of):
    lap, wat = {key(r): r for r in lapses}, {key(r): r for r in watch}
    hol, nam = {key(r): r for r in holidays}, {key(r): r for r in names}
    keys = sorted(set(hol) | set(nam), key=lambda k: (to_int((nam.get(k) or hol[k]).get('pref_id')), k))
    day = dt.date.fromisoformat(as_of)
    rows = []
    for k in keys:
        w, l, h, n = wat.get(k), lap.get(k), hol.get(k), nam.get(k)
        base = n or h
        row = {x: base.get(x, '') for x in BASE}
        end, src = '', ''
        if w:
            end, src = w.get('latest_feed_end_date', ''), 'watch'
        elif l and l.get('list_end_date'):
            end, src = l['list_end_date'], 'census'
        try:
            days_left = (dt.date.fromisoformat(end) - day).days
        except ValueError:
            days_left = ''
        row.update({'end_date': end, 'end_date_source': src, 'days_left': days_left,
                    'expiry': 'flag' if w else 'ok', 'expiry_status': w.get('status', '') if w else ''})
        for col in ('past_lapses', 'lapsed_days', 'longest_lapse_days'):
            row[col] = to_int(l.get('lapses' if col == 'past_lapses' else col)) if l else ''
        if h:
            shown, applicable = holiday_counts(h, as_of)
            row.update({'upcoming_ordinary': shown, 'upcoming_applicable': applicable,
                        'holidays': ('flag' if shown else 'ok') if applicable else 'n/a'})
        else:
            row.update({'upcoming_ordinary': '', 'upcoming_applicable': '', 'holidays': 'n/a'})
        if n:
            stops, reading, en = to_int(n.get('stops')), to_int(n.get('stops_reading')), to_int(n.get('stops_en'))
            row.update({'stops': stops, 'stops_reading': reading, 'readings': share_check(reading, stops),
                        'stops_en': en, 'english': share_check(en, stops)})
        else:
            row.update({'stops': '', 'stops_reading': '', 'readings': 'n/a', 'stops_en': '', 'english': 'n/a'})
        row['flags_required'] = sum(row[c] == 'flag' for c in REQUIRED)
        row['all_ok'] = 'yes' if all(row[c] == 'ok' for c in CHECKS) else 'no'
        rows.append(row)
    return rows


def two_by_two(rows, use, first, flagged):
    """Counts [flagged, all] for the rows where first() holds and for the rest, among the rows where use() holds."""
    sub = [r for r in rows if use(r)]
    one = [r for r in sub if first(r)]
    rest = [r for r in sub if not first(r)]
    a, c = sum(flagged(r) for r in one), sum(flagged(r) for r in rest)
    return a, len(one) - a, c, len(rest) - c


def fisher_row(a, b, c, d, statement=None):
    p = fisher_greater(a, b, c, d)
    out = {'first': [a, a + b], 'rest': [c, c + d], 'share_first': ratio(a, a + b), 'share_rest': ratio(c, c + d),
           'p': None if p is None else round(p, 6)}
    if statement:
        out = {'statement': statement, **out, 'held': p is not None and p < 0.05 and a * (c + d) > c * (a + b)}
    return out


def score(rows):
    hol_flag = lambda r: r['holidays'] == 'flag'  # noqa: E731
    d1 = two_by_two(rows, lambda r: r['past_lapses'] != '' and r['holidays'] != 'n/a',
                    lambda r: r['past_lapses'] >= 1, hol_flag)
    d2 = two_by_two(rows, lambda r: r['holidays'] != 'n/a' and r['english'] != 'n/a',
                    lambda r: r['english'] == 'flag', hol_flag)
    return {'D1': fisher_row(*d1, PREDICTIONS['D1']), 'D2': fisher_row(*d2, PREDICTIONS['D2'])}


def prefectures(rows):
    by = defaultdict(list)
    for r in rows:
        by[(to_int(r['pref_id']), r['pref_name'])].append(r)
    out = []
    for (pid, name), rs in sorted(by.items()):
        row = {'pref_id': pid, 'pref_name': name, 'feeds': len(rs),
               'any_required_flag': sum(r['flags_required'] > 0 for r in rs),
               'all_ok': sum(r['all_ok'] == 'yes' for r in rs)}
        row.update({f'{c}_flag': sum(r[c] == 'flag' for r in rs) for c in CHECKS})
        out.append(row)
    return out


def summarise(rows, watch, as_of):
    keys = {key(r) for r in rows}
    # Not a prediction: the expiry list of 2026-10-22 already showed that 31 of its 55 feeds had lapsed before.
    expiry = two_by_two(rows, lambda r: r['past_lapses'] != '', lambda r: r['past_lapses'] >= 1,
                        lambda r: r['expiry'] == 'flag')
    return {'as_of': as_of, 'feeds': len(rows),
            'checks': {c: dict(sorted(Counter(r[c] for r in rows).items())) for c in CHECKS},
            'flags_required': {str(k): v for k, v in sorted(Counter(r['flags_required'] for r in rows).items())},
            'any_required_flag': sum(r['flags_required'] > 0 for r in rows),
            'all_ok': sum(r['all_ok'] == 'yes' for r in rows),
            'watch_outside': dict(sorted(Counter(w.get('status', '') for w in watch if key(w) not in keys).items())),
            'expiry_by_past_lapses': fisher_row(*expiry),
            'predictions': score(rows),
            'generated_at': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'by': "MV2 of Munim, Inc. (made with AI agents working in MV2's name)"}


def report(s):
    c = s['checks']
    def n(check, v):  # noqa: E306
        return c[check].get(v, 0)
    lines = [f'# 公開データの健康診断 / GTFS-JP data-health table ({s["as_of"]})', '',
             'このリポジトリで公開した4つの集計（期限の一覧・空白の調査・祝日・停留所名）を、データごとに1行にまとめました。新しいダウンロードはしていません。',
             'One row per feed, joining the four censuses already published here (expiry list, lapse census, holidays, '
             'stop names). No new downloads.', '',
             f'Feeds: {s["feeds"]} (the active, openly licensed feeds whose current file was read on 2026-10-22).', '',
             '| check | ok | flag | n/a |', '|---|---|---|---|']
    for check, label in (('expiry', 'expiry: expired or ends within 60 days'),
                         ('holidays', 'holidays: ordinary timetable on a holiday or New Year day to come'),
                         ('readings', 'readings: kana reading for under 90% of stops'),
                         ('english', 'English: English name for under 90% of stops (recommended only)')):
        lines.append(f'| {label} | {n(check, "ok")} | {n(check, "flag")} | {n(check, "n/a")} |')
    lines += ['', f'Feeds with at least one flag among expiry, holidays and readings: {s["any_required_flag"]}; '
              f'feeds ok on all four checks: {s["all_ok"]}. Flags per feed (required three): '
              + ', '.join(f'{k}: {v}' for k, v in s['flags_required'].items()) + '.', '',
              f'Expiry-list feeds outside these feeds (not read by the file censuses): '
              + (', '.join(f'{k} {v}' for k, v in s['watch_outside'].items()) or 'none') + '.', '',
              '## Predictions recorded before the table was made', '']
    for name, p in s['predictions'].items():
        lines.append(f'- {name}: {p["statement"]} Result: {p["first"][0]} of {p["first"][1]} ({p["share_first"]}) '
                     f'against {p["rest"][0]} of {p["rest"][1]} ({p["share_rest"]}), p = {p["p"]}: '
                     + ('held.' if p['held'] else 'did not hold.'))
    e = s['expiry_by_past_lapses']
    lines += ['', f'Not a prediction: expiry flags among feeds with a past lapse {e["first"][0]} of {e["first"][1]} '
              f'({e["share_first"]}), without {e["rest"][0]} of {e["rest"][1]} ({e["share_rest"]}), one-sided '
              f'Fisher p = {e["p"]}.', '',
              'Limits: each census was read on its own day (lapses 2026-10-16, the rest 2026-10-22) and later files '
              'are not seen. A flag is a sign to check, not proof of a mistake: some routes really do run their '
              'weekday timetable on holidays, and English is only recommended. Place names in the data are records of '
              'fact, not judgements.', '',
              f'Generated {s["generated_at"]}. Source: GTFS Data Repository (https://gtfs-data.jp/); each feed\'s '
              'publisher and licence are in feeds.csv. Made by MV2 of Munim, Inc. with AI agents working in MV2\'s '
              'name. Data CC BY 4.0.']
    return '\n'.join(lines) + '\n'


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--lapses', required=True, help='data/2026-10-16/feeds.csv')
    ap.add_argument('--watch', required=True, help='watch/<date>/expiring.csv')
    ap.add_argument('--holidays', required=True, help='holidays/2026-10-22/feeds.csv')
    ap.add_argument('--names', required=True, help='names/2026-10-22/feeds.csv')
    ap.add_argument('--as-of', default='2026-10-22')
    ap.add_argument('--out', required=True)
    a = ap.parse_args(argv)
    watch = read_csv(a.watch)
    rows = build(read_csv(a.lapses), watch, read_csv(a.holidays), read_csv(a.names), a.as_of)
    s = summarise(rows, watch, a.as_of)
    os.makedirs(a.out, exist_ok=True)
    write_csv(os.path.join(a.out, 'feeds.csv'), rows, COLUMNS)
    write_csv(os.path.join(a.out, 'prefectures.csv'), prefectures(rows),
              ['pref_id', 'pref_name', 'feeds', 'any_required_flag', 'all_ok'] + [f'{c}_flag' for c in CHECKS])
    with open(os.path.join(a.out, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(s, f, ensure_ascii=False, indent=1)
    with open(os.path.join(a.out, 'health.md'), 'w', encoding='utf-8') as f:
        f.write(report(s))
    print(json.dumps(s, ensure_ascii=False))
    return s


if __name__ == '__main__':
    main()
