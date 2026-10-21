# cluster_band.py - how much wider the 2027-04-01 lapse forecast's range should be because feeds from one publisher
# (or one prefecture) tend to lapse together. For each year it estimates the intra-cluster correlation of April-1
# lapses among the feeds at risk (ANOVA estimator), widens the forecast's rough 90% range by the design effect of the
# 2027 cohort (fy2027_risk.py's cohort.csv), and back-tests the plain and the widened ranges on earlier years using
# only the year before. Needs repeat_cliff.py and fy_cliff.py in the same folder.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import argparse
import json
import math
import os
import time

from fy_cliff import read_csv
from repeat_cliff import at_risk_and_lapsed

Z90 = 1.645
YEARS = (2024, 2025, 2026)


def icc(clusters):
    """ANOVA estimate of the intra-cluster correlation of 0/1 outcomes; clusters = [(feeds, lapsed), ...].
    0.0 when it cannot be estimated (fewer than 2 clusters or no cluster with 2+ feeds). A negative value means no
    clustering; deff() floors it at 0."""
    cl = [(n, y) for n, y in clusters if n > 0]
    k, big_n = len(cl), sum(n for n, _ in cl)
    if k < 2 or big_n <= k:
        return 0.0
    p = sum(y for _, y in cl) / big_n
    msb = sum(n * (y / n - p) ** 2 for n, y in cl) / (k - 1)
    msw = sum(y - y * y / n for n, y in cl) / (big_n - k)
    n0 = (big_n - sum(n * n for n, _ in cl) / big_n) / (k - 1)
    den = msb + (n0 - 1) * msw
    return (msb - msw) / den if den > 0 else 0.0


def weighted_size(keys, cluster_of):
    """Size-weighted mean cluster size, sum(m^2) / sum(m): the m in the design effect 1 + (m - 1) * icc."""
    c = {}
    for k in keys:
        c[cluster_of(k)] = c.get(cluster_of(k), 0) + 1
    s = list(c.values())
    return sum(m * m for m in s) / sum(s) if s else 0.0


def deff(m_w, rho):
    return 1 + (m_w - 1) * max(0.0, rho)


def band(mean, var, d=1.0):
    """Rough 90% range as in fy2027_risk.expect, with the variance multiplied by the design effect d."""
    sd = math.sqrt(var * d)
    return max(0, math.floor(mean - Z90 * sd)), math.ceil(mean + Z90 * sd)


def year_clusters(risk, lapsed, y, cluster_of):
    c = {}
    now = lapsed.get(y, set())
    for k in risk.get(y, ()):
        n, hit = c.get(cluster_of(k), (0, 0))
        c[cluster_of(k)] = (n + 1, hit + (k in now))
    return list(c.values())


def year_rates(risk, lapsed, y):
    """The counts of repeat_cliff.py for one year: at risk, lapsed, and the prior/other split."""
    r, now, prior = risk.get(y, set()), lapsed.get(y, set()), lapsed.get(y - 1, set())
    pr, ot = r & prior, r - prior
    return {'at_risk': len(r), 'lapsed': len(r & now), 'prior': len(pr), 'prior_lapsed': len(pr & now),
            'other': len(ot), 'other_lapsed': len(ot & now)}


def grouped(n_prior, n_other, rp, ro):
    """(mean, variance) of the lapse count with independent feeds."""
    return n_prior * rp + n_other * ro, n_prior * rp * (1 - rp) + n_other * ro * (1 - ro)


