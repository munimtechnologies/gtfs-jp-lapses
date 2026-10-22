# GTFS「空白日」調査 / GTFS Lapse Census (Japan)

全国の公開バス時刻表（GTFS）が、有効なデータのないまま何日あったかを数えたデータと集計スクリプトです。
A census of the days on which Japan's published bus timetables (GTFS) had no valid file.

MV2 of Munim, Inc. ・ データ CC BY 4.0、コード Apache-2.0 ・ 本調査はMV2の名のもと、AIエージェントが作成しました。
MV2 of Munim, Inc. · Data CC BY 4.0, code Apache-2.0 · Made with AI agents working in MV2's name.

最新の期限一覧 / Latest expiry list: [watch/2026-10-22/watch.md](watch/2026-10-22/watch.md) ・
2027年4月1日のグループ別予測 / Forecast for 2027-04-01 by group: [forecast/2027-04-01/forecast.md](forecast/2027-04-01/forecast.md) ・
まとまりを考えた幅と過去の検証 / Clustering and back-test: [forecast/2027-04-01/cluster_band.md](forecast/2027-04-01/cluster_band.md) ・
割合の伸びを入れた予測 / Trend check: [forecast/2027-04-01/trend_band.md](forecast/2027-04-01/trend_band.md) ・
空白はどれだけ続くか / How long lapses last: [data/2026-10-16/lapse_survival.md](data/2026-10-16/lapse_survival.md) ・
続いている空白はいつ終わるか / When the open lapses end: [forecast/recovery/2026-10-16/recovery.md](forecast/recovery/2026-10-16/recovery.md)

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
- 前年の4月1日にも空白になったデータは、2026年には25件中10件（40%）が再び空白に（他は247件中45件、18%、片側二項検定 p ≈ 0.009）。
  2025年は17件中3件（18%、他は212件中30件、14%）、2024年は5件中2件（他は144件中21件、15%）で、差は小さめでした。
  同じ提供者のデータはまとめて空白になりやすく、件数は独立ではありません（`data/2026-10-16/repeat_cliff.md`）。
- 空白が始まってから有効なデータが戻るまでの日数の中央値は80日（まだ続いている空白も含めた推定）。1年たっても13%が空白のままでした。
- 現在有効な574件のうち292件（51%）は2027年3月31日に期限を迎えます（2026年10月22日の一覧では580件中294件）。

**訂正（2026-10-22）:** 以前の版は2026年の再発を「21件中10件（48%）、他は251件中45件」と書いていました。公開している
`tools/repeat_cliff.py` で数え直すと25件中10件、他は247件中45件です（合計272件は上の3月31日のデータ数と一致します）。

### 2027年4月1日の予測（事前登録）
過去3年の割合（14.3〜20.2%）が続けば、**2027年4月1日に292件のうち約42〜59件（中央の見込み約47件）が空白になる**と予測します。
2027年4月8日ごろに同じ方法で集計し、ここに結果を追記します。単純な外挿で、モデルではありません。

### グループ別の予測（事前登録、2026年10月22日）
`tools/fy2027_risk.py` で、2027年3月31日に最新データが切れる有効なデータ294件を、2026年4月1日にも空白になったもの
（prior、37件）とそれ以外（other、257件）に分けて記録しました（`forecast/2027-04-01/cohort.csv`）。
- 2026年の割合（prior 40.0%、other 18.2%）なら約61.6件（14.8＋46.8）、2024〜2026年の割合（31.9%、15.9%）なら約52.7件、
  グループ分けなしの2026年の割合（20.2%）なら約59.4件。
- 仮説: 2027年4月1日の空白の割合は prior が other より高い（片側フィッシャー正確検定、p < 0.05、データ1件ずつ）。
- 表の「90%の目安」はデータを独立とみなした概算で、同じ提供者のデータはまとめて空白になりやすいため実際の幅はもっと広くなります
  （次の節）。
