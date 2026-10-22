# holiday_check.py - do the files of Japan's open bus timetables in the GTFS Data Repository (https://gtfs-data.jp/)
# know the national holidays and the New Year break? For every active feed with an open licence it downloads the
# current file and, for each holiday from April 2026 to March 2027, compares the services that run that day with an
# ordinary day of the same weekday and with the nearest Sunday and Saturday. The file then shows the ordinary timetable
# on the holiday, no service, the Sunday or Saturday timetable, or something else. Reads calendar.txt,
# calendar_dates.txt, trips.txt and feed_info.txt only; no timetable data is kept. Standard library only.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import argparse
import csv
import datetime as dt
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from collections import Counter

API = 'https://api.gtfs-data.jp/v2'
UA = 'GTFS holiday check - MV2 of Munim, Inc. (mv2@munimtech.com)'
JST = dt.timezone(dt.timedelta(hours=9))
ONE = dt.timedelta(days=1)
# Open licences only: CC BY (any version), CC0, PDL 1.0.
LICENSE = re.compile(r'^\s*(CC[ -]?BY|CC0|PDL)', re.I)
WEEK = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
WD_JA = ['月', '火', '水', '木', '金', '土', '日']
WD_EN = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
PREFS = ['北海道', '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県', '茨城県', '栃木県', '群馬県',
         '埼玉県', '千葉県', '東京都', '神奈川県', '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県',
         '岐阜県', '静岡県', '愛知県', '三重県', '滋賀県', '京都府', '大阪府', '兵庫県', '奈良県', '和歌山県',
         '鳥取県', '島根県', '岡山県', '広島県', '山口県', '徳島県', '香川県', '愛媛県', '高知県', '福岡県',
         '佐賀県', '長崎県', '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県']

# Japan's national holidays from April 2026 to March 2027 (Cabinet Office list, read 2026-10-22), with the '休日' days
# the holiday law adds: a substitute holiday after a Sunday holiday, and a day between two holidays.
HOLIDAYS = {
    '2026-04-29': ('昭和の日', 'Showa Day'),
    '2026-05-03': ('憲法記念日', 'Constitution Day'),
    '2026-05-04': ('みどりの日', 'Greenery Day'),
    '2026-05-05': ('こどもの日', "Children's Day"),
    '2026-05-06': ('休日（振替休日）', 'substitute holiday'),
    '2026-07-20': ('海の日', 'Marine Day'),
    '2026-08-11': ('山の日', 'Mountain Day'),
    '2026-09-21': ('敬老の日', 'Respect for the Aged Day'),
    '2026-09-22': ('休日（国民の休日）', 'day between two holidays'),
    '2026-09-23': ('秋分の日', 'Autumnal Equinox Day'),
    '2026-10-12': ('スポーツの日', 'Sports Day'),
    '2026-11-03': ('文化の日', 'Culture Day'),
    '2026-11-23': ('勤労感謝の日', 'Labour Thanksgiving Day'),
    '2027-01-01': ('元日', "New Year's Day"),
    '2027-01-11': ('成人の日', 'Coming of Age Day'),
    '2027-02-11': ('建国記念の日', 'National Foundation Day'),
    '2027-02-23': ('天皇誕生日', "Emperor's Birthday"),
    '2027-03-21': ('春分の日', 'Vernal Equinox Day'),
    '2027-03-22': ('休日（振替休日）', 'substitute holiday'),
}
# The New Year break (年末年始) that many operators run differently, besides New Year's Day itself.
YEAR_END = ['2026-12-29', '2026-12-30', '2026-12-31', '2027-01-02', '2027-01-03']


def _span(a, b):
    d, out = dt.date.fromisoformat(a), set()
    while d <= dt.date.fromisoformat(b):
        out.add(d)
        d += ONE
    return out


# Days never used as the ordinary day to compare with: the holidays, the New Year break with a day either side, Obon.
AVOID = ({dt.date.fromisoformat(d) for d in HOLIDAYS} | _span('2026-12-28', '2027-01-04') |
         _span('2026-08-13', '2026-08-16'))
