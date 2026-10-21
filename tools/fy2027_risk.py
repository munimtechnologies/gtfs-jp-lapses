# fy2027_risk.py - the feeds in the GTFS Data Repository (https://gtfs-data.jp/) whose latest file ends on 2027-03-31,
# split by their own record in the lapse census: did the feed already have no valid file on 2026-04-01? The census's
# repeat table (repeat_cliff.csv) says such feeds lapsed again on the next April 1 far more often (2026: 10 of 25
# against 45 of 247), so the forecast for 2027-04-01 is recorded per group, before the day, and scored afterwards
# with a one-sided Fisher exact test (--score).
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import argparse
import datetime as dt
import json
import math
import os
import sys
import time

from expiry_watch import FEEDS_URL, feed_list, history
from fy_cliff import read_csv
from gtfs_lapses import FY_END, JST, day, fetch, pref_name, write_csv

PRIOR_DAY = dt.date(FY_END.year - 1, 4, 1)  # 2026-04-01
TARGET_DAY = FY_END + dt.timedelta(days=1)  # 2027-04-01
COLS = ['group', 'organization_id', 'feed_id', 'organization_name', 'feed_name', 'pref_id', 'pref_name', 'license',
        'latest_feed_start_date', 'latest_feed_end_date', 'last_published_at', 'in_census', 'past_lapses',
        'past_april1_lapses', 'lapsed_on_prior_day']
SCORE_COLS = COLS + ['lapsed_on_target_day']


def lapse_starts(lapse_rows):
    """{(org, feed): set of start dates} from the census's lapses.csv."""
    s = {}
    for x in lapse_rows:
        d = day(x.get('start'))
        if d:
            s.setdefault((x['organization_id'], x['feed_id']), set()).add(d)
    return s


def cohort(feeds, lapse_rows, census_keys):
    """Rows for the active feeds whose latest file ends exactly on FY_END. group is 'prior' when the feed had a lapse
    that began on PRIOR_DAY, otherwise 'other' (feeds new since the census have no record and count as 'other')."""
    hist, starts = history(lapse_rows), lapse_starts(lapse_rows)
    rows = []
    for f in feeds:
        if f.get('feed_is_discontinued') in (True, 'true'):
            continue
        if day(f.get('latest_feed_end_date')) != FY_END:
            continue
        k = (f['organization_id'], f['feed_id'])
        n, apr, _ = hist.get(k, (0, 0, None))
        prior = PRIOR_DAY in starts.get(k, ())
        try:
            pid = int(f.get('feed_pref_id') or 0)
        except (TypeError, ValueError):
            pid = 0
        pub = day(f.get('last_published_at'))
        start = day(f.get('latest_feed_start_date'))
        rows.append({'group': 'prior' if prior else 'other', 'organization_id': k[0], 'feed_id': k[1],
                     'organization_name': f.get('organization_name') or '', 'feed_name': f.get('feed_name') or '',
                     'pref_id': pid, 'pref_name': pref_name(pid), 'license': f.get('feed_license') or '',
                     'latest_feed_start_date': start.isoformat() if start else '',
                     'latest_feed_end_date': FY_END.isoformat(), 'last_published_at': pub.isoformat() if pub else '',
                     'in_census': 'true' if k in census_keys else 'false', 'past_lapses': n,
                     'past_april1_lapses': apr, 'lapsed_on_prior_day': 'true' if prior else 'false'})
    rows.sort(key=lambda r: (r['group'] != 'prior', r['pref_id'], r['organization_id'], r['feed_id']))
    return rows


def rates(repeat_rows, years):
    """(prior share, other share, prior n, other n) summed over the given years of repeat_cliff.csv."""
    pl = pn = ol = on = 0
    for r in repeat_rows:
        if int(r['year']) in years:
            pl += int(r['lapsed_again'] or 0)
            pn += int(r['prior_at_risk'] or 0)
            ol += int(r['others_lapsed'] or 0)
            on += int(r['others_at_risk'] or 0)
    if not pn or not on:
        raise ValueError(f'no feeds at risk in years {sorted(years)}')
    return pl / pn, ol / on, pn, on


