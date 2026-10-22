# 始発と終バス：事前に記録した予測 / First and last buses at every place in Japan: predictions recorded in advance

Recorded on 2026-10-22, before `tools/last_bus.py` read any file. The commit date of this file is the record.
この予測は、`tools/last_bus.py` がどのファイルも読む前の2026年10月22日に記録しました。

The census reads the current file of every feed in `names/2026-10-22/feeds.csv` (553 active, openly licensed feeds of
the GTFS Data Repository). For an ordinary Wednesday, Saturday and Sunday (2026-11-11, 2026-11-14 and 2026-11-15: no
national holiday, outside the New Year break) it finds the bus trips that run that service day (calendar.txt and
calendar_dates.txt; a day the file does not cover has no service) and gives each place, a stop name within one feed,
its first and last departure where riders may board (not a trip's last stop, pickup_type not 1). Times past 24:00 stay
on the service day they belong to. Only bus route types count (3, 200-299, 700-799).

| | prediction | holds if |
|---|---|---|
| L1 | Over all places with a bus departure on the Wednesday, the median last departure is between 19:00 and 21:00. | 19:00 ≤ median ≤ 21:00 |
| L2 | At least 25% of those places have their last departure before 19:00. | share ≥ 0.25 |
| L3 | At least 15% of those places, in files that cover the Sunday, have no bus departure on the Sunday. | share ≥ 0.15 |
| L4 | At least 30% of the feeds with a bus departure on the Wednesday have a median last departure before 18:00. | share ≥ 0.30 |
| L5 | Fewer than 10% of the places with a Wednesday departure have their last departure at 23:00 or later. | share < 0.10 |
| L6 | Of the places with a bus departure on both the Wednesday and the Sunday, at least 40% have an earlier last departure on the Sunday. | share ≥ 0.40 |

Why these: many feeds in the repository are municipal community buses, which usually stop running in the early evening
and often not at all on Sundays (L3, L4); city networks run later, but rarely past 23:00 (L5). Japanese news reports
say operators short of drivers have cut late-evening runs (a 2023 Teikoku Databank survey of 127 private operators found
that about 80% were cutting service, and that even around Tokyo the cuts fell mostly on suburb-to-suburb routes and on
early-morning and late-night runs), so we expect a weekday median nearer 19:00-21:00 than 22:00
(L1, L2). The median is the lower median (the smaller middle value for an even count).

Context, not predictions: we found no published all-Japan, stop-by-stop count of first and last bus times from GTFS
(searched 2026-10-22); route-by-route and stop-by-stop timetable sites exist, and national surveys count route cuts, not
last-bus times. A place's last departure can be in any direction, so it is the latest time a bus leaves there, not the
last bus home.

MV2 of Munim, Inc. Made with AI agents working in MV2's name. CC BY 4.0.
