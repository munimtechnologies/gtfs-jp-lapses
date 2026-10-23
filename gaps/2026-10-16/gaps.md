# 開始日が04-01のファイルとそれ以外 / Files starting on 04-01 against other days (2023-01-01 to 2026-06-30)

Source: `leads.csv` (tools/lead_history.py). A file is late when it was published after its start date; a late file is a gap when no earlier file still covered its start date (no valid file that day), and stale when one did (the old timetable stayed in force).

| group | files | late | gap | stale | late share | gap share | gap of late | feeds with a gap | publishers with a gap |
|---|---|---|---|---|---|---|---|---|---|
| day | 651 | 129 | 72 | 57 | 19.8% | 11.1% | 55.8% | 64 | 54 |
| other | 1468 | 494 | 39 | 455 | 33.7% | 2.7% | 7.9% | 35 | 30 |

- one-sided Fisher exact p, gap share of 04-01 greater: 2.6e-14
- one-sided Fisher exact p, late share of 04-01 smaller: 3.02e-11

## 開始年ごと / By start year

| year | day files | day gap | day gap share | other files | other gap | other gap share |
|---|---|---|---|---|---|---|
| 2023 | 67 | 6 | 9.0% | 228 | 4 | 1.8% |
| 2024 | 148 | 14 | 9.5% | 373 | 7 | 1.9% |
| 2025 | 202 | 24 | 11.9% | 615 | 20 | 3.2% |
| 2026 | 234 | 28 | 12.0% | 252 | 8 | 3.2% |

Limits: files are not independent (one publisher often publishes several feeds together), so the p-values are, if anything, too small. Only files that were eventually published are counted: a feed whose next file never came is a lapse in the census but has no row here. Publication dates are the repository's. Lead times are the publishers' and are reported as facts, not judgements.

Generated 2026-10-23T19:38:54Z. Source: GTFS Data Repository API v2 (https://gtfs-data.jp/). Made by MV2 of Munim, Inc. with AI agents working in MV2's name. Data CC BY 4.0.