def expect(n_prior, n_other, r_prior, r_other):
    """Expected lapses and a rough 90% range, treating feeds as independent coin flips (they are not: one
    publisher's feeds tend to lapse together, so the real spread is wider)."""
    mean = n_prior * r_prior + n_other * r_other
    sd = math.sqrt(n_prior * r_prior * (1 - r_prior) + n_other * r_other * (1 - r_other))
    return {'expected': round(mean, 1), 'low90': max(0, math.floor(mean - 1.645 * sd)),
            'high90': math.ceil(mean + 1.645 * sd),
            'expected_prior': round(n_prior * r_prior, 1), 'expected_other': round(n_other * r_other, 1)}


def fisher_greater(a, b, c, d):
    """One-sided Fisher exact p for the 2x2 table [[a, b], [c, d]] (a = prior lapsed, b = prior not, c = other
    lapsed, d = other not): P(prior lapsed >= a) with the margins fixed."""
    n1, k, n = a + b, a + c, a + b + c + d

    def pmf(x):
        return math.comb(n1, x) * math.comb(n - n1, k - x) / math.comb(n, k)
    return min(1.0, sum(pmf(x) for x in range(a, min(n1, k) + 1)))


def forecast(rows, repeat_rows):
    n_prior = sum(1 for r in rows if r['group'] == 'prior')
    n_other = len(rows) - n_prior
    out = {'cohort': len(rows), 'prior': n_prior, 'other': n_other,
           'prior_definition': f'a lapse that began on {PRIOR_DAY.isoformat()} in the census',
           'target_day': TARGET_DAY.isoformat(), 'models': {}}
    for name, years in (('rates_2026', {2026}), ('rates_2024_2026', {2024, 2025, 2026})):
        rp, ro, pn, on = rates(repeat_rows, years)
        m = expect(n_prior, n_other, rp, ro)
        m.update({'prior_share': round(rp, 4), 'other_share': round(ro, 4), 'from_prior_at_risk': pn,
                  'from_others_at_risk': on})
        out['models'][name] = m
    rp, ro, pn, on = rates(repeat_rows, {2026})
    flat = (rp * pn + ro * on) / (pn + on)
    m = expect(0, len(rows), 0, flat)
    m['share'] = round(flat, 4)
    out['models']['flat_2026'] = m
    out['hypothesis'] = ('On 2027-04-01 the prior group lapses at a higher share than the other group '
                         '(one-sided Fisher exact test, p < 0.05), feeds counted one by one.')
    return out


def score(rows, lapsed_keys):
    """Add lapsed_on_target_day to each row and test the hypothesis."""
    t = {'prior': [0, 0], 'other': [0, 0]}
    for r in rows:
        hit = (r['organization_id'], r['feed_id']) in lapsed_keys
        r['lapsed_on_target_day'] = 'true' if hit else 'false'
        t[r['group']][0 if hit else 1] += 1
    a, b = t['prior']
    c, d = t['other']
    return {'prior_lapsed': a, 'prior_not': b, 'other_lapsed': c, 'other_not': d, 'lapsed': a + c,
            'prior_share': round(a / (a + b), 4) if a + b else None,
            'other_share': round(c / (c + d), 4) if c + d else None,
            'p_one_sided': round(fisher_greater(a, b, c, d), 4) if a + b and c + d else None}


