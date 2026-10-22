# recovery_forecast.py - for every lapse still open on the census day, the chance that it is over (a valid file exists
# again) within 30 and 90 days, read off the Kaplan-Meier curve of all lapses given how long each has lasted so far,
# and the expected number of recoveries with a rough 90% range (Poisson-binomial, lapses treated as independent).
# Recorded before the horizon days; --score checks the forecast against a later census's lapses.csv.
# Uses lapse_survival.py from this folder. Standard library only.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import argparse
import csv
import datetime
import json
import os
import time

import lapse_survival as ls

HORIZONS = (30, 90)


def is_open(r):
    return str(r['ongoing']).strip().lower() == 'true'


def open_lapses(rows, as_of):
    """Lapses still running on the census day. A lapse marked ongoing whose end is before the census day stopped being
    followed when its feed was marked discontinued, so it cannot recover and is left out."""
    return [r for r in rows if is_open(r) and r['end'] == as_of]


def poisson_binomial(ps):
    """Distribution of the number of successes among independent events with probabilities ps."""
    dist = [1.0]
    for p in ps:
        new = [0.0] * (len(dist) + 1)
        for k, q in enumerate(dist):
            new[k] += q * (1 - p)
            new[k + 1] += q * p
        dist = new
    return dist


def quantile(dist, q):
    """Smallest count whose cumulative probability reaches q."""
    c = 0.0
    for k, x in enumerate(dist):
        c += x
        if c >= q - 1e-9:
            return k
    return len(dist) - 1


def forecast(rows, as_of, horizons=HORIZONS):
    steps = ls.km([(s['days'], s['ended']) for s in ls.spells(rows)])
    day = datetime.date.fromisoformat(as_of)
    lapses, probs = [], {h: [] for h in horizons}
    for r in open_lapses(rows, as_of):
        age = int(r['days'])
        s0 = ls.surv_at(steps, age)
        item = {'organization_id': r['organization_id'], 'feed_id': r['feed_id'], 'feed_name': r.get('feed_name', ''),
                'pref_id': r.get('pref_id', ''), 'start': r['start'], 'age_days': age,
                'april_1': r['start'][5:10] == '04-01'}
        for h in horizons:
            p = 1 - ls.surv_at(steps, age + h) / s0 if s0 > 0 else 1.0
            probs[h].append(p)
            item[f'p_over_within_{h}d'] = round(p, 4)
        lapses.append(item)
    out = []
    for h in horizons:
        dist = poisson_binomial(probs[h])
        out.append({'horizon_days': h, 'last_lapse_day': (day + datetime.timedelta(days=h)).isoformat(),
                    'open_lapses': len(probs[h]), 'expected_recoveries': round(sum(probs[h]), 2),
                    'median': quantile(dist, 0.5), 'range_90': [quantile(dist, 0.05), quantile(dist, 0.95)]})
    return {'as_of': as_of, 'excluded_discontinued': sum(1 for r in rows if is_open(r) and r['end'] != as_of),
            'horizons': out, 'lapses': lapses}


def score(fc, later_rows, later_as_of):
    """A lapse counts as over by a horizon if the later census shows it ended (same feed, same start) on or before the
    horizon's last lapse day; 'known by then' also needs the file that ended it to have been published by that day.
    'missing' = no lapse with that start in the later census (filled in by a back-dated file, or the feed left)."""
    later = {}
    for r in later_rows:
        later[(r['organization_id'], r['feed_id'], r['start'])] = r
    res = []
    for h in fc['horizons']:
        last = h['last_lapse_day']
        row = {'horizon_days': h['horizon_days'], 'last_lapse_day': last, 'expected_recoveries': h['expected_recoveries'],
               'range_90': h['range_90']}
        if later_as_of < last:
            row['status'] = 'not_due'
            res.append(row)
            continue
        counts = {'over': 0, 'over_known_by_then': 0, 'still_open': 0, 'missing': 0}
        for item in fc['lapses']:
            r = later.get((item['organization_id'], item['feed_id'], item['start']))
            if r is None:
                counts['missing'] += 1
            elif not is_open(r) and r['end'] <= last:
                counts['over'] += 1
                if (r.get('ended_by_file_published') or '9999') <= last:
                    counts['over_known_by_then'] += 1
            else:
                counts['still_open'] += 1
        row.update(counts)
        lo, hi = h['range_90']
        row['status'] = 'scored'
        row['within_range_90'] = lo <= counts['over'] <= hi
        res.append(row)
    return {'forecast_as_of': fc['as_of'], 'later_census_as_of': later_as_of, 'horizons': res}