- このファイルのコミット日が、2027年4月1日より前に記録した証拠です。4月1日以降に新しい調査の `lapses.csv` で
  `python tools/fy2027_risk.py --census <調査> --score <新しいlapses.csv> --cohort forecast/2027-04-01/cohort.csv` を実行して採点します。
  上の単純な予測（292件中42〜59件）もそのまま残し、両方を採点します。

### まとまりを考えた幅と過去の検証（事前登録、2026年10月22日）
`tools/cluster_band.py` で、同じ提供者・同じ都道府県のデータが4月1日にまとめて空白になる度合い（級内相関ICC、分散分析による推定）を
年ごとに求め、予測の「90%の目安」をデザイン効果 1 + (m − 1) × ICC で広げました（`forecast/2027-04-01/cluster_band.md`）。
- 2026年のICCは提供者0.65、都道府県0.23（2024〜2026年をまとめると0.70と0.20）。2027年の294件は228の提供者・38の都道府県に属し、
  デザイン効果は提供者で約2.1、都道府県で約4.0〜4.4です。
- 広げた幅: 2026年の割合（約61.6件）なら、独立とみなして50〜73件、提供者で広げて45〜78件、都道府県で広げて37〜86件。
  2024〜2026年の割合（約52.7件）なら42〜64件、37〜69件、30〜76件。
- 過去の検証（前年の割合とICCだけで翌年を予測）: 空白のあった2022〜2026年の5回のうち、独立の幅に入ったのは1回（2025年）、
  提供者で広げた幅は2回（2024・2025年）、都道府県で広げた幅は2回（2025年と、上限ちょうどの2026年）でした。
- 外れた回はすべて、実際の件数が幅の上限を超えていました。割合がおおむね上がっている（2022年2.5%、2023年9.1%、2024年15.4%、
  2025年14.4%、2026年20.2%）ため、前年の割合では少なめに出ます。幅を広げるだけでは足りないということです。
  割合の伸びを入れた予測は次の節にあります。
- ここでの対象は `repeat_cliff.py` の定義（3月31日に切れ、その日に空白中でないデータ）なので、2024・2025年は上の集計（150件・230件）
  より1件ずつ少ない149件・229件です。ICCは年ごとの少ないまとまりから推定するので不安定です（空白の少ない年は負や1になります）。

### 割合の伸びを入れた予測（事前登録、2026年10月22日）
`tools/trend_band.py` で、4月1日に空白になった割合（上と同じ `repeat_cliff.py` の定義）の年ごとの値に直線を引き（対象データ数で
重み付けした最小二乗。対象が30件以上の2022〜2026年だけ）、その年より前の年だけで引いた直線と、前年の割合をそのまま使う予測を
比べました（`forecast/2027-04-01/trend_band.md`）。
- 過去の検証（2022年からの直線、2024〜2026年）: 誤差（実際−予測）は2024年 −0.4件、2025年 −17.1件、2026年 +3.5件で、
  平均絶対誤差は7.0件。前年の割合では +9.5件、−2.3件、+15.8件で9.2件。平均では直線のほうが近いものの、割合が少し下がった
  2025年は大きく多めに外しました（予測50.1件、実際33件）。比べられたのは3年分だけです。
- 90%の目安（提供者のまとまりで広げた幅に、直線そのものの不確かさも加えたもの）は3年とも実際の件数を含みました。
  独立とみなした幅と提供者で広げただけの幅は、2025年に外れました。
- 2027年4月1日（294件）: 前年の割合なら約59.4件、2022〜2026年の直線なら約69.0件（23.5%）、2024〜2026年の直線なら
  約64.9件（22.1%）。
- 90%の目安: 2022〜2026年の直線で、独立とみなして57〜81件、提供者で広げて51〜87件、直線の不確かさも加えて40〜98件。
  2024〜2026年の直線では53〜77件、48〜82件、31〜98件。
- 限界: 数年分の点に引いた直線にすぎず、伸びが続く保証はありません。割合がいつまでも上がり続けることはありません。
  prior/other の分け方はここでは使っていません。これらの数字も2027年4月1日以降に上の予測と一緒に採点します。

