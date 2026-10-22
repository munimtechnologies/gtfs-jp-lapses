# lapse_survival.py - how long does a GTFS feed stay without a valid file once it lapses? Kaplan-Meier time to the next
# valid file for every lapse in the census's lapses.csv, counting lapses still open on the census day as censored (a
# median of the ended lapses alone runs short when many are still open). Compares lapses that began on April 1 with
# the rest and recent April-1 lapses with earlier ones (log-rank test), and turns the 2027-04-01 forecasts into
# expected feed-days without a valid file within a year (forecast count x restricted mean days of April-1 lapses).
# Standard library only.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import argparse
import csv
import json
import math
import os
import statistics
import time

TAU = 365
CHECKPOINTS = (30, 90, 180, 365)
MIN_GROUP = 5


def read_csv(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def load_json(path):
    if not path:
        return None
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def spells(rows):
    """One dict per lapse: start year, whether it began on April 1, its length in days (inclusive) and whether it
    ended (False = still open on the census day, so censored at that length)."""
    out = []
    for r in rows:
        out.append({'year': int(r['start'][:4]), 'apr1': r['start'][5:10] == '04-01', 'days': int(r['days']),
                    'ended': str(r['ongoing']).strip().lower() != 'true'})
    return out


def km(items):
    """Kaplan-Meier product-limit estimate from [(days, ended), ...]. Returns steps [(t, at_risk, ended_at_t, S(t),
    Greenwood standard error)] at each time a lapse ended; a lapse censored at t counts as at risk at t."""
    steps, s, gw = [], 1.0, 0.0
    for t in sorted({d for d, e in items if e}):
        n = sum(1 for d, _ in items if d >= t)
        k = sum(1 for d, e in items if e and d == t)
        s *= 1 - k / n
        gw = gw + k / (n * (n - k)) if n > k else math.inf
        se = 0.0 if s == 0 else s * math.sqrt(gw)
        steps.append((t, n, k, s, se))
    return steps


def surv_at(steps, t):
    """S(t): the share of lapses still without a valid file after t days."""
    s = 1.0
    for st in steps:
        if st[0] > t:
            break
        s = st[3]
    return s


def se_at(steps, t):
    se = 0.0
    for st in steps:
        if st[0] > t:
            break
        se = st[4]
    return se


def km_median(steps):
    """First time S(t) falls to 0.5 or below; None if it never does within the data."""
    for st in steps:
        if st[3] <= 0.5 + 1e-9:  # products like 3/4 * 2/3 can land a hair above 0.5
            return st[0]
    return None


def rmst(steps, tau=TAU):
    """Restricted mean: the area under S(t) from 0 to tau, i.e. the mean days without a valid file within tau days."""
    area, t0, s = 0.0, 0, 1.0
    for st in steps:
        if st[0] > tau:
            break
        area += s * (st[0] - t0)
        t0, s = st[0], st[3]
    return area + s * (tau - t0)


def followed_to(items):
    """Longest length observed; S(t) beyond it is not estimated."""
    return max((d for d, _ in items), default=0)


def logrank(a, b):
    """Two-group log-rank test. Returns (observed in a, expected in a, chi-square with 1 df, two-sided p)."""
    both = [(d, e, 0) for d, e in a] + [(d, e, 1) for d, e in b]
    o = ex = v = 0.0
    for t in sorted({d for d, e, _ in both if e}):
        n = sum(1 for d, _, _ in both if d >= t)
        na = sum(1 for d, _, g in both if d >= t and g == 0)
        k = sum(1 for d, e, _ in both if e and d == t)
        ka = sum(1 for d, e, g in both if e and d == t and g == 0)
        o += ka
        ex += k * na / n
        if n > 1:
            v += k * (na / n) * (1 - na / n) * (n - k) / (n - 1)
    chi2 = (o - ex) ** 2 / v if v > 0 else 0.0
    return o, ex, chi2, math.erfc(math.sqrt(chi2 / 2))


def summarise(name, group):
    items = [(g['days'], g['ended']) for g in group]
    steps = km(items)
    ended = [d for d, e in items if e]
    row = {'group': name, 'lapses': len(items), 'ended': len(ended), 'still_open': len(items) - len(ended),
           'followed_to_days': followed_to(items), 'km_median_days': km_median(steps),
           'ended_only_median_days': statistics.median(ended) if ended else None,
           'rmst_365_days': round(rmst(steps), 1)}
    for t in CHECKPOINTS:
        row[f'still_lapsed_{t}d'] = round(surv_at(steps, t), 3) if t <= row['followed_to_days'] else None
        row[f'still_lapsed_{t}d_se'] = round(se_at(steps, t), 3) if t <= row['followed_to_days'] else None
    return row


def analyse(lapse_rows, expected=None):
    sp = spells(lapse_rows)
    apr1 = [s for s in sp if s['apr1']]
    other = [s for s in sp if not s['apr1']]
    groups = [('all', sp), ('april_1', apr1), ('other_days', other)]
    years = sorted({s['year'] for s in apr1})
    for y in years:
        g = [s for s in apr1 if s['year'] == y]
        if len(g) >= MIN_GROUP:
            groups.append((f'april_1_{y}', g))
    rows = [summarise(n, g) for n, g in groups]

    pairs = lambda g: [(s['days'], s['ended']) for s in g]  # noqa: E731
    tests = []
    last = max(years) if years else None
    earlier = [s for s in apr1 if s['year'] < last] if last else []
    for name, a, b in (('april_1 vs other_days', apr1, other),
                       (f'april_1_{last} vs april_1 before {last}', [s for s in apr1 if s['year'] == last], earlier)):
        if a and b:
            o, ex, chi2, p = logrank(pairs(a), pairs(b))
            tests.append({'test': name, 'observed_ended_first': int(o), 'expected_ended_first': round(ex, 1),
                          'chi2': round(chi2, 3), 'p': round(p, 4),
                          'first_group_ends': 'sooner' if o > ex else 'later'})

    days_lost = []
    r = rmst(km(pairs(apr1)))
    for model, n in (expected or {}).items():
        days_lost.append({'model': model, 'expected_lapses': n, 'mean_days_per_lapse_365': round(r, 1),
                          'expected_feed_days_365': round(n * r)})
    return {'tau_days': TAU, 'groups': rows, 'tests': tests, 'forecast_2027_feed_days': days_lost}


def expected_counts(forecast=None, trend=None):
    """Expected 2027-04-01 lapse counts by model name from fy2027_risk.py's forecast.json and trend_band.json."""
    out = {}
    if forecast:
        for name, m in forecast['forecast']['models'].items():
            out[name] = m['expected']
    if trend:
        for m in trend['forecast_2027']:
            if not m['model'].startswith('persistence_'):
                out[m['model']] = m['expected']
    return out


def markdown(res, as_of):
    def cell(v, pct=False):
        if v is None:
            return '–'
        return f'{v * 100:.1f}%' if pct else str(v)
    lines = ['# 空白はどれだけ続くか / How long does a GTFS feed lapse last?', '',
             f'調査日（{as_of}）にまだ続いている空白は、その日までの長さで打ち切り（censored）として扱い、カプラン・マイヤー法で'
             '「空白が始まってから有効なデータが戻るまでの日数」を推定しました。終わった空白だけの中央値は、長く続いている空白を'
             '落とすので短めに出ます。',
             f'Each lapse runs from its first day without a valid file to the day before a valid file exists again. Lapses still '
             f'open on the census day ({as_of}) are censored at their length so far, and the time to recovery is estimated '
             'with the Kaplan-Meier method. A median of the ended lapses alone drops the long open ones and runs short.', '',
             '| group | lapses | ended | still open | followed to (days) | KM median days | ended-only median | '
             'still lapsed after 30 d | 90 d | 180 d | 365 d | mean days within 365 |',
             '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in res['groups']:
        lines.append(f'| {r["group"]} | {r["lapses"]} | {r["ended"]} | {r["still_open"]} | {r["followed_to_days"]} | '
                     f'{cell(r["km_median_days"])} | {cell(r["ended_only_median_days"])} | ' +
                     ' | '.join(cell(r[f'still_lapsed_{t}d'], True) for t in CHECKPOINTS) +
                     f' | {r["rmst_365_days"]} |')
    lines += ['', '"still lapsed after t d" = Kaplan-Meier S(t), the share of lapses with no valid file yet after t days '
              '(– where no lapse in the group was followed that long). "mean days within 365" = restricted mean, the '
              'area under S(t) up to 365 days. Standard errors (Greenwood) are in the JSON.', '',
              '## Log-rank tests', '', '| test | ended in the first group | expected | chi-square | p | first group ends |',
              '|---|---|---|---|---|---|']
    lines += [f'| {t["test"]} | {t["observed_ended_first"]} | {t["expected_ended_first"]} | {t["chi2"]} | {t["p"]} | '
              f'{t["first_group_ends"]} |' for t in res['tests']]
    if res['forecast_2027_feed_days']:
        lines += ['', '## 2027-04-01: feed-days without a valid file within a year (recorded before the day)', '',
                  'Expected April-1 lapses from the forecasts in forecast/2027-04-01/ times the mean days without a valid '
                  'file within 365 days of all April-1 lapses so far.', '',
                  '| forecast model | expected lapses | mean days per lapse | expected feed-days |', '|---|---|---|---|']
        lines += [f'| {d["model"]} | {d["expected_lapses"]} | {d["mean_days_per_lapse_365"]} | '
                  f'{d["expected_feed_days_365"]} |' for d in res['forecast_2027_feed_days']]
    lines += ['', '限界: 空白は独立ではありません（同じ提供者のデータはまとめて空白になり、まとめて戻ることが多い）。p値は小さめに出ます。'
              '運行終了の印がないまま終わった路線は、終わらない空白に見えます。',
              'Limits: lapses are not independent (one publisher\'s feeds often lapse and recover together), so the '
              'p-values are too small. A network that ended without being marked discontinued looks like a lapse that '
              'never ends. A lapse ends when any valid file exists again, which may be a back-dated file published later.',
              '', 'Source: GTFS Data Repository API v2 (https://gtfs-data.jp/) via the lapse census in this repository. '
              'Made by MV2 of Munim, Inc. with AI agents working in MV2\'s name. Data CC BY 4.0.', '']
    return '\n'.join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--lapses', required=True, help="the census's lapses.csv")
    ap.add_argument('--as-of', required=True, help='census day (YYYY-MM-DD), for the output folder and text')
    ap.add_argument('--forecast', help="fy2027_risk.py's forecast.json")
    ap.add_argument('--trend', help="trend_band.py's trend_band.json")
    ap.add_argument('--out', default='/out')
    a = ap.parse_args(argv)
    res = analyse(read_csv(a.lapses), expected_counts(load_json(a.forecast), load_json(a.trend)))
    res['as_of'] = a.as_of
    res['generated_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    res['by'] = 'MV2 of Munim, Inc. (made with AI agents working in MV2\'s name)'
    out = os.path.join(a.out, 'data', a.as_of)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'lapse_survival.json'), 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    with open(os.path.join(out, 'lapse_survival.md'), 'w', encoding='utf-8') as f:
        f.write(markdown(res, a.as_of))
    print(json.dumps(res, ensure_ascii=False))


if __name__ == '__main__':
    main()