def markdown(fc):
    lines = ['# 続いている空白はいつ終わるか / When will the open lapses end? (recorded in advance)', '',
             f'調査日（{fc["as_of"]}）にまだ続いていた空白{len(fc["lapses"])}回それぞれについて、全空白のカプラン・マイヤー曲線と'
             'それまでの長さから、30日・90日以内に有効なデータが戻る確率を求め、戻る件数の見込みを記録しました。',
             f'For each of the {len(fc["lapses"])} lapses still open on the census day ({fc["as_of"]}), the chance that a '
             'valid file exists again within 30 and 90 days, from the Kaplan-Meier curve of all lapses given how long the '
             'lapse has lasted so far, and the expected number that end.', '',
             '| horizon | last lapse day | open lapses | expected to end | median | rough 90% |', '|---|---|---|---|---|---|']
    for h in fc['horizons']:
        lines.append(f'| {h["horizon_days"]} d | {h["last_lapse_day"]} | {h["open_lapses"]} | {h["expected_recoveries"]} | '
                     f'{h["median"]} | {h["range_90"][0]}–{h["range_90"][1]} |')
    hz = [h['horizon_days'] for h in fc['horizons']]
    lines += ['', '| organization_id | feed_id | start | days so far | April 1 | ' +
              ' | '.join(f'P(over within {h} d)' for h in hz) + ' |', '|---|---|---|---|---|' + '---|' * len(hz)]
    for x in sorted(fc['lapses'], key=lambda x: (x['age_days'], x['organization_id'], x['feed_id'])):
        lines.append(f'| {x["organization_id"]} | {x["feed_id"]} | {x["start"]} | {x["age_days"]} | '
                     f'{"yes" if x["april_1"] else "no"} | ' +
                     ' | '.join(f'{x[f"p_over_within_{h}d"]:.2f}' for h in hz) + ' |')
    lines += ['', f'Left out: {fc["excluded_discontinued"]} open lapse(s) whose feed was marked discontinued before the '
              'census day.', '',
              '限界: 同じ提供者のデータはまとめて戻ることが多く、幅は実際より狭めです。曲線の後ろの方（数百日）は空白が少なく不確かで、'
              '最後に空白が終わった長さより長く続いている空白は、確率0と出ます。',
              'Limits: one publisher\'s feeds often recover together, so the real range is wider. The tail of the curve '
              '(hundreds of days) rests on few lapses; a lapse already longer than the longest one that ever ended gets '
              'probability 0. Scored with a later census (tools/recovery_forecast.py --score).', '',
              'Source: GTFS Data Repository API v2 (https://gtfs-data.jp/) via the lapse census in this repository. '
              'Made by MV2 of Munim, Inc. with AI agents working in MV2\'s name. Data CC BY 4.0.', '']
    return '\n'.join(lines)


def write_csv(path, items):
    if not items:
        return
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(items[0]))
        w.writeheader()
        w.writerows(items)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--lapses', required=True, help="the census's lapses.csv")
    ap.add_argument('--as-of', required=True, help='census day of --lapses (YYYY-MM-DD)')
    ap.add_argument('--out', default='/out')
    ap.add_argument('--score', help='with --forecast-json: a later census lapses.csv; --as-of is then its census day')
    ap.add_argument('--forecast-json', help='recovery.json written earlier by this script')
    a = ap.parse_args(argv)
    if a.score:
        with open(a.forecast_json, encoding='utf-8') as f:
            fc = json.load(f)
        res = score(fc, ls.read_csv(a.score), a.as_of)
        out = os.path.join(a.out, 'forecast', 'recovery', fc['as_of'], f'score-{a.as_of}')
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, 'score.json'), 'w', encoding='utf-8') as f:
            json.dump(res, f, ensure_ascii=False, indent=1)
        print(json.dumps(res, ensure_ascii=False))
        return
    fc = forecast(ls.read_csv(a.lapses), a.as_of)
    fc['generated_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    fc['by'] = 'MV2 of Munim, Inc. (made with AI agents working in MV2\'s name)'
    out = os.path.join(a.out, 'forecast', 'recovery', a.as_of)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'recovery.json'), 'w', encoding='utf-8') as f:
        json.dump(fc, f, ensure_ascii=False, indent=1)
    with open(os.path.join(out, 'recovery.md'), 'w', encoding='utf-8') as f:
        f.write(markdown(fc))
    write_csv(os.path.join(out, 'recovery.csv'), fc['lapses'])
    print(json.dumps({k: v for k, v in fc.items() if k != 'lapses'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
