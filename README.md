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
続いている空白はいつ終わるか / When the open lapses end: [forecast/recovery/2026-10-16/recovery.md](forecast/recovery/2026-10-16/recovery.md) ・
祝日・年末年始の扱い / Holidays and the New Year break: [holidays/2026-10-22/holidays.md](holidays/2026-10-22/holidays.md) ・
停留所名のよみがな・英語 / Stop-name readings and English: [names/2026-10-22/names.md](names/2026-10-22/names.md)（再集計 / recount: [verify/recount.md](names/2026-10-22/verify/recount.md)） ・
時刻と停留所位置・表定速度 / Timing, stop positions and bus speeds: [timing/2026-10-22/timing.md](timing/2026-10-22/timing.md) ・
始発と終バス / First and last buses: [lastbus/2026-10-22/lastbus.md](lastbus/2026-10-22/lastbus.md)（停留所ごとの表 / per-place tables: [places/index.csv](lastbus/2026-10-22/places/index.csv)） ・
掲載上の期限とファイル自体の期限 / Listed end date against the file's own dates: [calgap/2026-10-22/calendar_gap.md](calgap/2026-10-22/calendar_gap.md)（後続のファイル / later files: [next.md](calgap/2026-10-22/next/next.md)） ・
公開済みのファイルのつながり / The chain of published files: [chain/2026-10-23/chain.md](chain/2026-10-23/chain.md) ・
データの健康診断 / Data-health table: [health/2026-10-22/health.md](health/2026-10-22/health.md)

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

### 祝日・年末年始の扱い（2026年10月22日、予測は事前登録）
`tools/holiday_check.py` で、有効でオープンライセンスのデータ550件の現行ファイルについて、2026年4月〜2027年3月の祝日（日曜を除く）と
年末年始（12月29日〜1月2日）の各日に走る運行（service_id）を、同じ曜日のふだんの日（祝日・年末年始・お盆を除く最も近い日）と、
近くの日曜・土曜と比べました（`holidays/2026-10-22/holidays.md`）。日曜の運行が平日と違うデータなのに、祝日にふだんの平日（土曜なら土曜）の
運行がそのまま入っているものを「ふだんどおり」と数えます。日本全国のデータについてこの集計をした例は見つかりませんでした
（2026年10月22日に検索。カリフォルニアのデータを調べたCal-ITPの2023年の例や、1件ずつ確かめるツールはあります）。
- 祝日にふだんどおりの運行が入っている割合: 2026年の祝日は8.5〜10.4%（文化の日・11月3日は457件中47件、10.3%）、
  2027年の祝日は13.4〜16.8%（成人の日・1月11日は411件中69件）。
- 年末年始: 12月29日41.6%、30日28.0%、31日16.6%、元日5.7%。12月29日・30日にふだんの平日ダイヤで走る事業者も多いので、
  ここは誤りとは限りません。
- 同じファイルの中でも、先の祝日ほど抜けています。11月3日と2027年1月11日の両方が対象の405件のうち、11月3日は祝日として扱うのに
  1月11日はふだんどおりのものが31件、その逆は1件でした（符号検定 p ≈ 1.5×10⁻⁸）。11月の祝日を2つとも祝日として扱いながら
  1月11日はふだんどおりのデータが30件あり、うち17件は元日を祝日として扱っています。2027年の祝日はまだ入れていないとみられます。
- 11月3日と比べた先の祝日ごとの数（`holidays/2026-10-22/horizon.md`）: 同じ2026年の11月23日は2件対2件で差がなく、2027年の
  2月11日は19件対1件、2月23日は20件対2件、3月22日（振替休日）は22件対2件でした。年が変わる祝日から差が出ます。
- GTFS-JPの標準のservice_id（「平日（月～金）」など）だけのデータは5件です。仕様上、これらは国内の経路検索事業者が祝日を考慮しますが、
  それ以外のデータでは祝日をファイルに書く必要があります。calendar_dates.txt があるのは550件中513件。
- 事前に記録した4つの予測（`holidays/predictions-2026-10-22.md`）はすべて当たりました。P1（11月3日のふだんどおりが5〜30%）は
  10.3%で、幅の広い予測でした。P2（国民の休日・9月22日のふだんどおりが前後の祝日より多い）は30件対28件・26件で、差は小さく
  偶然の範囲です。P3（6つの祝日の扱いがそろうデータが80%以上）は368件中335件（91%）。P4（12月30日が11月3日より15ポイント以上高い）は
  17.7ポイント差でした。
- これからの祝日・年末年始にふだんどおりの運行が入っているデータは236件（`holidays/2026-10-22/upcoming.csv`）。
- 再確認（事前登録）: 2026年12月10日〜28日に同じ調査をもう一度行い、年末年始や2027年の祝日が12月に加わるかを
  `tools/holiday_recheck.py` で比べます。予測3つ（R1〜R3）は `holidays/predictions-recheck-2026-12.md` にあります。
- 限界: 祝日にふだんの平日ダイヤで走る路線もあり、「ふだんどおり」は誤りとは限りません。2027年の祝日の割合は、その日までを含む
  ファイルだけの値です。各データの現行ファイルを10月22日に1回読んだだけで、その後の更新は見ていません。個別の地域名は事実の記録であり、
  評価ではありません。

### 停留所名のよみがな・英語（2026年10月22日、予測は事前登録）
`tools/names_check.py` で、有効でオープンライセンスのデータ553件の現行ファイルについて、停留所（標柱、location_type 0）と行先
（trips.txt の trip_headsign）ごとに、translations.txt によみがな（ja-Hrkt）と英語（en）があるかを数えました（`names/2026-10-22/names.md`）。
GTFS-JP（第4.0版、2026年3月）では translations.txt とよみがなは必須、英語（ローマ字表記）は推奨です。GTFS本来の形式
（table_name・field_name と record_id か field_value）と、以前のGTFS-JPの形式（trans_id・lang・translation）の両方を読みます。
国土交通省は2025年10月の第1回GTFS-JPアップデート検討会の資料（https://www.mlit.go.jp/sogoseisaku/transport/content/001914061.pdf ）で、
全国の公開データについて項目ごとの設定率を示しています。停留所ごとに、よみがな・英語が付いているかを全国のデータで数えた例は
見つかりませんでした（2026年10月22日に検索。仕様・作り方の手引きとチェックツールはあります）。
- 停留所98,776か所のうち、よみがながあるのは97.9%、英語があるのは77.6%。
- 9割以上の停留所によみがなを付けたデータは553件中545件（98.6%）、英語は407件（73.6%）。英語がまったくないデータは124件。
- translations.txt の形式: GTFS本来の形式537件、以前のGTFS-JPの形式10件、空1件、ファイルなし5件。よみがなの付いていない
  データ6件は、この空・なしの6件です。
- よみがなに漢字が入っている停留所22か所。英語の名前にかな・漢字が入っている停留所133か所（英語のある76,662か所の0.2%）、
  うち日本語の名前をそのまま写したもの1か所。自分には訳がなく親の駅（location_type 1）にだけ訳がある標柱が608か所（うち606か所は1件のデータ）。
- 行先5,489種類のうち、よみがながあるのは16.0%、英語は17.1%。第4.0版は行先も訳の対象に挙げていますが、作り方の手引きが
  必ずよみがなを付けるとしているのは停留所名なので、ここは数だけを示し、不備とは扱いません。
