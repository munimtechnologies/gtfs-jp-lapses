# 割合の伸びと予測 / Is the April-1 lapse share rising? A trend check of the 2027-04-01 forecast

前年の割合をそのまま使う予測（persistence）と、各年の割合に引いた直線（trend、提供データ数で重み付け）を、その年より前のデータだけで比べました。
The year-before share (persistence) is compared with a straight line through the yearly shares (trend, weighted least squares by feeds at risk, years with at least 30 feeds at risk), each fitted on earlier years only. Ranges: independent = binomial; publisher = widened by the publisher design effect as in cluster_band.py; publisher_fit = also adds the uncertainty of the fitted line.

## Share of at-risk feeds lapsing on April 1

| year | at risk | lapsed | share | used in the line |
|---|---|---|---|---|
| 2019 | 4 | 0 | 0.0 | no |
| 2020 | 7 | 0 | 0.0 | no |
| 2021 | 14 | 0 | 0.0 | no |
| 2022 | 40 | 1 | 0.025 | yes |
| 2023 | 99 | 9 | 0.0909 | yes |
| 2024 | 149 | 23 | 0.1544 | yes |
| 2025 | 229 | 33 | 0.1441 | yes |
| 2026 | 272 | 55 | 0.2022 | yes |

## Back-test

| year | model | fit years | expected | observed | error | independent | publisher | publisher_fit |
|---|---|---|---|---|---|---|---|---|
| 2023 | persistence | 2022 | 2.5 | 9 | 6.5 |  |  |  |
| 2024 | persistence | 2023 | 13.5 | 23 | 9.5 |  |  |  |
| 2024 | trend_all | 2022-2023 | 23.4 | 23 | -0.4 | 16–31 ✓ | 11–36 ✓ | 0–64 ✓ |
| 2025 | persistence | 2024 | 35.3 | 33 | -2.3 |  |  |  |
| 2025 | trend_all | 2022-2024 | 50.1 | 33 | -17.1 | 39–61 ✗ | 36–65 ✗ | 16–84 ✓ |
| 2026 | persistence | 2025 | 39.2 | 55 | 15.8 |  |  |  |
| 2026 | trend_all | 2022-2025 | 51.5 | 55 | 3.5 | 40–63 ✓ | 36–67 ✓ | 23–80 ✓ |
| 2026 | trend_last3 | 2023-2025 | 47.2 | 55 | 7.8 | 36–58 ✓ | 33–62 ✓ | 17–77 ✓ |

Error = observed − expected. Each trend model against persistence, over the years it was tried in:

- trend_all (2024, 2025, 2026): mean error -4.67, mean absolute error 7.0; persistence 7.67 and 9.2
- trend_last3 (2026): mean error 7.8, mean absolute error 7.8; persistence 15.8 and 15.8

## 2027-04-01 (recorded before the day)

294 feeds; publisher design effect 2.055 (m = 2.633).

| model | share | expected | independent | publisher | publisher_fit |
|---|---|---|---|---|---|
| persistence_2026 | 0.2022 | 59.4 |  |  |  |
| trend_2022_2026 | 0.2348 | 69.0 | 57–81 | 51–87 | 40–98 |
| trend_2024_2026 | 0.2208 | 64.9 | 53–77 | 48–82 | 31–98 |

限界: 直線は数年分の点に引いただけで、伸びが続く保証はありません。prior/otherの層は分けていません。
Limits: a line through a few yearly points; nothing says the rise will continue, and a share cannot rise for ever. The prior/other split of fy2027_risk.py is not used here. These figures will be scored with the forecast after 2027-04-01.

Source: GTFS Data Repository API v2 (https://gtfs-data.jp/) via the lapse census in this repository. Made by MV2 of Munim, Inc. with AI agents working in MV2's name. Data CC BY 4.0.
