# 停留所名のよみがな・英語 / Readings and English names in Japan's GTFS files (2026-10-22)

GTFSデータリポジトリの有効なデータ（オープンライセンス）の現行ファイルについて、停留所（標柱、location_type 0）と行先（trip_headsign）ごとに、translations.txt によみがな（ja-Hrkt、GTFS-JPで必須）と英語（推奨）があるかを数えました。
For the current file of every active, openly licensed feed in the GTFS Data Repository, each stop (location_type 0) and each destination text (trip_headsign) was checked for a kana reading (ja-Hrkt, required by GTFS-JP) and an English name (recommended) in translations.txt.

Feeds checked: 553; skipped: discontinued 28, ended 27.

| | stops | with reading | with English | destinations | with reading | with English |
|---|---|---|---|---|---|---|
| all feeds | 98776 | 97.9% | 77.6% | 5489 | 16.0% | 17.1% |

| feeds giving it for | none of their stops | some | at least 90% |
|---|---|---|---|
| reading | 6 | 2 | 545 |
| English | 124 | 22 | 407 |

translations.txt: gtfs 537, jp_v2 10, empty 1, missing 5 (gtfs = table_name/field_name rows; jp_v2 = trans_id, lang, translation).

Checks: readings containing kanji 22; English names containing kana or kanji 133 (of which a copy of the Japanese name 1); stops without their own reading or English whose parent station has one: 608 / 608. Other languages (feeds): ja-latn 21, ko 11, zh-tw 7, zh-cn 6, zh-hans 3, zh-hant 3, zh 3, pt 1, pt-br 1, es 1, fr 1, hi 1, id 1, it 1, mn 1, ne 1, ru 1, ta 1, th 1, vi 1.

## 都道府県別 / By prefecture

| 都道府県 | feeds | stops | with reading | with English | feeds ≥90% reading | feeds ≥90% English |
|---|---|---|---|---|---|---|
| 北海道 | 5 | 618 | 100.0% | 71.2% | 5 | 3 |
| 青森県 | 28 | 5050 | 100.0% | 98.0% | 28 | 27 |
| 岩手県 | 3 | 1141 | 100.0% | 96.4% | 3 | 3 |
| 宮城県 | 2 | 239 | 100.0% | 100.0% | 2 | 2 |
| 秋田県 | 3 | 761 | 100.0% | 85.8% | 3 | 2 |
| 山形県 | 31 | 5881 | 100.0% | 55.2% | 31 | 8 |
| 福島県 | 4 | 1577 | 100.0% | 96.6% | 4 | 2 |
| 茨城県 | 8 | 1675 | 57.4% | 51.8% | 4 | 4 |
| 栃木県 | 7 | 1674 | 99.9% | 57.3% | 7 | 4 |
| 群馬県 | 4 | 836 | 100.0% | 80.0% | 4 | 3 |
| 埼玉県 | 19 | 1319 | 69.9% | 18.2% | 18 | 4 |
| 千葉県 | 10 | 1918 | 100.0% | 97.3% | 10 | 8 |
| 東京都 | 10 | 552 | 77.4% | 66.3% | 9 | 7 |
| 神奈川県 | 7 | 379 | 99.5% | 40.9% | 7 | 6 |
| 新潟県 | 5 | 1255 | 100.0% | 89.2% | 5 | 4 |
| 富山県 | 25 | 4357 | 99.9% | 97.9% | 25 | 24 |
| 石川県 | 6 | 735 | 100.0% | 55.4% | 6 | 5 |
| 山梨県 | 5 | 546 | 100.0% | 100.0% | 5 | 5 |
| 長野県 | 44 | 8002 | 99.9% | 59.7% | 44 | 26 |
| 岐阜県 | 35 | 7463 | 100.0% | 94.7% | 35 | 30 |
| 静岡県 | 8 | 1140 | 100.0% | 72.9% | 8 | 7 |
| 愛知県 | 32 | 5731 | 97.3% | 86.1% | 31 | 27 |
| 三重県 | 40 | 8214 | 100.0% | 100.0% | 40 | 40 |
| 滋賀県 | 9 | 1988 | 99.9% | 100.0% | 9 | 9 |
| 大阪府 | 1 | 11 | 100.0% | 100.0% | 1 | 1 |
| 兵庫県 | 33 | 4919 | 100.0% | 93.1% | 33 | 30 |
| 奈良県 | 2 | 137 | 100.0% | 0.0% | 2 | 0 |
| 和歌山県 | 13 | 2904 | 100.0% | 100.0% | 13 | 13 |
| 島根県 | 1 | 109 | 100.0% | 100.0% | 1 | 1 |
| 岡山県 | 10 | 1706 | 100.0% | 91.4% | 10 | 8 |
| 徳島県 | 16 | 3334 | 100.0% | 100.0% | 16 | 16 |
| 香川県 | 6 | 1106 | 100.0% | 39.9% | 6 | 3 |
| 高知県 | 51 | 8342 | 100.0% | 2.8% | 51 | 14 |
| 福岡県 | 40 | 3838 | 99.9% | 93.4% | 40 | 33 |
| 佐賀県 | 1 | 148 | 100.0% | 100.0% | 1 | 1 |
| 長崎県 | 1 | 155 | 100.0% | 100.0% | 1 | 1 |
| 熊本県 | 6 | 6712 | 100.0% | 100.0% | 6 | 6 |
| 大分県 | 19 | 927 | 100.0% | 78.9% | 19 | 18 |
| 鹿児島県 | 1 | 1180 | 45.9% | 45.9% | 0 | 0 |
| 沖縄県 | 2 | 197 | 96.4% | 96.4% | 2 | 2 |

## 事前に記録した予測 / Predictions recorded before the run (2026-10-22)

| | prediction | result | |
|---|---|---|---|
| N1 | At least 70% of the checked feeds give a kana reading (ja-Hrkt) for at least 90% of their stops. | {"feeds": 553, "most_reading": 545, "share": 0.986} | held |
| N2 | Between 20% and 60% of the checked feeds give an English name for at least 90% of their stops. | {"feeds": 553, "most_en": 407, "share": 0.736} | did not hold |
| N3 | Of all stops with an English name, at least 1% have kana or kanji in that English name. | {"stops_en": 76662, "en_japanese": 133, "share": 0.002} | did not hold |
| N4 | Of the feeds whose translations.txt has rows, at least 10% use the older GTFS-JP format (trans_id, lang, translation). | {"with_rows": 547, "jp_v2": 10, "share": 0.018} | did not hold |

限界: 停留所はレコード（標柱）単位で数えます。record_idで親の停留所（location_type 1）だけに訳を付けたデータは、標柱では「なし」になります（その数は上の parent station の値）。行先は trips.txt の trip_headsign だけで、stop_times.txt の stop_headsign は見ていません。英語の内容が正しいかは確かめていません（かな・漢字が入っているかだけ）。
Limits: stops are counted per record (pole). A file that translates only the parent station (location_type 1) by record_id shows "none" on its poles (counted above as parent station). Destinations are trip_headsign in trips.txt only, not stop_headsign. Whether an English name is right is not checked, only whether it has kana or kanji in it. Names are records of fact, not judgements.

Source: GTFS Data Repository API v2 (https://gtfs-data.jp/); each feed's publisher and licence are in feeds.csv. Made by MV2 of Munim, Inc. with AI agents working in MV2's name. Data CC BY 4.0.