- 英語以外では、ローマ字（ja-Latn）21件、韓国語11件、中国語（zh-tw 7、zh-cn 6、zh-hans 3、zh-hant 3、zh 3）などがありました。
  ローマ字（ja-Latn）は上の「英語」に数えていません。
- 都道府県による差が大きいのは英語です（`names/2026-10-22/prefectures.csv`）。よみがなは多くの都道府県でほぼ100%です。
- 事前に記録した4つの予測（`names/predictions-2026-10-22.md`）: N1（よみがなを9割以上に付けたデータが70%以上）は98.6%で当たり。
  N2（英語を9割以上に付けたデータが20〜60%）は73.6%で外れ、英語は予想よりずっと多く付いていました。N3（英語の名前の1%以上に
  かな・漢字）は0.2%で外れ。N4（訳のあるデータの10%以上が以前の形式）は547件中10件（1.8%）で外れました。
- 再集計: names_check.py とは別に書いたコード（`tools/verify_names.py`）で、553件の現行ファイルを調査の約1時間後にもう一度
  ダウンロードして数え直したところ、553件すべてで停留所・よみがな・英語の数が一致しました（UTF-8でないファイル0件、
  translations.txt の形式の読み違い0件。`names/2026-10-22/verify/`）。ローマ字（ja-Latn）も英語と同じように数えると、停留所の80.6%
  （79,607か所）に英語かローマ字があり、9割以上の停留所に付けたデータは416件（うち9件はローマ字があって初めて9割に届く）。
  ローマ字のある21件はすべて高知県のデータで、英語の代わりに ja-Latn でローマ字名を付けているものが多くあります。
  ローマ字の集計は事前登録の予測には含まれていません。
- 限界: 停留所は標柱ごとに数えます。訳があるかだけを見て、よみがなや英語の中身が正しいかは確かめていません（かな・漢字が入って
  いるかだけ）。行先は trip_headsign だけで、stop_headsign は見ていません。各データの現行ファイルは10月22日に読んだもの
  （再集計で2回）だけです。個別の地域名は事実の記録であり、評価ではありません。

### 時刻と停留所位置・バスの表定速度（2026年10月22日、予測は事前登録）
`tools/timing_check.py` で、停留所名の調査と同じ553件の現行ファイルを読み、時刻と停留所の位置の不自然な点を数え、バスの便ごとの
表定速度を求めました（`timing/2026-10-22/timing.md`）。速すぎる区間の基準は MobilityData のバリデーター
（fast_travel_between_consecutive_stops）と同じで、バスは時速150km、1分未満の区間は1分として数えます。表定速度は、停留所間の
直線距離の合計を始発から終着までの時間で割ったものです。全国の公開データについてこれらを数えた例や、GTFSから全国のバスの
表定速度を求めた例は見つかりませんでした（2026年10月22日に検索。1件ずつ評価する GTFS Scorecard などはあります）。
- 553件すべてを読み、便80,048本・区間2,267,151・標柱98,778か所を確かめました。
- 速すぎる区間があるのは4件（0.7%）・19区間で、うち16区間は時刻表上0分の区間です。前の停留所を出る前に着く区間は1件・1区間、
  座標が国外の標柱は1件・2か所（座標なし・0は0か所）、stops.txt にない停留所への参照は0件でした。これらのどれかがあるデータは6件です。
- 名前の違う標柱がまったく同じ座標に重なるデータは20件（3.6%）・645か所。多くは同じ停留所を路線ごとの名前で書いたもので、
  誤りとは限りません。
- バスの表定速度（直線距離）: 76,033便の中央値は時速17.5km（四分位 14.2〜22.0km）、524件のデータごとの中央値の中央値は18.5km。
  都道府県別では東京都11.7km（713便）、神奈川県12.7km、埼玉県13.5kmが遅く、秋田県27.9km（423便）、岩手県27.1km（377便）が
  速めです（`timing/2026-10-22/prefectures.csv`。データの少ない府県は揺れが大きくなります）。
- 事前に記録した6つの予測（`timing/predictions-2026-10-22.md`）のうち4つが当たりました。T1（速すぎる区間のあるデータが5〜30%）は
  0.7%で外れ、日本の公開データは予想よりずっと整っていました（参考: 米国736件を MobilityData のバリデーターで調べた ITS Feed の集計では
  17%。規則が違うので比較の基準ではありません）。T2（前の停留所を出る前に着く区間のあるデータが5%未満）は0.2%、T3（座標のおかしい
  標柱のあるデータが3%未満）は0.2%、T4（表定速度の中央値が時速12〜25km）は17.5km、T5（速すぎる区間の半分以上が1分未満）は84.2%で
  当たり。T6（重なる標柱のあるデータが10%以上）は3.6%で外れました。
- 限界: 直線距離は道のりより短いので、速度は低めに出ます。速すぎる区間が時刻の誤りか位置の誤りかは区別しません。時刻はふつう分単位
  なので、短い区間は粗くなります。各データの現行ファイルを10月22日に1回読んだだけです。flag は確かめるきっかけで、誤りの証明では
  ありません。個別の地域名は事実の記録であり、評価ではありません。

### 始発と終バス（2026年10月22日、予測は事前登録）
`tools/last_bus.py` で、同じ553件の現行ファイルから、ふだんの水曜（2026年11月11日）・土曜（11月14日）・日曜（11月15日）に、
それぞれの停留所（同じデータの中の同じ名前の標柱をまとめたもの）からバスが出る最初と最後の時刻を求めました
（`lastbus/2026-10-22/lastbus.md`、停留所ごとの表は `lastbus/2026-10-22/places/`）。乗車できる発車だけを数え（pickup_type が1でなく、
便の終点でない停留所）、24時を過ぎる時刻はその運行日のまま、frequencies.txt の便も含めます。全国の公開データについて停留所ごとの
終バスを数えた例は見つかりませんでした（2026年10月22日に検索。停留所ごとの時刻表サイトや、路線の減便・廃止を事業者に尋ねた調査は
あります）。
- 553件すべてを読み、3日を含むファイルは527件（22件は有効期間が11月11日より前に終わり、4件は読める有効期間がありませんでした）、
  水曜にバスが出るのは480件です。
- バスが出る停留所: 水曜56,496か所、土曜42,823か所、日曜33,468か所。
- 水曜の終バスの中央値は18時21分（10%が15時38分まで、25%が17時04分まで、75%が19時31分まで、90%が20時50分まで）。
  始発の中央値は7時22分。
- 終バスが18時より前の停留所は41.8%、19時より前は65.5%、20時より前は81.4%、21時より前は91.0%、23時以降は1.1%。
  最後の発車が10時より前（朝だけ）の停留所が1,024か所あります。
- 水曜にバスが出る停留所のうち、日曜にはバスが出ないのが41.2%（23,290か所）、土曜は26.0%（14,673か所）。両日に出る33,206か所の
  うち48.7%は日曜の終バスのほうが早くなっています（差の中央値は0分）。
- 停留所の終バスの中央値が18時より前のデータは480件中215件（44.8%）。停留所が1,000か所以上ある都道府県の中央値は17時22分〜
  19時32分です（`lastbus/2026-10-22/prefectures.csv`）。
