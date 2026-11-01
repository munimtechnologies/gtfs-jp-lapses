# Tests for score_f1.py on made-up chain.csv rows and feed lists. Every expected value is worked by hand.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import csv
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import score_f1 as sf  # noqa: E402

COLS = ['organization_id', 'feed_id', 'listed_end', 'class', 'in_force_from', 'in_force_to', 'next_from',
        'api_discontinued']


def row(org, fid, cls, to='', nxt=''):
    return {'organization_id': org, 'feed_id': fid, 'listed_end': '2026-10-31', 'class': cls,
            'in_force_from': '2026-04-01' if to else '', 'in_force_to': to, 'next_from': nxt,
            'api_discontinued': 'no'}


def listed(org, fid, disc=False, end='2026-10-31'):
    return {'organization_id': org, 'feed_id': fid, 'feed_is_discontinued': disc, 'latest_feed_end_date': end}


# tosaden none, rokkasho none, kamigori in force, kamishihoro discontinued (no row), self-bus in force,
# gobo api_failed (unresolved), sakurayamanami gone from the list (unresolved): 3 none, 2 unresolved
ROWS = [
    row('tosaden-kotsu', 'GTFS-Tosadentraffic_Airportbus', 'not_in_force', nxt='2026-11-10'),
    row('rokkashovillage', 'rokkasho-sharedtaxi', 'expired'),
    row('kamigoritown', 'ainorigo', 'continuous', '2027-03-31'),
    row('kamishihorotown', 'kamishihoro-self-bus', 'break', '2026-12-31'),
    row('kumanogobobus', 'kumanogobobus_gobo', 'api_failed'),
    row('someone', 'other', 'not_in_force'),                     # not one of the seven: ignored
]
LISTED = [
    listed('tosaden-kotsu', 'GTFS-Tosadentraffic_Airportbus'),
    listed('rokkashovillage', 'rokkasho-sharedtaxi', end='2026-10-30'),
    listed('kamigoritown', 'ainorigo', end='2027-03-31'),
    listed('kamishihorotown', 'kamishihoro', disc=True),
    listed('kamishihorotown', 'kamishihoro-self-bus', end='2027-03-31'),
    listed('kumanogobobus', 'kumanogobobus_gobo'),
]


class TestOutcome(unittest.TestCase):
    def test_in_force(self):
        for c in ('continuous', 'break', 'list_mismatch'):
            self.assertEqual(sf.outcome(row('a', 'b', c, '2027-01-01'), None), ('in_force', c))

    def test_in_force_class_without_to_is_unresolved(self):
        self.assertEqual(sf.outcome(row('a', 'b', 'break'), None)[0], 'unresolved')

    def test_none(self):
        self.assertEqual(sf.outcome(row('a', 'b', 'expired'), None), ('none', 'expired'))
        self.assertEqual(sf.outcome(row('a', 'b', 'not_in_force'), None), ('none', 'not_in_force'))

    def test_other_classes_unresolved(self):
        self.assertEqual(sf.outcome(row('a', 'b', 'api_failed'), None), ('unresolved', 'api_failed'))
        self.assertEqual(sf.outcome(row('a', 'b', 'no_files'), None), ('unresolved', 'no_files'))

    def test_missing_rows(self):
        self.assertEqual(sf.outcome(None, None), ('unresolved', 'not in the feed list'))
        self.assertEqual(sf.outcome(None, listed('a', 'b', disc=True))[0], 'none_discontinued')
        self.assertEqual(sf.outcome(None, listed('a', 'b', disc='true'))[0], 'none_discontinued')
        self.assertEqual(sf.outcome(None, listed('a', 'b', end=None)),
                         ('unresolved', 'no end date in the feed list'))
        self.assertEqual(sf.outcome(None, listed('a', 'b'))[0], 'unresolved')


