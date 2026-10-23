# ダイヤの新しい期間のファイルは何日前に公開されたか / How far ahead new timetable periods were published (versions to 2026-10-16)

GTFSデータリポジトリのAPIが10月16日の調査で返した全版（`data/2026-10-16/versions.csv`）について、新しい期間を始めるファイル（同じデータでそれより前に公開されたどのファイルよりも有効開始日が遅いもの）ごとに、有効開始日から公開日（日本時間）を引いた日数を数えました。修正・再公開の版と、データがリポジトリに加わった最初の公開日の版は数えますが、日数は付けません。
For every file in the version history the repository API returned in the 2026-10-16 census (`data/2026-10-16/versions.csv`), a file that starts a new period (a from_date later than that of every file of the same feed published before it) gets its lead: start date minus publication date in Japan time. Corrections and re-issues, and the files published on a feed's first publication day, are counted but get no lead.

- データ / feeds: 602; 版 / files: 9475 (読めない / unreadable: 0); 最初の公開日 / first publication day: 981; 修正・再公開 / corrections and re-issues: 6102; 新しい期間 / new periods: 2392
- 対象期間 / cohort: start 2023-01-01 to 2026-06-30: 2119 files
- 開始日より後に公開 / published after the start date: 623 (29.4%); うち古いファイルが有効のまま / old file still valid: 512, 有効なファイルなし / no valid file: 111
- 日数 / lead (days): median 2, quartiles -1.0–12.5, range -760–116; 7日以上 / at least 7: 36.7%; 14日以上 / at least 14: 22.8%; 21日以上 / at least 21: 13.5%

| 日数 / lead | files | share |
|---|---|---|
| late | 623 | 29.4% |
| same_day | 340 | 16.1% |
| 1-6 | 379 | 17.9% |
| 7-13 | 293 | 13.8% |
| 14-20 | 197 | 9.3% |
| 21-27 | 130 | 6.1% |
| 28+ | 157 | 7.4% |

## 開始年ごと / By start year (all new periods)

| year | files | late | late share | median lead | at least 14 days |
|---|---|---|---|---|---|
| 2022 | 12 | 9 | 75.0% | -109.0 | 0.0% |
| 2023 | 295 | 81 | 27.5% | 4 | 29.1% |
| 2024 | 521 | 155 | 29.8% | 3 | 22.5% |
| 2025 | 817 | 254 | 31.1% | 1 | 20.8% |
| 2026 | 746 | 189 | 25.3% | 4.0 | 25.7% |
| 2027 | 1 | 0 | 0.0% | 198 | 100.0% |

## 4月1日とそれ以外 / April 1 against other start days (cohort)

- 4月1日 / April 1: 129 of 651 late (19.8%), median 8
- それ以外 / other days: 494 of 1468 late (33.7%), median 0.0
- one-sided Fisher exact p = 1.0

## 版の種類とデータごと / By update type and by feed (cohort)

- NEW: 572 of 2015 late (28.4%)
- UPDATE: 51 of 104 late (49.0%)
- データ / feeds: 457; データごとの中央値の中央値 / median of feed medians: 2.5; 遅れた版のあるデータ / feeds with a late file: 307; 中央値が14日以上 / feed median at least 14: 81
- 新しい期間の多いデータ / feeds with the most new periods: nisshincity/communitybus 33, meikobus/meikobus 29, tokubus/tokushimabus 25, chitetsu/chitetsubus 22, nagai-unyu/Nagaibus 19
- その5件を除くと / without those 5: 1991 files, late 30.2%, median 2, at least 14 days 23.9%

## 事前に記録した予測 / Predictions fixed before the run

- P1: Between 15% and 45% of the new-period files that start in the cohort (2023-01-01 to 2026-06-30) were published after their start date (lead under 0 days). Result: 29.4%, held.
- P2: The median lead of those files is between 0 and 10 days. Result: 2 days, held.
- P3: Fewer than 35% of those files were published at least 14 days ahead. Result: 22.8%, held.
- P4: Those starting on April 1 were published after their start date more often than those starting on other days (one-sided Fisher exact test, p < 0.05). Result: p = 1.0, did not hold.

Benchmarks (guidance, not measurements): route-search providers about 2 weeks before a change, Google about 1 week, signage the same night (AIGID, https://front.geospatial.jp/no56_2/); MobilityData 3–4 weeks and at least 5 days (https://gtfs.org/documentation/schedule/schedule-best-practices/).

Limits: the publication date is the one the repository gives for each file; a file sent to apps or route planners by other means earlier is not seen, and old files no longer in the API are not seen. A file whose from_date was simply set to its upload day counts as a new period with lead 0. Starts after 2026-06-30 are left out of the cohort because files published very late for them may still be missing. Feeds from one publisher are not independent, so the p-value is, if anything, too small. Lead times are the publishers' and are reported as facts, not judgements.

Generated 2026-10-23T14:05:59Z. Source: GTFS Data Repository API v2 (https://gtfs-data.jp/), via data/2026-10-16/versions.csv; each feed's publisher and licence are in data/2026-10-16/feeds.csv. Made by MV2 of Munim, Inc. with AI agents working in MV2's name. Data CC BY 4.0.