- 事前に記録した6つの予測（`lastbus/predictions-2026-10-22.md`）のうち5つが当たりました。L1（終バスの中央値が19〜21時）は18時21分で
  外れ、予想より早く終わっていました。L2（19時より前が25%以上）65.5%、L3（日曜にバスがない停留所が15%以上）41.2%、L4（中央値が
  18時より前のデータが30%以上）44.8%、L5（23時以降が10%未満）1.1%、L6（日曜のほうが早い停留所が40%以上）48.7%で当たりです。
- 終バスが30時45分（翌朝6時45分）の停留所が1か所あります。ファイルのとおりに載せています。
- 停留所ごとの表は、リポジトリのファイルの大きさの上限に収めるため、都道府県ごとの40ファイル（`places/NN.csv`、NN は都道府県コード、
  一覧は `places/index.csv`）に分けました（`tools/split_places.py`）。分ける前に、10月23日に553件の現行ファイルをもう一度読み直し、
  データごとの集計がすべて公開した `feeds.csv` と一致することを確かめています（変わったデータは0件で `places/changed.csv` は空、
  計57,523行。`places/split.json`）。
- 限界: リポジトリにあるのは主に市町村のコミュニティバスと地方の事業者のデータで、他の場所だけで公開している大都市の事業者は含まれて
  いません。これは公開データにある停留所の数字で、全国のすべてのバス停の数字ではありません。停留所は同じデータの中の同じ名前を
  まとめたもので、2つの事業者が止まる停留所はデータごとに数えます。終バスはどの方向の便でもよく、「帰りの最終」ではありません。
  デマンド交通の便もファイルにあれば同じように数えます。時刻表だけを見ており、実際の運行や遅れは見ていません。各データの現行
  ファイルを10月22日に1回読んだだけです。個別の地域名は事実の記録であり、評価ではありません。
- 2027年4月のダイヤ改正のあとに同じ方法で数え直し、停留所ごとの終バスの繰り上げ・繰り下げを比べる予定です（予測はその前に記録します）。

### 掲載上の期限とファイル自体の期限（2026年10月22日・23日）
`tools/calendar_gap.py` で、リポジトリが各データについて示す期限（掲載上の期限。期限一覧と同じ latest_feed_end_date）と、10月22日に
読んだ現行ファイルの calendar.txt・calendar_dates.txt が実際に含む最後の運行日を、新しいダウンロードなしで比べました
（`calgap/2026-10-22/`）。そのあと `tools/calendar_next.py` で、ファイルのほうが早く終わる21件それぞれについて10月23日にAPIを1回読み、
後続のファイルがすでに公開されていて残りの日をつないでいるかを確かめました（`calgap/2026-10-22/next/`）。
- 553件のうち、期限が同じ506件、ファイルのほうが早く終わる21件、遅く終わる17件、ファイルの日付が読めない4件、掲載上の期限がない5件。
- 早く終わる21件のうち8件は、まだ有効になっていない次の版がすでに公開されていて、残りの日をすき間なくつないでいます。掲載上の期限は
  リポジトリにある最新の版の期限で、いま有効な版の期限ではないためです。現行ファイルだけと比べると空白を大きく見積もります。
  最初の集計で「隠れた期限切れ」（掲載上の期限は60日より先なのに、ファイルは60日以内に終わる）とした6件のうち5件はこれにあたるため、
  この区分は結果として公開していません。
- 後続のファイルがないのは13件です。1つの市の10路線は、現行ファイルのメモに「R8.10.1よりデマンド化に伴い、路線廃止」とあり、
  ファイルの運行日は2026年9月30日で終わっていますが、リポジトリでは運行終了の印がなく、10月31日まで有効と掲載されています。
  1件は観光路線で、運行日は11月30日までですがファイルの有効期間は2027年3月31日まで（季節運行とみられます）。残る2件の差は9日と3日です。
- 現行ファイルのメモに廃止・休止・運休などの語があるのは21件のうち12件で、上の10路線と、一部の路線・便の運休を書いた2件
  （どちらも後続のファイルあり。データ全体の終了ではありません）です。21件のうち運行終了の印が付いたものは0件でした。
- 限界: 後続のファイルは、リポジトリが示す有効期間（from_date・to_date）だけで見ており、その中の運行日は読んでいません。APIは10月23日に
  1回読んだだけです。ファイルに運行日のない日があっても、バスが走らないとは限りません（季節運行や、別のデータで公開された運行）。
  事前登録の予測はない記述的な集計です。個別の地域名は事実の記録であり、評価ではありません。

### 公開済みのファイルのつながり（2026年10月23日、予測は事前登録）
`tools/file_chain.py` で、一覧にある有効なデータ580件のうち期限の切れていない553件それぞれについて、10月23日にAPIを1回読み、
いま有効なファイルがいつ終わるか、次のファイルがいつ始まり何日前に公開されたか、今日から掲載上の期限まで公開済みのファイルが
すき間なくつながっているかを確かめました（`chain/2026-10-23/`）。時刻表ファイルはダウンロードせず、リポジトリが示す各ファイルの
有効期間と公開日時だけを使います。期限の一覧が見ている掲載上の期限は最新の版の期限なので、途中のすき間はこの確認でしか見えません。
- 553件すべてを読めました（API失敗0件）。途中にすき間のあるデータ、今日有効なファイルのないデータ、一覧の期限とファイルの期限が
  合わないデータはいずれも0件で、553件すべてが掲載上の期限までつながっていました。期限切れの27件は読んでいません。
- 後続のファイルがすでに公開されているのは20件（3.6%）。いま有効なファイルが60日以内に終わる33件のうち、後続のファイルがつないで
  いるのは7件（21.2%）で、うち6件は掲載上の期限が60日より先です。残る26件は、この日には後続のファイルがありませんでした。
- 後続のファイルの公開から開始までの日数: 中央値18日（四分位10〜28日、範囲4〜113日）。20件のうち7日未満は1件、14日未満は9件。
- 後続のファイルがないまま10月31日までに終わる17件のうち10件は、前の節の1つの市の10路線（メモに10月1日に廃止とある）です。
  残る7件について、2026年11月1日以降に最初にAPIを読んだ日に有効なファイルがないのは4件以上と予測しました（事前登録、
  `chain/predictions-2026-11-01.md`）。結果はここに追記します。
- 事前に記録した4つの予測（`chain/predictions-2026-10-23.md`）のうち3つが当たりました。C1（すき間のあるデータが2%未満）は0.0%、
  C3（60日以内に終わるデータのうち後続がつなぐのが10〜40%）は21.2%、C4（日数の中央値が14日以上）は18日で当たり。
  C2（後続のファイルが公開済みのデータが5〜30%）は3.6%で外れ、先の版を前もって公開しているデータは予想より少数でした。
- 注意: ある1日に見える「まだ有効でないファイル」は、早く公開されたものほど長く見えるので、この日数は長めに出ます。開始日より後に
  公開されたファイルはそもそも見えません。典型的な日数は、全版の履歴から数える必要があります。
- 限界: ファイルの中の運行日は読んでいません（`calgap/2026-10-22/`）。そのため、10月1日に廃止された10路線も、ファイルの上では
  10月31日までつながって見えます。リポジトリから消えた古い版は見えません。APIは10月23日に1回読んだだけです。すき間がないことは、
  バスが走ることの証明ではありません。個別の地域名は事実の記録であり、評価ではありません。

