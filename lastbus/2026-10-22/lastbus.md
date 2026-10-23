# 始発と終バス：全国の停留所 / First and last buses at every place in Japan (2026-10-22)

停留所名の調査（names/2026-10-22）と同じデータの現行ファイルを読み、平日（水曜 2026-11-11）・土曜（2026-11-14）・日曜（2026-11-15）に、それぞれの停留所（同じ事業者データ内の同じ名前の標柱をまとめたもの）からバスが出る最初と最後の時刻を求めました。
The current file of every feed in the stop-name census was read. For an ordinary Wednesday (2026-11-11), Saturday (2026-11-14) and Sunday (2026-11-15), each place (a stop name within one feed) gets its first and last scheduled bus departure where riders may board.

Feeds: 553; read 553; failed 0. Files covering the Wednesday 527; with a bus departure that day 480.

Places with a bus departure: Wednesday 56496, Saturday 42823, Sunday 33468.

Weekday last departure: 10% of places by 15:38, 25% by 17:04, median 18:21, 75% by 19:31, 90% by 20:50. Median first departure 7:22.

| last weekday bus | share of places |
|---|---|
| before 18:00 | 41.8% |
| before 19:00 | 65.5% |
| before 20:00 | 81.4% |
| before 21:00 | 91.0% |
| before 22:00 | 96.4% |
| from 23:00 | 1.1% |

No bus on the Sunday: 23290 of 56496 weekday places in files covering the Sunday (41.2%). Saturday: 14673 of 56496 (26.0%).
Earlier last bus on the Sunday: 16184 of 33206 places served both days (48.7%); median difference 0 minutes.
Feeds whose median last weekday departure is before 18:00: 215 of 480 (44.8%).

## Predictions recorded before any file was read

- L1: Over all places with a bus departure on the Wednesday, the median last departure is between 19:00 and 21:00. Result: 18:21: did not hold.
- L2: At least 25% of the places with a bus departure on the Wednesday have their last departure before 19:00. Result: 0.655: held.
- L3: At least 15% of the places with a bus departure on the Wednesday, in files that cover the Sunday, have no bus departure on the Sunday. Result: 0.412: held.
- L4: At least 30% of the feeds with a bus departure on the Wednesday have a median last departure (over their places) before 18:00. Result: 0.448: held.
- L5: Fewer than 10% of the places with a bus departure on the Wednesday have their last departure at 23:00 or later. Result: 0.011: held.
- L6: Of the places with a bus departure on both the Wednesday and the Sunday, at least 40% have an earlier last departure on the Sunday. Result: 0.487: held.

Limits: timetable files only, not real-time running. A place is a stop name within one feed, so two different stops with the same name in one feed are merged, and a stop served by two operators appears once per feed. Only bus trips are counted (route_type 3, 200-299 or 700-799); demand-responsive trips that are in the files are counted like any other. The last departure from a place can be in any direction, so it is the latest time a bus leaves there, not the last bus home. Stops with no time in stop_times are not counted. Only the current file of each feed is read, on the day of the run; a file that does not cover a day has no departures that day.

Generated 2026-10-22T21:43:48Z. Source: GTFS Data Repository API v2 (https://gtfs-data.jp/); each feed's publisher and licence are in feeds.csv. Made by MV2 of Munim, Inc. with AI agents working in MV2's name. Data CC BY 4.0.
