---
name: gtfs-jp-expiry
description: Use when building, testing or debugging anything that reads Japanese bus or ferry timetables (GTFS-JP) from the GTFS Data Repository (gtfs-data.jp, api.gtfs-data.jp), such as a route planner, a timetable app, a transit map or an accessibility study, or when a user asks whether a Japanese GTFS feed is still valid. Checks whether the feed's latest file has expired or runs out within 60 days, whether a newer file leaves days with no timetable, and warns about the 31 March fiscal-year cliff when about 6 in 10 past lapses began. Works offline from a bundled weekly list; network only when asked.
license: Apache-2.0
---

# GTFS-JP expiry check

Made with AI agents working in the name of MV2 of Munim, Inc. Skill and script: Apache-2.0. Bundled
list and figures: CC BY 4.0. Source, method and every weekly list:
https://github.com/munimtechnologies/gtfs-jp-lapses

Japan's GTFS Data Repository (https://gtfs-data.jp/) publishes about 600 open timetables, mostly
community buses run by towns. Each file is valid for a fixed date range. When the range ends and no
newer file has been published, an app that reads the feed silently shows no buses, or yesterday's
timetable. MV2's census of the repository's whole version history (602 feeds, 9,475 files, to
2026-10-16) counted 203 such lapses in 156 feeds. 121 of them (59.6%) began on 1 April, the first day
of Japan's fiscal year. Half of all lapses had lasted 80 days or more (Kaplan-Meier median). These are
records of fact, not judgements of any town or operator.

## When to use

- Code you are writing downloads a feed from `api.gtfs-data.jp` or a `gtfs-data.jp` link.
- A user reports that an app shows no buses for a Japanese town, or shows the wrong timetable.
- A user asks whether a feed is current, when it runs out, or which feeds in a prefecture expire soon.
- You are about to run an analysis on a date (a holiday, a day next April) that a feed may not cover.

## Step 1: check

Run the script from this skill folder. It needs Python 3.8+ and the standard library only. By default it
reads the copy of the weekly watch list bundled in `data/` (feeds that had ended, or had 60 days or less
left, on 2026-11-08) and makes no network request.

```
python scripts/gtfs_jp_expiry.py                          # the bundled list, worst first
python scripts/gtfs_jp_expiry.py --grep 中津市             # by Japanese name or id substring
python scripts/gtfs_jp_expiry.py --org nakatsucity --json
python scripts/gtfs_jp_expiry.py --pref 高知県 --as-of 2026-12-01
```

The bundled list goes stale: the script warns when it is more than 7 days older than the day you check.
A feed that is not in it had more than 60 days left on 2026-11-08 (or was discontinued, or is not in the
repository). For current data, either:

- ask the user before going online, then `--fetch`: one GET request to `https://api.gtfs-data.jp/v2/feeds`
  (about 0.6 MB, no key needed), which rates every feed in the list; or
- let the user save that URL themselves and pass `--feeds-json feeds.json`.

Filters combine: `--org` and `--feed` (exact ids), `--grep`, `--pref` (number 1-47 or name),
`--within DAYS`, `--status`, `--as-of YYYY-MM-DD` (default: today in Japan). `--summary` prints counts
by status, plus how many feeds end exactly on, and by, the next 31 March. Exit code 0 means rows
matched, 1 none, 2 the input could not be read.

Statuses: `expired` (the latest file ended before the day checked), `ends_7`, `ends_30`, `ends_60`
(days left: 0 means the day checked is the last valid day), `later`, `no_end_date`, `discontinued`
(the repository marks the service as ended; this is not a lapse).

## Step 2: check one feed's files (only when it matters)

The list gives only the latest file's end date. A newer file may already be published that starts some
days after the current one ends, so the list looks fine while the app will have empty days. For one
feed, read its file list:

```
python scripts/gtfs_jp_expiry.py --fetch-feed nakatsucity/Kii --as-of 2026-11-08
python scripts/gtfs_jp_expiry.py --detail-json saved-detail.json
```

`--fetch-feed` makes one request to `organizations/{org}/feeds/{feed}` on the same API. It reports
`covered` (until when), `gap_now` (no file covers the day; when the next one starts), `expired` or
`no_files`, and lists every gap ahead between published files. Do not loop it over hundreds of feeds:
use the list for that, and pause at least 1 s between requests if you must check several.

## Step 3: tell the user, and handle it in code

- Say plainly which feed, its end date and the days left, and that the figures come from the GTFS Data
  Repository list on the day checked (name the day; for the bundled list, 2026-11-08).
- Never fill a lapse with an old timetable without saying so. If an app falls back to the last file, it
  should show that the timetable may be out of date.
- An expired feed can mean two opposite things. Many towns keep running and publish the new file weeks
  late. Others have changed the service (fixed routes replaced by demand-responsive transport, a trial
  bus suspended) without the feed being marked discontinued. Do not guess which one: suggest checking the
  operator's own timetable page, and say which one you found.
- Around 31 March, expect many feeds to end on the same day (288 of 581 active feeds on 2026-11-08 ended
  exactly on 2027-03-31). Check again in early April before trusting any feed.
- Read each feed's licence (`license` column; mostly CC BY 4.0, some CC0 1.0 or CC BY 2.1 JP) and credit
  the publisher when you use its data.

## Limits

- Only what the repository lists. Feeds published elsewhere (an operator's own site, ODPT) are not seen.
- The end date is the list's `latest_feed_end_date`; a file can also leave out days inside its own range
  (calendar exceptions), which this check does not read.
- The bundled list and the census numbers are dated (2026-11-08 and 2026-10-16). A new list is published
  every week in `watch/<date>/expiring.csv` in the source repository.

## Source and credit

GTFS Data Repository API v2 (https://gtfs-data.jp/); each feed's publisher and licence are in the list.
This skill is not made or endorsed by the repository's operators. Weekly lists, census and method:
https://github.com/munimtechnologies/gtfs-jp-lapses. Report a problem at
https://github.com/munimtechnologies/gtfs-jp-lapses/issues.

MV2, Munim, Inc., mv2@munimtech.com
