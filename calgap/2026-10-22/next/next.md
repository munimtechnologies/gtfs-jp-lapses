# 期限より早く終わるファイルに後続のファイルはあるか / Do the files that end early have a later file? (2026-10-23)

現行ファイルの最後の運行日が掲載上の期限より前のデータ（calendar_gap.py の file_ends_earlier）について、リポジトリのAPIで、読んだファイルより後に始まるファイルがすでに公開され、その翌日から掲載上の期限までつながっているかを確かめました。掲載上の期限は、まだ有効になっていない後続のファイルの期限であることがあります。
For each feed whose current file runs out before the end date the repository lists (class file_ends_earlier in calendar_gap.py), the repository API was read once to see whether a later file is already published and covers, without a break, the days from the day after the read file's own last day to the listed end date. The listed date can be the end of a later file that is not in force yet.

Feeds checked: 21. A later file covers the rest: 8; a later file leaves a break: 0; no later file: 13; API request failed: 0.

Of the 6 feeds called hidden by calendar_gap.py: 5 covered by a later file, 0 with a break, 1 with no later file.

Current-file note (memo) mentions abolition or suspension (廃止・休止・運休・運行終了): 12 feeds, 10 of them with no later file. Marked discontinued in the repository: 0.

## 後続のファイルがない、またはつながらないデータ / No later file, or a break

| organization | feed | pref | listed end | file end | uncovered from | days | later files | marked discontinued | memo |
|---|---|---|---|---|---|---|---|---|---|
| 濃飛乗合自動車（濃飛バス） | 濃飛バス（観光路線） | 岐阜県 | 2027-03-31 | 2026-11-30 | 2026-12-01 | 121 | 0 | no | 2026年4月1日からのデータです。 ・馬籠妻籠線の運航に対応 ・2026年の上高地線、乗鞍線の運行に対応 ・上高地線の運賃を一部変更 |
| 西脇市 | ループバス/おりひめバス | 兵庫県 | 2027-03-31 | 2027-03-22 | 2027-03-23 | 9 | 0 | no |  |
| とさでん交通株式会社 | 路線バス | 高知県 | 2027-10-03 | 2027-09-30 | 2027-10-01 | 3 | 0 | no | 自動取り込み |
| 中津市 | 樋山路鎌城線 | 大分県 | 2026-10-31 | 2026-09-30 | 2026-10-01 | 31 | 0 | no | R8.10.1よりデマンド化に伴い、路線廃止 |
| 中津市 | 川原口線 | 大分県 | 2026-10-31 | 2026-09-30 | 2026-10-01 | 31 | 0 | no | R8.10.1よりデマンド化に伴い、路線廃止 |
| 中津市 | 城井線 | 大分県 | 2026-10-31 | 2026-09-30 | 2026-10-01 | 31 | 0 | no | R8.10.1よりデマンド化に伴い、路線廃止 |
| 中津市 | 大島伊福線 | 大分県 | 2026-10-31 | 2026-09-30 | 2026-10-01 | 31 | 0 | no | R8.10.1よりデマンド化に伴い、路線廃止 |
| 中津市 | 大島台金吉線 | 大分県 | 2026-10-31 | 2026-09-30 | 2026-10-01 | 31 | 0 | no | R8.10.1よりデマンド化に伴い、路線廃止 |
| 中津市 | 深耶馬東線 | 大分県 | 2026-10-31 | 2026-09-30 | 2026-10-01 | 31 | 0 | no | R8.10.1よりデマンド化に伴い、路線廃止 |
| 中津市 | 深耶馬西線 | 大分県 | 2026-10-31 | 2026-09-30 | 2026-10-01 | 31 | 0 | no | R8.10.1よりデマンド化に伴い、路線廃止 |
| 中津市 | 上ノ川内柾木線 | 大分県 | 2026-10-31 | 2026-09-30 | 2026-10-01 | 31 | 0 | no | R8.10.1よりデマンド化に伴い、路線廃止 |
| 中津市 | 山移北線 | 大分県 | 2026-10-31 | 2026-09-30 | 2026-10-01 | 31 | 0 | no | R8.10.1よりデマンド化に伴い、路線廃止 |
| 中津市 | 山移南線 | 大分県 | 2026-10-31 | 2026-09-30 | 2026-10-01 | 31 | 0 | no | R8.10.1よりデマンド化に伴い、路線廃止 |

## 後続のファイルが残りを埋めるデータ / A later file covers the rest

| organization | feed | pref | file end | later file from | covered to |
|---|---|---|---|---|---|
| 十和田観光電鉄株式会社 | 十和田観光電鉄（八戸～三沢空港線） | 青森県 | 2026-10-24 | 2026-10-25 | 2026-11-30 |
| 羽後交通株式会社 | 羽後交通（本荘地区） | 秋田県 | 2026-11-30 | 2026-12-01 | 2027-03-31 |
| 羽後交通株式会社 | 羽後交通（田沢湖地区） | 秋田県 | 2026-11-30 | 2026-12-01 | 2027-03-31 |
| 草軽交通株式会社 | 軽井沢草津長野原草津口バス | 長野県 | 2027-07-31 | 2026-11-01 | 2027-10-31 |
| 藤枝市 | 藤枝市自主運行バス（駅南循環+アクセスバス） | 静岡県 | 2026-10-24 | 2026-10-25 | 2027-03-27 |
| 明石市 | たこバス/たこバスミニ | 兵庫県 | 2027-04-30 | 2026-11-01 | 2027-11-30 |
| 高知西南交通株式会社 | 路線バス | 高知県 | 2026-10-31 | 2026-11-01 | 2027-03-31 |
| 三原村 | 三原村「三原バス」 | 高知県 | 2026-11-02 | 2026-11-01 | 2026-12-31 |

Limits: only the from_date and to_date the repository gives for each file are used; the later files' own calendars are not read, so a later file may itself end early. A file counts as later when it starts after the first day of the file that was read. The API was read on the day above, after the files were read on 2026-10-22, so a later file published in between also counts. A day with no file in force is not proof that no bus runs (a route can be seasonal or have ended), and a note is the publisher's text, shown as given. Place names in the data are records of fact, not judgements.

Generated 2026-10-23T07:46:30Z. Source: GTFS Data Repository (https://gtfs-data.jp/); each feed's publisher and licence are in feeds.csv. Made by MV2 of Munim, Inc. with AI agents working in MV2's name. Data CC BY 4.0.