### データの健康診断（2026年10月22日、予測は事前登録）
`tools/data_health.py` で、ここまでの4つの集計（10月22日の期限一覧、10月16日の空白の調査、祝日、停留所名）を、新しいダウンロードを
せずにデータごとに1行にまとめました（`health/2026-10-22/`）。対象は、祝日か停留所名の調査で現行ファイルを読んだ有効でオープンライセンスの
553件です。各データに4つの確認を ok・flag・n/a で付けます: 期限（期限切れか60日以内に切れる）、祝日（これからの祝日・年末年始の
どこか1日にふだんどおりの運行）、よみがな（9割未満の停留所にしかない）、英語（同じく9割未満。英語は推奨のみ）。
- 期限 flag 28件、祝日 flag 236件（対象485件中。対象外68件）、よみがな flag 8件、英語 flag 146件。
- 必須の3つ（期限・祝日・よみがな）のどれかに flag があるデータは553件中267件（48.3%）。2つに flag があるのは5件だけで、
  3つすべてのデータはありません。4つの確認がすべて ok のデータは168件です。都道府県ごとの数は `health/2026-10-22/prefectures.csv`。
- 表を作る前に記録した2つの予測（`tools/data_health.py` の PREDICTIONS）はどちらも外れました。
  D1（過去に空白のあったデータは祝日の flag が多い）: 115件中55件（47.8%）対 364件中178件（48.9%）、片側フィッシャー正確検定 p = 0.62。
  D2（英語が flag のデータは祝日の flag が多い）: 132件中59件（44.7%）対 353件中177件（50.1%）、p = 0.88。
  期限の更新が遅れたことのあるデータや英語を付けていないデータほど祝日の扱いが抜けている、とは言えません。
  こうした抜けは、データごとにばらばらに起きているように見えます。
- 予測ではない参考: 過去に空白のあったデータ126件のうち期限 flag は4件（3.2%）、空白のなかったデータは421件中23件（5.5%）。
- 期限一覧のうち期限切れの27件は、有効な現行ファイルがないため祝日・停留所名の調査で読んでおらず、この表には入っていません。
- 限界: 各集計はそれぞれの日に読んだもの（空白の調査は10月16日、その他は10月22日）で、その後の更新は見ていません。祝日の flag には、
  12月29日・30日のように本当にふだんの平日ダイヤで走る日も含まれます。flag は確かめるきっかけで、誤りの証明ではありません。
  個別の地域名は事実の記録であり、評価ではありません。

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
- 掲載上の期限は、まだ有効になっていない後続の版の期限であることがあります。また、路線が終わったあとも、ファイルが有効のまま
  掲載されていることがあります（`calgap/2026-10-22/`）。
- ある1日に見える後続のファイルの公開日数は、早く公開されたものほど見えやすいため長めに出ます（`chain/2026-10-23/`）。

### ファイル
- `data/2026-10-16/feeds.csv` データごとの集計（提供者・ライセンス付き）、`versions.csv` 全版、`lapses.csv` 空白1回ごと、
  `years.csv`、`prefectures.csv`、`fy_cliff.csv`（4月1日の集計）、`repeat_cliff.csv`・`repeat_cliff.md`（再発）、`summary.json`、`findings.md`、
  `lapse_survival.json`・`lapse_survival.md`（空白の続く日数）
- `watch/<日付>/` 期限の一覧
- `forecast/2027-04-01/` グループ別の予測（`cohort.csv`・`forecast.json`・`forecast.md`）、まとまりを考えた幅と過去の検証
  （`cluster_band.json`・`cluster_band.md`）、割合の伸びを入れた予測（`trend_band.json`・`trend_band.md`）
- `forecast/recovery/2026-10-16/` 続いている空白が終わる確率（`recovery.json`・`recovery.md`・`recovery.csv`）
- `holidays/2026-10-22/` 祝日・年末年始の扱い（`feeds.csv` データと日ごとの分類、`dates.csv` 日ごとの集計、`upcoming.csv`、
  `skipped.csv`、`summary.json`、`holidays.md`、先の祝日の比較 `horizon.json`・`horizon.md`）、
  `holidays/predictions-2026-10-22.md`・`holidays/predictions-recheck-2026-12.md`（事前登録）
- `names/2026-10-22/` 停留所名のよみがな・英語（`feeds.csv`、`prefectures.csv`、`skipped.csv`、`summary.json`、`names.md`、
  再集計 `verify/` の `recount.csv`・`recount.md`・`summary.json`）、`names/predictions-2026-10-22.md`（事前登録）
- `timing/2026-10-22/` 時刻と停留所位置・表定速度（`feeds.csv`、`prefectures.csv`、`fast_steps.csv` 速すぎる区間、`time_travel.csv`、
  `stacks.csv` 重なる標柱、`summary.json`、`timing.md`）、`timing/predictions-2026-10-22.md`（事前登録）
- `lastbus/2026-10-22/` 始発と終バス（`feeds.csv`、`prefectures.csv`、`places/` 停留所ごとの水・土・日の始発と終バス（都道府県ごとの
  `NN.csv`、一覧 `index.csv`、読み直しで変わったデータ `changed.csv`、`split.json`）、`summary.json`、`lastbus.md`）、
  `lastbus/predictions-2026-10-22.md`（事前登録）
- `calgap/2026-10-22/` 掲載上の期限とファイル自体の期限（`feeds.csv`、`summary.json`、`calendar_gap.md`、後続のファイルの確認 `next/` の
  `feeds.csv`・`summary.json`・`next.md`）
- `chain/2026-10-23/` 公開済みのファイルのつながり（`chain.csv` データごと、`summary.json`、`chain.md`）、
  `chain/predictions-2026-10-23.md`・`chain/predictions-2026-11-01.md`（事前登録）
- `health/2026-10-22/` データの健康診断（`feeds.csv` データごとの4つの確認、`prefectures.csv`、`summary.json`、`health.md`）
- `tools/gtfs_lapses.py`（集計）、`tools/fy_cliff.py`（4月1日）、`tools/repeat_cliff.py`（再発）、`tools/expiry_watch.py`（期限の一覧）、
  `tools/fy2027_risk.py`（グループ別の予測と採点）、`tools/cluster_band.py`（まとまりと幅）、`tools/trend_band.py`（割合の伸び）、
  `tools/lapse_survival.py`（空白の続く日数）、`tools/recovery_forecast.py`（続いている空白の予測と採点）、
  `tools/holiday_check.py`（祝日・年末年始）、`tools/holiday_recheck.py`（先の祝日の抜けと12月の再確認）、
  `tools/names_check.py`（停留所名）、`tools/verify_names.py`（停留所名の再集計）、`tools/timing_check.py`（時刻と位置）、
  `tools/last_bus.py`（始発と終バス）、`tools/split_places.py`（停留所ごとの表を都道府県ごとに分ける）、
  `tools/calendar_gap.py`（掲載上の期限とファイルの期限）、`tools/calendar_next.py`（後続のファイル）、
  `tools/file_chain.py`（公開済みのファイルのつながり）、`tools/data_health.py`（健康診断）、
  各 `test_*.py`
