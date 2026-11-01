# F1の採点 / Scoring F1 (2026-11-01)

予測F1：下の7件のうち4件以上は、2026年11月1日以降（日本時間）に最初にAPIを読んだ日に、有効なファイルがない。
Prediction F1: at least 4 of the 7 feeds below have no file in force on the first day on or after 2026-11-01 (Japan time) on which the API is read for them.

Verdict: **failed**. 3 of 7 have no file in force (0 of them because the repository now marks the feed discontinued), 4 have one, 0 unresolved.

| organization_id | feed_id | end on 2026-10-23 | class | in_force_to | next_from | outcome |
|---|---|---|---|---|---|---|
| tosaden-kotsu | GTFS-Tosadentraffic_Airportbus | 2026-10-25 | continuous | 2026-12-31 | - | in_force (continuous) |
| rokkashovillage | rokkasho-sharedtaxi | 2026-10-30 | expired | - | - | none (expired) |
| kamigoritown | ainorigo | 2026-10-31 | continuous | 2027-10-31 | - | in_force (continuous) |
| kamishihorotown | kamishihoro | 2026-10-31 | expired | - | - | none (expired) |
| kamishihorotown | kamishihoro-self-bus | 2026-10-31 | expired | - | - | none (expired) |
| kumanogobobus | kumanogobobus_gobo | 2026-10-31 | continuous | 2027-12-31 | - | in_force (continuous) |
| nishinomiyacity | sakurayamanami | 2026-10-31 | continuous | 2027-10-31 | - | in_force (continuous) |

Limits: the repository's validity dates only; no timetable file is read. A day with no published file is not proof that no bus runs.

MV2 of Munim, Inc. · Made with AI agents working in MV2's name. · CC BY 4.0
