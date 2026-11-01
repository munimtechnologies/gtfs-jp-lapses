# 公開済みのファイルのつながり / The chain of published files (2026-11-01)

GTFSデータリポジトリの一覧にある有効なデータそれぞれについて、APIを1回読み、いま有効なファイルがいつ終わるか、次のファイルがいつ始まり何日前に公開されたか、今日から掲載上の期限まで公開済みのファイルがすき間なくつながっているかを確かめました。掲載上の期限は、まだ有効になっていない後続のファイルの期限であることがあります。
For each active feed in the GTFS Data Repository list, the API was read once: when the file in force today ends, when the next file starts and how many days ahead it was published, and whether the published files run without a break from today to the end date the list gives (which can be the end of a later file not yet in force).

- 一覧 / in the list: 608; 運行終了 / discontinued: 28; 期限なし / no end date: 0; 有効 / active: 580; 期限切れ / expired (not read): 41
- 読めたデータ / read with files: 539; つながっている / continuous: 539; 途中にすき間 / break: 0; 今日有効なファイルなし / nothing in force today: 0; 一覧の期限と合わない / list mismatch: 0; ファイルなし / no files: 0; API失敗 / API failed: 0
- 後続のファイルが公開済み / with a later file published: 8 (1.5%)
- いま有効なファイルが60日以内に終わる / file in force ends within 60 days: 48; うち後続のファイルがつなぐ / continued by a later file: 3; うち掲載上の期限は60日より先 / of which the listed end is more than 60 days away: 3
- 次のファイルの公開から開始までの日数 / lead time of the next file (days): n 8, median 35.5, quartiles 18.5–53.0, range 10–113; under 7 days: 0
- いま有効なファイルのメモに廃止・休止・運休などの語 / note on the file in force mentions abolition or suspension: 35; APIで運行終了の印 / marked discontinued in the API: 0

## 事前に記録した予測 / Predictions fixed before the run

- C1: Fewer than 2% of the checked feeds have a break (a day with no published file) between today and their listed end date, counting feeds with no file in force today (classes break + not_in_force). Result: 0.0%, held.
- C2: Between 5% and 30% of the checked feeds already have at least one later file published. Result: 1.5%, did not hold.
- C3: Of the checked feeds whose file in force today ends within 60 days, between 10% and 40% already have a later file that continues it with no break. Result: 6.2%, did not hold.
- C4: The median lead time of the later files (start date minus publication date in Japan time) is at least 14 days. Result: 35.5 days, held.

## すき間・今日有効なファイルなし・一覧と合わない / Breaks, nothing in force, list mismatch

| organization | feed | pref | listed end | class | in force to | break from | days | resumes | memo |
|---|---|---|---|---|---|---|---|---|---|

## いま有効なファイルが60日以内に終わるデータ / File in force ends within 60 days