- 再現: `python tools/gtfs_lapses.py --as-of 2026-10-16 --pause 1.0 --out out` → `python tools/fy_cliff.py out/lapses/2026-10-16`
  → `python tools/repeat_cliff.py out/lapses/2026-10-16`。祝日: `python tools/holiday_check.py --as-of 2026-10-22 --out out`
  （その日の現行ファイルを読みます）→ `python tools/holiday_recheck.py --before holidays/2026-10-22/feeds.csv --out out`。
  停留所名: `python tools/names_check.py --as-of 2026-10-22 --out out` → `python tools/verify_names.py --feeds names/2026-10-22/feeds.csv --out out/verify`。
  時刻と位置: `python tools/timing_check.py --feeds names/2026-10-22/feeds.csv --pause 1.0 --out out`。
  始発と終バス: `python tools/last_bus.py --feeds names/2026-10-22/feeds.csv --pause 1.0 --out out`（どちらもその日の現行ファイルを読みます）
  → `python tools/split_places.py --places out/lastbus/2026-10-22/places.csv --rerun-feeds out/lastbus/2026-10-22/feeds.csv --published-feeds lastbus/2026-10-22/feeds.csv --out out/places`。
  掲載上の期限: `python tools/calendar_gap.py --health health/2026-10-22/feeds.csv --lastbus lastbus/2026-10-22/feeds.csv --as-of 2026-10-22 --out out/calgap`
  → `python tools/calendar_next.py --gaps out/calgap/feeds.csv --out out/calgap/next`（APIをその日に読みます）。
  ファイルのつながり: `python tools/file_chain.py --pause 1.0 --out out/chain`（APIをその日に読みます）。
  健康診断: `python tools/data_health.py --lapses data/2026-10-16/feeds.csv --watch watch/2026-10-22/expiring.csv --holidays holidays/2026-10-22/feeds.csv --names names/2026-10-22/feeds.csv --as-of 2026-10-22 --out out/health`

### 出典とライセンス
版履歴と時刻表ファイルはGTFSデータリポジトリ（https://gtfs-data.jp/ ）のAPIから取得しました。各データの提供者とライセンスは `feeds.csv` の
organization_name・license 列のとおりです。時刻表データそのものはここに含めていません。停留所ごとの表（`lastbus/2026-10-22/places/`、
`timing/2026-10-22/` の各表）は、各データから求めた停留所名・位置・時刻で、出典は各データの提供者です。

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

### Holidays and the New Year break (2026-10-22, predictions recorded in advance)
`tools/holiday_check.py` read the current file of each of 550 active, openly licensed feeds and compared the services
(service_ids) running on each national holiday from April 2026 to March 2027 (Sundays left out) and on each New Year
day (2026-12-29 to 2027-01-02) with the nearest ordinary day of the same weekday (not a holiday, New Year or Obon day)
and with the nearest Sunday and Saturday (`holidays/2026-10-22/holidays.md`). A file counts as showing the "ordinary"
timetable on a holiday when it runs its ordinary weekday (or Saturday) services that day although its Sunday services
differ. We found no earlier census of this across Japan's feeds (searched 2026-10-22; Cal-ITP studied California's
feeds in 2023, and there are tools that check one feed at a time).
- Share of applicable feeds showing the ordinary timetable: 8.5–10.4% on the 2026 holidays (Culture Day, 2026-11-03:
  47 of 457, 10.3%) and 13.4–16.8% on the 2027 ones (Coming of Age Day, 2027-01-11: 69 of 411).
- New Year break: 41.6% on 12-29, 28.0% on 12-30, 16.6% on 12-31, 5.7% on New Year's Day. Many operators really do
  run their weekday timetable on 12-29 and 12-30, so these days are not necessarily mistakes.
- Within one file, later holidays are left out more often. Of the 405 feeds applicable on both 2026-11-03 and
  2027-01-11, 31 handle 11-03 as a holiday but show the ordinary timetable on 01-11; 1 does the reverse (exact sign test
  p ≈ 1.5e-8). 30 feeds handle both November holidays but show the ordinary timetable on 2027-01-11, and 17 of those
  handle New Year's Day itself. The 2027 holidays have most likely not been entered yet.
- Against 2026-11-03, holiday by holiday (`holidays/2026-10-22/horizon.md`): 2026-11-23, in the same year, is 2 against 2
  (no difference); 2027-02-11 is 19 against 1, 2027-02-23 is 20 against 2 and 2027-03-22 (a substitute holiday) is
  22 against 2. The gap opens at the turn of the year.
- Only 5 files use nothing but GTFS-JP's standard service_ids (平日（月～金） …), for which the spec says domestic
  route-search providers apply the holidays themselves; every other file has to carry the holidays itself. 513 of the
  550 files have a calendar_dates.txt.
- All four predictions recorded before the run (`holidays/predictions-2026-10-22.md`) held. P1 (5–30% ordinary on
  2026-11-03) came out at 10.3%; it was a wide range. P2 (more ordinary on 2026-09-22, the day between two holidays,
  than on the holidays either side) held at 30 against 28 and 26, a gap well within chance. P3 (at least 80% of feeds
  treat all six upcoming weekday holidays alike) held at 335 of 368 (91%). P4 (12-30 at least 15 points above 11-03)
  held at 17.7 points.
- 236 feeds show the ordinary timetable on at least one holiday or New Year day still to come
  (`holidays/2026-10-22/upcoming.csv`).
- Re-check (recorded in advance): the same census will be run again between 2026-12-10 and 2026-12-28 and compared with
  this one by `tools/holiday_recheck.py`, to see whether the New Year break and the 2027 holidays are added in December.
  Its three predictions (R1–R3) are in `holidays/predictions-recheck-2026-12.md`.
- Limits: some routes really do run their weekday timetable on holidays, so "ordinary" is not always a mistake. The
  2027 shares cover only the files that reach those days. Each feed's current file was read once, on 2026-10-22; later
  files are not seen. Place names in the data are records of fact, not judgements.

### Stop-name readings and English (2026-10-22, predictions recorded in advance)
`tools/names_check.py` read the current file of each of 553 active, openly licensed feeds and checked, for every stop
(pole, location_type 0) and every destination text (trip_headsign in trips.txt), whether translations.txt gives a kana
reading (ja-Hrkt) and an English name (en) (`names/2026-10-22/names.md`). GTFS-JP (v4.0, March 2026) makes
translations.txt and the reading required and English (romanised) recommended. Both formats in use are read: GTFS's own
(table_name, field_name and record_id or field_value) and the older GTFS-JP one (trans_id, lang, translation). Japan's
transport ministry (MLIT) showed national setting rates per field for published feeds at its first GTFS-JP update
meeting in October 2025 (https://www.mlit.go.jp/sogoseisaku/transport/content/001914061.pdf). We found no earlier
stop-by-stop count of readings and English across Japan's feeds (searched 2026-10-22; there are specs, how-to guides
and checking tools).
- Of 98,776 stops, 97.9% have a reading and 77.6% an English name.
- 545 of the 553 feeds (98.6%) give a reading for at least 90% of their stops; 407 (73.6%) give English. 124 feeds
  give no English at all.
- translations.txt format: GTFS's own 537, older GTFS-JP 10, empty 1, missing 5. The 6 feeds with no readings are
  exactly these empty and missing ones.
- 22 stops have kanji in their reading. 133 stops have kana or kanji in their English name (0.2% of the 76,662 with
  English), 1 of them a straight copy of the Japanese name. 608 poles have no translation of their own while their
  parent station (location_type 1) has one (606 of them in one file).