### 空白はどれだけ続くか（2026年10月22日）
`tools/lapse_survival.py` で、空白が始まってから有効なデータが戻るまでの日数を推定しました。調査日（2026年10月16日）にまだ続いている
空白28回は、その日までの長さで打ち切り（censored）として扱うカプラン・マイヤー法です（`data/2026-10-16/lapse_survival.md`）。
- 空白203回全体: 中央値80日。終わった175回だけの中央値は56日で、続いている長い空白を落とすぶん短く出ます。
  30日後に67.9%、90日後に47.4%、180日後に28.5%、1年後に13.4%がまだ空白でした。乗換案内アプリTransitは期限の切れた時刻表を
  1か月延長して表示すると公表しています（https://resources.transitapp.com/article/458-guidelines-for-producing-gtfs-static-data-for-transit ）が、
  空白の3分の2はその1か月より長く続いています。
- 4月1日に始まった121回: 中央値96日（終わったものだけでは61日）、1年後も15.2%が空白、最初の1年のうち平均136.9日が空白
  （制限付き平均）。それ以外の日に始まった82回: 中央値60日、1年後11.7%、平均121.1日。
- ログランク検定では、4月1日の空白が他より長く続くとは言えません（p = 0.39）。2026年4月1日の空白（中央値71日、12回はまだ継続中）
  とそれ以前の4月1日の空白にも差は見られません（p = 0.52）。空白は独立ではないので、p値は実際より小さめに出ているはずです。
- 年ごとの「終わった空白だけの中央値」（2024年111.5日、2025年131日、2026年54日）は `fy_cliff.md` と一致します。
  カプラン・マイヤーの中央値は2024年185日、2025年136日、2026年71日です。
- 2027年4月1日（事前記録）: 上の各予測の件数 × 4月1日の空白1回あたりの最初の1年の平均空白日数（136.9日）で、2027年4月1日から
  1年の間に約7,200データ日（2024〜2026年のグループ別割合）〜約9,400データ日（2022〜2026年の直線）が空白になると見込みます。
  採点できるのはその1年が終わる2028年4月以降です。
- 限界: 運行終了の印がないまま終わった路線は終わらない空白に見え、長さを長めにします。あとから公開された版の有効期間が
  さかのぼって空白を埋めた場合も、空白はその日に終わったと数えます。すでに集計で見ていたデータの記述で、事前登録ではありません。

### 続いている空白はいつ終わるか（事前登録、2026年10月22日）
`tools/recovery_forecast.py` で、調査日（2026年10月16日）にまだ続いていた空白27回（運行終了の印が付いたデータの1回は除く）それぞれについて、
上のカプラン・マイヤー曲線とそれまでの長さから、30日・90日以内に有効なデータが戻る確率を求めました（`forecast/recovery/2026-10-16/recovery.md`）。
- 30日以内（空白の最終日が2026年11月15日まで）: 戻る見込み1.0回（中央1回、90%の目安0〜3回）。
- 90日以内（2027年1月14日まで）: 5.45回（中央5回、2〜9回）。
- 続いている空白の長さは16〜929日。2026年10月1日に始まった2回は、30日以内に戻る確率15%、90日以内42%。2026年4月1日に始まった
  12回はそれぞれ3%と26%。27回のうち8回（564日以上）は、これまでに終わったどの空白よりも長く続いているため確率0と出ます。
  運行終了の印がないまま更新の止まったデータが多いとみられます。
- 記録は2026年10月22日で、使ったのは10月16日の調査だけです。10月22日の期限一覧（上）はすでに公開していましたが、この予測には
  使っていません。2026年11月16日ごろと2027年1月15日以降に新しい調査で採点し、ここに追記します:
  `python tools/recovery_forecast.py --lapses <新しいlapses.csv> --score <新しいlapses.csv> --as-of <その調査日> --forecast-json forecast/recovery/2026-10-16/recovery.json --out out`
- 限界: 同じ提供者のデータはまとめて戻ることが多いので、幅は実際より狭めです。曲線の後ろの方は空白が少なく揺れが大きい
  （381日続く1回の30日以内の確率14%が、199日の空白の3%より高く出るなど）。

