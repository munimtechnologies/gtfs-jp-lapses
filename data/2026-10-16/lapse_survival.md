# 空白はどれだけ続くか / How long does a GTFS feed lapse last?

調査日（2026-10-16）にまだ続いている空白は、その日までの長さで打ち切り（censored）として扱い、カプラン・マイヤー法で「空白が始まってから有効なデータが戻るまでの日数」を推定しました。終わった空白だけの中央値は、長く続いている空白を落とすので短めに出ます。
Each lapse runs from its first day without a valid file to the day before a valid file exists again. Lapses still open on the census day (2026-10-16) are censored at their length so far, and the time to recovery is estimated with the Kaplan-Meier method. A median of the ended lapses alone drops the long open ones and runs short.

| group | lapses | ended | still open | followed to (days) | KM median days | ended-only median | still lapsed after 30 d | 90 d | 180 d | 365 d | mean days within 365 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 203 | 175 | 28 | 929 | 80 | 56 | 67.9% | 47.4% | 28.5% | 13.4% | 130.2 |
| april_1 | 121 | 103 | 18 | 929 | 96 | 61 | 72.7% | 51.2% | 29.8% | 15.2% | 136.9 |
| other_days | 82 | 72 | 10 | 807 | 60 | 50.0 | 60.7% | 41.7% | 26.6% | 11.7% | 121.1 |
| april_1_2023 | 9 | 9 | 0 | 760 | 25 | 25 | 22.2% | 22.2% | 22.2% | 22.2% | 93.4 |
| april_1_2024 | 23 | 20 | 3 | 929 | 185 | 111.5 | 73.9% | 60.9% | 52.2% | 21.7% | 167.7 |
| april_1_2025 | 33 | 30 | 3 | 564 | 136 | 131.0 | 81.8% | 60.6% | 27.3% | 10.9% | 145.5 |
| april_1_2026 | 55 | 43 | 12 | 199 | 71 | 54 | 74.5% | 47.3% | 23.6% | – | 133.2 |

"still lapsed after t d" = Kaplan-Meier S(t), the share of lapses with no valid file yet after t days (– where no lapse in the group was followed that long). "mean days within 365" = restricted mean, the area under S(t) up to 365 days. Standard errors (Greenwood) are in the JSON.

## Log-rank tests

| test | ended in the first group | expected | chi-square | p | first group ends |
|---|---|---|---|---|---|
| april_1 vs other_days | 103 | 108.5 | 0.74 | 0.3898 | later |
| april_1_2026 vs april_1 before 2026 | 43 | 40.0 | 0.409 | 0.5224 | sooner |

## 2027-04-01: feed-days without a valid file within a year (recorded before the day)

Expected April-1 lapses from the forecasts in forecast/2027-04-01/ times the mean days without a valid file within 365 days of all April-1 lapses so far.

| forecast model | expected lapses | mean days per lapse | expected feed-days |
|---|---|---|---|
| rates_2026 | 61.6 | 136.9 | 8433 |
| rates_2024_2026 | 52.7 | 136.9 | 7215 |
| flat_2026 | 59.4 | 136.9 | 8132 |
| trend_2022_2026 | 69.0 | 136.9 | 9447 |
| trend_2024_2026 | 64.9 | 136.9 | 8885 |

限界: 空白は独立ではありません（同じ提供者のデータはまとめて空白になり、まとめて戻ることが多い）。p値は小さめに出ます。運行終了の印がないまま終わった路線は、終わらない空白に見えます。
Limits: lapses are not independent (one publisher's feeds often lapse and recover together), so the p-values are too small. A network that ended without being marked discontinued looks like a lapse that never ends. A lapse ends when any valid file exists again, which may be a back-dated file published later.

Source: GTFS Data Repository API v2 (https://gtfs-data.jp/) via the lapse census in this repository. Made by MV2 of Munim, Inc. with AI agents working in MV2's name. Data CC BY 4.0.