- Of 5,489 destination texts, 16.0% have a reading and 17.1% English. v4.0 lists destinations among the names to
  translate, but the how-to guides make the reading a must only for stop names, so this is reported as a count, not as
  a defect.
- Other languages: romanised Japanese (ja-Latn) in 21 feeds, Korean in 11, Chinese (zh-tw 7, zh-cn 6, zh-hans 3,
  zh-hant 3, zh 3) and others. ja-Latn is not counted as English above.
- English varies most by prefecture (`names/2026-10-22/prefectures.csv`); readings are close to 100% in most.
- The four predictions recorded before the run (`names/predictions-2026-10-22.md`): N1 (at least 70% of feeds give
  readings for at least 90% of stops) held at 98.6%. N2 (20–60% of feeds give English for at least 90% of stops) did
  not hold: 73.6%, so English is far more common than we expected. N3 (at least 1% of English names contain kana or
  kanji) did not hold at 0.2%. N4 (at least 10% of feeds with rows use the older format) did not hold: 10 of 547 (1.8%).
- Recount: code written separately from names_check.py (`tools/verify_names.py`) downloaded the current file of all
  553 feeds again within about an hour of the census and got the same stop, reading and English counts for every one
  of them (553 of 553 match; no file that is not valid UTF-8; no translations.txt format read differently;
  `names/2026-10-22/verify/`). Counting romanised names (ja-Latn) alongside English, 80.6% of stops (79,607) have one
  or the other, and 416 feeds give one for at least 90% of their stops, 9 of them only thanks to ja-Latn. All 21 feeds
  with ja-Latn are in Kochi Prefecture, and many of them give romanised names as ja-Latn instead of en. The ja-Latn
  counts were not among the predictions recorded in advance.
- Limits: stops are counted per pole. Only whether a translation exists is checked, not whether the reading or English
  is right (apart from kana or kanji in it). Destinations are trip_headsign only, not stop_headsign. Each feed's
  current file was read on 2026-10-22 only (twice, counting the recount). Place names in the data are records of fact,
  not judgements.

### Timing, stop positions and scheduled bus speeds (2026-10-22, predictions recorded in advance)
`tools/timing_check.py` read the current file of the same 553 feeds as the stop-name census, counted timing and
stop-position oddities, and gave each bus trip its scheduled speed (`timing/2026-10-22/timing.md`). A step is too fast
under the limits of MobilityData's validator check fast_travel_between_consecutive_stops (bus 150 km/h; a step under one
minute counts as one minute). The scheduled speed is the sum of the straight-line distances between a trip's stops
divided by the time from its first to its last stop. We found no earlier all-Japan count of these checks and no
all-Japan figure for scheduled bus speeds (表定速度) from GTFS (searched 2026-10-22; GTFS Scorecard grades feeds one by one).
- All 553 files were read: 80,048 trips, 2,267,151 steps and 98,778 poles.
- 4 files (0.7%) have a too-fast step, 19 steps in all, 16 of them scheduled at 0 minutes. 1 file has a step that
  arrives before the trip left the stop before (1 step); 1 file has 2 poles outside Japan (none missing or at zero); no
  file points to a stop missing from stops.txt. 6 files have at least one of these.
- 20 files (3.6%) have stacks of differently named poles at exactly the same coordinates, 645 poles in all. Many are one
  physical stop named once per route, which is not necessarily a mistake.
- Scheduled bus speed (straight line): median 17.5 km/h over 76,033 bus trips (quartiles 14.2 and 22.0); the median of
  the 524 feeds' medians is 18.5 km/h. By prefecture, Tokyo (11.7 km/h, 713 trips), Kanagawa (12.7) and Saitama (13.5)
  are slowest, and Akita (27.9, 423 trips) and Iwate (27.1, 377 trips) among the fastest
  (`timing/2026-10-22/prefectures.csv`; prefectures with few feeds are noisy).
- Four of the six predictions recorded before the run (`timing/predictions-2026-10-22.md`) held. T1 (5–30% of files
  with a too-fast step) did not: 0.7%, so Japan's published files are much cleaner on this check than we expected (for
  context, an ITS Feed census of 736 US feeds with MobilityData's validator found 17%; the rules differ, so it is not a
  benchmark). T2 (under 5% with a step arriving before the previous departure) held at 0.2%, T3 (under 3% with a bad
  pole position) at 0.2%, T4 (median bus speed 12–25 km/h) at 17.5 km/h and T5 (at least half of too-fast steps under
  one minute) at 84.2%. T6 (at least 10% of files with a stack) did not hold: 3.6%.
- Limits: straight lines are shorter than roads, so speeds run low. A too-fast step can come from a wrong time or a wrong
  position; the census does not say which. Times are mostly given to the minute, so short steps are coarse. Each feed's
  current file was read once, on 2026-10-22. A flag is a sign to check, not proof of a mistake. Place names in the data
  are records of fact, not judgements.

### First and last buses (2026-10-22, predictions recorded in advance)
`tools/last_bus.py` read the current file of the same 553 feeds and found, for an ordinary Wednesday (2026-11-11),
Saturday (2026-11-14) and Sunday (2026-11-15), the first and last scheduled bus departure at every place (a stop name
within one feed) (`lastbus/2026-10-22/lastbus.md`; one row per place in `lastbus/2026-10-22/places/`). Only
departures where riders may board count (pickup_type not 1, and not a trip's last stop); times past 24:00 stay on their
service day; frequencies.txt trips are included. We found no earlier all-Japan, stop-by-stop count of last buses from
the published feeds (searched 2026-10-22; there are per-stop timetable sites and operator surveys of route cuts).
- All 553 files were read. 527 cover the three days (22 end before 2026-11-11 and 4 gave no date range we could read);
  480 have a bus departure on the Wednesday.
- Places with a bus departure: 56,496 on the Wednesday, 42,823 on the Saturday, 33,468 on the Sunday.
- Weekday last departure: median 18:21 (10% of places by 15:38, 25% by 17:04, 75% by 19:31, 90% by 20:50). Median
  first departure 7:22.
- The last weekday bus leaves before 18:00 at 41.8% of places, before 19:00 at 65.5%, before 20:00 at 81.4% and before
  21:00 at 91.0%; 1.1% have one at 23:00 or later. 1,024 places have their last departure before 10:00 (morning only).
- Of the places with a weekday bus, 41.2% (23,290) have no bus on the Sunday and 26.0% (14,673) none on the Saturday. Of
  the 33,206 places served on both the Wednesday and the Sunday, 48.7% have an earlier last bus on the Sunday (median
  difference 0 minutes).
- 215 of the 480 feeds (44.8%) have a median last weekday departure before 18:00. Among prefectures with at least 1,000
  places, the median last departure ranges from 17:22 to 19:32 (`lastbus/2026-10-22/prefectures.csv`).
- Five of the six predictions recorded before the run (`lastbus/predictions-2026-10-22.md`) held. L1 (median last
  departure 19:00–21:00) did not: 18:21, so the buses in these files stop earlier than we expected. L2 (at least 25%
  before 19:00) held at 65.5%, L3 (at least 15% with no Sunday bus) at 41.2%, L4 (at least 30% of feeds with a median
  before 18:00) at 44.8%, L5 (under 10% at 23:00 or later) at 1.1% and L6 (at least 40% with an earlier Sunday last bus)
  at 48.7%.
- One place has a last departure at 30:45 (6:45 the next morning); it is listed as the file gives it.
- The per-place table is split into 40 files, one per prefecture (`places/NN.csv`, NN = prefecture code;
  `places/index.csv` lists them), to stay under the repository's file-size limit (`tools/split_places.py`). Before the
  split, all 553 current files were read again on 2026-10-23, and every feed's row matched the published `feeds.csv`
  (0 feeds changed, so `places/changed.csv` is empty; 57,523 rows in all; `places/split.json`).
- Limits: the repository holds mostly municipal community buses and regional operators; large city operators that
  publish only elsewhere are not included. These are figures for the places in the published files, not for every bus
  stop in Japan. A place is a stop name within one feed, so a stop served by two operators appears once per feed. The
  last departure can be in any direction, so it is the latest time a bus leaves, not the last bus home.
  Demand-responsive trips in the files count like any other. Timetables only, not real-time running. Each feed's
  current file was read once, on 2026-10-22 (and once more on 2026-10-23 to check the per-place table). Place names in
  the data are records of fact, not judgements.
- After the April 2027 timetable changes the same census will be run again to compare each place's last bus (earlier or
  later); predictions will be recorded before that run.

