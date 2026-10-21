# 提供者・都道府県ごとのまとまりと予測の幅 / Clustering and the width of the 2027-04-01 forecast

同じ提供者（または同じ都道府県）のデータは4月1日にまとめて空白になりやすく、件数は独立ではありません。
各年の級内相関（ICC、分散分析による推定）から、予測の「90%の目安」をデザイン効果 1 + (m − 1) × ICC で広げます。
Feeds from one publisher (or one prefecture) tend to lapse together on April 1, so counts are not independent. The rough 90% range is widened by the design effect 1 + (m - 1) x ICC, with the intra-cluster correlation (ICC, ANOVA estimate) of each year's April-1 lapses and m the size-weighted mean cluster size of the 2027 cohort.

2027 cohort: 294 feeds (prior 37, other 257), 228 publishers (m = 2.633, largest 14 feeds), 38 prefectures (m = 15.83, largest 36 feeds).

## ICC by year

| year | at risk | lapsed | publishers | with a lapse | ICC publisher | prefectures | with a lapse | ICC prefecture |
|---|---|---|---|---|---|---|---|---|
| 2019 | 4 | 0 | 3 | 0 | 0.0 | 2 | 0 | 0.0 |
| 2020 | 7 | 0 | 6 | 0 | 0.0 | 3 | 0 | 0.0 |
| 2021 | 14 | 0 | 13 | 0 | 0.0 | 7 | 0 | 0.0 |
| 2022 | 40 | 1 | 35 | 1 | -3.0789 | 8 | 1 | -0.1905 |
| 2023 | 99 | 9 | 80 | 9 | 1.0 | 17 | 4 | -0.0893 |
| 2024 | 149 | 23 | 112 | 18 | 0.5916 | 23 | 12 | 0.2958 |
| 2025 | 229 | 33 | 179 | 32 | 0.8394 | 30 | 15 | 0.1202 |
| 2026 | 272 | 55 | 218 | 48 | 0.6463 | 34 | 21 | 0.2298 |

Pooled 2024-2026 (clusters counted per year): publisher 0.6954, prefecture 0.2038.

## Back-test (rates and ICC from the year before only)

| year | model | expected | observed | independent | publisher | prefecture |
|---|---|---|---|---|---|---|
| 2020 | flat | 0.0 | 0 | 0–0 ✓ (deff 1.0) | 0–0 ✓ (deff 1.0) | 0–0 ✓ (deff 1.0) |
| 2021 | flat | 0.0 | 0 | 0–0 ✓ (deff 1.0) | 0–0 ✓ (deff 1.0) | 0–0 ✓ (deff 1.0) |
| 2022 | flat | 0.0 | 1 | 0–0 ✗ (deff 1.0) | 0–0 ✗ (deff 1.0) | 0–0 ✗ (deff 1.0) |
| 2023 | flat | 2.5 | 9 | 0–6 ✗ (deff 1.0) | 0–6 ✗ (deff 1.0) | 0–6 ✗ (deff 1.0) |
| 2024 | flat | 13.5 | 23 | 7–20 ✗ (deff 1.0) | 3–24 ✓ (deff 2.785) | 7–20 ✗ (deff 1.0) |
| 2025 | flat | 35.3 | 33 | 26–45 ✓ (deff 1.0) | 23–48 ✓ (deff 1.837) | 15–56 ✓ (deff 5.066) |
| 2025 | by_group | 37.7 | 33 | 28–47 ✓ (deff 1.0) | 25–51 ✓ (deff 1.837) | 17–59 ✓ (deff 5.066) |
| 2026 | flat | 39.2 | 55 | 29–49 ✗ (deff 1.0) | 26–53 ✗ (deff 1.889) | 23–55 ✓ (deff 2.737) |
| 2026 | by_group | 39.4 | 55 | 29–49 ✗ (deff 1.0) | 26–53 ✗ (deff 1.889) | 23–56 ✓ (deff 2.737) |

## 2027-04-01: rough 90% ranges (recorded before the day)

| model | expected | independent | publisher_icc_2026 | publisher_icc_pooled | prefecture_icc_2026 | prefecture_icc_pooled |
|---|---|---|---|---|---|---|
| rates_2026 | 61.6 | 50–73 (deff 1.0) | 45–78 (deff 2.055) | 45–79 (deff 2.135) | 37–86 (deff 4.408) | 38–85 (deff 4.022) |
| rates_2024_2026 | 52.7 | 42–64 (deff 1.0) | 37–69 (deff 2.055) | 37–69 (deff 2.135) | 30–76 (deff 4.408) | 31–75 (deff 4.022) |
| flat_2026 | 59.4 | 48–71 (deff 1.0) | 43–76 (deff 2.055) | 42–77 (deff 2.135) | 35–84 (deff 4.408) | 36–83 (deff 4.022) |

限界: ICCは年ごとの少ないまとまりから推定するので不安定です。デザイン効果はprior/otherの層を区別しない近似です。
Limits: the ICC is estimated from few clusters per year and is noisy; the design effect ignores the prior/other strata; feeds new since the census get their prefecture from cohort.csv. These ranges will be scored with the forecast after 2027-04-01.

Source: GTFS Data Repository API v2 (https://gtfs-data.jp/) via the lapse census in this repository. Made by MV2 of Munim, Inc. with AI agents working in MV2's name. Data CC BY 4.0.
