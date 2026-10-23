# file_chain.py - looks ahead along each active feed's published files in the GTFS Data Repository
# (https://gtfs-data.jp/): the file in force today and any later files already published (next_1, next_2 ...).
# The repository's list gives one end date per feed, the end of the latest file it holds, which can be a later
# file not yet in force. This tool reads each feed's API entry once and says, for every active feed, when the file
# in force today ends, when the next file starts and how far ahead it was published, and whether the published
# files run without a break from today to the listed end date. Only the files' from_date, to_date and published_at
# as the repository gives them are used; no timetable file is downloaded. Standard library only.
# The predictions in PREDICTIONS were fixed in this file before its first run.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import argparse
import csv
import datetime as dt
import json
import os
import re
import statistics
import sys
import time
import urllib.parse
import urllib.request

API = 'https://api.gtfs-data.jp/v2'
UA = 'GTFS file-chain check - MV2 of Munim, Inc. (mv2@munimtech.com)'
JST = dt.timezone(dt.timedelta(hours=9))
WARN_DAYS = 60
ONE = dt.timedelta(days=1)
PREFS = ['北海道', '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県', '茨城県', '栃木県', '群馬県', '埼玉県',
         '千葉県', '東京都', '神奈川県', '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県', '岐阜県', '静岡県',
         '愛知県', '三重県', '滋賀県', '京都府', '大阪府', '兵庫県', '奈良県', '和歌山県', '鳥取県', '島根県', '岡山県',
         '広島県', '山口県', '徳島県', '香川県', '愛媛県', '高知県', '福岡県', '佐賀県', '長崎県', '熊本県', '大分県',
         '宮崎県', '鹿児島県', '沖縄県']
ENDED = re.compile('廃止|休止|運休|運行終了|運行を終了')
MEMO_CHARS = 80
CLASSES = ['continuous', 'break', 'not_in_force', 'list_mismatch', 'no_files', 'api_failed', 'expired']
OK = ['continuous', 'break', 'not_in_force', 'list_mismatch']
COLUMNS = ['organization_id', 'feed_id', 'organization_name', 'feed_name', 'pref_id', 'pref_name', 'license',
           'listed_end', 'class', 'in_force_from', 'in_force_to', 'in_force_days_left', 'later_files', 'next_from',
           'next_published', 'next_lead_days', 'covered_to', 'break_from', 'break_days', 'resume_from',
           'break_within_60', 'continued', 'api_discontinued', 'memo_ended', 'in_force_memo']
# Fixed before the first run (2026-10-23). Shares are of the feeds whose API entry was read and has files (OK).
PREDICTIONS = {
    'C1': 'Fewer than 2% of the checked feeds have a break (a day with no published file) between today and their '
          'listed end date, counting feeds with no file in force today (classes break + not_in_force).',
    'C2': 'Between 5% and 30% of the checked feeds already have at least one later file published.',
    'C3': 'Of the checked feeds whose file in force today ends within 60 days, between 10% and 40% already have a '
          'later file that continues it with no break.',
    'C4': 'The median lead time of the later files (start date minus publication date in Japan time) is at least 14 '
          'days.',
}


def day(v):
    try:
        return dt.date.fromisoformat((v or '').strip()[:10])
    except ValueError:
        return None


def jst_day(ts):
    """'2026-10-13T15:59:14.520716+09:00' -> its date in Japan time."""
    if not ts:
        return None
    try:
        t = dt.datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
    except ValueError:
        return day(ts)
    return (t.astimezone(JST) if t.tzinfo else t).date()


def iso(d):
    return d.isoformat() if d else ''


def clean(text):
    """One line, no table-breaking bars."""
    return ' '.join(str(text or '').replace('|', '／').split())


def pref(pid):
    try:
        i = int(pid or 0)
    except (TypeError, ValueError):
        i = 0
    return (i, PREFS[i - 1]) if 1 <= i <= 47 else (i, '')


def read_csv(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, columns):
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def get_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode('utf-8'))


def fetch_body(org, feed):
    """The body of the feed's API entry, or None."""
    q = lambda s: urllib.parse.quote(s, safe='')  # noqa: E731
    try:
        data = get_json(f'{API}/organizations/{q(org)}/feeds/{q(feed)}')
    except Exception:  # noqa: BLE001 - recorded as api_failed
        return None
    return data.get('body') if isinstance(data, dict) and data.get('code') == 200 else None


def feed_list(doc):
    """The API's /feeds answer ({'body': [...]}) or a bare list -> the feed dicts that have both ids."""
    body = doc.get('body') if isinstance(doc, dict) else doc
    return [f for f in body or [] if isinstance(f, dict) and f.get('organization_id') and f.get('feed_id')]