### Listed end date against the file's own dates (2026-10-22 and 10-23)
`tools/calendar_gap.py` compares, with no new downloads, the end date the repository lists for each feed
(latest_feed_end_date, the date the expiry list uses) with the last service day in calendar.txt and calendar_dates.txt
of the current file read on 2026-10-22 (`calgap/2026-10-22/`). `tools/calendar_next.py` then read the API once, on
2026-10-23, for each of the 21 feeds whose file ends earlier, to see whether a later file is already published and
covers the remaining days (`calgap/2026-10-22/next/`).
- Of 553 feeds: same end 506; the file ends earlier 21; the file ends later 17; no readable file dates 4; no listed
  date 5.
- 8 of the 21 already have the next version published, not yet in force, and it covers the remaining days with no
  break. The listed date is the end of the latest file the repository holds, not of the file in force, so comparing
  with the current file alone overstates gaps. A first pass called 6 feeds "hidden" expiries (listed date more than 60
  days away, file ending within 60); 5 of them are of this kind, so that class was not published as a result.
- 13 have no later file. Ten routes of one city: the current file's note reads "R8.10.1よりデマンド化に伴い、路線廃止"
  (route abolished from 2026-10-01 with the switch to demand-responsive service), and the file's service days end on
  2026-09-30, yet the repository does not mark them discontinued and lists them as valid to 2026-10-31. One is a
  sightseeing network whose service days end on 2026-11-30 in a file valid to 2027-03-31 (most likely seasonal). The
  other two differ by 9 and 3 days.
- 12 of the 21 have a current-file note with a word such as 廃止, 休止 or 運休 (abolished, suspended): the 10 routes
  above, and 2 notes about some routes or trips being suspended (both have a later file; neither is the end of the whole
  feed). None of the 21 is marked discontinued.
- Limits: later files are judged by the validity dates the repository gives (from_date, to_date) only; their own
  service days were not read. The API was read once, on 2026-10-23. A day with no service in a file does not prove that
  no bus runs (seasonal routes, or service published in another feed). Descriptive, with no predictions recorded in
  advance. Place names in the data are records of fact, not judgements.

### The chain of published files (2026-10-23, predictions recorded in advance)
`tools/file_chain.py` read the API entry of each of the 553 feeds among the 580 active ones whose listed end date had
not passed, once, on 2026-10-23, and found when the file in force today ends, when the next file starts and how many
days ahead it was published, and whether the published files run without a break from today to the listed end date
(`chain/2026-10-23/`). No timetable file is downloaded; only the validity dates and publication times the repository
gives for each file are used. The expiry list reads only the listed end date, the end of the latest file held, so a
break between files can be seen only this way.
- All 553 were read (no API failures). None has a break, none has no file in force today and none has a listed end date
  that the files do not reach: all 553 chains run unbroken to the listed end. The 27 expired feeds were not read.
- 20 feeds (3.6%) already have a later file published. Of the 33 whose file in force ends within 60 days, 7 (21.2%)
  are continued by a later file, 6 of them with a listed end more than 60 days away; the other 26 had no later file
  that day.
- Lead time of the next file (start date minus publication date in Japan time): median 18 days (quartiles 10 and 28,
  range 4 to 113). Of the 20, 1 was published under 7 days ahead and 9 under 14 days ahead.
- 17 feeds end by 2026-10-31 with no later file; 10 of them are the ten routes of one city in the section above (their
  note says they ended on 2026-10-01). For the other 7 we predicted, before their end dates, that at least 4 will have
  no file in force on the first day on or after 2026-11-01 on which the API is read (`chain/predictions-2026-11-01.md`).
  The result will be added here.
- Three of the four predictions recorded before the run (`chain/predictions-2026-10-23.md`) held. C1 (under 2% with a
  break) held at 0.0%, C3 (10–40% of feeds ending within 60 days continued by a later file) at 21.2% and C4 (median
  lead at least 14 days) at 18 days. C2 (5–30% with a later file published) did not hold: 3.6%, so far fewer feeds
  publish their next version ahead of time than we expected.
- Caution: a file not yet in force stays visible on more days the earlier it is published, so a one-day snapshot like
  this overstates lead times, and files published after their start date are never seen in it. Typical lead times have
  to be counted over the whole version history.
- Limits: the files' own service days are not read (`calgap/2026-10-22/`), so the ten routes that ended on 2026-10-01
  still look continuous to 2026-10-31 here. Old files no longer in the API are not seen. The API was read once, on
  2026-10-23. An unbroken chain of files is not proof that buses run. Place names in the data are records of fact, not
  judgements.

### Data-health table (2026-10-22, predictions recorded in advance)
`tools/data_health.py` joins the four censuses above (the 2026-10-22 expiry list, the 2026-10-16 lapse census, holidays
and stop names) into one row per feed, with no new downloads (`health/2026-10-22/`). It covers the 553 active, openly
licensed feeds whose current file the holiday or stop-name census read. Each feed gets four checks, each ok, flag or
n/a: expiry (expired or ending within 60 days), holidays (the ordinary timetable on at least one holiday or New Year day
still to come), readings (a kana reading for under 90% of its stops) and English (an English name for under 90% of its
stops; English is only recommended).
- Expiry flag 28 feeds, holidays flag 236 (of 485 applicable; 68 n/a), readings flag 8, English flag 146.
- 267 of the 553 feeds (48.3%) have at least one flag among the three required checks (expiry, holidays, readings).
  Only 5 have two, and none has all three. 168 feeds are ok on all four checks. Counts by prefecture are in
  `health/2026-10-22/prefectures.csv`.
- Both predictions fixed before the table was first made (PREDICTIONS in `tools/data_health.py`) did not hold.
  D1 (feeds with a past lapse get a holiday flag more often): 55 of 115 (47.8%) against 178 of 364 (48.9%), one-sided
  Fisher exact p = 0.62. D2 (feeds flagged on English get a holiday flag more often): 59 of 132 (44.7%) against 177 of
  353 (50.1%), p = 0.88. Feeds that have lapsed before, or that give no English, are no more likely to leave holidays
  out. These gaps seem to arise feed by feed, not as one "careless publisher" trait.
