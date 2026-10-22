# 時刻と停留所位置の確かめ: 事前に記録した予測 / Timing and stop-position census: predictions recorded in advance

Recorded on 2026-10-22, before `tools/timing_check.py` read any file. The commit date of this file is the record.
この予測は、`tools/timing_check.py` がどのファイルも読む前の2026年10月22日に記録しました。

The census reads the current file of every feed in `names/2026-10-22/feeds.csv` (553 active, openly licensed feeds of
the GTFS Data Repository) and counts, per file: steps between two consecutive timed stops faster than the limit for the
route_type (MobilityData's fast_travel_between_consecutive_stops limits: bus 150 km/h, ferry 80, rail 500 …; a step under
one minute counts as one minute), steps that arrive before the trip left the stop before, poles with missing, zero or
outside-Japan coordinates, stacks of differently named poles at exactly the same coordinates, and timed stop_times that
point to a stop missing from stops.txt. For bus trips it gives the scheduled straight-line speed.

| | prediction | holds if |
|---|---|---|
| T1 | Between 5% and 30% of the files read have at least one too-fast step. | 0.05 ≤ share ≤ 0.30 |
| T2 | Fewer than 5% of the files read have a step that arrives before it left the stop before. | share < 0.05 |
| T3 | Fewer than 3% of the files read have a pole with missing, zero or outside-Japan coordinates. | share < 0.03 |
| T4 | The median scheduled straight-line speed over all bus trips is between 12 and 25 km/h. | 12 ≤ median ≤ 25 |
| T5 | At least half of all too-fast steps are scheduled at under one minute. | share ≥ 0.5 |
| T6 | At least 10% of the files read have a stack of differently named poles at the same coordinates. | share ≥ 0.10 |

Why these: an ITS Feed census of 736 US feeds (MobilityData validator v8.0.1, 2026-09-29) found
fast_travel_between_consecutive_stops in 17% of feeds (context for T1; the rules differ, so it is not a benchmark).
T. Shimada's list of Japanese GTFS feeds warns that in some files the poles are not at their real places but all sit on
one spot (T6). Japanese timetables are mostly given to the minute, so we expect most too-fast steps to be 0-minute
steps rather than wrong positions (T5). The median is the lower median (the smaller middle value for an even count).

Context, not predictions: GTFS Scorecard (https://gtfsscorecard.org/) grades some Japanese feeds one by one with the
MobilityData validator. We found no published all-Japan count of these checks, and no all-Japan figure for scheduled bus
speeds (表定速度) from GTFS (searched 2026-10-22).

MV2 of Munim, Inc. Made with AI agents working in MV2's name. CC BY 4.0.