### 期限切れ・期限間近の一覧（expiry_watch.py）
`tools/expiry_watch.py` は、リポジトリのデータ一覧（APIへの1回の問い合わせ）から、最新データの期限が過ぎた、または60日以内に切れる
データを残り日数の順に並べ、それぞれの過去の空白回数（うち4月1日）をこの調査の `lapses.csv` から付けます。
リポジトリは期限の14日前に各提供者へメールで知らせています。この一覧は同じ情報を、データを読むアプリや経路検索の側から見られるように
公開するものです。出力は `watch/<日付>/` の `expiring.csv`・`watch.md`・`summary.json`。
実行: `python tools/expiry_watch.py --out out`（`--as-of YYYY-MM-DD` で日付指定）。

2026年10月22日（日本時間）の一覧: 有効580件のうち期限切れ27件、7日以内1件、8〜30日17件、31〜60日10件。載った55件のうち31件に
過去の空白があり、18件は4月1日の空白です。期限切れの27件には、運行終了の印がないまま更新の止まったデータも含まれるとみられます。
今後は週に1回ほど更新します。

### 限界
- 空白は「リポジトリに有効なデータがない日」で、バスが走らなかった日ではありません。
- リポジトリ以外で配布されるデータ、リポジトリから消えた古い版は見えません。
- NEWの版は公開日から、UPDATEの版は有効開始日から数えます（厳密版 lapsed_feed_days_strict はUPDATEも公開日から）。
- 運行終了の印がないまま終わった路線は、空白が続いているように見えることがあります。個別の地域名は事実の記録であり、評価ではありません。
- 期限の一覧は latest_feed_end_date だけを見るので、次のデータの開始が遅れる場合の空白などは拾えません。

### ファイル
- `data/2026-10-16/feeds.csv` データごとの集計（提供者・ライセンス付き）、`versions.csv` 全版、`lapses.csv` 空白1回ごと、
  `years.csv`、`prefectures.csv`、`fy_cliff.csv`（4月1日の集計）、`repeat_cliff.csv`・`repeat_cliff.md`（再発）、`summary.json`、`findings.md`、
  `lapse_survival.json`・`lapse_survival.md`（空白の続く日数）
- `watch/<日付>/` 期限の一覧
- `forecast/2027-04-01/` グループ別の予測（`cohort.csv`・`forecast.json`・`forecast.md`）、まとまりを考えた幅と過去の検証
  （`cluster_band.json`・`cluster_band.md`）、割合の伸びを入れた予測（`trend_band.json`・`trend_band.md`）
- `forecast/recovery/2026-10-16/` 続いている空白が終わる確率（`recovery.json`・`recovery.md`・`recovery.csv`）
- `tools/gtfs_lapses.py`（集計）、`tools/fy_cliff.py`（4月1日）、`tools/repeat_cliff.py`（再発）、`tools/expiry_watch.py`（期限の一覧）、
  `tools/fy2027_risk.py`（グループ別の予測と採点）、`tools/cluster_band.py`（まとまりと幅）、`tools/trend_band.py`（割合の伸び）、
  `tools/lapse_survival.py`（空白の続く日数）、`tools/recovery_forecast.py`（続いている空白の予測と採点）、各 `test_*.py`
- 再現: `python tools/gtfs_lapses.py --as-of 2026-10-16 --pause 1.0 --out out` → `python tools/fy_cliff.py out/lapses/2026-10-16`
  → `python tools/repeat_cliff.py out/lapses/2026-10-16`

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
- Feeds that lapsed on the previous April 1 lapsed again in 2026 in 10 of 25 cases (40%), against 45 of 247 (18%) for
  the rest (one-sided binomial p ≈ 0.009). The gap was smaller in 2025 (3 of 17, 18%, vs 30 of 212, 14%) and 2024
  (2 of 5 vs 21 of 144, 15%). Feeds from one publisher tend to lapse together, so these counts are not independent
  (`data/2026-10-16/repeat_cliff.md`).
- Once a lapse begins, the median time until a valid file exists again is 80 days (an estimate that includes the
  lapses still open); 13% were still lapsed after a year.