- Not a prediction: 4 of the 126 feeds with a past lapse (3.2%) are on the expiry list, against 23 of 421 (5.5%)
  without one.
- The 27 expired feeds on the expiry list have no valid current file, so the file censuses did not read them and they
  are not in this table.
- Limits: each census was read on its own day (lapses 2026-10-16, the rest 2026-10-22) and later files are not seen. The
  holiday flag includes days such as 12-29 and 12-30 on which many routes really do run their weekday timetable. A flag
  is a sign to check, not proof of a mistake. Place names in the data are records of fact, not judgements.

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
- The listed end date can belong to a later file that is not in force yet, and a file can stay listed as valid after
  its routes have ended (`calgap/2026-10-22/`).
- Lead times of the later files seen on one day run long, because files published early are visible for longer
  (`chain/2026-10-23/`).

### Files
- `data/2026-10-16/feeds.csv` per feed (with publisher and licence), `versions.csv` every file, `lapses.csv` one row per
  lapse, `years.csv`, `prefectures.csv`, `fy_cliff.csv` (April 1), `repeat_cliff.csv` and `repeat_cliff.md` (repeats),
  `summary.json`, `findings.md`, `lapse_survival.json` and `lapse_survival.md` (how long lapses last)
- `watch/<date>/` expiry lists
- `forecast/2027-04-01/` the forecast by group (`cohort.csv`, `forecast.json`, `forecast.md`), the clustering
  ranges with their back-test (`cluster_band.json`, `cluster_band.md`) and the trend check (`trend_band.json`,
  `trend_band.md`)
- `forecast/recovery/2026-10-16/` the chance that each open lapse ends (`recovery.json`, `recovery.md`, `recovery.csv`)
- `holidays/2026-10-22/` holidays and the New Year break (`feeds.csv` one class per feed and day, `dates.csv` per day,
  `upcoming.csv`, `skipped.csv`, `summary.json`, `holidays.md`, later holidays against 11-03 in `horizon.json` and
  `horizon.md`); `holidays/predictions-2026-10-22.md` and `holidays/predictions-recheck-2026-12.md` (recorded in advance)
- `names/2026-10-22/` stop-name readings and English (`feeds.csv`, `prefectures.csv`, `skipped.csv`, `summary.json`,
  `names.md`, the recount in `verify/`: `recount.csv`, `recount.md`, `summary.json`); `names/predictions-2026-10-22.md`
  (recorded in advance)
- `timing/2026-10-22/` timing, stop positions and bus speeds (`feeds.csv`, `prefectures.csv`, `fast_steps.csv` too-fast
  steps, `time_travel.csv`, `stacks.csv` stacked poles, `summary.json`, `timing.md`); `timing/predictions-2026-10-22.md`
  (recorded in advance)
- `lastbus/2026-10-22/` first and last buses (`feeds.csv`, `prefectures.csv`, `places/` with each place's first and
  last bus on the Wednesday, Saturday and Sunday: one `NN.csv` per prefecture, `index.csv`, `changed.csv` for feeds that
  changed on the re-read, `split.json`; `summary.json`, `lastbus.md`); `lastbus/predictions-2026-10-22.md` (recorded in
  advance)
- `calgap/2026-10-22/` the listed end date against the file's own dates (`feeds.csv`, `summary.json`, `calendar_gap.md`,
  and the later-file check in `next/`: `feeds.csv`, `summary.json`, `next.md`)
- `chain/2026-10-23/` the chain of published files (`chain.csv` one row per feed, `summary.json`, `chain.md`);
  `chain/predictions-2026-10-23.md` and `chain/predictions-2026-11-01.md` (recorded in advance)
- `health/2026-10-22/` the data-health table (`feeds.csv` four checks per feed, `prefectures.csv`, `summary.json`,
  `health.md`)
- `tools/gtfs_lapses.py` (census), `tools/fy_cliff.py` (April 1), `tools/repeat_cliff.py` (repeats),
  `tools/expiry_watch.py` (expiry list), `tools/fy2027_risk.py` (forecast by group and its score),
  `tools/cluster_band.py` (clustering and ranges), `tools/trend_band.py` (trend check),
  `tools/lapse_survival.py` (how long lapses last), `tools/recovery_forecast.py` (open-lapse forecast and its score),
  `tools/holiday_check.py` (holidays), `tools/holiday_recheck.py` (later holidays and the December re-check),
  `tools/names_check.py` (stop names), `tools/verify_names.py` (stop-name recount), `tools/timing_check.py` (timing and
  positions), `tools/last_bus.py` (first and last buses), `tools/split_places.py` (per-place table by prefecture),
  `tools/calendar_gap.py` (listed end against the file's dates), `tools/calendar_next.py` (later files),
  `tools/file_chain.py` (the chain of published files), `tools/data_health.py` (data-health table), each with
  `test_*.py`
- Reproduce: `python tools/gtfs_lapses.py --as-of 2026-10-16 --pause 1.0 --out out` →
  `python tools/fy_cliff.py out/lapses/2026-10-16` → `python tools/repeat_cliff.py out/lapses/2026-10-16`.
  Holidays: `python tools/holiday_check.py --as-of 2026-10-22 --out out` (reads the files current on the day it runs) →
  `python tools/holiday_recheck.py --before holidays/2026-10-22/feeds.csv --out out`.
  Stop names: `python tools/names_check.py --as-of 2026-10-22 --out out` →
  `python tools/verify_names.py --feeds names/2026-10-22/feeds.csv --out out/verify`.
  Timing and positions: `python tools/timing_check.py --feeds names/2026-10-22/feeds.csv --pause 1.0 --out out`.
  First and last buses: `python tools/last_bus.py --feeds names/2026-10-22/feeds.csv --pause 1.0 --out out` (both read
  the files current on the day they run) →
  `python tools/split_places.py --places out/lastbus/2026-10-22/places.csv --rerun-feeds out/lastbus/2026-10-22/feeds.csv --published-feeds lastbus/2026-10-22/feeds.csv --out out/places`.
  Listed end dates: `python tools/calendar_gap.py --health health/2026-10-22/feeds.csv --lastbus lastbus/2026-10-22/feeds.csv --as-of 2026-10-22 --out out/calgap` →
  `python tools/calendar_next.py --gaps out/calgap/feeds.csv --out out/calgap/next` (reads the API on the day it runs).
  Chain of files: `python tools/file_chain.py --pause 1.0 --out out/chain` (reads the API on the day it runs).
  Data health: `python tools/data_health.py --lapses data/2026-10-16/feeds.csv --watch watch/2026-10-22/expiring.csv --holidays holidays/2026-10-22/feeds.csv --names names/2026-10-22/feeds.csv --as-of 2026-10-22 --out out/health`

### Sources and licences
Version histories and timetable files come from the GTFS Data Repository API (https://gtfs-data.jp/). Each feed's
publisher and licence are in the organization_name and license columns of `feeds.csv`. No timetable files are
redistributed here. The per-place and per-feed tables (`lastbus/2026-10-22/places/` and the tables in
`timing/2026-10-22/`) hold stop names, positions and times derived from each feed; their source is each feed's publisher.

Contact: MV2, Munim, Inc., mv2@munimtech.com
