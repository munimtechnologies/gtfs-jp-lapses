# trend_band.py - does last year's April-1 lapse share run low because the share keeps rising? Fits a straight line
# to the share of at-risk feeds whose lapse began on April 1 (weighted least squares, weights = feeds at risk, only
# years with at least MIN_AT_RISK feeds at risk), back-tests it against the year-before share using earlier years only,
# and records a trend forecast for the 2027 cohort (fy2027_risk.py's cohort.csv) with independent and
# publisher-widened ranges as in cluster_band.py. Needs cluster_band.py, repeat_cliff.py and fy_cliff.py in the same
# folder.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import argparse
import json
import math
import os
import time

from cluster_band import Z90, deff, icc, weighted_size, year_clusters
from fy_cliff import read_csv
from repeat_cliff import at_risk_and_lapsed

MIN_AT_RISK = 30
LAST_N = 3
publisher = lambda k: k[0]  # noqa: E731


def line(points):
    """Weighted least-squares line through [(year, at_risk, lapsed), ...] with weight at_risk.
    Returns (predict, fit_var): predict(x) is the share at year x clipped to [0, 1]; fit_var(x, p) the variance of
    that share from the fit itself, taking each year's share as binomial with probability p. None with fewer than
    two years."""
    pts = [(x, n, k) for x, n, k in points if n > 0]
    if len({x for x, _, _ in pts}) < 2:
        return None
    w = sum(n for _, n, _ in pts)
    xbar = sum(n * x for x, n, _ in pts) / w
    sbar = sum(k for _, _, k in pts) / w
    sxx = sum(n * (x - xbar) ** 2 for x, n, _ in pts)
    b = sum(n * (x - xbar) * (k / n - sbar) for x, n, k in pts) / sxx
    return (lambda x: min(1.0, max(0.0, sbar + b * (x - xbar))),
            lambda x, p: p * (1 - p) * (1 / w + (x - xbar) ** 2 / sxx))


def band(mean, var, n):
    """Rough 90% range as in cluster_band.band, capped at the number of feeds."""
    sd = math.sqrt(var)
    return max(0, math.floor(mean - Z90 * sd)), min(n, math.ceil(mean + Z90 * sd))


def trend_row(pts, x, n, d):
    """Expected count and ranges for n feeds at year x from the line through pts; d is the publisher design effect."""
    fit = line(pts)
    if fit is None:
        return None
    predict, fit_var = fit
    p = predict(x)
    proc, par = n * p * (1 - p), n * n * fit_var(x, p)
    row = {'share': round(p, 4), 'expected': round(n * p, 1)}
    for name, var in (('independent', proc), ('publisher', proc * d), ('publisher_fit', (proc + par) * d)):
        row[f'{name}_low90'], row[f'{name}_high90'] = band(n * p, var, n)
    return row


