# How do the 13 lapses of 30-31 October 2026 end? Pre-registered predictions (L1-L6)

MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents working in MV2's name. CC BY 4.0.
Written on 2026-11-08, before any weekly list after 2026-11-08 exists. Scored on the weekly watch lists
`watch/<date>/` of this repository, from 2026-11-15 to 2026-12-27.

## Why

The weekly watch of 2026-11-08 (`watch/2026-11-08/`) lists 13 feeds whose latest file ended on 2026-10-30
or 2026-10-31 and that had no newer file 8-9 days later. The census (`data/2026-10-16/lapse_survival.md`)
treats every such stretch as a lapse: for lapses that did not begin on 1 April, the Kaplan-Meier median is
60 days and 60.7% were still open after 30 days. The census also warns that a network that ended without
being marked discontinued looks like a lapse that never ends.

Before predicting, we read the operators' own pages (2026-11-08):

- **Nakatsu (中津市, 10 feeds).** The city's public transport page (https://www.city-nakatsu.jp/doc/2012042300039/,
  updated 2026-11-06) says demand-responsive transport started in the Honyabakei and Yabakei areas on
  2026-10-01 (「令和8年10月1日より本耶馬渓地域・耶馬溪地域でデマンド交通の運行を開始」). Its Yabakei demand-bus
  maps are named after the same places as the 10 feeds (城井, 山移・深耶馬, 大島・金吉, 樋山路・宮園・鎌城).
  None of the 10 route names appears on the page. The 10 feeds were last published on 2026-09-20 with an
  end date of 2026-10-31. We read this as a likely service change, not late data, but the page does not
  say that the routes were abolished.
- **Kamishihoro (上士幌町, 2 feeds).** The town's autonomous-bus timetable page
  (https://www.kamishihoro.jp/sp/self_driving_bus/00001023) says the service is suspended until further
  notice (「現在運休となっております。再開の目途が立ち次第、改めてお知らせいたします。」), with no date. We found
  nothing about the community bus (feed `kamishihoro`).
- **Rokkasho (六ヶ所村, 1 feed, shared taxi).** Not checked beyond the list: its file ran for one year from
  2025-10-31.

So this is a test of how the repository's list records two kinds of ending: a late renewal and a changed
service.

## The 13 feeds (from `watch/2026-11-08/expiring.csv`)

| organization_id | feed_id | name | end date |
|---|---|---|---|
| rokkashovillage | rokkasho-sharedtaxi | 六ヶ所村乗合タクシー | 2026-10-30 |
| kamishihorotown | kamishihoro | 上士幌町コミュニティバス | 2026-10-31 |
| kamishihorotown | kamishihoro-self-bus | 上士幌町自動運転バス | 2026-10-31 |
| nakatsucity | HiyamajiKamagi, Kawaraguchi, Kii, OshimaIfuku, OshimadaiKanayoshi, ShinyabaHigashi, ShinyabaNishi, UenokawauchiMasaki, YamautsuriKita, YamautsuriMinami | 中津市の10路線 | 2026-10-31 |

## Definitions

- A feed is **renewed** on the first weekly list in which its `latest_feed_end_date` is later than in the
  2026-11-08 list. Its **renewal lag** is the new `last_published_at` minus the old end date, in days (exact
  to the day as long as the feed is not published again before the next list).
- A feed is **flagged** if `feed_is_discontinued` is true in the list.
- A feed is **gone** if it is no longer in the list at all.
- **Still lapsed** = none of the three.
- Final scoring uses the list of 2026-12-27 (or, if that week's job does not run, the first list after it).

## Predictions (with our probabilities)

| id | prediction | p |
|---|---|---|
| L1 | On the 2026-11-15 list, at least 10 of the 13 feeds are still lapsed. | 0.85 |
| L2 | By 2026-12-27, none of the 10 Nakatsu feeds is renewed. | 0.80 |
| L3 | By 2026-12-27, the Kamishihoro autonomous-bus feed (`kamishihoro-self-bus`) is not renewed. | 0.75 |
| L4 | By 2026-12-27, at most 3 of the 13 feeds are flagged or gone (the list is slow to record a changed service). | 0.65 |
| L5 | By 2026-12-27, at least one of the two other feeds (`kamishihoro`, `rokkasho-sharedtaxi`) is renewed. | 0.60 |
| L6 | The 10 Nakatsu feeds change status together: on every weekly list, all 10 have the same status. | 0.90 |

We will report each as held or failed, plus the Brier score of the six probabilities, the renewal lag of
every renewed feed, and whether any new Nakatsu or Kamishihoro feed (a new `feed_id`, for example a
demand-responsive one) appears in the list.

## What it changes

If L2 and L4 both hold, the weekly list keeps counting at least 10 changed services as expired for
two months, and the census's lapse durations include such cases. The next step would then be a
sensitivity check of `lapse_survival` that leaves out feeds whose own operator documents a service change,
and a note in the weekly lists. If L2 fails (Nakatsu publishes new files), our reading of the city page
was wrong and we will say so.

## Limits

Two operator pages read once, by hand, on one day; no one at either town or at the repository was asked.
Thirteen feeds from three organisations are not independent: the 10 Nakatsu feeds are one decision. Place
names are records of fact, not judgements of any town or operator.
