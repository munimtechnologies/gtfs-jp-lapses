# 祝日・年末年始の再確認: 事前に記録した予測 / Holiday re-check: predictions recorded in advance

記録 / Recorded: 2026-10-22, after the first census (holidays/2026-10-22/) and before the re-check is run.
MV2 of Munim, Inc.; made with AI agents working in MV2's name.

## 何をするか / What will be done
2026年12月10日〜28日のある日に `tools/holiday_check.py` をもう一度走らせ、その `feeds.csv` を2026年10月22日のものと
`tools/holiday_recheck.py` で比べます。12月に年末年始の運行や2027年の祝日を入れたデータに更新されるかを見ます。

On one day between 2026-12-10 and 2026-12-28, `tools/holiday_check.py` will be run again on every active, openly
licensed feed, and its `feeds.csv` compared with the 2026-10-22 one by `tools/holiday_recheck.py`. The question is
whether publishers update their files in December to carry the New Year break and the 2027 holidays.

## 10月22日に見えたこと / What the first census showed
Within one file, later holidays are left out far more often than near ones. Of 405 feeds applicable on both
2026-11-03 and 2027-01-11, 31 handle 11-03 but show the ordinary timetable on 01-11; only 1 does the reverse (exact
sign test p ≈ 1.5e-8). 30 feeds handle both November holidays and show the ordinary timetable on 2027-01-11; 17 of
them handle New Year's Day itself. This was seen in the data, so it is a description, not a prediction. The
predictions below are about what happens next.

## 予測 / Predictions (scored by `predictions()` in `tools/holiday_recheck.py`)
- **R1** Of the feeds that on 2026-10-22 handled both 2026-11-03 and 2026-11-23 but showed the ordinary timetable on
  2027-01-11 (30 feeds), and that are applicable on 2027-01-11 at the re-check, at most one third handle 2027-01-11 at
  the re-check.
- **R2** Of the (feed, New Year day) pairs from 2026-12-29 to 2027-01-02 that showed the ordinary timetable on
  2026-10-22 and are applicable at the re-check, fewer than 25% are handled at the re-check.
- **R3** At the re-check, at least 12% of the feeds applicable on 2027-01-11 show the ordinary timetable that day
  (16.8% on 2026-10-22).

These are guesses, not results. All three will be reported whatever they turn out to be. If the re-check cannot run
inside the window, it will be run as soon as possible after it and marked as outside the window.

## 限界 / Limits
Some operators really do run the ordinary timetable on 2026-12-29 or on a holiday, so "ordinary" is not always a
mistake, and "handled" at the re-check can also come from a file that changed for other reasons. A feed's current
file is read once on each day. Place names in the output are records of fact, not judgements.
