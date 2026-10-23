# 公開済みのファイルのつながり / The chain of published files (2026-10-23)

GTFSデータリポジトリの一覧にある有効なデータそれぞれについて、APIを1回読み、いま有効なファイルがいつ終わるか、次のファイルがいつ始まり何日前に公開されたか、今日から掲載上の期限まで公開済みのファイルがすき間なくつながっているかを確かめました。掲載上の期限は、まだ有効になっていない後続のファイルの期限であることがあります。
For each active feed in the GTFS Data Repository list, the API was read once: when the file in force today ends, when the next file starts and how many days ahead it was published, and whether the published files run without a break from today to the end date the list gives (which can be the end of a later file not yet in force).

- 一覧 / in the list: 608; 運行終了 / discontinued: 28; 期限なし / no end date: 0; 有効 / active: 580; 期限切れ / expired (not read): 27
- 読めたデータ / read with files: 553; つながっている / continuous: 553; 途中にすき間 / break: 0; 今日有効なファイルなし / nothing in force today: 0; 一覧の期限と合わない / list mismatch: 0; ファイルなし / no files: 0; API失敗 / API failed: 0
- 後続のファイルが公開済み / with a later file published: 20 (3.6%)
- いま有効なファイルが60日以内に終わる / file in force ends within 60 days: 33; うち後続のファイルがつなぐ / continued by a later file: 7; うち掲載上の期限は60日より先 / of which the listed end is more than 60 days away: 6
- 次のファイルの公開から開始までの日数 / lead time of the next file (days): n 20, median 18.0, quartiles 10.0–28.0, range 4–113; under 7 days: 1
- いま有効なファイルのメモに廃止・休止・運休などの語 / note on the file in force mentions abolition or suspension: 46; APIで運行終了の印 / marked discontinued in the API: 0

## 事前に記録した予測 / Predictions fixed before the run

- C1: Fewer than 2% of the checked feeds have a break (a day with no published file) between today and their listed end date, counting feeds with no file in force today (classes break + not_in_force). Result: 0.0%, held.
- C2: Between 5% and 30% of the checked feeds already have at least one later file published. Result: 3.6%, did not hold.
- C3: Of the checked feeds whose file in force today ends within 60 days, between 10% and 40% already have a later file that continues it with no break. Result: 21.2%, held.
- C4: The median lead time of the later files (start date minus publication date in Japan time) is at least 14 days. Result: 18.0 days, held.

## すき間・今日有効なファイルなし・一覧と合わない / Breaks, nothing in force, list mismatch

| organization | feed | pref | listed end | class | in force to | break from | days | resumes | memo |
|---|---|---|---|---|---|---|---|---|---|

## いま有効なファイルが60日以内に終わるデータ / File in force ends within 60 days