class TestVerdict(unittest.TestCase):
    def test_held(self):
        self.assertEqual(sf.verdict(['none'] * 4 + ['in_force'] * 3, '2026-11-01'), 'held')
        self.assertEqual(sf.verdict(['none'] * 2 + ['none_discontinued'] * 2 + ['in_force'] * 3, '2026-11-05'),
                         'held')

    def test_failed(self):
        self.assertEqual(sf.verdict(['none'] * 3 + ['in_force'] * 4, '2026-11-02'), 'failed')

    def test_undetermined(self):
        self.assertEqual(sf.verdict(['none'] * 3 + ['unresolved'] + ['in_force'] * 3, '2026-11-02'),
                         'undetermined')

    def test_dates(self):
        out = ['none'] * 7
        self.assertEqual(sf.verdict(out, '2026-10-31'), 'invalid_date')
        self.assertEqual(sf.verdict(out, '2026-11-06'), 'invalid_date')


class TestScore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def make(self, rows, as_of='2026-11-02'):
        folder = os.path.join(self.dir, 'chain', as_of)
        os.makedirs(folder)
        with open(os.path.join(folder, 'chain.csv'), 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=COLS)
            w.writeheader()
            w.writerows(rows)
        with open(os.path.join(folder, 'summary.json'), 'w', encoding='utf-8') as f:
            json.dump({'as_of': as_of}, f)
        feeds = os.path.join(self.dir, 'feeds.json')
        with open(feeds, 'w', encoding='utf-8') as f:
            json.dump({'code': 200, 'body': LISTED}, f)
        return os.path.join(self.dir, 'chain'), feeds

    def test_seven_feeds(self):
        self.assertEqual(len(set((o, f) for o, f, _ in sf.FEEDS)), 7)

    def test_undetermined_end_to_end(self):
        chain, feeds = self.make(ROWS)
        out = os.path.join(self.dir, 'out')
        res = sf.main(['--chain-dir', chain, '--feeds', feeds, '--out', out])
        self.assertEqual(res['as_of'], '2026-11-02')
        self.assertEqual(res['counts'], {'in_force': 2, 'none': 2, 'none_discontinued': 1, 'unresolved': 2})
        self.assertEqual(res['none_total'], 3)
        self.assertEqual(res['verdict'], 'undetermined')
        by = {x['feed_id']: x for x in res['feeds']}
        self.assertEqual(by['GTFS-Tosadentraffic_Airportbus']['next_from'], '2026-11-10')
        self.assertEqual(by['sakurayamanami']['reason'], 'not in the feed list')
        self.assertEqual(by['kamishihoro']['outcome'], 'none_discontinued')
        with open(os.path.join(out, 'score.json'), encoding='utf-8') as f:
            self.assertEqual(json.load(f)['verdict'], 'undetermined')
        with open(os.path.join(out, 'score.md'), encoding='utf-8') as f:
            md = f.read()
        self.assertIn('Verdict: **undetermined**. 3 of 7', md)
        self.assertEqual(sum(1 for line in md.splitlines()
                             if line.startswith('| ') and not line.startswith('| organization_id')), 7)

    def test_held_end_to_end(self):
        rows = [dict(r) for r in ROWS]
        rows[4]['class'] = 'not_in_force'                         # gobo: 4 none
        chain, feeds = self.make(rows)
        self.assertEqual(sf.score(chain, feeds)['verdict'], 'held')

    def test_failed_end_to_end(self):
        rows = [dict(r) for r in ROWS[:4]]
        rows.append(row('kumanogobobus', 'kumanogobobus_gobo', 'continuous', '2027-03-31'))
        rows.append(row('nishinomiyacity', 'sakurayamanami', 'list_mismatch', '2027-03-31'))
        chain, feeds = self.make(rows)
        res = sf.score(chain, feeds)
        self.assertEqual(res['none_total'], 3)
        self.assertEqual(res['verdict'], 'failed')

    def test_invalid_date(self):
        chain, feeds = self.make(ROWS, as_of='2026-10-31')
        self.assertEqual(sf.score(chain, feeds)['verdict'], 'invalid_date')

    def test_needs_one_run_folder(self):
        chain, feeds = self.make(ROWS)
        os.makedirs(os.path.join(chain, '2026-11-03'))
        open(os.path.join(chain, '2026-11-03', 'chain.csv'), 'w').close()
        with self.assertRaises(SystemExit):
            sf.score(chain, feeds)


if __name__ == '__main__':
    unittest.main()
