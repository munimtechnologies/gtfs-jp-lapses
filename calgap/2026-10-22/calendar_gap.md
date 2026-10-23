# 掲載上の期限とファイル自体の期限 / Listed end date against the file's own dates (2026-10-22)

GTFSデータリポジトリが各データについて示す期限（掲載上の期限）と、現行ファイルの calendar.txt・calendar_dates.txt （feed_info.txt があればその期間で絞ったもの）が実際に含む最後の日を比べました。新しいダウンロードはしていません。
For each feed, the end date the GTFS Data Repository lists is compared with the last day the current file itself covers (calendar.txt and calendar_dates.txt, narrowed to feed_info.txt where given). No new downloads.

Feeds: 553. Same end: 506; file ends earlier: 21; file ends later: 17; no readable file dates: 4; no listed date: 5; not read: 0.

File ends earlier than listed: 21 feeds; by more than 7 days 20, by more than 30 days 19; median gap 31 days, largest 214.

Hidden (the listed date is more than 60 days away, but the file's own dates end within 60 days or have already ended): 6. Files whose own dates had already ended on 2026-10-22 while the listed date had not: 10.

## Feeds whose file ends more than 7 days before the listed date

| organization | feed | pref | listed end | file end | gap (days) | hidden |
|---|---|---|---|---|---|---|
| 明石市 | たこバス/たこバスミニ | 兵庫県 | 2027-11-30 | 2027-04-30 | 214 | no |
| 藤枝市 | 藤枝市自主運行バス（駅南循環+アクセスバス） | 静岡県 | 2027-03-27 | 2026-10-24 | 154 | yes |
| 高知西南交通株式会社 | 路線バス | 高知県 | 2027-03-31 | 2026-10-31 | 151 | yes |
| 濃飛乗合自動車（濃飛バス） | 濃飛バス（観光路線） | 岐阜県 | 2027-03-31 | 2026-11-30 | 121 | yes |
| 羽後交通株式会社 | 羽後交通（本荘地区） | 秋田県 | 2027-03-31 | 2026-11-30 | 121 | yes |
| 羽後交通株式会社 | 羽後交通（田沢湖地区） | 秋田県 | 2027-03-31 | 2026-11-30 | 121 | yes |
| 草軽交通株式会社 | 軽井沢草津長野原草津口バス | 長野県 | 2027-10-31 | 2027-07-31 | 92 | no |
| 三原村 | 三原村「三原バス」 | 高知県 | 2026-12-31 | 2026-11-02 | 59 | yes |
| 十和田観光電鉄株式会社 | 十和田観光電鉄（八戸～三沢空港線） | 青森県 | 2026-11-30 | 2026-10-24 | 37 | no |
| 中津市 | 樋山路鎌城線 | 大分県 | 2026-10-31 | 2026-09-30 | 31 | no |
| 中津市 | 川原口線 | 大分県 | 2026-10-31 | 2026-09-30 | 31 | no |
| 中津市 | 城井線 | 大分県 | 2026-10-31 | 2026-09-30 | 31 | no |
| 中津市 | 大島伊福線 | 大分県 | 2026-10-31 | 2026-09-30 | 31 | no |
| 中津市 | 大島台金吉線 | 大分県 | 2026-10-31 | 2026-09-30 | 31 | no |
| 中津市 | 深耶馬東線 | 大分県 | 2026-10-31 | 2026-09-30 | 31 | no |
| 中津市 | 深耶馬西線 | 大分県 | 2026-10-31 | 2026-09-30 | 31 | no |
| 中津市 | 上ノ川内柾木線 | 大分県 | 2026-10-31 | 2026-09-30 | 31 | no |
| 中津市 | 山移北線 | 大分県 | 2026-10-31 | 2026-09-30 | 31 | no |
| 中津市 | 山移南線 | 大分県 | 2026-10-31 | 2026-09-30 | 31 | no |
| 西脇市 | ループバス/おりひめバス | 兵庫県 | 2027-03-31 | 2027-03-22 | 9 | no |

Limits: descriptive only; no predictions were recorded, and some of these files had already been seen in the last-bus census. The listed date comes from the expiry list of 2026-10-22 where the feed is on it, else from the lapse census of 2026-10-16, and the file was read on 2026-10-22. "No readable file dates" can mean dates in an unexpected format rather than a missing calendar. A gap is a sign to check, not proof of a mistake. Place names in the data are records of fact, not judgements.

Generated 2026-10-23T01:30:12Z. Source: GTFS Data Repository (https://gtfs-data.jp/); each feed's publisher and licence are in feeds.csv. Made by MV2 of Munim, Inc. with AI agents working in MV2's name. Data CC BY 4.0.