| organization | feed | pref | in force to | days left | next file from | published | continued | listed end |
|---|---|---|---|---|---|---|---|---|
| 藤枝市 | 藤枝市自主運行バス（駅南循環+アクセスバス） | 静岡県 | 2026-10-24 | 1 | 2026-10-25 | 2026-10-14 | yes | 2027-03-27 |
| 十和田観光電鉄株式会社 | 十和田観光電鉄（八戸～三沢空港線） | 青森県 | 2026-10-24 | 1 | 2026-10-25 | 2026-10-15 | yes | 2026-11-30 |
| とさでん交通株式会社 | 空港連絡バス | 高知県 | 2026-10-25 | 2 |  |  | no | 2026-10-25 |
| 六ヶ所村 | 六ヶ所村乗合タクシー | 青森県 | 2026-10-30 | 7 |  |  | no | 2026-10-30 |
| 上郡町 | 愛のり号 | 兵庫県 | 2026-10-31 | 8 |  |  | no | 2026-10-31 |
| 上士幌町 | 上士幌町コミュニティバス | 北海道 | 2026-10-31 | 8 |  |  | no | 2026-10-31 |
| 上士幌町 | 上士幌町自動運転バス | 北海道 | 2026-10-31 | 8 |  |  | no | 2026-10-31 |
| 株式会社高知駅前観光 | 空港連絡バス | 高知県 | 2026-10-31 | 8 | 2026-10-25 | 2026-10-16 | yes | 2026-12-30 |
| 高知西南交通株式会社 | 路線バス | 高知県 | 2026-10-31 | 8 | 2026-11-01 | 2026-10-07 | yes | 2027-03-31 |
| 熊野御坊南海バス株式会社 | 熊野御坊南海バス 御坊エリア | 和歌山県 | 2026-10-31 | 8 |  |  | no | 2026-10-31 |
| 中津市 | 樋山路鎌城線 | 大分県 | 2026-10-31 | 8 |  |  | no | 2026-10-31 |
| 中津市 | 川原口線 | 大分県 | 2026-10-31 | 8 |  |  | no | 2026-10-31 |
| 中津市 | 城井線 | 大分県 | 2026-10-31 | 8 |  |  | no | 2026-10-31 |
| 中津市 | 大島伊福線 | 大分県 | 2026-10-31 | 8 |  |  | no | 2026-10-31 |
| 中津市 | 大島台金吉線 | 大分県 | 2026-10-31 | 8 |  |  | no | 2026-10-31 |
| 中津市 | 深耶馬東線 | 大分県 | 2026-10-31 | 8 |  |  | no | 2026-10-31 |
| 中津市 | 深耶馬西線 | 大分県 | 2026-10-31 | 8 |  |  | no | 2026-10-31 |
| 中津市 | 上ノ川内柾木線 | 大分県 | 2026-10-31 | 8 |  |  | no | 2026-10-31 |
| 中津市 | 山移北線 | 大分県 | 2026-10-31 | 8 |  |  | no | 2026-10-31 |
| 中津市 | 山移南線 | 大分県 | 2026-10-31 | 8 |  |  | no | 2026-10-31 |
| 西宮市 | さくらやまなみバス | 兵庫県 | 2026-10-31 | 8 |  |  | no | 2026-10-31 |
| 三原村 | 三原村「三原バス」 | 高知県 | 2026-11-02 | 10 | 2026-11-01 | 2026-10-13 | yes | 2026-12-31 |
| 長電バス株式会社 | おぶせロマン号 | 長野県 | 2026-11-23 | 31 |  |  | no | 2026-11-23 |
| 山形交通 | 山交バス | 山形県 | 2026-11-24 | 32 |  |  | no | 2026-11-24 |
| 伊勢市 | 伊勢市コミュニティバス「おかげバス」 | 三重県 | 2026-11-30 | 38 |  |  | no | 2026-11-30 |
| 菰野町 | 菰野町「かもしか号」 | 三重県 | 2026-11-30 | 38 |  |  | no | 2026-11-30 |
| 大町市 | 特急バス「雷鳥ライナー」 | 長野県 | 2026-11-30 | 38 |  |  | no | 2026-11-30 |
| 尾張旭市 | 尾張旭市あさぴー号 | 愛知県 | 2026-11-30 | 38 |  |  | no | 2026-11-30 |
| 羽後交通株式会社 | 羽後交通（本荘地区） | 秋田県 | 2026-11-30 | 38 | 2026-12-01 | 2026-09-03 | yes | 2027-03-31 |
| 羽後交通株式会社 | 羽後交通（田沢湖地区） | 秋田県 | 2026-11-30 | 38 | 2026-12-01 | 2026-08-10 | yes | 2027-03-31 |
| 米沢市 | 米沢市営バス | 山形県 | 2026-11-30 | 38 |  |  | no | 2026-11-30 |
| 長電バス株式会社 | 長電バス急行 | 長野県 | 2026-12-04 | 42 |  |  | no | 2026-12-04 |
| 南信州地域交通問題協議会（南信州広域連合） | 【喬木村】E3喬木大島線せせらぎ/E4氏乗線そよかぜ/E5 たかぎコミュニティバス阿島線/E6 たかぎコミュニティバス伊久間線/E7たかぎコミュニティバス厚生病院線/E8上平線/E9富田線 | 長野県 | 2026-12-15 | 53 |  |  | no | 2026-12-15 |

Limits: only the from_date, to_date and published_at the repository gives for each file are used; the files' own calendars are not read, so a file can run out of service days before its to_date (see calgap/2026-10-22/). Old files no longer in the API are not seen. The API was read once per feed on the day above. A break in the published files is not proof that no bus runs. Place names in the data are records of fact, not judgements.

Generated 2026-10-23T11:19:18Z. Source: GTFS Data Repository API v2 (https://gtfs-data.jp/); each feed's publisher and licence are in chain.csv. Made by MV2 of Munim, Inc. with AI agents working in MV2's name. Data CC BY 4.0.
