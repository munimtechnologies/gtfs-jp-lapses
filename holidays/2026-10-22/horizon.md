# 先の祝日ほど抜けるか / Are later holidays left out of the files?

### data/feeds.csv (550 feeds)

| 2026-11-03 vs | feeds | both handled | handled → ordinary | ordinary → handled | both ordinary | sign test p |
|---|---|---|---|---|---|---|
| 2026-11-23 | 445 | 404 | 2 | 2 | 37 | 1 |
| 2027-01-11 | 405 | 338 | 31 | 1 | 35 | 1.5e-08 |
| 2027-02-11 | 387 | 335 | 19 | 1 | 32 | 4e-05 |
| 2027-02-23 | 395 | 335 | 20 | 2 | 38 | 0.00012 |
| 2027-03-22 | 372 | 319 | 22 | 2 | 29 | 3.6e-05 |

Feeds that handle both November holidays but show the ordinary timetable on 2027-01-11: 30

"Handled" = no service, the Sunday or Saturday timetable, or a special one; "ordinary" = the ordinary timetable (classes from holiday_check.py). Feeds not applicable on either day are left out. Made by MV2 of Munim, Inc. with AI agents working in MV2's name. Data CC BY 4.0.
