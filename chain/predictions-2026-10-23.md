# 公開済みのファイルのつながり：事前に記録した予測 / The chain of published files: predictions recorded in advance (2026-10-23)

`tools/file_chain.py` は、GTFSデータリポジトリの一覧にある有効なデータそれぞれについてAPIを1回読み、いま有効なファイルがいつ終わるか、
次のファイルがいつ始まり何日前に公開されたか、今日から掲載上の期限まで公開済みのファイルがすき間なくつながっているかを調べます。
以下の4つの予測は、このファイルとツール（PREDICTIONS）をコミットした時点で、まだどのデータも読む前に記録したものです。

`tools/file_chain.py` reads each active feed's entry in the GTFS Data Repository API once and finds when the file in
force today ends, when the next file starts and how many days ahead it was published, and whether the published files
run without a break from today to the end date the repository lists. The four predictions below were recorded, in this
file and in the tool's PREDICTIONS, before any feed was read. Shares are of the feeds whose API entry was read and has
files.

- C1: 掲載上の期限までのあいだに、公開済みのファイルのない日（すき間）があるデータは2%未満（今日有効なファイルがないデータも含む）。
  Fewer than 2% of the checked feeds have a break (a day with no published file) between today and their listed end
  date, counting feeds with no file in force today.
- C2: 後続のファイルがすでに公開されているデータは5%〜30%。
  Between 5% and 30% of the checked feeds already have at least one later file published.
- C3: いま有効なファイルが60日以内に終わるデータのうち、後続のファイルがすき間なくつないでいるのは10%〜40%。
  Of the checked feeds whose file in force today ends within 60 days, between 10% and 40% already have a later file that
  continues it with no break.
- C4: 後続のファイルの公開から開始までの日数（日本時間）の中央値は14日以上。
  The median lead time of the later files (start date minus publication date in Japan time) is at least 14 days.

Why: on 2026-10-23 a check of 21 feeds whose current file ends before the listed date (`calgap/2026-10-22/next/`) found
that 8 already had a later file covering the rest. That suggests the listed end date often belongs to a later file; this
census asks how often across all active feeds, and whether the chains have breaks the expiry list cannot see.

Lead-time benchmarks (guidance, not measurements): MobilityData's best practices aim for 3–4 weeks and at least 5 days (https://gtfs.org/documentation/schedule/schedule-best-practices/); the Transit app asks for at least 7
days (https://resources.transitapp.com/article/458-guidelines-for-producing-gtfs-static-data-for-transit). A search on
2026-10-23 found guidance like this but no count of the lead times feeds actually have.

Limits: only the from_date, to_date and published_at the repository gives are used; the files' own calendars are not
read. A break in the published files is not proof that no bus runs.

MV2 of Munim, Inc. · Made with AI agents working in MV2's name. · CC BY 4.0
