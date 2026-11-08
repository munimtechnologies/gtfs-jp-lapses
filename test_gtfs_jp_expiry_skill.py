# Tests for the gtfs-jp-expiry agent skill (skills/gtfs-jp-expiry/). Offline: no network request is made.
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import contextlib
import datetime as dt
import importlib.util
import io
import json
import os
import re
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.join(HERE, 'skills', 'gtfs-jp-expiry')
SCRIPT = os.path.join(SKILL, 'scripts', 'gtfs_jp_expiry.py')

spec = importlib.util.spec_from_file_location('gtfs_jp_expiry', SCRIPT)
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)

D = dt.date.fromisoformat
AS_OF = D('2026-11-08')


def feed(org, fid, end, disc=False, pref=39, pub='2026-10-01'):
    return {'organization_id': org, 'feed_id': fid, 'organization_name': org + '町', 'feed_name': fid + 'バス',
            'feed_pref_id': pref, 'feed_license': 'CC BY 4.0', 'latest_feed_start_date': '2026-04-01',
            'latest_feed_end_date': end, 'last_published_at': pub, 'feed_is_discontinued': disc}


DOC = {'code': 200, 'message': 'ok', 'body': [
    feed('a', 'gone', '2026-10-30'),
    feed('b', 'today', '2026-11-08'),
    feed('c', 'soon', '2026-11-28', pref=2),
    feed('d', 'fy', '2027-03-31'),
    feed('e', 'long', '2027-09-30'),
    feed('f', 'stopped', '2026-01-31', disc=True),
    feed('g', 'nodate', ''),
    {'organization_id': '', 'feed_id': 'x'},
]}


