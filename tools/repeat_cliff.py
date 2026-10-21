# repeat_cliff.py - do feeds that lapsed on April 1 one year lapse again on April 1 the next year? For each
# year, compares feeds that lapsed on the previous April 1 with all other feeds at risk (a file ending March 31
# and watched past April 1, as in fy_cliff.py). Reads a gtfs_lapses.py output folder and writes
# repeat_cliff.csv and repeat_cliff.md next to it. Needs fy_cliff.py in the same folder.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import argparse
import csv
import datetime as dt
import math
import os

from fy_cliff import day, read_csv


def binom_tail(k, n, p):
    """P(X >= k) for X ~ Binomial(n, p)."""
    if n == 0 or k <= 0:
        return 1.0
    return min(1.0, sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1)))


def at_risk_and_lapsed(feed_rows, version_rows, lapse_rows):
    """{year: set of feeds at risk on April 1}, {year: set of feeds whose lapse began on April 1}.
    Unlike fy_cliff.py, a feed already in a lapse on March 31 is not at risk, even if a file published later
    was back-dated to end on March 31."""
    window_end = {(r['organization_id'], r['feed_id']): day(r['window_end']) for r in feed_rows}
    risk, lapsed, gap_mar31 = {}, {}, set()
    for x in lapse_rows:
        s = day(x['start'])
        if not s:
            continue
        k = (x['organization_id'], x['feed_id'])
        if s.month == 4 and s.day == 1:
            lapsed.setdefault(s.year, set()).add(k)
        end = s + dt.timedelta(days=int(x['days']) - 1)
        for y in range(s.year, end.year + 1):
            if s <= dt.date(y, 3, 31) <= end:
                gap_mar31.add((k, y))
    for v in version_rows:
        to = day(v['to_date'])
        k = (v['organization_id'], v['feed_id'])
        if (to and to.month == 3 and to.day == 31 and (k, to.year) not in gap_mar31
                and window_end.get(k) and window_end[k] >= dt.date(to.year, 4, 1)):
            risk.setdefault(to.year, set()).add(k)
    return risk, lapsed


def repeats(feed_rows, version_rows, lapse_rows):
    """One row per year that has feeds at risk and a previous April-1 lapse year."""
    risk, lapsed = at_risk_and_lapsed(feed_rows, version_rows, lapse_rows)
    rows = []
    for y in sorted(risk):
        prior = lapsed.get(y - 1, set())
        if not prior:
            continue
        now = lapsed.get(y, set())
        prior_risk = prior & risk[y]
        again = prior_risk & now
        others = risk[y] - prior
        others_lapsed = others & now
        p_others = len(others_lapsed) / len(others) if others else 0.0
        rows.append({'year': y, 'prior_lapsers': len(prior), 'prior_at_risk': len(prior_risk),
                     'lapsed_again': len(again), 'lapsed_again_orgs': len({k[0] for k in again}),
                     'repeat_share': round(len(again) / len(prior_risk), 4) if prior_risk else '',
                     'others_at_risk': len(others), 'others_lapsed': len(others_lapsed),
                     'others_share': round(p_others, 4) if others else '',
                     'p_one_sided': round(binom_tail(len(again), len(prior_risk), p_others), 4)
                     if prior_risk and others else ''})
    return rows


COLS = ['year', 'prior_lapsers', 'prior_at_risk', 'lapsed_again', 'lapsed_again_orgs', 'repeat_share',
        'others_at_risk', 'others_lapsed', 'others_share', 'p_one_sided']


def markdown(rows):
    lines = ['# Repeat April-1 lapses', '',
             'prior = feeds whose lapse began on April 1 of the previous year; at risk = a published file valid '
             'until March 31 of this year and watched past April 1. p_one_sided = binomial P(lapsed_again or more '
             '| prior_at_risk, others_share). Feeds from one publisher often lapse together, so they are not '
             'independent and p is only a rough guide.', '',
             '| ' + ' | '.join(COLS) + ' |', '|' + '---|' * len(COLS)]
    lines += ['| ' + ' | '.join(str(r[c]) for c in COLS) + ' |' for r in rows]
    return '\n'.join(lines) + '\n'


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('folder', help='a gtfs_lapses.py output folder, e.g. /out/lapses/2026-10-16')
    a = ap.parse_args(argv)
    p = lambda n: os.path.join(a.folder, n)  # noqa: E731
    rows = repeats(read_csv(p('feeds.csv')), read_csv(p('versions.csv')), read_csv(p('lapses.csv')))
    with open(p('repeat_cliff.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLS, lineterminator='\r\n')
        w.writeheader()
        w.writerows(rows)
    with open(p('repeat_cliff.md'), 'w', encoding='utf-8') as f:
        f.write(markdown(rows))
    print(markdown(rows))


if __name__ == '__main__':
    main()
