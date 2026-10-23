# 時刻と停留所位置の確かめ・バスの表定速度 / Timing and stop-position census, scheduled bus speeds (2026-10-22)

停留所名の調査（names/2026-10-22）と同じデータの現行ファイルを読み、速すぎる区間・前の停留所を出る前に着く区間・座標のない停留所や国外の停留所・同じ座標に名前の違う停留所が重なるもの・stops.txt にない停留所への参照を数え、バスの便ごとの表定速度（停留所間の直線距離の合計 ÷ 始発から終着までの時間）を求めました。
The current file of every feed in the stop-name census was read again. Counted: steps faster than the limit for the route_type, steps that arrive before the previous stop was left, poles with missing, zero or outside-Japan coordinates, stacks of differently named poles at exactly the same coordinates, and stop_times pointing to stops that are not in stops.txt; and, per bus trip, the scheduled straight-line speed.

Feeds: 553; read 553; failed 0. Trips 80048; steps checked for speed 2267151; poles 98778.

| check | feeds | count |
|---|---|---|
| too fast for its route_type (under one minute counted as one) | 4 | 19 steps (16 under one minute) |
| arrives before it left the stop before | 1 | 1 steps |
| pole with missing, zero or outside-Japan coordinates | 1 | 0 missing or zero, 2 outside |
| stack: differently named poles at the same coordinates | 20 | 645 poles |
| stop_times pointing to a stop not in stops.txt | 0 | 0 rows |

Timing check per feed (flag = any of the rows above except stacks): flag 6, n/a 3, ok 544.

Scheduled bus speed (straight line through the timed stops): 76033 bus trips, median 17.5 km/h (quartiles 14.2 and 22.0); median of the 524 feeds' medians 18.5 km/h.

## Predictions recorded before any file was read

- T1: Between 5% and 30% of the files read have at least one step faster than the limit for its route_type. Result: 0.007: did not hold.
- T2: Fewer than 5% of the files read have at least one step where a trip arrives before it left the stop before. Result: 0.002: held.
- T3: Fewer than 3% of the files read have a pole with missing, zero or outside-Japan coordinates. Result: 0.002: held.
- T4: The median scheduled straight-line speed of bus trips, over all bus trips in all files read, is between 12 and 25 km/h. Result: 17.5: held.
- T5: At least half of all too-fast steps are scheduled at under one minute (0 minutes in a timetable given to the minute). Result: 0.842: held.
- T6: At least 10% of the files read have a stack: two or more differently named poles at exactly the same coordinates. Result: 0.036: did not hold.

Limits: straight lines between stops are shorter than the road, so the speeds run low, and a too-fast step can come from a wrong time or a wrong position; the census does not say which. Times are mostly given to the minute, so short steps are coarse. Only the current file of each feed is read, on the day of the run. A flag is a sign to check, not proof of a mistake. Place names in the data are records of fact, not judgements.

Generated 2026-10-22T21:03:26Z. Source: GTFS Data Repository API v2 (https://gtfs-data.jp/); each feed's publisher and licence are in feeds.csv. Made by MV2 of Munim, Inc. with AI agents working in MV2's name. Data CC BY 4.0.
