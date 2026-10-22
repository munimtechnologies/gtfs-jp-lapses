# 続いている空白はいつ終わるか / When will the open lapses end? (recorded in advance)

調査日（2026-10-16）にまだ続いていた空白27回それぞれについて、全空白のカプラン・マイヤー曲線とそれまでの長さから、30日・90日以内に有効なデータが戻る確率を求め、戻る件数の見込みを記録しました。
For each of the 27 lapses still open on the census day (2026-10-16), the chance that a valid file exists again within 30 and 90 days, from the Kaplan-Meier curve of all lapses given how long the lapse has lasted so far, and the expected number that end.

| horizon | last lapse day | open lapses | expected to end | median | rough 90% |
|---|---|---|---|---|---|
| 30 d | 2026-11-15 | 27 | 1.0 | 1 | 0–3 |
| 90 d | 2027-01-14 | 27 | 5.45 | 5 | 2–9 |

| organization_id | feed_id | start | days so far | April 1 | P(over within 30 d) | P(over within 90 d) |
|---|---|---|---|---|---|---|
| higashiomicity | higasiohmisicommunitybus | 2026-10-01 | 16 | no | 0.15 | 0.42 |
| kotosan | kotohira-local | 2026-10-01 | 16 | no | 0.15 | 0.42 |
| andotown | andocombus | 2026-04-01 | 199 | yes | 0.03 | 0.26 |
| kamikatsutown | kamikatsutownbus | 2026-04-01 | 199 | yes | 0.03 | 0.26 |
| kiyosato | kiyosato-picnicbus | 2026-04-01 | 199 | yes | 0.03 | 0.26 |
| minobutown | furusekikaiiwamasen | 2026-04-01 | 199 | yes | 0.03 | 0.26 |
| minobutown | furusekizyunkansen | 2026-04-01 | 199 | yes | 0.03 | 0.26 |
| minobutown | iitomimotosukosen | 2026-04-01 | 199 | yes | 0.03 | 0.26 |
| nirasakicity | shiminbus | 2026-04-01 | 199 | yes | 0.03 | 0.26 |
| okayacity | silkybus | 2026-04-01 | 199 | yes | 0.03 | 0.26 |
| rittocity | rittoukurichanbus | 2026-04-01 | 199 | yes | 0.03 | 0.26 |
| sanjocity | guruttosan | 2026-04-01 | 199 | yes | 0.03 | 0.26 |
| tateshinatown | tateshinasmile | 2026-04-01 | 199 | yes | 0.03 | 0.26 |
| tochigi-nakagawatown | nakagawamaticommunitybus | 2026-04-01 | 199 | yes | 0.03 | 0.26 |
| tokushima-minamitown | minabubyoinrenrakubus | 2026-03-21 | 210 | no | 0.06 | 0.26 |
| uozucity | omotenashi | 2026-03-17 | 214 | no | 0.06 | 0.29 |
| waketown | wakechoueibasu | 2026-01-01 | 289 | no | 0.04 | 0.35 |
| iijimatown | iichanbus | 2025-12-10 | 311 | no | 0.05 | 0.37 |
| chiba-rainbow-bus | chibarainbowbus | 2025-10-01 | 381 | no | 0.14 | 0.21 |
| katocity | yashiroshigaichinoriaitaxi | 2025-04-01 | 564 | yes | 0.00 | 0.00 |
| susamitown | Communitybus | 2025-04-01 | 564 | yes | 0.00 | 0.00 |
| nagano-nakanocity | fureaibus | 2025-01-12 | 643 | no | 0.00 | 0.00 |
| yabucity | waiwai-sekimiya-yoka | 2025-01-01 | 654 | no | 0.00 | 0.00 |
| kanumacity | ri-bus | 2024-08-01 | 807 | no | 0.00 | 0.00 |
| hyogo-kamitown | kamichominbus | 2024-04-01 | 929 | yes | 0.00 | 0.00 |
| kitaaikivillage | soneibus | 2024-04-01 | 929 | yes | 0.00 | 0.00 |
| shinanotown | rosenbus | 2024-04-01 | 929 | yes | 0.00 | 0.00 |

Left out: 1 open lapse(s) whose feed was marked discontinued before the census day.

限界: 同じ提供者のデータはまとめて戻ることが多く、幅は実際より狭めです。曲線の後ろの方（数百日）は空白が少なく不確かで、最後に空白が終わった長さより長く続いている空白は、確率0と出ます。
Limits: one publisher's feeds often recover together, so the real range is wider. The tail of the curve (hundreds of days) rests on few lapses; a lapse already longer than the longest one that ever ended gets probability 0. Scored with a later census (tools/recovery_forecast.py --score).

Source: GTFS Data Repository API v2 (https://gtfs-data.jp/) via the lapse census in this repository. Made by MV2 of Munim, Inc. with AI agents working in MV2's name. Data CC BY 4.0.
