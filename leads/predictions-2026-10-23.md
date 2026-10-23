# ダイヤの新しい期間のファイルは何日前に公開されたか：事前に記録した予測 / How far ahead new timetable periods were published: predictions recorded in advance (2026-10-23)

`tools/lead_history.py` は、10月16日の調査の全版（`data/2026-10-16/versions.csv`）から、新しい期間を始めるファイル（同じデータで
それより前に公開されたどのファイルよりも有効開始日が遅いもの）ごとに、有効開始日から公開日（日本時間）を引いた日数を数えます。
修正・再公開の版と、データがリポジトリに加わった最初の公開日の版には日数を付けません。以下の4つの予測は、このファイルとツール
（PREDICTIONS）をコミットした時点で、まだこの集計を一度も実行する前に記録したものです。対象は有効開始日が2023年1月1日〜2026年6月30日の
ファイルです（それより後に始まるファイルは、ごく遅れて公開される版がまだ出そろっていないため）。

`tools/lead_history.py` takes every file in the 2026-10-16 census (`data/2026-10-16/versions.csv`) and, for each file
that starts a new period (a from_date later than that of every file of the same feed published before it), counts the
days from its publication date (Japan time) to its start date. Corrections, re-issues and the files published on a
feed's first publication day get no lead. The four predictions below were recorded, in this file and in the tool's
PREDICTIONS, before the tool was ever run. The cohort is the files starting 2023-01-01 to 2026-06-30 (files starting
later may still be joined by very late ones).

- P1: 開始日より後に公開されたファイルは15%〜45%。
  Between 15% and 45% of the new-period files in the cohort were published after their start date (lead under 0 days).
- P2: 日数の中央値は0〜10日。
  The median lead of those files is between 0 and 10 days.
- P3: 14日以上前に公開されたファイルは35%未満。
  Fewer than 35% of those files were published at least 14 days ahead.
- P4: 4月1日に始まるファイルは、それ以外の日に始まるファイルより、開始日より後に公開される割合が高い（片側フィッシャー正確検定、p < 0.05）。
  Those starting on April 1 were published after their start date more often than those starting on other days
  (one-sided Fisher exact test, p < 0.05).

Why: on 2026-10-23, `tools/file_chain.py` found 20 files already published but not yet in force, with a median lead
of 18 days (`chain/2026-10-23/`). A snapshot like that sees a file published 60 days ahead on many more days than one
published 2 days ahead, and never sees files published after their start, so it overstates typical lead times. The
full history has neither bias. The lapse census (`data/2026-10-16/`) already showed that 121 of 203 lapses began on
April 1, which is why P4 expects April 1 files to be late more often.

What we already knew when writing this: the yearly medians of start date minus publication date over all files,
corrections included (`data/2026-10-16/findings.md`: 2023 −98, 2024 −8.0, 2025 −27, 2026 −25 days; most corrections
keep their period's original start date, so those medians are negative), the lapse counts above, the 20-file snapshot,
and three rows of versions.csv seen while checking its columns. The new-period leads themselves had not been computed.

Benchmarks (guidance, not measurements): route-search providers need data about 2 weeks before a change, Google about
1 week, and signage the same night (AIGID, July 2026, https://front.geospatial.jp/no56_2/); MobilityData's best
practices aim for 3–4 weeks and at least 5 days (https://gtfs.org/documentation/schedule/schedule-best-practices/).
Searches on 2026-10-23 found guidance like this, and a 2017 Transitland study of how often feeds were updated and how
much their schedules overlapped (https://www.transit.land/news/2017/10/10/transitland-historical-feed-versions), but no
count of the lead times feeds actually had, in Japan or elsewhere.

Robustness, reported but not predicted: the median of per-feed medians, and the cohort figures without the 5 feeds
with the most new-period files (a feed that uploads very often could otherwise dominate).

Limits: the publication date is the repository's; data sent to apps by other means is not seen. A file whose start
date was set to its upload day counts as a new period with lead 0.

MV2 of Munim, Inc. · Made with AI agents working in MV2's name. · CC BY 4.0
