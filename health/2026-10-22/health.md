# 公開データの健康診断 / GTFS-JP data-health table (2026-10-22)

このリポジトリで公開した4つの集計（期限の一覧・空白の調査・祝日・停留所名）を、データごとに1行にまとめました。新しいダウンロードはしていません。
One row per feed, joining the four censuses already published here (expiry list, lapse census, holidays, stop names). No new downloads.

Feeds: 553 (the active, openly licensed feeds whose current file was read on 2026-10-22).

| check | ok | flag | n/a |
|---|---|---|---|
| expiry: expired or ends within 60 days | 525 | 28 | 0 |
| holidays: ordinary timetable on a holiday or New Year day to come | 249 | 236 | 68 |
| readings: kana reading for under 90% of stops | 545 | 8 | 0 |
| English: English name for under 90% of stops (recommended only) | 407 | 146 | 0 |

Feeds with at least one flag among expiry, holidays and readings: 267; feeds ok on all four checks: 168. Flags per feed (required three): 0: 286, 1: 262, 2: 5.

Expiry-list feeds outside these feeds (not read by the file censuses): expired 27.

## Predictions recorded before the table was made

- D1: Among feeds with a lapse-census row and a holiday check, feeds with at least one past lapse have a holiday flag more often than feeds with none (one-sided Fisher exact test, p < 0.05). Result: 55 of 115 (0.478) against 178 of 364 (0.489), p = 0.620766: did not hold.
- D2: Among feeds with a holiday check and an English check, feeds whose English check is flagged have a holiday flag more often than feeds whose English check is ok (one-sided Fisher exact test, p < 0.05). Result: 59 of 132 (0.447) against 177 of 353 (0.501), p = 0.879017: did not hold.

Not a prediction: expiry flags among feeds with a past lapse 4 of 126 (0.032), without 23 of 421 (0.055), one-sided Fisher p = 0.904529.

Limits: each census was read on its own day (lapses 2026-10-16, the rest 2026-10-22) and later files are not seen. A flag is a sign to check, not proof of a mistake: some routes really do run their weekday timetable on holidays, and English is only recommended. Place names in the data are records of fact, not judgements.

Generated 2026-10-22T13:20:00Z. Source: GTFS Data Repository (https://gtfs-data.jp/); each feed's publisher and licence are in feeds.csv. Made by MV2 of Munim, Inc. with AI agents working in MV2's name. Data CC BY 4.0.