# The days checked: every holiday and New Year day except Sundays, which already have the Sunday timetable.
CHECKS = sorted([(dt.date.fromisoformat(d), ja, en, 'holiday') for d, (ja, en) in HOLIDAYS.items()] +
                [(dt.date.fromisoformat(d), '年末年始', 'New Year break', 'year_end') for d in YEAR_END
                 if d not in HOLIDAYS])
CHECKS = [c for c in CHECKS if c[0].weekday() != 6]
# GTFS-JP's eight standard service_ids. For these, the spec says domestic route-search providers apply the holidays
# even without calendar_dates.txt; other readers (Google and apps abroad) see only what the file says.
STANDARD_IDS = ['平日（月～金）', '平日（月～土）', '土曜', '日曜', '祝日', '日曜・祝日', '土曜・日曜', '土曜・日曜・祝日']
# What each class means for a reader of the file, and the two groups used in the shares.
GROUPS = {'ordinary': 'shown', 'ordinary_std': 'shown', 'no_service': 'encoded', 'sunday': 'encoded',
          'saturday': 'encoded', 'special': 'encoded'}
CLASSES = ['ordinary', 'ordinary_std', 'no_service', 'sunday', 'saturday', 'special', 'same_as_weekend',
           'no_ordinary_service', 'no_reference', 'outside']
# Fixed before any file was read (2026-10-22); scored by predictions() on the first run.
UPCOMING_NATIONAL = ['2026-11-03', '2026-11-23', '2027-01-11', '2027-02-11', '2027-02-23', '2027-03-22']
PREDICTIONS = {
    'P1': 'On 2026-11-03, between 5% and 30% of applicable feeds show the ordinary weekday timetable.',
    'P2': 'Among feeds applicable on all three of 2026-09-21, 09-22 and 09-23, more show the ordinary timetable on '
          '09-22 (the day between two holidays) than on 09-21 or on 09-23.',
    'P3': 'Of the feeds applicable on all six upcoming weekday holidays (2026-11-03 to 2027-03-22), at least 80% treat '
          'all six the same way (all ordinary or all handled).',
    'P4': 'The share showing the ordinary timetable on 2026-12-30 is at least 15 points higher than on 2026-11-03.',
}


def norm_id(s):
    s = (s or '').replace('〜', '～').replace('~', '～').replace('(', '（').replace(')', '）').replace('･', '・')
    return re.sub(r'[\s　]', '', s)


STANDARD = {norm_id(x) for x in STANDARD_IDS}


def is_standard(sid):
    return norm_id(sid) in STANDARD


def gdate(s):
    """'20261103' -> date; anything else -> None."""
    s = (s or '').strip()
    if len(s) == 8 and s.isdigit():
        try:
            return dt.date(int(s[:4]), int(s[4:6]), int(s[6:]))
        except ValueError:
            return None
    return None


def iso_day(s):
    s = (s or '').strip()
    try:
        return dt.date.fromisoformat(s[:10]) if len(s) >= 10 else None
    except ValueError:
        return None


def pref_name(pid):
    return PREFS[pid - 1] if 1 <= pid <= len(PREFS) else 'その他・広域'


def member(zf, name):
    """The member called `name`, at the top of the zip or in a folder (the shallowest one)."""
    best = None
    for n in zf.namelist():
        if n.startswith('__MACOSX') or n.rsplit('/', 1)[-1].lower() != name:
            continue
        if best is None or n.count('/') < best.count('/'):
            best = n
    return best


def zip_rows(zf, name):
    n = member(zf, name)
    if not n:
        return
    with zf.open(n) as raw:
        text = io.TextIOWrapper(raw, encoding='utf-8-sig', errors='replace', newline='')
        for r in csv.DictReader(text):
            yield {(k or '').strip().lstrip('﻿'): (v.strip() if isinstance(v, str) else v) for k, v in r.items()}


