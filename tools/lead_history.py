# lead_history.py - how many days before their start date the timetable files in the GTFS Data Repository
# (https://gtfs-data.jp/) were published, over every file the repository's API listed in the 2026-10-16 census
# (data/2026-10-16/versions.csv). A one-day snapshot of the files not yet in force (tools/file_chain.py) sees a file
# published long ahead for longer than one published the day before, so it over-represents long lead times; the
# full history does not have that bias, and it also sees the files published after their start date.
# A file counts here when it starts a new period: its from_date is later than that of every file of the same feed
# published before it. Corrections and re-issues of a period already published, and every file published on a
# feed's first publication day (the feed joining the repository, often with its history), are counted but given no
# lead time. Lead = from_date - publication date in Japan time (the census's published_date). A late file (lead under
# 0) is 'stale' when an earlier file still covered its start date (riders saw the old timetable) and 'gap' when none
# did (no valid file until it was published). No network; standard library only.
# The predictions in PREDICTIONS were fixed in this file before its first run.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import argparse
import csv
import datetime as dt
import json
import math
import os
import statistics

COHORT = (dt.date(2023, 1, 1), dt.date(2026, 6, 30))
BUCKETS = [('late', None, -1), ('same_day', 0, 0), ('1-6', 1, 6), ('7-13', 7, 13), ('14-20', 14, 20),
           ('21-27', 21, 27), ('28+', 28, None)]
TOP = 5
COLUMNS = ['organization_id', 'feed_id', 'rid', 'gtfs_file_uid', 'update_type', 'published_date', 'from_date',
           'to_date', 'lead_days', 'bucket', 'april_1', 'in_cohort', 'before_from', 'before_to', 'late_kind']
# Fixed before the first run (2026-10-23). Shares are of the new-period files whose from_date is in COHORT.
PREDICTIONS = {
    'P1': 'Between 15% and 45% of the new-period files that start in the cohort (2023-01-01 to 2026-06-30) were '
          'published after their start date (lead under 0 days).',
    'P2': 'The median lead of those files is between 0 and 10 days.',
    'P3': 'Fewer than 35% of those files were published at least 14 days ahead.',
    'P4': 'Those starting on April 1 were published after their start date more often than those starting on other '
          'days (one-sided Fisher exact test, p < 0.05).',
}


def day(v):
    try:
        return dt.date.fromisoformat((v or '').strip()[:10])
    except ValueError:
        return None


def iso(d):
    return d.isoformat() if d else ''


def read_csv(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, columns):
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def bucket(lead):
    for name, lo, hi in BUCKETS:
        if (lo is None or lead >= lo) and (hi is None or lead <= hi):
            return name
    return ''


def new_periods(rows):
    """versions.csv rows -> (one row per new-period file, counts)."""
    feeds, unreadable = {}, 0
    for r in rows:
        pub, a, b = day(r.get('published_date')), day(r.get('from_date')), day(r.get('to_date'))
        if not (pub and a and b):
            unreadable += 1
            continue
        feeds.setdefault((r.get('organization_id', ''), r.get('feed_id', '')), []).append((pub, a, b, r))
    counts = {'feeds': len(feeds), 'files': 0, 'unreadable': unreadable, 'first_day': 0, 'reissue': 0,
              'new_period': 0}
    out = []
    for key in sorted(feeds):
        vs = sorted(feeds[key], key=lambda v: (v[0], v[1], v[2]))
        first = vs[0][0]
        max_from = max_to = None
        for pub, a, b, r in vs:
            counts['files'] += 1
            if pub == first:
                counts['first_day'] += 1
            elif a > max_from:
                counts['new_period'] += 1
                lead = (a - pub).days
                out.append({'organization_id': key[0], 'feed_id': key[1], 'rid': r.get('rid', ''),
                            'gtfs_file_uid': r.get('gtfs_file_uid', ''), 'update_type': r.get('update_type', ''),
                            'published_date': iso(pub), 'from_date': iso(a), 'to_date': iso(b), 'lead_days': lead,
                            'bucket': bucket(lead), 'april_1': 'yes' if (a.month, a.day) == (4, 1) else 'no',
                            'in_cohort': 'yes' if COHORT[0] <= a <= COHORT[1] else 'no',
                            'before_from': iso(max_from), 'before_to': iso(max_to),
                            'late_kind': '' if lead >= 0 else ('stale' if max_to >= a else 'gap')})
            else:
                counts['reissue'] += 1
            max_from = a if max_from is None else max(max_from, a)
            max_to = b if max_to is None else max(max_to, b)
    return out, counts