| organization | feed | pref | in force to | days left | next file from | published | continued | listed end |
|---|---|---|---|---|---|---|---|---|
| 長電バス株式会社 | おぶせロマン号 | 長野県 | 2026-11-23 | 22 |  |  | no | 2026-11-23 |
| 山形交通 | 山交バス | 山形県 | 2026-11-24 | 23 |  |  | no | 2026-11-24 |
| 伊勢市 | 伊勢市コミュニティバス「おかげバス」 | 三重県 | 2026-11-30 | 29 |  |  | no | 2026-11-30 |
| 菰野町 | 菰野町「かもしか号」 | 三重県 | 2026-11-30 | 29 |  |  | no | 2026-11-30 |
| 大町市 | 特急バス「雷鳥ライナー」 | 長野県 | 2026-11-30 | 29 |  |  | no | 2026-11-30 |
| 尾張旭市 | 尾張旭市あさぴー号 | 愛知県 | 2026-11-30 | 29 |  |  | no | 2026-11-30 |
| 十和田観光電鉄株式会社 | 十和田観光電鉄（八戸～三沢空港線） | 青森県 | 2026-11-30 | 29 |  |  | no | 2026-11-30 |
| 羽後交通株式会社 | 羽後交通（本荘地区） | 秋田県 | 2026-11-30 | 29 | 2026-12-01 | 2026-09-03 | yes | 2027-03-31 |
| 羽後交通株式会社 | 羽後交通（田沢湖地区） | 秋田県 | 2026-11-30 | 29 | 2026-12-01 | 2026-08-10 | yes | 2027-03-31 |
| 米沢市 | 米沢市営バス | 山形県 | 2026-11-30 | 29 |  |  | no | 2026-11-30 |
| 長電バス株式会社 | 長電バス急行 | 長野県 | 2026-12-04 | 33 |  |  | no | 2026-12-04 |
| 南信州地域交通問題協議会（南信州広域連合） | 【喬木村】E3喬木大島線せせらぎ/E4氏乗線そよかぜ/E5 たかぎコミュニティバス阿島線/E6 たかぎコミュニティバス伊久間線/E7たかぎコミュニティバス厚生病院線/E8上平線/E9富田線 | 長野県 | 2026-12-15 | 44 |  |  | no | 2026-12-15 |
| 有限会社黒岩観光 | 路線バス | 高知県 | 2026-12-25 | 54 |  |  | no | 2026-12-25 |
| 仁淀川町 | 仁淀川町町民バス | 高知県 | 2026-12-27 | 56 |  |  | no | 2026-12-27 |
| 有限会社嶺北観光自動車 | 路線バス | 高知県 | 2026-12-27 | 56 |  |  | no | 2026-12-27 |
| 熊本電鉄 | 熊本電鉄電車 | 熊本県 | 2026-12-28 | 57 |  |  | no | 2026-12-28 |
| 柳津町 | 柳津町町民バス”ふれあい号” | 福島県 | 2026-12-28 | 57 |  |  | no | 2026-12-28 |
| 高知高陵交通株式会社 | 路線バス | 高知県 | 2026-12-29 | 58 |  |  | no | 2026-12-29 |
| 成田市 | 成田市コミュニティバス | 千葉県 | 2026-12-30 | 59 |  |  | no | 2026-12-30 |
| 知立市 | 知立市「ミニバス」（コミュニティバス） | 愛知県 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |
| 飯能市 | 飯能市乗合ワゴン 原市場 | 埼玉県 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |
| 飯能市 | 飯能市乗合ワゴン 南高麗 | 埼玉県 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |
| いの町 | いの町営バス「伊野循環線」 | 高知県 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |
| JR東日本盛岡支社 | わんタク定時便 | 青森県 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |
| 河北町 | 河北町営バス | 山形県 | 2026-12-31 | 60 | 2026-12-01 | 2026-10-21 | yes | 2027-03-31 |
| 葛飾区 | さくら | 東京都 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |
| 株式会社高知駅前観光 | 空港連絡バス | 高知県 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |
| 株式会社高知駅前観光 | 高速バス | 高知県 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |
| 三原村 | 三原村「三原バス」 | 高知県 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |
| 中泊町 | 中泊町コミュニティバス | 青森県 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |
| 二宮町 | 二宮町コミュニティバス | 神奈川県 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |
| 大鰐町 | 大鰐町スネカラバス | 青森県 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |
| 龍ケ崎市 | 龍ケ崎市コミュニティバス | 茨城県 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |
| 寒川町 | 寒川町コミュニティバス「もくせい号」東ルート | 神奈川県 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |
| 寒川町 | 寒川町コミュニティバス「もくせい号」倉見大村ルート | 神奈川県 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |
| 寒川町 | 寒川町コミュニティバス「もくせい号」南ルート | 神奈川県 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |
| 新郷村 | 新郷村営バス | 青森県 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |
| 外ヶ浜町 | 外ヶ浜町営バス | 青森県 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |
| 土岐市 | 土岐市民バス | 岐阜県 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |
| 常滑市 | コミュニティバスグルーン | 愛知県 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |
| 徳島バス南部株式会社 | 徳島バス南部株式会社 | 徳島県 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |
| とさでん交通株式会社 | 空港連絡バス | 高知県 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |
| 十和田市 | 十和田市コミュニティバス | 青森県 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |
| つがる市 | つがる市地域内交通 | 青森県 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |
| 内灘町 | コミュニティバス | 石川県 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |
| 和光市 | 和光市内循環バス（わこば） | 埼玉県 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |
| 合同会社やんばる急行バス | やんばる急行バス | 沖縄県 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |
| 四日市市 | 四日市市自主運行バス | 三重県 | 2026-12-31 | 60 |  |  | no | 2026-12-31 |

Limits: only the from_date, to_date and published_at the repository gives for each file are used; the files' own calendars are not read, so a file can run out of service days before its to_date (see calgap/2026-10-22/). Old files no longer in the API are not seen. The API was read once per feed on the day above. A break in the published files is not proof that no bus runs. Place names in the data are records of fact, not judgements.

Generated 2026-11-01T08:14:07Z. Source: GTFS Data Repository API v2 (https://gtfs-data.jp/); each feed's publisher and licence are in chain.csv. Made by MV2 of Munim, Inc. with AI agents working in MV2's name. Data CC BY 4.0.