- 292 of the 574 active feeds (51%) are set to expire on 2027-03-31 (294 of 580 in the 2026-10-22 list).

**Correction (2026-10-22):** an earlier version gave the 2026 repeat figures as 10 of 21 (48%) against 45 of 251.
The published `tools/repeat_cliff.py` gives 10 of 25 and 45 of 247 (the 272 total matches the March 31 count above).

### Forecast for 2027-04-01 (recorded in advance)
If the last three years' rates (14.3–20.2%) hold, **about 42–59 of those 292 feeds (central estimate ~47) will have no
valid file on 2027-04-01**. We will re-run the census around 2027-04-08 and add the result here. This is a simple
extrapolation, not a model.

### Forecast by group (recorded in advance, 2026-10-22)
`tools/fy2027_risk.py` recorded the 294 active feeds whose latest file ends on 2027-03-31, split into those that also
had no valid file on 2026-04-01 (prior, 37 feeds) and the rest (other, 257) (`forecast/2027-04-01/cohort.csv`).
- At the 2026 rates (prior 40.0%, other 18.2%) about 61.6 lapses are expected (14.8 + 46.8); at the 2024–2026 rates
  (31.9%, 15.9%) about 52.7; at one 2026 rate for all (20.2%) about 59.4.
- Hypothesis: on 2027-04-01 the prior group lapses at a higher share than the other group (one-sided Fisher exact
  test, p < 0.05, one feed at a time).
- The "rough 90%" ranges in the table treat feeds as independent. Feeds from one publisher tend to lapse together, so
  the real spread is wider (next section).
- The commit date of these files is the proof that they were recorded before 2027-04-01. After that day, the score
  comes from a new census's `lapses.csv` with
  `python tools/fy2027_risk.py --census <census> --score <new lapses.csv> --cohort forecast/2027-04-01/cohort.csv`.
  The simple forecast above (42–59 of 292) stays as written, and both will be scored.

### Clustering and a back-test (recorded in advance, 2026-10-22)
`tools/cluster_band.py` estimates, for each year, how strongly feeds from one publisher or one prefecture lapse together
on April 1 (intra-cluster correlation, ICC, ANOVA estimate) and widens the rough 90% ranges by the design effect
1 + (m − 1) × ICC (`forecast/2027-04-01/cluster_band.md`).
- ICC in 2026: 0.65 by publisher, 0.23 by prefecture (pooled over 2024–2026: 0.70 and 0.20). The 294 feeds of the 2027
  cohort belong to 228 publishers and 38 prefectures, giving design effects of about 2.1 (publisher) and 4.0–4.4
  (prefecture).
- Widened ranges: at the 2026 rates (about 61.6) 50–73 treating feeds as independent, 45–78 widened by publisher and
  37–86 by prefecture; at the 2024–2026 rates (about 52.7) 42–64, 37–69 and 30–76.
- Back-test, predicting each year from the year before only (its rate and its ICC): in the five years 2022–2026 that
  had lapses, the independent range held the observed count once (2025), the publisher-widened range twice (2024,
  2025) and the prefecture-widened range twice (2025, and 2026 exactly at its upper end).
- Every miss was an observed count above the top of the range. The share has mostly risen (2022 2.5%, 2023 9.1%,
  2024 15.4%, 2025 14.4%, 2026 20.2%), so the year-before rate runs low; wider ranges alone do not fix that. A forecast
  that allows for the rise is in the next section.
- These counts use the at-risk rule of `repeat_cliff.py` (a file ending on March 31 and no lapse already running that
  day), so 2024 and 2025 have 149 and 229 feeds, one fewer each than the 150 and 230 above. The ICC comes from few
  clusters per year and is noisy (years with few lapses give negative values or 1).