def analyse(feed_rows, version_rows, lapse_rows, cohort_rows, min_at_risk=None, last_n=LAST_N):
    min_at_risk = MIN_AT_RISK if min_at_risk is None else min_at_risk
    risk, lapsed = at_risk_and_lapsed(feed_rows, version_rows, lapse_rows)
    counts = {y: (len(risk[y]), len(risk[y] & lapsed.get(y, set()))) for y in sorted(risk)}
    years = [y for y, (n, _) in counts.items() if n >= min_at_risk]
    shares = [{'year': y, 'at_risk': n, 'lapsed': k, 'share': round(k / n, 4), 'used': y in years}
              for y, (n, k) in counts.items()]
    pts = lambda ys: [(y, *counts[y]) for y in ys]  # noqa: E731

    # Back-test: each year from the years before it only; the year-before share is the persistence model.
    backtest = []
    for y in years:
        before = [x for x in years if x < y]
        if not before or y - 1 not in counts:
            continue
        n, obs = counts[y]
        d = deff(weighted_size(risk[y], publisher), icc(year_clusters(risk, lapsed, y - 1, publisher)))
        n0, k0 = counts[y - 1]
        models = {'persistence': {'share': round(k0 / n0, 4), 'expected': round(n * k0 / n0, 1)}}
        for name, ys in (('trend_all', before), ('trend_last3', before[-last_n:] if len(before) > last_n else [])):
            r = trend_row(pts(ys), y, n, d)
            if r:
                models[name] = dict(r, fit_years=f'{ys[0]}-{ys[-1]}')
        for name, r in models.items():
            row = {'year': y, 'model': name, 'at_risk': n, 'observed': obs, 'publisher_deff': round(d, 3)}
            row.update(r)
            row['error'] = round(obs - r['expected'], 1)
            for b in ('independent', 'publisher', 'publisher_fit'):
                if f'{b}_low90' in r:
                    row[f'{b}_covered'] = r[f'{b}_low90'] <= obs <= r[f'{b}_high90']
            backtest.append(row)

    # Mean error and mean absolute error of each trend model and of persistence over the years that model was tried in.
    tried = {}
    for r in backtest:
        tried.setdefault(r['model'], {})[r['year']] = r['error']
    per = tried.get('persistence', {})
    mean = lambda v, ys, f: round(sum(f(v[y]) for y in ys) / len(ys), 2)  # noqa: E731
    scores = []
    for m, v in tried.items():
        ys = sorted(y for y in v if y in per)
        if m != 'persistence' and ys:
            scores.append({'model': m, 'years': ys, 'mean_error': mean(v, ys, float), 'mean_abs_error': mean(v, ys, abs),
                           'persistence_mean_error': mean(per, ys, float),
                           'persistence_mean_abs_error': mean(per, ys, abs)})

    # The 2027 cohort, recorded before the day.
    keys = [(r['organization_id'], r['feed_id']) for r in cohort_rows]
    n, last = len(keys), max(years)
    d = deff(weighted_size(keys, publisher), icc(year_clusters(risk, lapsed, last, publisher)))
    nl, kl = counts[last]
    forecast = [{'model': f'persistence_{last}', 'share': round(kl / nl, 4), 'expected': round(n * kl / nl, 1)}]
    fits = [(f'trend_{years[0]}_{last}', years)]
    if len(years) > last_n:
        fits.append((f'trend_{years[-last_n]}_{last}', years[-last_n:]))
    for name, ys in fits:
        r = trend_row(pts(ys), last + 1, n, d)
        if r:
            forecast.append(dict({'model': name}, **r))
    return {'min_at_risk': min_at_risk, 'shares': shares, 'backtest': backtest, 'scores': scores,
            'cohort_2027': {'feeds': n, 'publisher_weighted_size': round(weighted_size(keys, publisher), 3),
                            'publisher_deff': round(d, 3)},
            'forecast_2027': forecast}


def check_forecast(result, fc):
    """True when the persistence mean equals the flat model that fy2027_risk.py recorded in forecast.json."""
    want = {name: m['expected'] for name, m in fc['forecast']['models'].items() if name.startswith('flat_')}
    got = {r['model'].replace('persistence_', 'flat_'): r['expected'] for r in result['forecast_2027']
           if r['model'].startswith('persistence_')}
    return bool(want) and want == got


