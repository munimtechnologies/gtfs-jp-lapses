# 2027年4月1日に始まるファイルは、遅れたときに空白を生むか：事前に記録した予測 / Do late files starting on 2027-04-01 leave no valid file? Predictions recorded in advance (2026-10-23)

10月16日の調査の版履歴（`leads/2026-10-16/leads.csv`）では、4月1日に始まる新しい期間のファイルは、それ以外の日に始まるものより
開始日より後に公開される割合が低い一方（19.8%対33.7%）、遅れたときには前の版がすでに切れていて、有効なファイルのない日（gap）を
生むことがずっと多くありました（遅れた129件中72件、他の日は494件中39件）。この差は事前の予測ではなく、集計のあとに `leads.csv` から
数えたものです。そこで、まだ1件も存在しない2027年4月1日のファイルについて、次の3つの予測を記録します。

In the version history of the 2026-10-16 census (`leads/2026-10-16/leads.csv`), new-period files starting on April 1
were published after their start date less often than files starting on other days (19.8% against 33.7%), but when
they were late they far more often left no valid file on their start date (a 'gap'): 72 of the 129 late April-1 files,
against 39 of the 494 late files on other days. That split was not predicted; it was counted from `leads.csv` after
the run. So we record three predictions for the files starting on 2027-04-01, none of which exists yet.

- G1: 2027年4月1日に始まる新しい期間のファイルのうち、その日に有効なファイルがなかった（gap）ものは6%〜18%。
  Of the new-period files starting on 2027-04-01, between 6% and 18% left no valid file on that day (gap).
- G2: その割合は、2026年10月1日〜2027年3月31日のそれ以外の日に始まる新しい期間のファイルより高い（片側フィッシャー正確検定、p < 0.05）。
  That share is higher than for the new-period files starting on other days from 2026-10-01 to 2027-03-31
  (one-sided Fisher exact test, p < 0.05).
- G3: 2027年4月1日に始まり開始日より後に公開されたファイルのうち、40%以上は有効なファイルのない日を生んだ。
  Of the files starting on 2027-04-01 that were published after their start date, at least 40% left no valid file on
  that day.

採点 / Scoring: on or after 2027-07-01, run a new census (`tools/gtfs_lapses.py`), then `tools/lead_history.py` on its
`versions.csv`, and count the rows of the new `leads.csv` whose from_date is 2026-10-01 to 2027-04-01: the "day" group
is from_date 2027-04-01, the "other" group the rest; a file is late when lead_days < 0 and a gap when late_kind is
`gap`. G1 = gap / files of the day group; G2 = one-sided Fisher exact p that the day group's gap share is greater;
G3 = gap / late of the day group. The result will be added to the README.

What we knew when writing this (all from `leads/2026-10-16/leads.csv`, files starting 2023-01-01 to 2026-06-30):

| start year | April 1 files | April 1 gaps | share | other files | other gaps | share |
|---|---|---|---|---|---|---|
| 2023 | 67 | 6 | 9.0% | 228 | 4 | 1.8% |
| 2024 | 148 | 14 | 9.5% | 373 | 7 | 1.9% |
| 2025 | 202 | 24 | 11.9% | 615 | 20 | 3.3% |
| 2026 (to 06-30) | 234 | 28 | 12.0% | 252 | 8 | 3.2% |
| all | 651 | 72 | 11.1% | 1,468 | 39 | 2.7% |

The 72 April-1 gaps come from 64 feeds of 54 publishers; 40 of all 111 gaps (both groups) came 100 days or more after
the start date, several of them old periods uploaded together later (four feeds of one publisher on one day, for example). The G1 range is wider than the yearly spread
(9.0–12.0%) because one publisher often publishes several feeds together.

Limits: only files that were eventually published are counted. A feed whose next file never came is a lapse in the
census (`data/2026-10-16/lapses.csv`) but has no row in `leads.csv`, so these shares are not the lapse forecasts for
2027-04-01 in `forecast/2027-04-01/`, which count feeds. Publication dates are the repository's; data sent to apps by
other means is not seen. Files from one publisher are not independent, so the p-value is, if anything, too small.

MV2 of Munim, Inc. · Made with AI agents working in MV2's name. · CC BY 4.0