def build(read):
    """The service calendar of one file. read(name) yields the rows of calendar.txt, calendar_dates.txt, trips.txt
    and feed_info.txt as dicts. The days checked are those the file covers: feed_info's dates where given, within the
    span of the calendar."""
    cal, add, rem, trips = {}, {}, {}, Counter()
    lo = hi = None
    for r in read('calendar.txt'):
        sid, s, e = r.get('service_id', ''), gdate(r.get('start_date')), gdate(r.get('end_date'))
        if not sid or not s or not e:
            continue
        cal[sid] = (tuple(r.get(w, '0') == '1' for w in WEEK), s, e)
        lo, hi = min(lo or s, s), max(hi or e, e)
    n_cd = 0
    for r in read('calendar_dates.txt'):
        sid, d, t = r.get('service_id', ''), gdate(r.get('date')), r.get('exception_type', '')
        if not sid or not d or t not in ('1', '2'):
            continue
        n_cd += 1
        (add if t == '1' else rem).setdefault(d, set()).add(sid)
        lo, hi = min(lo or d, d), max(hi or d, d)
    for r in read('trips.txt'):
        if r.get('service_id'):
            trips[r['service_id']] += 1
    fs = fe = None
    for r in list(read('feed_info.txt'))[:1]:
        fs, fe = gdate(r.get('feed_start_date')), gdate(r.get('feed_end_date'))
    cover, cover_from = (lo, hi) if lo else None, 'calendar'
    if fs and fe and fs <= fe:
        a, b = (max(fs, lo), min(fe, hi)) if lo else (fs, fe)
        cover, cover_from = ((a, b) if a <= b else None), 'feed_info'
    used = [s for s in trips if s in cal or any(s in x for x in add.values())]
    return {'cal': cal, 'add': add, 'rem': rem, 'trips': trips, 'cover': cover, 'cover_from': cover_from,
            'calendar_dates_rows': n_cd, 'services': len(used), 'standard_services': sum(map(is_standard, used)),
            'cache': {}}


def services(m, d):
    """The service_ids that run at least one trip on day d."""
    if d not in m['cache']:
        on = {sid for sid, (wk, s, e) in m['cal'].items() if s <= d <= e and wk[d.weekday()]}
        on |= m['add'].get(d, set())
        on -= m['rem'].get(d, set())
        m['cache'][d] = frozenset(s for s in on if m['trips'].get(s))
    return m['cache'][d]


def covered(m, d):
    return m['cover'] is not None and m['cover'][0] <= d <= m['cover'][1]


def nearest(m, d, weekday):
    """The closest covered day (within four weeks, earlier first on a tie) on `weekday` that is not a holiday, in
    the New Year break or in Obon."""
    for i in sorted((i for i in range(-28, 29) if i), key=lambda i: (abs(i), i)):
        x = d + dt.timedelta(days=i)
        if x.weekday() == weekday and x not in AVOID and covered(m, x):
            return x
    return None


def classify(m, d):
    """(class, ordinary day compared with). See CLASSES and the README for the meaning of each class."""
    if not covered(m, d):
        return 'outside', None
    ref = nearest(m, d, d.weekday())
    if ref is None:
        return 'no_reference', None
    sr = services(m, ref)
    if not sr:
        return 'no_ordinary_service', ref
    sun, sat = nearest(m, d, 6), nearest(m, d, 5)
    sd = services(m, d)
    if sd == sr:
        others = [services(m, x) for x in (sun, sat) if x is not None]
        if not others:
            return 'no_reference', ref
        if all(o == sr for o in others):  # the ordinary day runs the weekend's services: nothing to tell apart
            return 'same_as_weekend', ref
        return ('ordinary_std' if all(is_standard(s) for s in sd) else 'ordinary'), ref
    if not sd:
        return 'no_service', ref
    if sun is not None and sd == services(m, sun):
        return 'sunday', ref
    if sat is not None and sd == services(m, sat):
        return 'saturday', ref
    return 'special', ref


