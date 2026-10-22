# 停留所名の再集計 / Independent recount of the stop-name census (names/2026-10-22)

names_check.py とは別に書いたコードで、同じフィードの現行ファイルをもう一度ダウンロードし、停留所（標柱）ごとのよみがな・英語の数を数え直しました。ローマ字（ja-Latn）も数えています（事前登録の予測には含まれません）。
Code written separately from names_check.py downloaded the current file of every feed in the census again and recounted the stops (poles) with a reading and an English name. It also counts romanised names (ja-Latn), which were not part of the predictions recorded before the census.

Feeds: 553; match 553; files not valid UTF-8: 0; translations format read differently: 0.

Stops 98776: reading 0.979, English 0.776, English or ja-Latn 0.806. Feeds with any ja-Latn: 21.
Feeds giving it for at least 90% of their stops: reading 545, English 407, English or ja-Latn 416 (9 only through ja-Latn).

A file updated after the census (2026-10-22 ~10:17 UTC) can differ for that reason alone. Generated 2026-10-22T11:25:02Z. Source: GTFS Data Repository API v2 (https://gtfs-data.jp/). Made by MV2 of Munim, Inc. with AI agents working in MV2's name. Data CC BY 4.0.