def analyse(feed_rows, version_rows, lapse_rows, cohort_rows, years=YEARS):
    risk, lapsed = at_risk_and_lapsed(feed_rows, version_rows, lapse_rows)
    pref = {(r['organization_id'], r['feed_id']): str(r.get('pref_id') or 'none') for r in feed_rows}
    for r in cohort_rows:
        pref.setdefault((r['organization_id'], r['feed_id']), str(r.get('pref_id') or 'none'))
    by = {'publisher': lambda k: k[0], 'prefecture': lambda k: pref.get(k, 'none')}

    by_year = []
    for y in sorted(risk):
        rt = year_rates(risk, lapsed, y)
        row = {'year': y, 'at_risk': rt['at_risk'], 'lapsed': rt['lapsed']}
        for name, f in by.items():
            cl = year_clusters(risk, lapsed, y, f)
            row[f'{name}_clusters'] = len(cl)
            row[f'{name}_clusters_lapsed'] = sum(1 for _, hit in cl if hit)
            row[f'{name}_icc'] = round(icc(cl), 4)
        by_year.append(row)
    pooled = {name: round(icc([c for y in years for c in year_clusters(risk, lapsed, y, f)]), 4)
              for name, f in by.items()}

    # Back-test: predict each year from the year before only (rates and icc), then look at what happened.
    backtest = []
    for y in sorted(risk):
        if y - 1 not in risk:
            continue
        base, tgt = year_rates(risk, lapsed, y - 1), year_rates(risk, lapsed, y)
        f = base['lapsed'] / base['at_risk']
        models = {'flat': grouped(0, tgt['at_risk'], 0, f)}
        if base['prior'] and base['other'] and tgt['prior']:
            models['by_group'] = grouped(tgt['prior'], tgt['other'], base['prior_lapsed'] / base['prior'],
                                         base['other_lapsed'] / base['other'])
        ds = {'independent': 1.0}
        for name, fn in by.items():
            ds[name] = deff(weighted_size(risk[y], fn), icc(year_clusters(risk, lapsed, y - 1, fn)))
        for m, (mean, var) in models.items():
            row = {'year': y, 'model': m, 'rates_from': y - 1, 'at_risk': tgt['at_risk'], 'expected': round(mean, 1),
                   'observed': tgt['lapsed']}
            for b, d in ds.items():
                lo, hi = band(mean, var, d)
                row[f'{b}_deff'] = round(d, 3)
                row[f'{b}_low90'], row[f'{b}_high90'] = lo, hi
                row[f'{b}_covered'] = lo <= tgt['lapsed'] <= hi
            backtest.append(row)

    # The 2027 cohort, recorded before the day.
    keys = [(r['organization_id'], r['feed_id']) for r in cohort_rows]
    n_prior = sum(1 for r in cohort_rows if r['group'] == 'prior')
    n_other = len(cohort_rows) - n_prior
    last = max(years)
    r1 = year_rates(risk, lapsed, last)
    s = {k: sum(year_rates(risk, lapsed, y)[k] for y in years) for k in ('prior', 'prior_lapsed', 'other',
                                                                         'other_lapsed')}
    f1 = r1['lapsed'] / r1['at_risk']
    models = {f'rates_{last}': grouped(n_prior, n_other, r1['prior_lapsed'] / r1['prior'],
                                       r1['other_lapsed'] / r1['other']),
              f'rates_{min(years)}_{last}': grouped(n_prior, n_other, s['prior_lapsed'] / s['prior'],
                                                    s['other_lapsed'] / s['other']),
              f'flat_{last}': grouped(0, len(keys), 0, f1)}
    sizes = {name: weighted_size(keys, fn) for name, fn in by.items()}
    last_icc = {name: icc(year_clusters(risk, lapsed, last, fn)) for name, fn in by.items()}
    ds = {'independent': 1.0}
    for name in by:
        ds[f'{name}_icc_{last}'] = deff(sizes[name], last_icc[name])
        ds[f'{name}_icc_pooled'] = deff(sizes[name], pooled[name])
    forecast = []
    for m, (mean, var) in models.items():
        row = {'model': m, 'expected': round(mean, 1)}
        for b, d in ds.items():
            row[f'{b}_deff'] = round(d, 3)
            row[f'{b}_low90'], row[f'{b}_high90'] = band(mean, var, d)
        forecast.append(row)
    counts = {name: {} for name in by}
    for k in keys:
        for name, fn in by.items():
            counts[name][fn(k)] = counts[name].get(fn(k), 0) + 1
    cohort = {'feeds': len(keys), 'prior': n_prior, 'other': n_other,
              'publishers': len(counts['publisher']), 'prefectures': len(counts['prefecture']),
              'publisher_weighted_size': round(sizes['publisher'], 3),
              'prefecture_weighted_size': round(sizes['prefecture'], 3),
              'largest_publisher_feeds': max(counts['publisher'].values()) if keys else 0,
              'largest_prefecture_feeds': max(counts['prefecture'].values()) if keys else 0}
    return {'icc_by_year': by_year, 'icc_pooled': pooled, 'pooled_years': list(years), 'backtest': backtest,
            'cohort_2027': cohort, 'forecast_2027': forecast}


def check_forecast(result, fc):
    """True when the means agree with the forecast.json that fy2027_risk.py recorded."""
    want = {name: m['expected'] for name, m in fc['forecast']['models'].items()}
    got = {r['model']: r['expected'] for r in result['forecast_2027']}
    return want == got