def markdown(fc, as_of, sc=None):
    m26, m3, fl = fc['models']['rates_2026'], fc['models']['rates_2024_2026'], fc['models']['flat_2026']
    lines = [f'# 2027年4月1日の空白予測（グループ別） / Forecast for 2027-04-01 by group (recorded {as_of})', '',
             f'2027-03-31 に最新データが切れる有効なデータ: {fc["cohort"]} 件。うち2026年4月1日にも空白になったもの'
             f'（prior）{fc["prior"]} 件、それ以外（other）{fc["other"]} 件。',
             f'Active feeds whose latest file ends on 2027-03-31: {fc["cohort"]}. Of these, {fc["prior"]} also had no '
             f'valid file on 2026-04-01 (prior) and {fc["other"]} did not (other).', '',
             '| 予測 / model | prior の割合 | other の割合 | 予測件数 / expected | 90%の目安 / rough 90% |',
             '|---|---|---|---|---|',
             f'| 2026年の割合 / 2026 rates | {m26["prior_share"]:.1%} | {m26["other_share"]:.1%} | '
             f'{m26["expected"]} ({m26["expected_prior"]} + {m26["expected_other"]}) | {m26["low90"]}–{m26["high90"]} |',
             f'| 2024〜2026年の割合 / 2024-2026 rates | {m3["prior_share"]:.1%} | {m3["other_share"]:.1%} | '
             f'{m3["expected"]} ({m3["expected_prior"]} + {m3["expected_other"]}) | {m3["low90"]}–{m3["high90"]} |',
             f'| グループ分けなし / one rate for all (2026) | {fl["share"]:.1%} | {fl["share"]:.1%} | {fl["expected"]} | '
             f'{fl["low90"]}–{fl["high90"]} |', '',
             '仮説（事前登録）: 2027年4月1日の空白の割合は prior が other より高い（片側フィッシャー正確検定、p < 0.05、データ1件ずつ）。',
             'Hypothesis (recorded in advance): on 2027-04-01 the prior group lapses at a higher share than the other '
             'group (one-sided Fisher exact test, p < 0.05, one feed at a time).', '',
             '90%の目安はデータを独立とみなした概算です。同じ提供者のデータはまとめて空白になりやすいので、実際の幅はもっと広くなります。',
             'The 90% range treats feeds as independent. Feeds from one publisher tend to lapse together, so the real '
             'spread is wider.']
    if sc:
        lines += ['', f'## 結果 / Result ({TARGET_DAY.isoformat()})', '',
                  f'- prior: {sc["prior_lapsed"]} / {sc["prior_lapsed"] + sc["prior_not"]} lapsed; other: '
                  f'{sc["other_lapsed"]} / {sc["other_lapsed"] + sc["other_not"]}; total {sc["lapsed"]}',
                  f'- p_one_sided = {sc["p_one_sided"]}']
    lines += ['', 'Source: GTFS Data Repository API v2 (https://gtfs-data.jp/) and the lapse census in this repository. '
              'Place names in cohort.csv are records of fact, not judgements. Made by MV2 of Munim, Inc. with AI agents '
              'working in MV2\'s name. Data CC BY 4.0.', '']
    return '\n'.join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--feeds-json', help='a saved copy of the API\'s /feeds answer (default: fetch it)')
    ap.add_argument('--census', required=True, help='folder of the census (feeds.csv, lapses.csv, repeat_cliff.csv)')
    ap.add_argument('--as-of', help='the day the forecast is recorded (YYYY-MM-DD); default: today in Japan')
    ap.add_argument('--score', help='a later census lapses.csv; feeds with a lapse that began on 2027-04-01 count as lapsed')
    ap.add_argument('--cohort', help='with --score: the cohort.csv recorded before the day (default: rebuild it)')
    ap.add_argument('--min-feeds', type=int, default=400)
    ap.add_argument('--out', default='/out')
    a = ap.parse_args(argv)
    as_of = day(a.as_of) if a.as_of else dt.datetime.now(JST).date()
    lapse_rows = read_csv(os.path.join(a.census, 'lapses.csv'))
    census_keys = {(r['organization_id'], r['feed_id']) for r in read_csv(os.path.join(a.census, 'feeds.csv'))}
    repeat_rows = read_csv(os.path.join(a.census, 'repeat_cliff.csv'))
    if a.cohort:
        rows = read_csv(a.cohort)
    else:
        text = open(a.feeds_json, encoding='utf-8').read() if a.feeds_json else fetch(FEEDS_URL)
        feeds = feed_list(json.loads(text))
        if len(feeds) < a.min_feeds:
            sys.exit(f'the feed list has {len(feeds)} feeds, fewer than {a.min_feeds}')
        rows = cohort(feeds, lapse_rows, census_keys)
    if not rows:
        sys.exit(f'no active feed ends on {FY_END.isoformat()}')
    fc = forecast(rows, repeat_rows)
    sc = None
    if a.score:
        hits = {k for k, s in lapse_starts(read_csv(a.score)).items() if TARGET_DAY in s}
        sc = score(rows, hits)
    out = os.path.join(a.out, 'forecast', TARGET_DAY.isoformat())
    os.makedirs(out, exist_ok=True)
    write_csv(os.path.join(out, 'scored.csv' if sc else 'cohort.csv'), SCORE_COLS if sc else COLS, rows)
    summary = {'recorded': as_of.isoformat(), 'source': FEEDS_URL + (' (saved copy)' if a.feeds_json else ''),
               'census': a.census, 'forecast': fc, 'result': sc,
               'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
               'by': 'MV2 of Munim, Inc. (made with AI agents working in MV2\'s name)'}
    with open(os.path.join(out, 'score.json' if sc else 'forecast.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    with open(os.path.join(out, 'score.md' if sc else 'forecast.md'), 'w', encoding='utf-8') as f:
        f.write(markdown(fc, as_of, sc))
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
