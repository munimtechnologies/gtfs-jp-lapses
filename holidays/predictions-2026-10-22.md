# 祝日・年末年始の扱い: 事前に記録した予測 / Holidays and the New Year break: predictions recorded before the run

記録 / Recorded: 2026-10-22, before any feed file was read. MV2 of Munim, Inc.; made with AI agents working in MV2's name.

## 何を調べるか / What will be checked
`tools/holiday_check.py` は、GTFSデータリポジトリ（https://gtfs-data.jp/ ）の有効なデータ（オープンライセンス）の現行ファイルについて、
2026年4月〜2027年3月の祝日（日曜を除く）と年末年始（12月29日〜1月2日）の各日に走る運行（service_id）を、同じ曜日のふだんの日
（祝日・年末年始・お盆を除く最も近い日）と、近くの日曜・土曜と比べます。

For the current file of every active, openly licensed feed in the GTFS Data Repository, `tools/holiday_check.py` compares
the services that run on each national holiday from April 2026 to March 2027 (Sundays left out) and on each New Year day
(2026-12-29 to 2027-01-02) with the nearest ordinary day of the same weekday (not a holiday, New Year or Obon day) and
with the nearest Sunday and Saturday. Each feed and day gets one class:

- `ordinary`: the ordinary weekday (or Saturday) services run, although the file's Sunday services differ.
- `ordinary_std`: the same, but every service running is one of GTFS-JP's eight standard service_ids (平日（月～金） …).
  For these the GTFS-JP spec says domestic route-search providers apply the holidays themselves; other readers do not.
- `no_service`, `sunday`, `saturday`, `special`: the file runs something else that day (handled).
- `same_as_weekend` (the ordinary day already runs the weekend's services), `no_ordinary_service`, `no_reference`,
  `outside` (the file does not cover the day): not counted.

"Applicable" = ordinary + ordinary_std + handled. "Ordinary share" = (ordinary + ordinary_std) / applicable.

## 予測 / Predictions (scored by `predictions()` in the tool, on the first run)
- **P1** On 2026-11-03 (文化の日), between 5% and 30% of applicable feeds show the ordinary weekday timetable.
- **P2** Among feeds applicable on all three of 2026-09-21, 09-22 and 09-23, more show the ordinary timetable on 09-22
  (国民の休日, the rare day between two holidays) than on 09-21 or on 09-23.
- **P3** Of the feeds applicable on all six weekday holidays still to come (2026-11-03, 11-23, 2027-01-11, 02-11,
  02-23, 03-22), at least 80% treat all six the same way (all ordinary, or all handled).
- **P4** The ordinary share on 2026-12-30 (an ordinary Wednesday in law, but inside the New Year break many operators
  run differently) is at least 15 percentage points higher than on 2026-11-03.

These are guesses written before seeing any data, not results. Whatever they turn out to be, all four are reported.

## 先行例 / Prior art (searched 2026-10-22)
Cal-ITP studied holiday service in California's GTFS feeds (2023), and the GTFS·X validator warns when a pattern has no
exceptions on US federal holidays. In Japan, the GTFS-JP spec and busdata.or.jp's guide ask publishers to put holidays
in calendar_dates.txt, and the 運行日チェッカー shows one uploaded feed's calendar. We found no census across Japan's
feeds of whether the files carry the national holidays and the New Year break.

## 限界 / Limits
Some routes really do run their weekday timetable on holidays, so `ordinary` is not always a mistake. A feed's
current file is read once, on the day the job runs; files published later are not seen. Place names in the output are
records of fact, not judgements.