def markdown(res):
    c = res['cohort_2027']
    lines = ['# 提供者・都道府県ごとのまとまりと予測の幅 / Clustering and the width of the 2027-04-01 forecast', '',
             '同じ提供者（または同じ都道府県）のデータは4月1日にまとめて空白になりやすく、件数は独立ではありません。',
             '各年の級内相関（ICC、分散分析による推定）から、予測の「90%の目安」をデザイン効果 1 + (m − 1) × ICC で広げます。',
             'Feeds from one publisher (or one prefecture) tend to lapse together on April 1, so counts are not '
             'independent. The rough 90% range is widened by the design effect 1 + (m - 1) x ICC, with the '
             'intra-cluster correlation (ICC, ANOVA estimate) of each year\'s April-1 lapses and m the size-weighted '
             'mean cluster size of the 2027 cohort.', '',
             f'2027 cohort: {c["feeds"]} feeds (prior {c["prior"]}, other {c["other"]}), {c["publishers"]} publishers '
             f'(m = {c["publisher_weighted_size"]}, largest {c["largest_publisher_feeds"]} feeds), '
             f'{c["prefectures"]} prefectures (m = {c["prefecture_weighted_size"]}, largest '
             f'{c["largest_prefecture_feeds"]} feeds).', '',
             '## ICC by year', '',
             '| year | at risk | lapsed | publishers | with a lapse | ICC publisher | prefectures | with a lapse | '
             'ICC prefecture |', '|---|---|---|---|---|---|---|---|---|']
    for r in res['icc_by_year']:
        lines.append(f'| {r["year"]} | {r["at_risk"]} | {r["lapsed"]} | {r["publisher_clusters"]} | '
                     f'{r["publisher_clusters_lapsed"]} | {r["publisher_icc"]} | {r["prefecture_clusters"]} | '
                     f'{r["prefecture_clusters_lapsed"]} | {r["prefecture_icc"]} |')
    y0, y1 = min(res['pooled_years']), max(res['pooled_years'])
    lines += ['', f'Pooled {y0}-{y1} (clusters counted per year): publisher {res["icc_pooled"]["publisher"]}, '
              f'prefecture {res["icc_pooled"]["prefecture"]}.', '',
              '## Back-test (rates and ICC from the year before only)', '',
              '| year | model | expected | observed | independent | publisher | prefecture |', '|---|---|---|---|---|---|---|']

    def cell(r, b):
        return f'{r[b + "_low90"]}–{r[b + "_high90"]} {"✓" if r[b + "_covered"] else "✗"} (deff {r[b + "_deff"]})'
    for r in res['backtest']:
        lines.append(f'| {r["year"]} | {r["model"]} | {r["expected"]} | {r["observed"]} | {cell(r, "independent")} | '
                     f'{cell(r, "publisher")} | {cell(r, "prefecture")} |')
    keys = [k[:-5] for k in res['forecast_2027'][0] if k.endswith('_deff')]
    lines += ['', '## 2027-04-01: rough 90% ranges (recorded before the day)', '',
              '| model | expected | ' + ' | '.join(keys) + ' |', '|---|---|' + '---|' * len(keys)]
    for r in res['forecast_2027']:
        lines.append(f'| {r["model"]} | {r["expected"]} | ' +
                     ' | '.join(f'{r[k + "_low90"]}–{r[k + "_high90"]} (deff {r[k + "_deff"]})' for k in keys) + ' |')
    lines += ['', '限界: ICCは年ごとの少ないまとまりから推定するので不安定です。デザイン効果はprior/otherの層を区別しない近似です。',
              'Limits: the ICC is estimated from few clusters per year and is noisy; the design effect ignores the '
              'prior/other strata; feeds new since the census get their prefecture from cohort.csv. These ranges will '
              'be scored with the forecast after 2027-04-01.', '',
              'Source: GTFS Data Repository API v2 (https://gtfs-data.jp/) via the lapse census in this repository. '
              'Made by MV2 of Munim, Inc. with AI agents working in MV2\'s name. Data CC BY 4.0.', '']
    return '\n'.join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--census', required=True, help='folder of the census (feeds.csv, versions.csv, lapses.csv)')
    ap.add_argument('--cohort', required=True, help='cohort.csv recorded by fy2027_risk.py')
    ap.add_argument('--forecast', help='forecast.json recorded by fy2027_risk.py (checks that the means agree)')
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
    with open(os.path.join(out, 'cluster_band.json'), 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    with open(os.path.join(out, 'cluster_band.md'), 'w', encoding='utf-8') as f:
        f.write(markdown(res))
    print(json.dumps(res, ensure_ascii=False))


if __name__ == '__main__':
    main()
