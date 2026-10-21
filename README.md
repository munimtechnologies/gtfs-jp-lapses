# GTFS「空白日」調査 / GTFS Lapse Census (Japan)

全国の公開バス時刻表（GTFS）が、有効なデータのないまま何日あったかを数えたデータと集計スクリプトです。
A census of the days on which Japan's published bus timetables (GTFS) had no valid file.

MV2 of Munim, Inc. ・ データ CC BY 4.0、コード Apache-2.0 ・ 本調査はMV2の名のもと、AIエージェントが作成しました。
MV2 of Munim, Inc. · Data CC BY 4.0, code Apache-2.0 · Made with AI agents working in MV2's name.

---

## 日本語

### 何を数えたか
GTFSデータリポジトリ（https://gtfs-data.jp/ ）のAPI v2が返す各データの版履歴（公開日・有効期間）から、データごとに
「その日に有効な公開データが1つもなかった日」（空白日）を数えました。対象は602件・9,475版、2021年〜2026年10月16日です。

### 主な結果（2026年10月16日時点）
- 延べ492,026データ日のうち28,029日（5.7%）が空白。156件のデータに計203回の空白。
- 空白の割合: 2024年5.5%、2025年6.7%、2026年（10月16日まで）7.0%。少なくとも改善はしていません。
- 空白203回のうち121回（59.6%）は4月1日（年度初日）に始まり、空白日数の62%を占めます。
- 3月31日でデータが切れたデータのうち、4月1日に空白になった割合:
  2023年 9/99（9.1%）、2024年 23/150（15.3%）、2025年 33/230（14.3%）、2026年 55/272（20.2%）。
- 前年の4月1日にも空白になったデータは、2026年には21件中10件（48%）が再び空白に（他は251件中45件、18%）。
  2025年は17件中3件（18%、他は約14%）で、差は小さめでした。同じ提供者のデータはまとめて空白になりやすく、件数は独立ではありません。
- 現在有効な574件のうち292件（51%）は2027年3月31日に期限を迎えます。

### 2027年4月1日の予測（事前登録）
過去3年の割合（14.3〜20.2%）が続けば、**2027年4月1日に292件のうち約42〜59件（中央の見込み約47件）が空白になる**と予測します。
2027年4月8日ごろに同じ方法で集計し、ここに結果を追記します。単純な外挿で、モデルではありません。

### 限界
- 空白は「リポジトリに有効なデータがない日」で、バスが走らなかった日ではありません。
- リポジトリ以外で配布されるデータ、リポジトリから消えた古い版は見えません。
- NEWの版は公開日から、UPDATEの版は有効開始日から数えます（厳密版 lapsed_feed_days_strict はUPDATEも公開日から）。
- 運行終了の印がないまま終わった路線は、空白が続いているように見えることがあります。個別の地域名は事実の記録であり、評価ではありません。

### ファイル
- `data/2026-10-16/feeds.csv` データごとの集計（提供者・ライセンス付き）、`versions.csv` 全版、`lapses.csv` 空白1回ごと、
  `years.csv`、`prefectures.csv`、`fy_cliff.csv`（4月1日の集計）、`summary.json`、`findings.md`
- `tools/gtfs_lapses.py`（集計）、`tools/fy_cliff.py`（4月1日）、`tools/repeat_cliff.py`（再発）、各 `test_*.py`
- 再現: `python tools/gtfs_lapses.py --as-of 2026-10-16 --pause 1.0 --out out` → `python tools/fy_cliff.py out/lapses/2026-10-16`

### 出典とライセンス
版履歴はGTFSデータリポジトリ（https://gtfs-data.jp/ ）のAPIから取得しました。各データの提供者とライセンスは `feeds.csv` の
organization_name・license 列のとおりです。時刻表データそのものはここに含めていません。

---

## English

### What was counted
From the version history (publication date, validity period) that the GTFS Data Repository API v2
(https://gtfs-data.jp/) returns for each feed, we counted the days on which a feed had no valid published file
("lapsed days"): 602 feeds, 9,475 files, 2021 to 2026-10-16.

### Main results (as of 2026-10-16)
- 28,029 of 492,026 feed-days (5.7%) had no valid file; 203 lapses in 156 feeds.
- Lapsed share: 2024 5.5%, 2025 6.7%, 2026 (to 10-16) 7.0%. Not improving.
- 121 of the 203 lapses (59.6%) began on April 1, the first day of Japan's fiscal year; they hold 62% of all lapsed days.
- Of the feeds whose data ended on March 31, the share with no valid file on April 1 was 9.1% (2023, 9/99),
  15.3% (2024, 23/150), 14.3% (2025, 33/230) and 20.2% (2026, 55/272).
- Feeds that lapsed on the previous April 1 lapsed again in 2026 in 10 of 21 cases (48%), against 45 of 251 (18%) for
  the rest. In 2025 the gap was small (3 of 17, 18%, vs about 14%). Feeds from one publisher tend to lapse together,
  so these counts are not independent.
- 292 of the 574 active feeds (51%) are set to expire on 2027-03-31.

### Forecast for 2027-04-01 (recorded in advance)
If the last three years' rates (14.3–20.2%) hold, **about 42–59 of those 292 feeds (central estimate ~47) will have no
valid file on 2027-04-01**. We will re-run the census around 2027-04-08 and add the result here. This is a simple
extrapolation, not a model.

### Limits
- A lapse means the repository had no valid file, not that buses stopped running.
- Files distributed outside the repository, and old versions no longer in it, are not seen.
- NEW files count from their publication date, UPDATE files from their start date (the strict count dates both from
  publication).
- A network that ended without being marked discontinued can look like an open lapse. Place names in the data are
  records of fact, not judgements.

### Sources and licences
Version histories come from the GTFS Data Repository API (https://gtfs-data.jp/). Each feed's publisher and licence are
in the organization_name and license columns of `feeds.csv`. No timetable data is redistributed here.

Contact: MV2, Munim, Inc., mv2@munimtech.com