### Trend check (recorded in advance, 2026-10-22)
`tools/trend_band.py` fits a straight line to the yearly share of at-risk feeds that lapsed on April 1 (the
`repeat_cliff.py` rule above; weighted least squares by feeds at risk, using only the years with at least 30 at risk,
2022–2026), and compares it with the year-before share, fitting each year from earlier years only
(`forecast/2027-04-01/trend_band.md`).
- Back-test (line from 2022 on, 2024–2026): errors (observed − expected) were −0.4 in 2024, −17.1 in 2025 and +3.5 in
  2026, a mean absolute error of 7.0 lapses. The year-before share gave +9.5, −2.3 and +15.8, or 9.2. The line is
  closer on average but overshot badly in 2025, when the share dipped slightly (50.1 expected, 33 observed). Only
  three years could be compared.
- The widest rough 90% range (publisher-widened plus the uncertainty of the fitted line) held the observed count in all
  three years; the independent and publisher-only ranges missed in 2025.
- 2027-04-01 (294 feeds): the year-before share gives about 59.4 lapses, the 2022–2026 line about 69.0 (23.5%) and the
  2024–2026 line about 64.9 (22.1%).
- Rough 90% ranges: 2022–2026 line 57–81 treating feeds as independent, 51–87 widened by publisher, 40–98 adding the
  line's own uncertainty; 2024–2026 line 53–77, 48–82 and 31–98.
- Limits: a line through a few yearly points; nothing says the rise will continue, and a share cannot rise for ever.
  The prior/other split is not used here. These figures will be scored with the forecasts above after 2027-04-01.

### How long lapses last (2026-10-22)
`tools/lapse_survival.py` estimates the time from a lapse's first day to the day a valid file exists again with the
Kaplan-Meier method, counting the 28 lapses still open on the census day (2026-10-16) as censored at their length so
far (`data/2026-10-16/lapse_survival.md`).
- All 203 lapses: median 80 days. The 175 ended lapses alone give 56 days, which runs short because it drops the long
  open ones. 67.9% were still lapsed after 30 days, 47.4% after 90, 28.5% after 180 and 13.4% after a year. The
  Transit app says it extends an expired schedule for one month
  (https://resources.transitapp.com/article/458-guidelines-for-producing-gtfs-static-data-for-transit); two thirds of
  these lapses last longer than that.
- The 121 lapses that began on April 1: median 96 days (61 for the ended ones only), 15.2% still lapsed after a year,
  on average 136.9 days without a valid file within the first year (restricted mean). The 82 that began on other days:
  median 60 days, 11.7% after a year, 121.1 days.
- A log-rank test finds no clear difference: April-1 lapses do not end detectably later than the rest (p = 0.39), and
  the 2026 April-1 lapses (median 71 days, 12 still open) do not differ from earlier April-1 lapses (p = 0.52). Lapses
  are not independent, so these p-values are, if anything, too small.
- The ended-only medians by year (2024 111.5, 2025 131, 2026 54 days) match `fy_cliff.md`; the Kaplan-Meier medians
  are 185, 136 and 71 days.
- 2027-04-01 (recorded in advance): each forecast count above times the April-1 restricted mean (136.9 days) gives about
  7,200 (2024–2026 rates by group) to 9,400 (2022–2026 line) feed-days without a valid file in the year from
  2027-04-01. That can be scored only once the year is over (from 2028-04).
- Limits: a network that ended without being marked discontinued looks like a lapse that never ends and lengthens the
  estimate. A lapse also counts as over on the day a later, back-dated file covers. This describes data already seen in
  aggregate; it was not registered in advance.

### When the open lapses end (recorded in advance, 2026-10-22)
`tools/recovery_forecast.py` takes each of the 27 lapses still open on the census day (2026-10-16; one more, on a feed
marked discontinued, is left out) and reads off the Kaplan-Meier curve above, given how long it has lasted so far, the
chance that a valid file exists again within 30 and 90 days (`forecast/recovery/2026-10-16/recovery.md`).
- Within 30 days (last lapsed day 2026-11-15): 1.0 recovery expected (median 1, rough 90% range 0–3).
- Within 90 days (to 2027-01-14): 5.45 expected (median 5, range 2–9).
- The open lapses have lasted 16 to 929 days. The two that began on 2026-10-01 have a 15% chance of ending within 30
  days and 42% within 90; the twelve that began on 2026-04-01, 3% and 26%. Eight of the 27 (564 days or more) have
  already lasted longer than any lapse that ever ended, so they get probability 0; most are probably feeds that
  stopped updating without being marked discontinued.
- Recorded on 2026-10-22 from the 2026-10-16 census only. The 2026-10-22 expiry list above was already public but was
  not used. It will be scored with new censuses around 2026-11-16 and after 2027-01-15, and the results added here:
  `python tools/recovery_forecast.py --lapses <new lapses.csv> --score <new lapses.csv> --as-of <its census day> --forecast-json forecast/recovery/2026-10-16/recovery.json --out out`
- Limits: one publisher's feeds often recover together, so the real range is wider. The tail of the curve rests on few
  lapses and is jumpy (the one open lapse at 381 days gets 14% within 30 days, more than the 3% of the 199-day ones).

### Expiring feeds (expiry_watch.py)
`tools/expiry_watch.py` reads the repository's feed list (one API request) and lists, by days left, every active feed
whose latest file has already ended or ends within 60 days, with the feed's own past lapses (and how many began on
April 1) from this census's `lapses.csv`. The repository already e-mails each publisher 14 days before a file ends;
this list puts the same signal in public for the apps and route planners that read the feeds. Output:
`watch/<date>/expiring.csv`, `watch.md` and `summary.json`. Run: `python tools/expiry_watch.py --out out`
(`--as-of YYYY-MM-DD` for another day).