def base_row(f):
    pid, pname = pref(f.get('feed_pref_id'))
    row = {c: '' for c in COLUMNS}
    row.update({'organization_id': f['organization_id'], 'feed_id': f['feed_id'],
                'organization_name': clean(f.get('organization_name')), 'feed_name': clean(f.get('feed_name')),
                'pref_id': pid, 'pref_name': pname, 'license': f.get('feed_license') or '',
                'listed_end': iso(day(f.get('latest_feed_end_date')))})
    return row


def chain(f, body, as_of):
    """One output row for one active feed whose listed end is today or later, given its API body (None if the
    request failed)."""
    out = base_row(f)
    listed = day(f.get('latest_feed_end_date'))
    if body is None:
        out['class'] = 'api_failed'
        return out
    out['api_discontinued'] = 'yes' if body.get('is_discontinued') else 'no'
    files = sorted((x for x in body.get('gtfs_files') or [] if day(x.get('from_date')) and day(x.get('to_date'))),
                   key=lambda x: (day(x['from_date']), day(x['to_date'])))
    if not files:
        out['class'] = 'no_files'
        return out
    now = [x for x in files if day(x['from_date']) <= as_of <= day(x['to_date'])]
    later = [x for x in files if day(x['from_date']) > as_of]
    out['later_files'] = len(later)
    if later:
        nxt, pub = later[0], jst_day(later[0].get('published_at'))
        out.update({'next_from': nxt['from_date'], 'next_published': iso(pub),
                    'next_lead_days': (day(nxt['from_date']) - pub).days if pub else ''})
    covered, brk = as_of - ONE, None
    for x in files:
        a, b = day(x['from_date']), day(x['to_date'])
        if b <= covered:
            continue
        if a > covered + ONE:
            brk = (covered + ONE, a)
            break
        covered = b
    if covered >= as_of:
        out['covered_to'] = iso(covered)
    if now:
        to = max(day(x['to_date']) for x in now)
        memo_file = next((x for x in now if x.get('rid') == 'current'), max(now, key=lambda x: day(x['to_date'])))
        out.update({'in_force_from': iso(min(day(x['from_date']) for x in now)), 'in_force_to': iso(to),
                    'in_force_days_left': (to - as_of).days, 'continued': 'yes' if covered > to else 'no',
                    'memo_ended': 'yes' if ENDED.search(memo_file.get('memo') or '') else 'no',
                    'in_force_memo': clean(memo_file.get('memo'))[:MEMO_CHARS]})
    if not now:
        out['class'] = 'not_in_force'
        out.update({'break_from': iso(as_of), 'resume_from': out['next_from'],
                    'break_days': (day(out['next_from']) - as_of).days if out['next_from'] else ''})
    elif covered >= listed:
        out['class'] = 'continuous'
    elif brk:
        out['class'] = 'break'
        out.update({'break_from': iso(brk[0]), 'resume_from': iso(brk[1]), 'break_days': (brk[1] - brk[0]).days})
    else:
        out['class'] = 'list_mismatch'
    if out['break_from']:
        out['break_within_60'] = 'yes' if (day(out['break_from']) - as_of).days <= WARN_DAYS else 'no'
    return out


def quartiles(xs):
    if not xs:
        return {'n': 0}
    xs = sorted(xs)
    q = statistics.quantiles(xs, n=4, method='inclusive') if len(xs) > 1 else [xs[0]] * 3
    return {'n': len(xs), 'min': xs[0], 'q1': q[0], 'median': statistics.median(xs), 'q3': q[2], 'max': xs[-1]}


def share(a, b):
    return round(a / b, 4) if b else None


def summarise(rows, counts, as_of):
    ok = [r for r in rows if r['class'] in OK]
    cls = {c: sum(r['class'] == c for r in rows) for c in CLASSES}
    breaks = cls['break'] + cls['not_in_force']
    with_later = sum(1 for r in ok if int(r['later_files'] or 0) > 0)
    ending = [r for r in ok if r['in_force_days_left'] != '' and int(r['in_force_days_left']) <= WARN_DAYS]
    continued = sum(r['continued'] == 'yes' for r in ending)
    hidden = sum(1 for r in ending if (day(r['listed_end']) - as_of).days > WARN_DAYS)
    leads = [int(r['next_lead_days']) for r in ok if r['next_lead_days'] != '']
    lead = quartiles(leads)
    s = {'as_of': iso(as_of), 'counts': counts, 'classes': cls, 'checked_ok': len(ok), 'breaks': breaks,
         'break_within_60': sum(r['break_within_60'] == 'yes' for r in rows),
         'with_later_file': with_later, 'in_force_ends_within_60': len(ending),
         'in_force_ends_within_60_continued': continued,
         'in_force_ends_within_60_listed_later': hidden,
         'memo_ended': sum(r['memo_ended'] == 'yes' for r in ok),
         'api_discontinued': sum(r['api_discontinued'] == 'yes' for r in rows),
         'lead_days': lead, 'lead_days_under_7': sum(1 for x in leads if x < 7)}
    p = {'C1': (share(breaks, len(ok)), share(breaks, len(ok)) is not None and breaks / len(ok) < 0.02),
         'C2': (share(with_later, len(ok)), share(with_later, len(ok)) is not None
                and 0.05 <= with_later / len(ok) <= 0.30),
         'C3': (share(continued, len(ending)), share(continued, len(ending)) is not None
                and 0.10 <= continued / len(ending) <= 0.40),
         'C4': (lead.get('median'), lead.get('median') is not None and lead['median'] >= 14)}
    s['predictions'] = {k: {'text': PREDICTIONS[k], 'value': v, 'held': held} for k, (v, held) in p.items()}
    s['generated_at'] = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    s['by'] = "MV2 of Munim, Inc. (made with AI agents working in MV2's name)"
    return s


