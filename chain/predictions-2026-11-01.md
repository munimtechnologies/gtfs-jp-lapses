# 10月末に終わり後続のファイルがない7件：事前に記録した予測 / Seven feeds ending in late October with no later file: a prediction recorded in advance (2026-10-23)

2026年10月23日の `tools/file_chain.py`（`chain/2026-10-23/`）では、いま有効なファイルが10月31日までに終わり、後続のファイルがまだ
公開されていないデータが17件ありました。うち10件は、現行ファイルのメモに2026年10月1日に廃止とある1つの市の10路線です
（`calgap/2026-10-22/`）。残る7件について、次の予測を記録します。

On 2026-10-23, `tools/file_chain.py` (`chain/2026-10-23/`) found 17 feeds whose file in force ends by 2026-10-31 with no
later file published yet. Ten are the routes of one city whose current-file note says they ended on 2026-10-01
(`calgap/2026-10-22/`). For the other seven, this prediction is recorded before their end dates:

- F1: 下の7件のうち4件以上は、2026年11月1日以降（日本時間）に最初にAPIを読んだ日に、有効なファイルがない。
  At least 4 of the 7 feeds below have no file in force on the first day on or after 2026-11-01 (Japan time) on which
  the API is read for them.

| organization_id | feed_id | file in force ends (2026-10-23) |
|---|---|---|
| tosaden-kotsu | GTFS-Tosadentraffic_Airportbus | 2026-10-25 |
| rokkashovillage | rokkasho-sharedtaxi | 2026-10-30 |
| kamigoritown | ainorigo | 2026-10-31 |
| kamishihorotown | kamishihoro | 2026-10-31 |
| kamishihorotown | kamishihoro-self-bus | 2026-10-31 |
| kumanogobobus | kumanogobobus_gobo | 2026-10-31 |
| nishinomiyacity | sakurayamanami | 2026-10-31 |

How it will be scored: `python tools/file_chain.py --pause 1.0 --out out/chain` run on a day from 2026-11-01 to
2026-11-05 (Japan time). A feed has a file in force when its row's class is continuous, break or list_mismatch and its
in_force_to is filled; classes expired and not_in_force mean no file in force. A feed missing from chain.csv because the
repository now marks it discontinued also counts as no file in force, and is reported separately: a network that has
really ended is not a publishing delay. The score, right or wrong, is added to the README.

Why at least 4: these files have one week or less left and no successor 8 days before; the later files seen on
2026-10-23 were published a median of 18 days ahead (only 1 of 20 under 7 days), and in the lapse census
(`data/2026-10-16/`) 20.2% of the feeds whose data ended on 2026-03-31 had no valid file on 2026-04-01. A successor can
still be published late and dated back, which would end the gap but not undo it; this prediction is about the day of
the read only.

Limits: the repository's validity dates only; no timetable file is read. A day with no published file is not proof that
no bus runs. Place names in the data are records of fact, not judgements.

MV2 of Munim, Inc. · Made with AI agents working in MV2's name. · CC BY 4.0