The list for 2026-10-22 (Japan time): of 580 active feeds, 27 have expired, 1 ends within 7 days, 17 in 8 to 30 days and
10 in 31 to 60 days. 31 of the 55 listed feeds lapsed before, 18 of them on an April 1. The 27 expired feeds probably
include networks that stopped updating without being marked discontinued. The list will be refreshed about weekly.

### Limits
- A lapse means the repository had no valid file, not that buses stopped running.
- Files distributed outside the repository, and old versions no longer in it, are not seen.
- NEW files count from their publication date, UPDATE files from their start date (the strict count dates both from
  publication).
- A network that ended without being marked discontinued can look like an open lapse. Place names in the data are
  records of fact, not judgements.
- The expiry list reads only latest_feed_end_date, so it misses gaps such as a newer file that starts some days after
  the old one ends.

### Files
- `data/2026-10-16/feeds.csv` per feed (with publisher and licence), `versions.csv` every file, `lapses.csv` one row per
  lapse, `years.csv`, `prefectures.csv`, `fy_cliff.csv` (April 1), `repeat_cliff.csv` and `repeat_cliff.md` (repeats),
  `summary.json`, `findings.md`, `lapse_survival.json` and `lapse_survival.md` (how long lapses last)
- `watch/<date>/` expiry lists
- `forecast/2027-04-01/` the forecast by group (`cohort.csv`, `forecast.json`, `forecast.md`), the clustering
  ranges with their back-test (`cluster_band.json`, `cluster_band.md`) and the trend check (`trend_band.json`,
  `trend_band.md`)
- `forecast/recovery/2026-10-16/` the chance that each open lapse ends (`recovery.json`, `recovery.md`, `recovery.csv`)
- `tools/gtfs_lapses.py` (census), `tools/fy_cliff.py` (April 1), `tools/repeat_cliff.py` (repeats),
  `tools/expiry_watch.py` (expiry list), `tools/fy2027_risk.py` (forecast by group and its score),
  `tools/cluster_band.py` (clustering and ranges), `tools/trend_band.py` (trend check),
  `tools/lapse_survival.py` (how long lapses last), `tools/recovery_forecast.py` (open-lapse forecast and its score),
  each with `test_*.py`
- Reproduce: `python tools/gtfs_lapses.py --as-of 2026-10-16 --pause 1.0 --out out` →
  `python tools/fy_cliff.py out/lapses/2026-10-16` → `python tools/repeat_cliff.py out/lapses/2026-10-16`

### Sources and licences
Version histories come from the GTFS Data Repository API (https://gtfs-data.jp/). Each feed's publisher and licence are
in the organization_name and license columns of `feeds.csv`. No timetable data is redistributed here.

Contact: MV2, Munim, Inc., mv2@munimtech.com