def markdown(res):
    def rng(r, b):
        if f'{b}_low90' not in r:
            return ''
        mark = '' if f'{b}_covered' not in r else (' ✓' if r[f'{b}_covered'] else ' ✗')
        return f'{r[b + "_low90"]}–{r[b + "_high90"]}{mark}'
    lines = ['# 割合の伸びと予測 / Is the April-1 lapse share rising? A trend check of the 2027-04-01 forecast', '',
             '前年の割合をそのまま使う予測（persistence）と、各年の割合に引いた直線（trend、提供データ数で重み付け）を、'
             'その年より前のデータだけで比べました。',
             'The year-before share (persistence) is compared with a straight line through the yearly shares (trend, '
             f'weighted least squares by feeds at risk, years with at least {res["min_at_risk"]} feeds at risk), each '
             'fitted on earlier years only. Ranges: independent = binomial; publisher = widened by the publisher design '
             'effect as in cluster_band.py; publisher_fit = also adds the uncertainty of the fitted line.', '',
             '## Share of at-risk feeds lapsing on April 1', '', '| year | at risk | lapsed | share | used in the line |',
             '|---|---|---|---|---|']
    lines += [f'| {r["year"]} | {r["at_risk"]} | {r["lapsed"]} | {r["share"]} | {"yes" if r["used"] else "no"} |'
              for r in res['shares']]
    lines += ['', '## Back-test', '',
              '| year | model | fit years | expected | observed | error | independent | publisher | publisher_fit |',
              '|---|---|---|---|---|---|---|---|---|']
    lines += [f'| {r["year"]} | {r["model"]} | {r.get("fit_years", str(r["year"] - 1))} | {r["expected"]} | '
              f'{r["observed"]} | {r["error"]} | {rng(r, "independent")} | {rng(r, "publisher")} | '
              f'{rng(r, "publisher_fit")} |' for r in res['backtest']]
    lines += ['', 'Error = observed − expected. Each trend model against persistence, over the years it was tried in:', '']
    lines += [f'- {s["model"]} ({", ".join(str(y) for y in s["years"])}): mean error {s["mean_error"]}, mean absolute '
              f'error {s["mean_abs_error"]}; persistence {s["persistence_mean_error"]} and '
              f'{s["persistence_mean_abs_error"]}' for s in res['scores']]
    c = res['cohort_2027']
    lines += ['', '## 2027-04-01 (recorded before the day)', '',
              f'{c["feeds"]} feeds; publisher design effect {c["publisher_deff"]} (m = {c["publisher_weighted_size"]}).',
              '', '| model | share | expected | independent | publisher | publisher_fit |', '|---|---|---|---|---|---|']
    lines += [f'| {r["model"]} | {r["share"]} | {r["expected"]} | {rng(r, "independent")} | {rng(r, "publisher")} | '
              f'{rng(r, "publisher_fit")} |' for r in res['forecast_2027']]
    lines += ['', '限界: 直線は数年分の点に引いただけで、伸びが続く保証はありません。prior/otherの層は分けていません。',
              'Limits: a line through a few yearly points; nothing says the rise will continue, and a share cannot rise '
              'for ever. The prior/other split of fy2027_risk.py is not used here. These figures will be scored with '
              'the forecast after 2027-04-01.', '',
              'Source: GTFS Data Repository API v2 (https://gtfs-data.jp/) via the lapse census in this repository. '
              'Made by MV2 of Munim, Inc. with AI agents working in MV2\'s name. Data CC BY 4.0.', '']
    return '\n'.join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--census', required=True, help='folder of the census (feeds.csv, versions.csv, lapses.csv)')
    ap.add_argument('--cohort', required=True, help='cohort.csv recorded by fy2027_risk.py')
    ap.add_argument('--forecast', help='forecast.json recorded by fy2027_risk.py (checks the persistence mean)')
    ap.add_argument('--out', default='/out')
    a = ap.parse_args(argv)
    p = lambda n: os.path.join(a.census, n)  # noqa: E731
    res = analyse(read_csv(p('feeds.csv')), read_csv(p('versions.csv')), read_csv(p('lapses.csv')),
                  read_csv(a.cohort))
    if a.forecast:
        with open(a.forecast, encoding='utf-8') as f:
            res['matches_forecast'] = check_forecast(res, json.load(f))
    res['generated_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    res['by'] = 'MV2 of Munim, Inc. (made with AI agents working in MV2\'s name)'
    out = os.path.join(a.out, 'forecast', '2027-04-01')
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'trend_band.json'), 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    with open(os.path.join(out, 'trend_band.md'), 'w', encoding='utf-8') as f:
        f.write(markdown(res))
    print(json.dumps(res, ensure_ascii=False))


if __name__ == '__main__':
    main()