def run(*args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = G.main(list(args))
    return code, out.getvalue(), err.getvalue()


class Rating(unittest.TestCase):
    def test_band_edges(self):
        self.assertEqual([G.band(n) for n in (-1, 0, 7, 8, 30, 31, 60, 61)],
                         ['expired', 'ends_7', 'ends_7', 'ends_30', 'ends_30', 'ends_60', 'ends_60', 'later'])

    def test_fy_end(self):
        self.assertEqual(G.fy_end(D('2026-11-08')), D('2027-03-31'))
        self.assertEqual(G.fy_end(D('2027-03-31')), D('2027-03-31'))
        self.assertEqual(G.fy_end(D('2027-04-01')), D('2028-03-31'))

    def test_rate_all(self):
        rows = G.rate_all(G.feed_list(DOC), AS_OF)
        by = {r['feed_id']: r for r in rows}
        self.assertEqual(len(rows), 7)  # the row without organization_id is dropped
        self.assertEqual((by['gone']['status'], by['gone']['days_left']), ('expired', -9))
        self.assertEqual((by['today']['status'], by['today']['days_left']), ('ends_7', 0))
        self.assertEqual(by['soon']['status'], 'ends_30')
        self.assertEqual(by['soon']['pref_name'], '青森県')
        self.assertEqual(by['fy']['status'], 'later')
        self.assertTrue(by['fy']['ends_on_fy_end'])
        self.assertEqual(by['stopped']['status'], 'discontinued')
        self.assertEqual(by['nodate']['status'], 'no_end_date')
        self.assertEqual(rows[0]['feed_id'], 'gone')  # worst first
        s = G.summary(rows, AS_OF)
        self.assertEqual(s['by_status']['expired'], 1)
        self.assertEqual(s['ending_on_fy_end'], 1)
        self.assertEqual(s['ending_by_fy_end'], 4)  # gone, today, soon, fy

    def test_select(self):
        rows = G.rate_all(G.feed_list(DOC), AS_OF)
        self.assertEqual([r['feed_id'] for r in G.select(rows, within=60)], ['gone', 'today', 'soon'])
        self.assertEqual([r['feed_id'] for r in G.select(rows, grep='SOON')], ['soon'])
        self.assertEqual([r['feed_id'] for r in G.select(rows, pref='青森県')], ['soon'])
        self.assertEqual([r['feed_id'] for r in G.select(rows, pref='2')], ['soon'])
        self.assertEqual([r['feed_id'] for r in G.select(rows, org='d', feed='fy')], ['fy'])


class Coverage(unittest.TestCase):
    def detail(self, *spans):
        return {'body': {'gtfs_files': [{'rid': f'r{i}', 'from_date': a, 'to_date': b,
                                         'published_at': '2026-09-01T10:00:00+09:00'}
                                        for i, (a, b) in enumerate(spans)] + [{'rid': 'bad', 'from_date': 'x'}]}}

    def test_continuous(self):
        r = G.coverage(self.detail(('2026-10-01', '2026-10-31'), ('2026-11-01', '2026-11-30')), D('2026-11-08'))
        self.assertEqual((r['status'], r['covered_until'], r['days_left'], r['files']),
                         ('covered', '2026-11-30', 22, 2))
        self.assertEqual(r['gaps_ahead'], [])

    def test_gap_ahead(self):
        r = G.coverage(self.detail(('2026-10-01', '2026-10-31'), ('2026-11-05', '2026-12-31')), D('2026-10-15'))
        self.assertEqual(r['status'], 'covered')
        self.assertEqual(r['gaps_ahead'], [{'from': '2026-11-01', 'to': '2026-11-04', 'days': 4}])

    def test_inside_gap(self):
        r = G.coverage(self.detail(('2026-10-01', '2026-10-31'), ('2026-11-05', '2026-12-31')), D('2026-11-02'))
        self.assertEqual((r['status'], r['next_covered_from']), ('gap_now', '2026-11-05'))

    def test_expired_and_empty(self):
        r = G.coverage(self.detail(('2026-04-01', '2026-10-31')), D('2026-11-08'))
        self.assertEqual((r['status'], r['days_left'], r['last_covered_day']), ('expired', -8, '2026-10-31'))
        self.assertEqual(G.coverage({'body': {'gtfs_files': []}}, AS_OF)['status'], 'no_files')


class Snapshot(unittest.TestCase):
    def test_bundled_list(self):
        rows = G.snapshot_rows(G.SNAPSHOT, AS_OF)
        self.assertGreaterEqual(len(rows), 80)
        by = {(r['organization_id'], r['feed_id']): r for r in rows}
        r = by[('rokkashovillage', 'rokkasho-sharedtaxi')]
        self.assertEqual((r['status'], r['days_left'], r['latest_feed_end_date']), ('expired', -9, '2026-10-30'))
        self.assertTrue(all(x['days_left'] <= 60 for x in rows))

    def test_recomputed_for_a_later_day(self):
        rows = G.snapshot_rows(G.SNAPSHOT, D('2026-12-01'))
        by = {(r['organization_id'], r['feed_id']): r for r in rows}
        self.assertEqual(by[('nagadenbus', 'obuse-romango')]['status'], 'expired')


class Cli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, 'feeds.json')
        with open(self.path, 'w', encoding='utf-8') as fh:
            json.dump(DOC, fh, ensure_ascii=False)

    def tearDown(self):
        self.tmp.cleanup()

    def test_list_and_exit_codes(self):
        code, out, _ = run('--feeds-json', self.path, '--as-of', '2026-11-08')
        self.assertEqual(code, 0)
        self.assertEqual(len(out.strip().splitlines()), 3)
        code, out, _ = run('--feeds-json', self.path, '--as-of', '2026-11-08', '--org', 'e', '--json')
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)[0]['status'], 'later')
        code, _, _ = run('--feeds-json', self.path, '--as-of', '2026-11-08', '--org', 'zzz')
        self.assertEqual(code, 1)
        code, _, _ = run('--feeds-json', os.path.join(self.tmp.name, 'missing.json'))
        self.assertEqual(code, 2)

    def test_summary(self):
        code, out, _ = run('--feeds-json', self.path, '--as-of', '2026-11-08', '--summary')
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)['feeds'], 7)

    def test_snapshot_lookup_miss_explains(self):
        code, _, err = run('--as-of', '2026-11-08', '--org', 'no-such-org')
        self.assertEqual(code, 1)
        self.assertIn('not on the 2026-11-08 watch list', err)

    def test_detail_file(self):
        p = os.path.join(self.tmp.name, 'detail.json')
        with open(p, 'w', encoding='utf-8') as fh:
            json.dump({'body': {'gtfs_files': [{'from_date': '2026-10-01', 'to_date': '2026-10-31'},
                                               {'from_date': '2026-11-03', 'to_date': '2026-12-31'}]}}, fh)
        code, out, _ = run('--detail-json', p, '--as-of', '2026-10-20')
        self.assertEqual(code, 0)
        self.assertIn('gap ahead: 2026-11-01 .. 2026-11-02 (2 days', out)


class SkillFile(unittest.TestCase):
    def test_frontmatter(self):
        with open(os.path.join(SKILL, 'SKILL.md'), encoding='utf-8') as fh:
            text = fh.read()
        m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
        self.assertIsNotNone(m)
        meta = dict(line.split(': ', 1) for line in m.group(1).splitlines() if ': ' in line)
        self.assertEqual(meta['name'], 'gtfs-jp-expiry')
        self.assertEqual(meta['license'], 'Apache-2.0')
        self.assertLessEqual(len(meta['description']), 1024)
        # Compare lower case with lower case (run 248's version looked for 'AI' in lowered text and always failed).
        self.assertIn('made with ai agents', text.lower())
        self.assertIn('scripts/gtfs_jp_expiry.py', text)


if __name__ == '__main__':
    unittest.main()
