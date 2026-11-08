# 2026-11-01 → 2026-11-08: 1週間の変化 / what changed in a week

MV2 of Munim, Inc. (mv2@munimtech.com)。MV2の名のもとAIエージェントが作成。CC BY 4.0。
Made by MV2 of Munim, Inc. with AI agents working in MV2's name. CC BY 4.0.

`watch/2026-11-01/` と `watch/2026-11-08/`（どちらもGTFSデータリポジトリの一覧 https://api.gtfs-data.jp/v2/feeds を
その日に取得）を手で比べました。
A hand comparison of `watch/2026-11-01/` and `watch/2026-11-08/`, each built from the GTFS Data Repository list read
that day.

| | 2026-11-01 | 2026-11-08 |
|---|---|---|
| 一覧 / in the list | 608 | 609 |
| 有効 / active | 580 | 581 |
| 期限切れ / expired | 41 | 41 |
| 8〜30日 / 8-30 days | 8 | 7 |
| 31〜60日 / 31-60 days | 37 | 39 |
| 2027-03-31 に切れる / ending exactly on 2027-03-31 | 290 | 288 |
| それまでに切れる / ending by then | 423 | 417 |

**更新されて一覧から外れたもの / renewed, so no longer listed (3):** 山形交通「山交バス」（期限 2026-11-24 だった）、
大町市 特急バス「雷鳥ライナー」（11-30）、南信州地域交通問題協議会【喬木村】（12-15）。
Yamako Bus (was ending 2026-11-24), Omachi's Raicho Liner express bus (11-30) and the Takagi village routes of the
Minami-Shinshu council (12-15) published newer files.

**新たに期限切れになったもの / newly expired: なし / none.** 先週すでに期限切れだった41件は、今週もすべて期限切れのままです。
2026年10月30〜31日に切れた13件（六ヶ所村乗合タクシー、上士幌町の2件、中津市の10路線）も、8〜9日たった今も新しい
データが出ていません。
None. All 41 feeds that were expired a week ago still are, including the 13 that ended on 2026-10-30/31 (Rokkasho's
shared taxi, two Kamishihoro feeds and ten Nakatsu routes): 8-9 days on, none has a newer file in the list.

**60日の枠に新しく入ったもの / newly inside the 60-day window (4):** 須崎市営バス、須崎市営巡航船（2027-01-04）、
バスネット津「ぐるっと・つーバス」、いの町営バス「本川地区」（2027-01-05）。枠が1週間進んだためで、期限が変わった
わけではありません。
Susaki city bus and ferry (2027-01-04), Tsu's Gurutto Tsu bus and Ino town's Honkawa bus (2027-01-05). They entered
because the window moved a week, not because their end dates changed.

**ほかの変化 / other changes:** 高知高陵交通「路線バス」は11月3日に新しいデータが公開され、期限が12-29から12-30に
1日延びました（まだ60日以内）。一覧には新しいデータが1件増えました（608 → 609）。2027年3月31日に切れるデータは
290 → 288、それまでに切れるデータは 423 → 417 に減りました。
Kochi Koryo Kotsu's route bus published a new file on 11-03 that moves its end date by one day (12-29 → 12-30,
still within 60 days). One feed was added to the list (608 → 609). Feeds ending exactly on 2027-03-31 went from
290 to 288, and feeds ending by then from 423 to 417.

限界 / limits: 一覧の latest_feed_end_date だけを見ています。一覧から消えたデータや、次のデータが後日から始まる空白は
この比較には出ません。地域名は事実の記録であり、評価ではありません。
Only the list's latest_feed_end_date is compared. A feed removed from the list, or a newer file that starts days
after the old one ends, would not show here. Place names are records of fact, not judgements.
