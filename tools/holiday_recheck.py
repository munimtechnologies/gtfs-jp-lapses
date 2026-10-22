# holiday_recheck.py - two readings of the feeds.csv that holiday_check.py writes. (1) horizon: within one file, are
# the later holidays handled as often as the near ones? For 2026-11-03 against each later weekday holiday it counts the
# feeds that handle both days, show the ordinary timetable on both, or switch between them, with an exact sign test
# on the switches. (2) recheck: compare the 2026-10-22 census with a later one (planned for mid-December 2026) and
# score the three predictions recorded on 2026-10-22, before the later census was run
# (holidays/predictions-recheck-2026-12.md). Standard library only.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import argparse
import csv
import json
import os
from collections import Counter
from math import comb

SHOWN = {'ordinary', 'ordinary_std'}
HANDLED = {'no_service', 'sunday', 'saturday', 'special'}
BASE = '2026-11-03'
LATER = ['2026-11-23', '2027-01-11', '2027-02-11', '2027-02-23', '2027-03-22']
NEW_YEAR = ['2026-12-29', '2026-12-30', '2026-12-31', '2027-01-01', '2027-01-02']
TRACKED = NEW_YEAR + LATER[1:]
# Fixed on 2026-10-22, before the later census; scored by predictions() on the first re-check dated in WINDOW.
WINDOW = ('2026-12-10', '2026-12-28')
PREDICTIONS = {
    'R1': 'Of the feeds that on 2026-10-22 handled both 2026-11-03 and 2026-11-23 but showed the ordinary timetable '
          'on 2027-01-11, and that are applicable on 2027-01-11 at the re-check, at most one third handle 2027-01-11 '
          'at the re-check.',
    'R2': 'Of the (feed, New Year day) pairs from 2026-12-29 to 2027-01-02 that showed the ordinary timetable on '
          '2026-10-22 and are applicable at the re-check, fewer than 25% are handled at the re-check.',
    'R3': 'At the re-check, at least 12% of the feeds applicable on 2027-01-11 show the ordinary timetable that day.',
}


def group(c):
    return 'shown' if c in SHOWN else 'handled' if c in HANDLED else None


def read_feeds(path):
    """{(organization_id, feed_id): row} from a holiday_check.py feeds.csv (UTF-8 with BOM)."""
    with open(path, encoding='utf-8-sig', newline='') as f:
        return {(r['organization_id'], r['feed_id']): r for r in csv.DictReader(f)}


def sign_p(a, b):
    """Exact two-sided sign test for a switches one way and b the other; None when there are none."""
    n = a + b
    if not n:
        return None
    return min(1.0, 2 * sum(comb(n, i) for i in range(min(a, b) + 1)) / 2 ** n)


def horizon(rows, base=BASE, later=LATER):
    out = []
    for d in later:
        n = Counter()
        for r in rows.values():
            a, b = group(r.get(base)), group(r.get(d))
            if a and b:
                n[(a, b)] += 1
        h2s, s2h = n[('handled', 'shown')], n[('shown', 'handled')]
        out.append({'date': d, 'feeds': sum(n.values()), 'both_handled': n[('handled', 'handled')],
                    'handled_then_shown': h2s, 'shown_then_handled': s2h, 'both_shown': n[('shown', 'shown')],
                    'sign_test_p': sign_p(h2s, s2h)})
    return out


def cohort_r1(rows):
    """Feeds that handle both November holidays but show the ordinary timetable on 2027-01-11."""
    return sorted(k for k, r in rows.items() if group(r.get('2026-11-03')) == 'handled' and
                  group(r.get('2026-11-23')) == 'handled' and group(r.get('2027-01-11')) == 'shown')


def share_shown(rows, d):
    gs = [group(r.get(d)) for r in rows.values()]
    gs = [g for g in gs if g]
    return sum(g == 'shown' for g in gs), len(gs)


def predictions(before, after, as_of):
    out = {}
    cohort = cohort_r1(before)
    keep = [k for k in cohort if k in after and group(after[k].get('2027-01-11'))]
    fixed = sum(group(after[k]['2027-01-11']) == 'handled' for k in keep)
    out['R1'] = {'cohort': len(cohort), 'applicable_after': len(keep), 'handled_after': fixed,
                 'held': (fixed <= len(keep) / 3) if keep else None}
    n = handled = 0
    for k, r in before.items():
        if k not in after:
            continue
        for d in NEW_YEAR:
            if group(r.get(d)) == 'shown' and group(after[k].get(d)):
                n += 1
                handled += group(after[k][d]) == 'handled'
    out['R2'] = {'pairs': n, 'handled_after': handled, 'share': round(handled / n, 3) if n else None,
                 'held': (handled < 0.25 * n) if n else None}
    k3, n3 = share_shown(after, '2027-01-11')
    kb, nb = share_shown(before, '2027-01-11')
    out['R3'] = {'shown': k3, 'applicable': n3, 'share': round(k3 / n3, 3) if n3 else None,
                 'share_2026_10_22': round(kb / nb, 3) if nb else None, 'held': (k3 >= 0.12 * n3) if n3 else None}
    for key, text in PREDICTIONS.items():
        out[key]['text'] = text
        out[key]['in_window'] = WINDOW[0] <= as_of <= WINDOW[1]
    return out