def check_feed(m):
    checks, refs = {}, {}
    for d, _ja, _en, _kind in CHECKS:
        c, ref = classify(m, d)
        checks[d.isoformat()], refs[d.isoformat()] = c, ref.isoformat() if ref else ''
    return {'checks': checks, 'refs': refs}


def skip_reason(f, as_of):
    if f.get('feed_is_discontinued') in (True, 'true'):
        return 'discontinued'
    end = iso_day(f.get('latest_feed_end_date'))
    if end and end < as_of:
        return 'ended'
    if not LICENSE.match(f.get('feed_license') or ''):
        return 'license'
    return None


def skip_row(f, reason, detail=''):
    return {'organization_id': f.get('organization_id', ''), 'feed_id': f.get('feed_id', ''),
            'feed_name': f.get('feed_name') or '', 'reason': reason, 'detail': str(detail)[:200]}


def run(feeds, as_of, get_zip, pause=2.0, limit=None, budget_s=None, log=print):
    """(results, skipped). get_zip(feed) returns the bytes of the feed's current zip."""
    results, skipped, tried, started = [], [], 0, time.time()
    for f in feeds:
        why = skip_reason(f, as_of)
        if why:
            skipped.append(skip_row(f, why))
            continue
        if (limit is not None and tried >= limit) or (budget_s is not None and time.time() - started > budget_s):
            skipped.append(skip_row(f, 'not_reached'))
            continue
        if tried and pause:
            time.sleep(pause)
        tried += 1
        try:
            data = get_zip(f)
        except Exception as e:  # noqa: BLE001 - any failed download is recorded and skipped
            skipped.append(skip_row(f, 'download_failed', e))
            continue
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                m = build(lambda name: zip_rows(zf, name))
        except Exception as e:  # noqa: BLE001 - a broken file is recorded and skipped
            skipped.append(skip_row(f, 'bad_zip', e))
            continue
        if not m['services']:
            skipped.append(skip_row(f, 'no_trips'))
            continue
        res = check_feed(m)
        res.update(feed=f, cover_from=m['cover_from'], calendar_dates_rows=m['calendar_dates_rows'],
                   services=m['services'], standard_services=m['standard_services'],
                   cover_start=m['cover'][0].isoformat() if m['cover'] else '',
                   cover_end=m['cover'][1].isoformat() if m['cover'] else '')
        results.append(res)
        n = Counter(GROUPS.get(c, '-') for c in res['checks'].values())
        log(f"ok {f['organization_id']}/{f['feed_id']} shown={n['shown']} encoded={n['encoded']}")
    return results, skipped


def shown(results, d, keep=None):
    xs = [r['checks'][d] for r in (keep if keep is not None else results) if r['checks'][d] in GROUPS]
    return sum(GROUPS[x] == 'shown' for x in xs), len(xs)


def ratio(k, n):
    return round(k / n, 3) if n else None


def predictions(results):
    """The four predictions above, scored on this run's files."""
    out = {}
    k, n = shown(results, '2026-11-03')
    s1 = ratio(k, n)
    out['P1'] = {'shown': k, 'applicable': n, 'share': s1, 'held': (0.05 <= k / n <= 0.30) if n else None}
    three = ['2026-09-21', '2026-09-22', '2026-09-23']
    keep = [r for r in results if all(r['checks'][d] in GROUPS for d in three)]
    cnt = {d: shown(results, d, keep)[0] for d in three}
    out['P2'] = {'feeds': len(keep), 'shown': cnt,
                 'held': (cnt[three[1]] > cnt[three[0]] and cnt[three[1]] > cnt[three[2]]) if keep else None}
    keep = [r for r in results if all(r['checks'][d] in GROUPS for d in UPCOMING_NATIONAL)]
    same = sum(len({GROUPS[r['checks'][d]] for d in UPCOMING_NATIONAL}) == 1 for r in keep)
    out['P3'] = {'feeds': len(keep), 'consistent': same, 'share': ratio(same, len(keep)),
                 'held': (same / len(keep) >= 0.80) if keep else None}
    k4, n4 = shown(results, '2026-12-30')
    diff = round(k4 / n4 - k / n, 3) if n and n4 else None
    out['P4'] = {'shown': k4, 'applicable': n4, 'share': ratio(k4, n4), 'share_2026_11_03': s1,
                 'difference': diff, 'held': (diff >= 0.15) if diff is not None else None}
    for key, text in PREDICTIONS.items():
        out[key]['text'] = text
    return out