def quartiles(xs):
    if not xs:
        return {'n': 0}
    xs = sorted(xs)
    q = statistics.quantiles(xs, n=4, method='inclusive') if len(xs) > 1 else [xs[0]] * 3
    return {'n': len(xs), 'min': xs[0], 'q1': q[0], 'median': statistics.median(xs), 'q3': q[2], 'max': xs[-1]}


def share(a, b):
    return round(a / b, 4) if b else None


def fisher_greater(a, b, c, d):
    """One-sided Fisher exact p that a/(a+b) is greater than c/(c+d)."""
    n1, n2, k = a + b, c + d, a + c
    if not n1 or not n2:
        return None
    lo, hi = max(0, k - n2), min(k, n1)
    num = sum(math.comb(n1, x) * math.comb(n2, k - x) for x in range(max(a, lo), hi + 1))
    return round(num / math.comb(n1 + n2, k), 6)


def stats(rows):
    leads = [int(r['lead_days']) for r in rows]
    n = len(leads)
    late = sum(1 for x in leads if x < 0)
    s = {'n': n, 'late': late, 'late_share': share(late, n), 'lead_days': quartiles(leads),
         'buckets': {name: sum(1 for r in rows if r['bucket'] == name) for name, _, _ in BUCKETS}}
    for k in (7, 14, 21):
        s[f'share_at_least_{k}'] = share(sum(1 for x in leads if x >= k), n)
    return s


def summarise(periods, counts, as_of):
    cohort = [r for r in periods if r['in_cohort'] == 'yes']
    c = stats(cohort)
    years = {}
    for r in periods:
        years.setdefault(r['from_date'][:4], []).append(r)
    by_year = {y: {k: v for k, v in stats(rs).items() if k != 'buckets'} for y, rs in sorted(years.items())}
    apr = [r for r in cohort if r['april_1'] == 'yes']
    oth = [r for r in cohort if r['april_1'] == 'no']
    al, ol = sum(int(r['lead_days']) < 0 for r in apr), sum(int(r['lead_days']) < 0 for r in oth)
    p4 = fisher_greater(al, len(apr) - al, ol, len(oth) - ol)
    april = {'april_1': {'n': len(apr), 'late': al, 'late_share': share(al, len(apr)),
                         'median': quartiles([int(r['lead_days']) for r in apr]).get('median')},
             'other': {'n': len(oth), 'late': ol, 'late_share': share(ol, len(oth)),
                       'median': quartiles([int(r['lead_days']) for r in oth]).get('median')},
             'fisher_p_greater': p4}
    types = {}
    for r in cohort:
        t = types.setdefault(r['update_type'] or '(none)', {'n': 0, 'late': 0})
        t['n'] += 1
        t['late'] += int(r['lead_days']) < 0
    for t in types.values():
        t['late_share'] = share(t['late'], t['n'])
    kinds = {k: sum(r['late_kind'] == k for r in cohort) for k in ('stale', 'gap')}
    per_feed = {}
    for r in cohort:
        per_feed.setdefault((r['organization_id'], r['feed_id']), []).append(int(r['lead_days']))
    medians = [statistics.median(v) for v in per_feed.values()]
    top = sorted(per_feed.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:TOP]
    top_keys = {k for k, _ in top}
    rest = [r for r in cohort if (r['organization_id'], r['feed_id']) not in top_keys]
    feeds = {'feeds': len(per_feed), 'median_of_feed_medians': statistics.median(medians) if medians else None,
             'feeds_any_late': sum(1 for v in per_feed.values() if min(v) < 0),
             'feeds_median_at_least_14': sum(1 for m in medians if m >= 14),
             'top': [{'organization_id': k[0], 'feed_id': k[1], 'files': len(v)} for k, v in top],
             'without_top': {k: v for k, v in stats(rest).items() if k != 'buckets'}}
    med = c['lead_days'].get('median')
    p = {'P1': (c['late_share'], c['late_share'] is not None and 0.15 <= c['late_share'] <= 0.45),
         'P2': (med, med is not None and 0 <= med <= 10),
         'P3': (c['share_at_least_14'], c['share_at_least_14'] is not None and c['share_at_least_14'] < 0.35),
         'P4': (p4, p4 is not None and p4 < 0.05)}
    s = {'census': iso(as_of), 'cohort': [iso(COHORT[0]), iso(COHORT[1])], 'counts': counts,
         'all_new_periods': len(periods), 'cohort_stats': c, 'by_start_year': by_year, 'april_1_vs_other': april,
         'by_update_type': types, 'late_kind': kinds, 'per_feed': feeds,
         'predictions': {k: {'text': PREDICTIONS[k], 'value': v, 'held': held} for k, (v, held) in p.items()}}
    s['generated_at'] = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    s['by'] = "MV2 of Munim, Inc. (made with AI agents working in MV2's name)"
    return s


