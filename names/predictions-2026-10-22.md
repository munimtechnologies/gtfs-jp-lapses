# 停留所名のよみがな・英語：事前に記録した予測 / Readings and English names: predictions recorded before the run

Recorded on 2026-10-22 (UTC), before `tools/names_check.py` read any feed file. The census reads the current file of
every active, openly licensed feed in the GTFS Data Repository (https://gtfs-data.jp/) and checks each stop
(location_type 0) and each destination text (trip_headsign) for a kana reading (ja-Hrkt) and an English name in
translations.txt.

Why it matters: GTFS-JP makes translations.txt and stop-name readings required (domestic route-search providers need
the readings) and recommends English. Version 4.0 of the spec (MLIT, March 2026) keeps this. We found no published
count, across Japan's open feeds, of how many actually give them.

A feed "gives" readings or English when at least 90% of its stops have them.

| | prediction |
|---|---|
| N1 | At least 70% of the checked feeds give a kana reading (ja-Hrkt) for at least 90% of their stops. |
| N2 | Between 20% and 60% of the checked feeds give an English name for at least 90% of their stops. |
| N3 | Of all stops with an English name, at least 1% have kana or kanji in that English name. |
| N4 | Of the feeds whose translations.txt has rows, at least 10% use the older GTFS-JP format (trans_id, lang, translation). |

The same texts are fixed in `PREDICTIONS` in `tools/names_check.py`, which scores them on the first run. Results
go to `names/<date>/` whatever they are.

Limits known in advance: stops are counted per record (pole), so a file that translates only parent stations by
record_id shows "none" on its poles (the tool counts those separately). Destinations are trip_headsign only. The
English text is not checked for correctness, only for kana or kanji in it.

MV2 of Munim, Inc. Made with AI agents working in MV2's name. Text CC BY 4.0.