def date_rows(results):
    rows = []
    for d, ja, en, kind in CHECKS:
        key = d.isoformat()
        c = Counter(r['checks'][key] for r in results)
        k, n = shown(results, key)
        row = {'date': key, 'weekday': WD_EN[d.weekday()], 'name_ja': ja, 'name_en': en, 'kind': kind,
               'feeds': len(results), 'covered': len(results) - c['outside'], 'applicable': n}
        row.update({x: c[x] for x in CLASSES if x != 'outside'})
        row['share_shown'] = ratio(k, n)
        row['share_shown_nonstandard'] = ratio(c['ordinary'], n)
        rows.append(row)
    return rows


def feed_base(r):
    f = r['feed']
    try:
        pid = int(f.get('feed_pref_id') or 0)
    except (TypeError, ValueError):
        pid = 0
    return {'organization_id': f['organization_id'], 'feed_id': f['feed_id'],
            'organization_name': f.get('organization_name') or '', 'feed_name': f.get('feed_name') or '',
            'pref_id': pid, 'pref_name': pref_name(pid), 'license': f.get('feed_license') or ''}


def upcoming(results, as_of):
    """Feeds whose file shows the ordinary timetable on at least one holiday or New Year day still to come."""
    days = [(d.isoformat(), kind) for d, _ja, _en, kind in CHECKS if d >= as_of]
    rows = []
    for r in results:
        nat = [r['checks'][d] for d, kind in days if kind == 'holiday' and r['checks'][d] in GROUPS]
        ny = [r['checks'][d] for d, kind in days if (kind == 'year_end' or d == '2027-01-01') and r['checks'][d] in GROUPS]
        first = next((d for d, _k in days if GROUPS.get(r['checks'][d]) == 'shown'), '')
        if not first:
            continue
        row = feed_base(r)
        row.update({'first_shown': first, 'holidays_shown': sum(GROUPS[x] == 'shown' for x in nat),
                    'holidays_applicable': len(nat), 'new_year_shown': sum(GROUPS[x] == 'shown' for x in ny),
                    'new_year_applicable': len(ny),
                    'standard_ids': 'yes' if any(r['checks'][d] == 'ordinary_std' for d, _k in days) else 'no'})
        rows.append(row)
    rows.sort(key=lambda x: (-x['holidays_shown'], -x['new_year_shown'], x['pref_id'], x['organization_id'],
                             x['feed_id']))
    return rows


def write_csv(path, cols, rows):
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def pct(x):
    return '–' if x is None or x == '' else f'{x * 100:.1f}%'


