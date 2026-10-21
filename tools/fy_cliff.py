# fy_cliff.py - how many of the lapses found by gtfs_lapses.py begin on April 1, the first day of Japan's
# fiscal year, and how many feeds whose data ran out on March 31 were renewed in time. Reads the census
# output folder (feeds.csv, versions.csv, lapses.csv) and writes fy_cliff.csv and fy_cliff.md next to them.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import argparse
import csv
import datetime as dt
import os


def day(s):
    s = (s or '').strip()
    try:
        return dt.date.fromisoformat(s[:10]) if len(s) >= 10 else None
    except ValueError:
        return None


def read_csv(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def median(xs):
    if not xs:
        return None
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def cliff(feed_rows, version_rows, lapse_rows):
    """One row per year: feeds at risk (a file ending March 31 and watched past April 1), how many lapsed on
    April 1, how many of those are still open, the median length of the ones that ended, feed-days lost, and
    the share of all lapses that started that year which began on April 1."""
    window_end = {(r['organization_id'], r['feed_id']): day(r['window_end']) for r in feed_rows}
    ends = {}
    for v in version_rows:
        to = day(v['to_date'])
        if to and to.month == 3 and to.day == 31:
            ends.setdefault(to.year, set()).add((v['organization_id'], v['feed_id']))
    years = sorted(set(ends) | {day(x['start']).year for x in lapse_rows})
    rows = []
    for y in years:
        fy0 = dt.date(y, 4, 1)
        at_risk = {k for k in ends.get(y, ()) if window_end.get(k) and window_end[k] >= fy0}
        started = [x for x in lapse_rows if day(x['start']).year == y]
        on_fy0 = [x for x in started if day(x['start']) == fy0]
        lapsed = {(x['organization_id'], x['feed_id']) for x in on_fy0}
        ended = [int(x['days']) for x in on_fy0 if x['ongoing'] == 'false']
        rows.append({'year': y, 'feeds_ending_mar31': len(at_risk),
                     'renewed_in_time': len(at_risk - lapsed), 'lapsed_apr1': len(lapsed),
                     'lapsed_share': round(len(lapsed) / len(at_risk), 4) if at_risk else '',
                     'still_open': sum(1 for x in on_fy0 if x['ongoing'] == 'true'),
                     'median_days_ended': median(ended) if ended else '',
                     'feed_days_lost': sum(int(x['days']) for x in on_fy0),
                     'lapses_started': len(started),
                     'apr1_share_of_lapses': round(len(on_fy0) / len(started), 4) if started else ''})
    return rows


COLS = ['year', 'feeds_ending_mar31', 'renewed_in_time', 'lapsed_apr1', 'lapsed_share', 'still_open',
        'median_days_ended', 'feed_days_lost', 'lapses_started', 'apr1_share_of_lapses']


def markdown(rows):
    lines = ['# Fiscal-year cliff: lapses that begin on April 1', '',
             'feeds ending Mar 31 = feeds with a published file valid until March 31 of that year and watched '
             'past April 1 (discontinued networks are not watched past their end).', '',
             '| ' + ' | '.join(COLS) + ' |', '|' + '---|' * len(COLS)]
    lines += ['| ' + ' | '.join(str(r[c]) for c in COLS) + ' |' for r in rows]
    return '\n'.join(lines) + '\n'


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('folder', help='a gtfs_lapses.py output folder, e.g. /out/lapses/2026-10-16')
    a = ap.parse_args(argv)
    p = lambda n: os.path.join(a.folder, n)  # noqa: E731
    rows = cliff(read_csv(p('feeds.csv')), read_csv(p('versions.csv')), read_csv(p('lapses.csv')))
    with open(p('fy_cliff.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLS, lineterminator='\r\n')
        w.writeheader()
        w.writerows(rows)
    with open(p('fy_cliff.md'), 'w', encoding='utf-8') as f:
        f.write(markdown(rows))
    print(markdown(rows))


if __name__ == '__main__':
    main()