def pct(x):
    return '' if x is None else f'{100 * x:.1f}%'


def report(s):
    k, c, a = s['counts'], s['cohort_stats'], s['april_1_vs_other']
    q = c['lead_days']
    lines = [f'# ダイヤの新しい期間のファイルは何日前に公開されたか / How far ahead new timetable periods were published '
             f'(versions to {s["census"]})', '',
             'GTFSデータリポジトリのAPIが10月16日の調査で返した全版（`data/2026-10-16/versions.csv`）について、新しい期間を始める'
             'ファイル（同じデータでそれより前に公開されたどのファイルよりも有効開始日が遅いもの）ごとに、有効開始日から公開日'
             '（日本時間）を引いた日数を数えました。修正・再公開の版と、データがリポジトリに加わった最初の公開日の版は数えますが、'
             '日数は付けません。',
             'For every file in the version history the repository API returned in the 2026-10-16 census '
             '(`data/2026-10-16/versions.csv`), a file that starts a new period (a from_date later than that of every '
             'file of the same feed published before it) gets its lead: start date minus publication date in Japan '
             'time. Corrections and re-issues, and the files published on a feed\'s first publication day, are counted '
             'but get no lead.', '',
             f'- データ / feeds: {k["feeds"]}; 版 / files: {k["files"]} (読めない / unreadable: {k["unreadable"]}); '
             f'最初の公開日 / first publication day: {k["first_day"]}; 修正・再公開 / corrections and re-issues: '
             f'{k["reissue"]}; 新しい期間 / new periods: {k["new_period"]}',
             f'- 対象期間 / cohort: start {s["cohort"][0]} to {s["cohort"][1]}: {c["n"]} files',
             f'- 開始日より後に公開 / published after the start date: {c["late"]} ({pct(c["late_share"])}); '
             f'うち古いファイルが有効のまま / old file still valid: {s["late_kind"]["stale"]}, '
             f'有効なファイルなし / no valid file: {s["late_kind"]["gap"]}',
             f'- 日数 / lead (days): median {q.get("median")}, quartiles {q.get("q1")}–{q.get("q3")}, range '
             f'{q.get("min")}–{q.get("max")}; 7日以上 / at least 7: {pct(c["share_at_least_7"])}; 14日以上 / at '
             f'least 14: {pct(c["share_at_least_14"])}; 21日以上 / at least 21: {pct(c["share_at_least_21"])}', '',
             '| 日数 / lead | files | share |', '|---|---|---|']
    for name, _, _ in BUCKETS:
        lines.append(f'| {name} | {c["buckets"][name]} | {pct(share(c["buckets"][name], c["n"]))} |')
    lines += ['', '## 開始年ごと / By start year (all new periods)', '',
              '| year | files | late | late share | median lead | at least 14 days |', '|---|---|---|---|---|---|']
    for y, v in s['by_start_year'].items():
        lines.append(f'| {y} | {v["n"]} | {v["late"]} | {pct(v["late_share"])} | {v["lead_days"].get("median")} | '
                     f'{pct(v["share_at_least_14"])} |')
    f = s['per_feed']
    lines += ['', '## 4月1日とそれ以外 / April 1 against other start days (cohort)', '',
              f'- 4月1日 / April 1: {a["april_1"]["late"]} of {a["april_1"]["n"]} late '
              f'({pct(a["april_1"]["late_share"])}), median {a["april_1"]["median"]}',
              f'- それ以外 / other days: {a["other"]["late"]} of {a["other"]["n"]} late '
              f'({pct(a["other"]["late_share"])}), median {a["other"]["median"]}',
              f'- one-sided Fisher exact p = {a["fisher_p_greater"]}', '',
              '## 版の種類とデータごと / By update type and by feed (cohort)', '']
    for t, v in sorted(s['by_update_type'].items()):
        lines.append(f'- {t}: {v["late"]} of {v["n"]} late ({pct(v["late_share"])})')
    w = f['without_top']
    lines += [f'- データ / feeds: {f["feeds"]}; データごとの中央値の中央値 / median of feed medians: '
              f'{f["median_of_feed_medians"]}; 遅れた版のあるデータ / feeds with a late file: {f["feeds_any_late"]}; '
              f'中央値が14日以上 / feed median at least 14: {f["feeds_median_at_least_14"]}',
              '- 新しい期間の多いデータ / feeds with the most new periods: '
              + ', '.join(f'{t["organization_id"]}/{t["feed_id"]} {t["files"]}' for t in f['top']),
              f'- その{TOP}件を除くと / without those {TOP}: {w["n"]} files, late {pct(w["late_share"])}, median '
              f'{w["lead_days"].get("median")}, at least 14 days {pct(w["share_at_least_14"])}', '',
              '## 事前に記録した予測 / Predictions fixed before the run', '']
    for key, p in s['predictions'].items():
        v = p['value']
        shown = pct(v) if key in ('P1', 'P3') else ('' if v is None else (f'{v} days' if key == 'P2' else f'p = {v}'))
        lines.append(f'- {key}: {p["text"]} Result: {shown}, {"held" if p["held"] else "did not hold"}.')
    lines += ['', 'Benchmarks (guidance, not measurements): route-search providers about 2 weeks before a change, Google '
              'about 1 week, signage the same night (AIGID, https://front.geospatial.jp/no56_2/); MobilityData 3–4 '
              'weeks and at least 5 days (https://gtfs.org/documentation/schedule/schedule-best-practices/).', '',
              'Limits: the publication date is the one the repository gives for each file; a file sent to apps or route '
              'planners by other means earlier is not seen, and old files no longer in the API are not seen. A file '
              'whose from_date was simply set to its upload day counts as a new period with lead 0. Starts after '
              f'{s["cohort"][1]} are left out of the cohort because files published very late for them may still be '
              'missing. Feeds from one publisher are not independent, so the p-value is, if anything, too small. Lead '
              'times are the publishers\' and are reported as facts, not judgements.', '',
              f'Generated {s["generated_at"]}. Source: GTFS Data Repository API v2 (https://gtfs-data.jp/), via '
              'data/2026-10-16/versions.csv; each feed\'s publisher and licence are in data/2026-10-16/feeds.csv. Made '
              'by MV2 of Munim, Inc. with AI agents working in MV2\'s name. Data CC BY 4.0.']
    return '\n'.join(lines) + '\n'


def main(argv=None):
    ap = argparse.ArgumentParser(description='Publication lead times of new timetable periods.')
    ap.add_argument('--versions', required=True, help='versions.csv of a gtfs_lapses.py census')
    ap.add_argument('--as-of', default='2026-10-16', help='the census day (YYYY-MM-DD), for the output folder')
    ap.add_argument('--out', required=True)
    a = ap.parse_args(argv)
    as_of = day(a.as_of)
    periods, counts = new_periods(read_csv(a.versions))
    s = summarise(periods, counts, as_of)
    out = os.path.join(a.out, iso(as_of))
    os.makedirs(out, exist_ok=True)
    write_csv(os.path.join(out, 'leads.csv'), periods, COLUMNS)
    with open(os.path.join(out, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(s, f, ensure_ascii=False, indent=1)
    with open(os.path.join(out, 'leads.md'), 'w', encoding='utf-8') as f:
        f.write(report(s))
    print(json.dumps(s, ensure_ascii=False))
    return s


if __name__ == '__main__':
    main()