def pct(x):
    return '' if x is None else f'{100 * x:.1f}%'


def report(rows, s):
    c, k = s['classes'], s['counts']
    lead = s['lead_days']
    lines = [f'# 公開済みのファイルのつながり / The chain of published files ({s["as_of"]})', '',
             'GTFSデータリポジトリの一覧にある有効なデータそれぞれについて、APIを1回読み、いま有効なファイルがいつ終わるか、'
             '次のファイルがいつ始まり何日前に公開されたか、今日から掲載上の期限まで公開済みのファイルがすき間なくつながって'
             'いるかを確かめました。掲載上の期限は、まだ有効になっていない後続のファイルの期限であることがあります。',
             'For each active feed in the GTFS Data Repository list, the API was read once: when the file in force today '
             'ends, when the next file starts and how many days ahead it was published, and whether the published files '
             'run without a break from today to the end date the list gives (which can be the end of a later file not '
             'yet in force).', '',
             f'- 一覧 / in the list: {k["feeds_in_list"]}; 運行終了 / discontinued: {k["discontinued"]}; '
             f'期限なし / no end date: {k["no_end_date"]}; 有効 / active: {k["active"]}; '
             f'期限切れ / expired (not read): {c["expired"]}',
             f'- 読めたデータ / read with files: {s["checked_ok"]}; つながっている / continuous: {c["continuous"]}; '
             f'途中にすき間 / break: {c["break"]}; 今日有効なファイルなし / nothing in force today: {c["not_in_force"]}; '
             f'一覧の期限と合わない / list mismatch: {c["list_mismatch"]}; ファイルなし / no files: {c["no_files"]}; '
             f'API失敗 / API failed: {c["api_failed"]}',
             f'- 後続のファイルが公開済み / with a later file published: {s["with_later_file"]} '
             f'({pct(share(s["with_later_file"], s["checked_ok"]))})',
             f'- いま有効なファイルが{WARN_DAYS}日以内に終わる / file in force ends within {WARN_DAYS} days: '
             f'{s["in_force_ends_within_60"]}; うち後続のファイルがつなぐ / continued by a later file: '
             f'{s["in_force_ends_within_60_continued"]}; うち掲載上の期限は{WARN_DAYS}日より先 / of which the listed '
             f'end is more than {WARN_DAYS} days away: {s["in_force_ends_within_60_listed_later"]}',
             f'- 次のファイルの公開から開始までの日数 / lead time of the next file (days): n {lead["n"]}'
             + (f', median {lead["median"]}, quartiles {lead["q1"]}–{lead["q3"]}, range {lead["min"]}–{lead["max"]}; '
                f'under 7 days: {s["lead_days_under_7"]}' if lead['n'] else ''),
             f'- いま有効なファイルのメモに廃止・休止・運休などの語 / note on the file in force mentions abolition or '
             f'suspension: {s["memo_ended"]}; APIで運行終了の印 / marked discontinued in the API: {s["api_discontinued"]}',
             '', '## 事前に記録した予測 / Predictions fixed before the run', '']
    for key, p in s['predictions'].items():
        v = p['value']
        shown = pct(v) if key != 'C4' else ('' if v is None else f'{v} days')
        lines.append(f'- {key}: {p["text"]} Result: {shown}, '
                     f'{"held" if p["held"] else "did not hold"}.')
    lines += ['', '## すき間・今日有効なファイルなし・一覧と合わない / Breaks, nothing in force, list mismatch', '',
              '| organization | feed | pref | listed end | class | in force to | break from | days | resumes | memo |',
              '|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        if r['class'] in ('break', 'not_in_force', 'list_mismatch'):
            lines.append(f'| {r["organization_name"]} | {r["feed_name"]} | {r["pref_name"]} | {r["listed_end"]} | '
                         f'{r["class"]} | {r["in_force_to"]} | {r["break_from"]} | {r["break_days"]} | '
                         f'{r["resume_from"]} | {r["in_force_memo"]} |')
    lines += ['', f'## いま有効なファイルが{WARN_DAYS}日以内に終わるデータ / File in force ends within {WARN_DAYS} days', '',
              '| organization | feed | pref | in force to | days left | next file from | published | continued | '
              'listed end |', '|---|---|---|---|---|---|---|---|---|']
    ending = sorted((r for r in rows if r['class'] in OK and r['in_force_days_left'] != ''
                     and int(r['in_force_days_left']) <= WARN_DAYS),
                    key=lambda r: (int(r['in_force_days_left']), r['organization_id'], r['feed_id']))
    for r in ending:
        lines.append(f'| {r["organization_name"]} | {r["feed_name"]} | {r["pref_name"]} | {r["in_force_to"]} | '
                     f'{r["in_force_days_left"]} | {r["next_from"]} | {r["next_published"]} | {r["continued"]} | '
                     f'{r["listed_end"]} |')
    lines += ['', 'Limits: only the from_date, to_date and published_at the repository gives for each file are used; '
              'the files\' own calendars are not read, so a file can run out of service days before its to_date (see '
              'calgap/2026-10-22/). Old files no longer in the API are not seen. The API was read once per feed on the '
              'day above. A break in the published files is not proof that no bus runs. Place names in the data are '
              'records of fact, not judgements.', '',
              f'Generated {s["generated_at"]}. Source: GTFS Data Repository API v2 (https://gtfs-data.jp/); each '
              'feed\'s publisher and licence are in chain.csv. Made by MV2 of Munim, Inc. with AI agents working in '
              'MV2\'s name. Data CC BY 4.0.']
    return '\n'.join(lines) + '\n'


def run(feeds, as_of, fetch=fetch_body, pause=1.0):
    """(rows, counts) for the feed list. Discontinued feeds and feeds with no listed end are counted, not listed;
    expired feeds are listed with class expired and not read."""
    counts = {'feeds_in_list': len(feeds), 'discontinued': 0, 'no_end_date': 0, 'active': 0}
    rows, calls = [], 0
    for f in feeds:
        if f.get('feed_is_discontinued') in (True, 'true'):
            counts['discontinued'] += 1
            continue
        listed = day(f.get('latest_feed_end_date'))
        if not listed:
            counts['no_end_date'] += 1
            continue
        counts['active'] += 1
        if listed < as_of:
            row = base_row(f)
            row['class'] = 'expired'
            rows.append(row)
            continue
        if calls and pause:
            time.sleep(pause)
        calls += 1
        rows.append(chain(f, fetch(f['organization_id'], f['feed_id']), as_of))
    order = {c: i for i, c in enumerate(CLASSES)}
    rows.sort(key=lambda r: (order[r['class']], r['break_from'] or '9999', r['organization_id'], r['feed_id']))
    return rows, counts


def main(argv=None, fetch=fetch_body):
    ap = argparse.ArgumentParser(description='Look ahead along each active feed\'s published files.')
    ap.add_argument('--as-of', help='the day to check (YYYY-MM-DD); default: today in Japan')
    ap.add_argument('--feeds-json', help='a saved copy of the API\'s /feeds answer (default: fetch it)')
    ap.add_argument('--min-feeds', type=int, default=400, help='stop if the list has fewer feeds than this')
    ap.add_argument('--pause', type=float, default=1.0)
    ap.add_argument('--out', required=True)
    a = ap.parse_args(argv)
    as_of = day(a.as_of) if a.as_of else dt.datetime.now(JST).date()
    if a.feeds_json:
        with open(a.feeds_json, encoding='utf-8') as f:
            doc = json.load(f)
    else:
        doc = get_json(f'{API}/feeds')
    feeds = feed_list(doc)
    if len(feeds) < a.min_feeds:
        sys.exit(f'the feed list has {len(feeds)} feeds, fewer than {a.min_feeds}')
    rows, counts = run(feeds, as_of, fetch, a.pause)
    s = summarise(rows, counts, as_of)
    out = os.path.join(a.out, iso(as_of))
    os.makedirs(out, exist_ok=True)
    write_csv(os.path.join(out, 'chain.csv'), rows, COLUMNS)
    with open(os.path.join(out, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(s, f, ensure_ascii=False, indent=1)
    with open(os.path.join(out, 'chain.md'), 'w', encoding='utf-8') as f:
        f.write(report(rows, s))
    print(json.dumps(s, ensure_ascii=False))
    return s


if __name__ == '__main__':
    main()
