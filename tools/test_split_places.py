# Tests for split_places.py on small tables built here; every expected value was worked out by hand
# (an empty CSV with header 'a' and BOM is 6 bytes, each row 'xxxx' adds 6, so a limit of 18 holds two rows).
# MV2 of Munim, Inc. - Apache-2.0 license. Made with AI agents working in MV2's name.
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import split_places as sp  # noqa: E402

FEEDS_HEAD = 'organization_id,feed_id,organization_name,feed_name,pref_id,status,last_wed_median\r\n'
PUBLISHED = FEEDS_HEAD + ('o,A,事業者,路線A,1,ok,18:00\r\n'
                          'o,B,事業者,路線B,1,ok,19:00\r\n'
                          'o,C,事業者,路線C,13,ok,20:00\r\n'
                          'o,D,事業者,路線D,13,failed,\r\n'
                          'o,E,事業者,路線E,13,ok,17:00\r\n')
RERUN = FEEDS_HEAD + ('o,A,事業者,路線A,1,ok,18:00\r\n'
                      'o,B,事業者,路線B,1,ok,19:30\r\n'
                      'o,C,事業者,路線C,13,ok,20:00\r\n'
                      'o,D,事業者,路線D,13,failed,\r\n')
PLACES = ('organization_id,feed_id,pref_id,place,last_wed\r\n'
          'o,A,1,駅前,18:00\r\n'
          'o,A,1,病院前,17:10\r\n'
          'o,B,1,役場,19:30\r\n'
          'o,C,13,団地,20:00\r\n')


def write(folder, name, text):
    path = os.path.join(folder, name)
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        f.write(text)
    return path


class SplitPlacesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        self.published = write(d, 'published.csv', PUBLISHED)
        self.rerun = write(d, 'rerun.csv', RERUN)
        self.places = write(d, 'places.csv', PLACES)
        self.out = os.path.join(d, 'out')

    def tearDown(self):
        self.tmp.cleanup()

    def test_compare(self):
        kept, changed = sp.compare(sp.read_csv(self.published), sp.read_csv(self.rerun))
        self.assertEqual(kept, {('o', 'A'), ('o', 'C')})
        self.assertEqual([(c['feed_id'], c['reason'], c['columns']) for c in changed],
                         [('B', 'row_differs', 'last_wed_median'), ('D', 'not_read', ''),
                          ('E', 'missing_in_rerun', '')])

    def test_pref_code(self):
        self.assertEqual([sp.pref_code(v) for v in ('1', '13', '', None, 'x')], ['01', '13', '00', '00', '00'])

    def test_chunks(self):
        rows_ = [{'a': 'xxxx'}] * 3
        self.assertEqual(len(sp.to_csv(['a'], []).encode('utf-8')), 6)
        self.assertEqual([len(p) for p in sp.chunks(['a'], rows_, 18)], [2, 1])
        self.assertEqual([len(p) for p in sp.chunks(['a'], rows_, 1000)], [3])
        self.assertEqual(sp.chunks(['a'], [], 18), [[]])

    def test_split_names(self):
        rows_ = [{'organization_id': 'o', 'feed_id': 'A', 'pref_id': '1', 'a': 'xxxx'}] * 3
        files, index = sp.split(rows_, ['a'], {('o', 'A')}, 18)
        self.assertEqual(sorted(files), ['01-1.csv', '01-2.csv'])
        self.assertEqual([(i['file'], i['rows'], i['bytes']) for i in index], [('01-1.csv', 2, 18), ('01-2.csv', 1, 12)])

    def test_main(self):
        s = sp.main(['--places', self.places, '--rerun-feeds', self.rerun, '--published-feeds', self.published,
                     '--out', self.out])
        self.assertEqual(sorted(os.listdir(self.out)), ['01.csv', '13.csv', 'changed.csv', 'index.csv', 'split.json'])
        self.assertEqual((s['published_feeds'], s['kept_feeds'], s['changed_feeds']), (5, 2, 3))
        self.assertEqual(s['changed_by_reason'], {'row_differs': 1, 'not_read': 1, 'missing_in_rerun': 1})
        self.assertEqual((s['rows_in'], s['rows_out'], s['files']), (4, 3, 2))
        with open(os.path.join(self.out, '01.csv'), 'rb') as f:
            raw = f.read()
        self.assertTrue(raw.startswith(b'\xef\xbb\xbforganization_id,feed_id,pref_id,place,last_wed\r\n'))
        self.assertEqual([r['place'] for r in sp.read_csv(os.path.join(self.out, '01.csv'))], ['駅前', '病院前'])
        index = sp.read_csv(os.path.join(self.out, 'index.csv'))
        self.assertEqual([(i['pref_id'], i['file'], i['feeds'], i['rows']) for i in index],
                         [('01', '01.csv', '1', '2'), ('13', '13.csv', '1', '1')])
        self.assertEqual(int(index[0]['bytes']), len(raw))
        with open(os.path.join(self.out, 'split.json'), encoding='utf-8') as f:
            self.assertEqual(json.load(f)['rows_out'], 3)


if __name__ == '__main__':
    unittest.main()