def changes(before, after):
    rows = []
    for k in sorted(set(before) & set(after)):
        for d in TRACKED:
            a, b = before[k].get(d, ''), after[k].get(d, '')
            if a != b:
                r = after[k]
                rows.append({'organization_id': k[0], 'feed_id': k[1], 'organization_name': r.get('organization_name', ''),
                             'feed_name': r.get('feed_name', ''), 'pref_name': r.get('pref_name', ''), 'date': d,
                             'before': a, 'after': b})
    return rows


def horizon_md(h, title):
    lines = [f'### {title}', '',
             '| 2026-11-03 vs | feeds | both handled | handled → ordinary | ordinary → handled | both ordinary | '
             'sign test p |', '|---|---|---|---|---|---|---|']
    for x in h:
        p = '–' if x['sign_test_p'] is None else f'{x["sign_test_p"]:.2g}'
        lines.append(f'| {x["date"]} | {x["feeds"]} | {x["both_handled"]} | {x["handled_then_shown"]} | '
                     f'{x["shown_then_handled"]} | {x["both_shown"]} | {p} |')
    return lines


NOTE = ['', '"Handled" = no service, the Sunday or Saturday timetable, or a special one; "ordinary" = the ordinary '
        'timetable (classes from holiday_check.py). Feeds not applicable on either day are left out. Made by MV2 of '
        'Munim, Inc. with AI agents working in MV2\'s name. Data CC BY 4.0.', '']


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--before', required=True, help='feeds.csv of the 2026-10-22 census')
    ap.add_argument('--after', help='feeds.csv of a later census')
    ap.add_argument('--as-of', help='YYYY-MM-DD of the later census')
    ap.add_argument('--out', default='/out')
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    before = read_feeds(a.before)
    hb = horizon(before)
    doc = {'feeds': len(before), 'horizon': hb, 'cohort_r1': ['/'.join(k) for k in cohort_r1(before)]}
    with open(os.path.join(a.out, 'horizon.json'), 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    md = ['# 先の祝日ほど抜けるか / Are later holidays left out of the files?', ''] + \
        horizon_md(hb, f'{a.before} ({len(before)} feeds)') + \
        ['', f'Feeds that handle both November holidays but show the ordinary timetable on 2027-01-11: '
             f'{len(doc["cohort_r1"])}'] + NOTE
    with open(os.path.join(a.out, 'horizon.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    print(json.dumps(doc, ensure_ascii=False))
    if not a.after:
        return
    if not a.as_of:
        ap.error('--after needs --as-of')
    after = read_feeds(a.after)
    p = predictions(before, after, a.as_of)
    ch = changes(before, after)
    res = {'as_of': a.as_of, 'feeds_before': len(before), 'feeds_after': len(after),
           'removed': ['/'.join(k) for k in sorted(set(before) - set(after))],
           'added': ['/'.join(k) for k in sorted(set(after) - set(before))],
           'changed_pairs': len(ch), 'predictions': p, 'horizon_after': horizon(after),
           'by': 'MV2 of Munim, Inc. (made with AI agents working in MV2\'s name)'}
    with open(os.path.join(a.out, 'recheck.json'), 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    with open(os.path.join(a.out, 'changes.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['organization_id', 'feed_id', 'organization_name', 'feed_name', 'pref_name',
                                          'date', 'before', 'after'])
        w.writeheader()
        w.writerows(ch)
    held = {True: 'held', False: 'did not hold', None: 'not scorable'}
    md = [f'# 祝日・年末年始の再確認 / Holiday re-check ({a.as_of} against 2026-10-22)', '',
          f'Feeds: {len(before)} then {len(after)} ({len(res["removed"])} gone, {len(res["added"])} new); '
          f'{len(ch)} (feed, day) classes changed (changes.csv).', '',
          '## 2026-10-22に記録した予測 / Predictions recorded on 2026-10-22', '', '| | prediction | result | |',
          '|---|---|---|---|']
    for key in ('R1', 'R2', 'R3'):
        x = p[key]
        r = {k: v for k, v in x.items() if k not in ('text', 'held', 'in_window')}
        tag = held[x['held']] + ('' if x['in_window'] else ' (outside the planned window)')
        md.append(f'| {key} | {x["text"]} | {json.dumps(r, ensure_ascii=False)} | {tag} |')
    md += [''] + horizon_md(res['horizon_after'], f'Horizon at the re-check ({a.as_of})') + NOTE
    with open(os.path.join(a.out, 'recheck.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    print(json.dumps(res, ensure_ascii=False))


if __name__ == '__main__':
    main()