def markdown(summary, drows, up, limit=80):
    p = summary['predictions']
    held = {True: 'held', False: 'did not hold', None: 'not scorable'}
    lines = [f'# 祝日・年末年始の扱い / Holidays and the New Year break in Japan\'s GTFS files ({summary["as_of"]})', '',
             'GTFSデータリポジトリの有効なデータ（オープンライセンス）の現行ファイルについて、2026年4月〜2027年3月の祝日と年末年始の各日に'
             '走る運行（service_id）を、同じ曜日のふだんの日・近くの日曜・土曜と比べました。「ふだんどおり」は、日曜の運行が平日と違う'
             'データなのに、祝日にふだんの平日（土曜なら土曜）の運行がそのまま入っていることを指します。',
             'For the current file of every active, openly licensed feed in the GTFS Data Repository, the services running on '
             'each holiday and New Year day from April 2026 to March 2027 were compared with an ordinary day of the same '
             'weekday and with the nearest Sunday and Saturday. "Ordinary" means the file runs its ordinary weekday (or '
             'Saturday) services on the holiday although its Sunday services differ.', '',
             f'Feeds checked: {summary["feeds_checked"]}; skipped: ' +
             (', '.join(f'{k} {v}' for k, v in summary['skipped_by_reason'].items()) or 'none') + '.', '',
             '| date | day | holiday | covered | applicable | ordinary (standard ids) | no service | Sunday | Saturday | '
             'special | same as weekend | ordinary share |',
             '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in drows:
        lines.append(f'| {r["date"]} | {r["weekday"]} | {r["name_ja"]} / {r["name_en"]} | {r["covered"]} | '
                     f'{r["applicable"]} | {r["ordinary"] + r["ordinary_std"]} ({r["ordinary_std"]}) | {r["no_service"]} | '
                     f'{r["sunday"]} | {r["saturday"]} | {r["special"]} | {r["same_as_weekend"]} | {pct(r["share_shown"])} |')
    lines += ['', '## 事前に記録した予測 / Predictions recorded before the run (2026-10-22)', '',
              '| | prediction | result | |', '|---|---|---|---|']
    for key in ('P1', 'P2', 'P3', 'P4'):
        x = p[key]
        res = {k: v for k, v in x.items() if k not in ('text', 'held')}
        lines.append(f'| {key} | {x["text"]} | {json.dumps(res, ensure_ascii=False)} | {held[x["held"]]} |')
    lines += ['', f'## これからの祝日・年末年始にふだんどおりの運行が入っているデータ / Feeds showing the ordinary timetable '
              f'on a holiday or New Year day still to come ({len(up)})', '',
              '| 提供者 / operator | データ / feed | 都道府県 | first | holidays (shown/applicable) | New Year (shown/applicable) | '
              'standard ids |', '|---|---|---|---|---|---|---|']
    for r in up[:limit]:
        lines.append(f'| {r["organization_name"]} | {r["feed_name"]} | {r["pref_name"]} | {r["first_shown"]} | '
                     f'{r["holidays_shown"]}/{r["holidays_applicable"]} | {r["new_year_shown"]}/{r["new_year_applicable"]} | '
                     f'{r["standard_ids"]} |')
    if len(up) > limit:
        lines.append(f'| … | {len(up) - limit} more in upcoming.csv | | | | | |')
    lines += ['', '限界: 祝日にふだんの平日ダイヤで走る路線もあり、「ふだんどおり」は誤りとは限りません。標準のservice_id（「平日（月～金）」など）'
              'だけのデータは、仕様上、国内の経路検索事業者が祝日を考慮します（表の括弧内）。それ以外の利用者（海外の地図アプリなど）には'
              'ファイルの内容がそのまま届きます。比べる日は祝日・年末年始・お盆を避けた同じ曜日の最も近い日です。',
              'Limits: some routes really do run their weekday timetable on holidays, so "ordinary" is not always a mistake. '
              'For files that use only GTFS-JP\'s standard service_ids (the count in brackets), the spec says domestic '
              'route-search providers apply the holidays themselves; every other reader (map apps abroad, for example) '
              'gets what the file says. The ordinary day compared is the nearest same weekday outside holidays, the New '
              'Year break and Obon. Place names are records of fact, not judgements.', '',
              'Source: GTFS Data Repository API v2 (https://gtfs-data.jp/); each feed\'s publisher and licence are in '
              'feeds.csv. Made by MV2 of Munim, Inc. with AI agents working in MV2\'s name. Data CC BY 4.0.', '']
    return '\n'.join(lines)


def write_outputs(out_root, as_of, results, skipped, feeds_listed, generated_at):
    out = os.path.join(out_root, 'holidays', as_of.isoformat())
    os.makedirs(out, exist_ok=True)
    days = [d.isoformat() for d, _ja, _en, _kind in CHECKS]
    fcols = ['organization_id', 'feed_id', 'organization_name', 'feed_name', 'pref_id', 'pref_name', 'license',
             'cover_from', 'cover_start', 'cover_end', 'services', 'standard_services', 'calendar_dates_rows'] + days
    frows = []
    for r in sorted(results, key=lambda r: feed_base(r)['pref_id']):
        row = feed_base(r)
        row.update({k: r[k] for k in ('cover_from', 'cover_start', 'cover_end', 'services', 'standard_services',
                                      'calendar_dates_rows')})
        row.update(r['checks'])
        frows.append(row)
    write_csv(os.path.join(out, 'feeds.csv'), fcols, frows)
    drows = date_rows(results)
    write_csv(os.path.join(out, 'dates.csv'), list(drows[0]), drows)
    up = upcoming(results, as_of)
    write_csv(os.path.join(out, 'upcoming.csv'),
              ['organization_id', 'feed_id', 'organization_name', 'feed_name', 'pref_id', 'pref_name', 'license',
               'first_shown', 'holidays_shown', 'holidays_applicable', 'new_year_shown', 'new_year_applicable',
               'standard_ids'], up)
    write_csv(os.path.join(out, 'skipped.csv'), ['organization_id', 'feed_id', 'feed_name', 'reason', 'detail'], skipped)
    summary = {'as_of': as_of.isoformat(), 'feeds_listed': feeds_listed, 'feeds_checked': len(results),
               'skipped_by_reason': dict(Counter(s['reason'] for s in skipped)),
               'feeds_with_calendar_dates': sum(1 for r in results if r['calendar_dates_rows']),
               'feeds_all_standard_ids': sum(1 for r in results if r['services'] and
                                             r['standard_services'] == r['services']),
               'feeds_upcoming_shown': len(up), 'predictions': predictions(results),
               'source': API + '/feeds and each feed\'s files/feed.zip?rid=current',
               'generated_at': generated_at, 'by': 'MV2 of Munim, Inc. (made with AI agents working in MV2\'s name)'}
    with open(os.path.join(out, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    with open(os.path.join(out, 'holidays.md'), 'w', encoding='utf-8') as f:
        f.write(markdown(summary, drows, up))
    return summary


def fetch(url, timeout=180):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def zip_url(f):
    q = lambda s: urllib.parse.quote(s, safe='')  # noqa: E731
    return f"{API}/organizations/{q(f['organization_id'])}/feeds/{q(f['feed_id'])}/files/feed.zip?rid=current"


def get_zip(f):
    try:
        return fetch(zip_url(f))
    except Exception:  # noqa: BLE001 - one retry
        time.sleep(5)
        return fetch(zip_url(f))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--as-of', help='YYYY-MM-DD; default: today in Japan')
    ap.add_argument('--feeds-json', help='a saved copy of the API\'s /feeds answer (default: fetch it)')
    ap.add_argument('--out', default='/out')
    ap.add_argument('--pause', type=float, default=2.0, help='seconds between downloads')
    ap.add_argument('--limit', type=int, help='download at most this many files')
    ap.add_argument('--budget-min', type=float, default=150)
    ap.add_argument('--min-feeds', type=int, default=400)
    a = ap.parse_args(argv)
    as_of = iso_day(a.as_of) if a.as_of else dt.datetime.now(JST).date()
    if a.feeds_json:
        with open(a.feeds_json, encoding='utf-8') as f:
            doc = json.load(f)
    else:
        doc = json.loads(fetch(API + '/feeds').decode('utf-8'))
    body = doc.get('body') if isinstance(doc, dict) else doc
    feeds = [f for f in body or [] if isinstance(f, dict) and f.get('organization_id') and f.get('feed_id')]
    if len(feeds) < a.min_feeds:
        sys.exit(f'the feed list has {len(feeds)} feeds, fewer than {a.min_feeds}')
    print(f'feeds listed: {len(feeds)}', flush=True)
    results, skipped = run(feeds, as_of, get_zip, a.pause, a.limit, a.budget_min * 60,
                           log=lambda s: print(s, flush=True))
    summary = write_outputs(a.out, as_of, results, skipped, len(feeds),
                            time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
