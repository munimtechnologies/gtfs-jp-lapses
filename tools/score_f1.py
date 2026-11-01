# Scores prediction F1 (chain/predictions-2026-11-01.md) from one run of tools/file_chain.py.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
#
# F1: at least 4 of the 7 feeds below have no file in force on the first day on or after 2026-11-01
# (Japan time) on which the API is read for them.
#
# Rules, written 2026-10-28 before any of the seven was read again:
# - in force: class continuous, break or list_mismatch with in_force_to filled (as pre-registered).
# - none: class expired or not_in_force (as pre-registered).
# - none, discontinued: no chain.csv row and the saved feed list marks the feed discontinued; counted as
#   none and reported separately (as pre-registered).
# - unresolved: anything the pre-registration does not cover (api_failed, no_files, an in-force class
#   without in_force_to, a feed with no end date, a feed gone from the list). These are not guessed:
#   F1 holds if at least 4 are none with every unresolved feed counted as in force, fails if fewer than 4
#   would be none with every unresolved feed counted as none, and is undetermined otherwise.
# - the run's as_of must fall on 2026-11-01..2026-11-05 (Japan time), or the verdict is invalid_date.
import argparse
import csv
import json
import os
import sys

FEEDS = [
    ('tosaden-kotsu', 'GTFS-Tosadentraffic_Airportbus', '2026-10-25'),
    ('rokkashovillage', 'rokkasho-sharedtaxi', '2026-10-30'),
    ('kamigoritown', 'ainorigo', '2026-10-31'),
    ('kamishihorotown', 'kamishihoro', '2026-10-31'),
    ('kamishihorotown', 'kamishihoro-self-bus', '2026-10-31'),
    ('kumanogobobus', 'kumanogobobus_gobo', '2026-10-31'),
    ('nishinomiyacity', 'sakurayamanami', '2026-10-31'),
]
IN_FORCE = ('continuous', 'break', 'list_mismatch')
NONE = ('expired', 'not_in_force')
FIRST, LAST = '2026-11-01', '2026-11-05'
NEED = 4


def feed_list(doc):
    body = doc.get('body') if isinstance(doc, dict) else doc
    return [f for f in body or [] if isinstance(f, dict) and f.get('organization_id') and f.get('feed_id')]


def outcome(row, listed):
    """(outcome, reason) for one feed: row is its chain.csv row or None, listed its feed-list entry or None."""
    if row is not None:
        c = row.get('class') or ''
        if c in IN_FORCE:
            return ('in_force', c) if row.get('in_force_to') else ('unresolved', c + ' without in_force_to')
        if c in NONE:
            return 'none', c
        return 'unresolved', c or 'no class'
    if listed is None:
        return 'unresolved', 'not in the feed list'
    if listed.get('feed_is_discontinued') in (True, 'true'):
        return 'none_discontinued', 'discontinued in the feed list'
    if not listed.get('latest_feed_end_date'):
        return 'unresolved', 'no end date in the feed list'
    return 'unresolved', 'in the feed list but no chain.csv row'


def verdict(outcomes, as_of):
    if not (FIRST <= as_of <= LAST):
        return 'invalid_date'
    none = sum(o in ('none', 'none_discontinued') for o in outcomes)
    unresolved = sum(o == 'unresolved' for o in outcomes)
    if none >= NEED:
        return 'held'
    if none + unresolved < NEED:
        return 'failed'
    return 'undetermined'


def run_folder(chain_dir):
    subs = sorted(d for d in os.listdir(chain_dir) if os.path.isfile(os.path.join(chain_dir, d, 'chain.csv')))
    if len(subs) != 1:
        sys.exit(f'{chain_dir} should hold exactly one <as_of>/chain.csv, found {len(subs)}')
    return os.path.join(chain_dir, subs[0])


def score(chain_dir, feeds_path):
    folder = run_folder(chain_dir)
    with open(os.path.join(folder, 'summary.json'), encoding='utf-8') as f:
        as_of = json.load(f)['as_of']
    with open(os.path.join(folder, 'chain.csv'), encoding='utf-8-sig', newline='') as f:
        rows = {(r['organization_id'], r['feed_id']): r for r in csv.DictReader(f)}
    with open(feeds_path, encoding='utf-8') as f:
        listed = {(x['organization_id'], x['feed_id']): x for x in feed_list(json.load(f))}
    feeds = []
    for org, fid, end in FEEDS:
        r = rows.get((org, fid))
        o, why = outcome(r, listed.get((org, fid)))
        r = r or {}
        feeds.append({'organization_id': org, 'feed_id': fid, 'end_2026_10_23': end, 'outcome': o, 'reason': why,
                      'class': r.get('class', ''), 'in_force_to': r.get('in_force_to', ''),
                      'next_from': r.get('next_from', ''), 'listed_end': r.get('listed_end', ''),
                      'api_discontinued': r.get('api_discontinued', '')})
    counts = {k: sum(x['outcome'] == k for x in feeds)
              for k in ('in_force', 'none', 'none_discontinued', 'unresolved')}
    return {'prediction': 'F1', 'as_of': as_of, 'need': NEED, 'feeds': feeds, 'counts': counts,
            'none_total': counts['none'] + counts['none_discontinued'],
            'verdict': verdict([x['outcome'] for x in feeds], as_of)}


def markdown(res):
    c = res['counts']
    lines = [
        f"# F1の採点 / Scoring F1 ({res['as_of']})",
        '',
        '予測F1：下の7件のうち4件以上は、2026年11月1日以降（日本時間）に最初にAPIを読んだ日に、有効なファイルがない。',
        'Prediction F1: at least 4 of the 7 feeds below have no file in force on the first day on or after 2026-11-01 '
        '(Japan time) on which the API is read for them.',
        '',
        f"Verdict: **{res['verdict']}**. {res['none_total']} of 7 have no file in force "
        f"({c['none_discontinued']} of them because the repository now marks the feed discontinued), "
        f"{c['in_force']} have one, {c['unresolved']} unresolved.",
        '',
        '| organization_id | feed_id | end on 2026-10-23 | class | in_force_to | next_from | outcome |',
        '|---|---|---|---|---|---|---|',
    ]
    for x in res['feeds']:
        lines.append(f"| {x['organization_id']} | {x['feed_id']} | {x['end_2026_10_23']} | {x['class'] or '-'} | "
                     f"{x['in_force_to'] or '-'} | {x['next_from'] or '-'} | {x['outcome']} ({x['reason']}) |")
    lines += ['', 'Limits: the repository\'s validity dates only; no timetable file is read. A day with no published '
              'file is not proof that no bus runs.', '',
              "MV2 of Munim, Inc. · Made with AI agents working in MV2's name. · CC BY 4.0", '']
    return '\n'.join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description='Score prediction F1 from one tools/file_chain.py run.')
    ap.add_argument('--chain-dir', required=True, help='the --out folder of tools/file_chain.py')
    ap.add_argument('--feeds', required=True, help='the saved /feeds answer that file_chain.py read (--feeds-json)')
    ap.add_argument('--out', required=True)
    a = ap.parse_args(argv)
    res = score(a.chain_dir, a.feeds)
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, 'score.json'), 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    with open(os.path.join(a.out, 'score.md'), 'w', encoding='utf-8') as f:
        f.write(markdown(res))
    print(json.dumps({k: res[k] for k in ('as_of', 'verdict', 'none_total', 'counts')}, ensure_ascii=False))
    return res


if __name__ == '__main__':
    main()
