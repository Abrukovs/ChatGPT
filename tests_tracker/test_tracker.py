import base64
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from tracker.parser import parse_text, parse_file
from tracker.model import prepare, validate, FIELDS
from tracker.storage import LocalStore, GitHubStore, save_predictions, read_csv, encode_csv, PATH
from tracker.journal import journal, stats, safe_export
from tracker.results import KHLProvider, save_results
from tracker.share import fetch_share

ROOT = Path(__file__).resolve().parents[1]


def pick(**kwargs):
    row = {'forecast_date': '2026-10-23', 'event_date': '2026-10-23', 'sport': 'football',
           'competition': 'Ligue 1', 'event': 'Брест — Ницца', 'market': 'Ницца ИТМ 1.5',
           'line': '1.5', 'odds': '1.53', 'probability': '69', 'category': 'B', 'role': 'final'}
    row.update(kwargs)
    return prepare(row)


class ParserTests(unittest.TestCase):
    def test_user_real_example_text(self):
        rows = parse_file('example.txt', (ROOT / 'examples/predictions.txt').read_bytes())
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual((r['event'], r['odds'], r['line'], r['probability'], r['category'], r['role']),
                         ('Брест — Ницца', '1.53', '1.5', '69', 'B', 'final'))
        self.assertFalse(validate(r))
    def test_csv_and_json(self):
        for suffix in ('csv', 'json'):
            rows = parse_file('example.' + suffix, (ROOT / ('examples/predictions.' + suffix)).read_bytes())
            self.assertEqual(rows[0]['event'], 'Брест — Ницца')
            self.assertFalse(validate(rows[0]))
    def test_real_final_table_with_missing_dates(self):
        text = '''Итоговая сравнительная таблица
| Место | Матч | Лучший рассмотренный рынок | Вероятность | Категория |
| --- | --- | --- | --- | --- |
| 1 | Брест — Ницца | Ницца ИТМ 1,5 · 1.53 | 69% | 🟡 B |
| 2 | Витория — Маритиму | П1 · 1.60 | 58% | 🟠 PASS |'''
        rows = parse_text(text)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]['category'], 'PASS')
        self.assertEqual(rows[0]['event_date'], '')
        self.assertIn('Дата неизвестна', rows[0]['review_notes'])
    def test_alternative_not_final_from_other_heading(self):
        text = '''Итоговая таблица
| Матч | Рынок | Категория |
| --- | --- | --- |
| A — B | П1 | B |
Альтернативные рынки
| Матч | Рынок | Категория |
| --- | --- | --- |
| A — B | ТБ2.5 | B |'''
        rows = parse_text(text)
        self.assertEqual([r['role'] for r in rows], ['final', 'alternative'])
        self.assertTrue(validate(rows[1]))
    def test_prose_is_manual_not_guessed(self):
        r = parse_text('Сегодня, возможно, стоит посмотреть победу СКА за 1.5')[0]
        self.assertEqual(r['event'], '')
        self.assertEqual(r['odds'], '')
        self.assertEqual(r['event_date'], '')
    def test_reported_win_is_not_verified(self):
        r = parse_file('p.json', json.dumps({'event':'A - B', 'status':'WIN'}).encode())[0]
        self.assertEqual(r['status'], 'PENDING')
        self.assertEqual(r['reported_status'], 'WIN')
    def test_chatgpt_branch_and_author(self):
        conv = {'title':'test', 'current_node':'final', 'mapping':{
            'user': {'parent':None, 'message':{'author':{'role':'user'},'content':{'parts':['Матч: FAKE - PICK']}}},
            'final': {'parent':'user', 'message':{'create_time':1792756800,'author':{'role':'assistant'},'content':{'parts':['Матч: A - B\nРынок: П1\nКатегория: B']}}},
            'other': {'parent':'user', 'message':{'author':{'role':'assistant'},'content':{'parts':['Матч: WRONG - BRANCH']}}}}}
        rows = parse_file('conversations.json', json.dumps([conv]).encode())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['event'], 'A - B')
    def test_invalid_exports_rejected(self):
        for content in ('[5]', '{bad', '{"mapping":{}}'):
            with self.assertRaises(ValueError):
                parse_file('bad.json', content.encode())
    def test_semicolon_csv(self):
        r = parse_file('p.csv', 'матч;рынок;категория\nA - B;П1;B'.encode())[0]
        self.assertEqual(r['event'], 'A - B')
    def test_pass_without_selected_market(self):
        self.assertFalse(validate(pick(category='PASS', market='')))
    def test_unknown_dates_export_reimport_is_duplicate(self):
        r=pick(forecast_date='',event_date='',source_text='original fragment')
        imported=parse_file('journal.csv', encode_csv([r], FIELDS).encode())[0]
        self.assertEqual(r['id'], imported['id'])
    def test_100pct_and_bad_numbers(self):
        self.assertFalse(validate(pick(probability='100')))
        self.assertTrue(validate(pick(probability='NaN')))
        self.assertTrue(validate(pick(odds='1.0')))
    def test_two_labeled_blocks_preserve_dates(self):
        text = (ROOT / 'examples/predictions.txt').read_text()
        rows = parse_text(text + '\n' + text.replace('2026-10-23', '2026-10-24').replace('Брест', 'Лилль'))
        self.assertEqual([r['forecast_date'] for r in rows], ['2026-10-23', '2026-10-24'])


class StoreTests(unittest.TestCase):
    def test_atomic_append_dedup_and_immutable(self):
        with tempfile.TemporaryDirectory() as d:
            s = LocalStore(d)
            self.assertEqual(save_predictions(s, [pick(), pick()]), 1)
            old = s.read(PATH)
            self.assertEqual(save_predictions(s, [pick(category='A')]), 0)
            self.assertEqual(old, s.read(PATH))
            self.assertEqual(save_predictions(s, [pick(event='Лилль — Ницца')]), 1)
            self.assertTrue(s.read(PATH).startswith(old))
    def test_no_partial_save_on_invalid_batch(self):
        with tempfile.TemporaryDirectory() as d:
            s = LocalStore(d)
            with self.assertRaises(ValueError):
                save_predictions(s, [pick(), pick(sport='unknown')])
            self.assertEqual(s.read(PATH), '')
    def test_legacy_files_not_changed(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ('predictions.csv','daily_decisions.csv','settlements.csv'):
                (Path(d)/name).write_bytes((ROOT/name).read_bytes())
            s=LocalStore(d); before={p.name:p.read_bytes() for p in Path(d).glob('*.csv')}
            self.assertGreater(len(journal(s)), 0)
            save_predictions(s, [pick()])
            self.assertEqual(before, {name:(Path(d)/name).read_bytes() for name in before})
    def test_unknown_dates_are_allowed_after_review(self):
        self.assertFalse(validate(pick(forecast_date='', event_date='')))
    def test_bad_header_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/PATH; p.parent.mkdir(); p.write_text('id,wrong\n')
            with self.assertRaises(ValueError):
                save_predictions(LocalStore(d), [pick()])
    def test_sha_conflict_reloads_and_preserves_concurrent_row(self):
        store=GitHubStore('test'); other=pick(event='Другая — Команда')
        concurrent=encode_csv([other], FIELDS)
        final=encode_csv([other, pick()], FIELDS)
        store.get=Mock(side_effect=[('', None), (concurrent, 'sha2'), (final, 'sha3')])
        store.request=Mock(side_effect=[Mock(status_code=409), Mock(status_code=200)])
        self.assertEqual(save_predictions(store, [pick()]), 1)
        payload=store.request.call_args.kwargs['json']
        self.assertEqual(payload['sha'], 'sha2')
        self.assertEqual(len(read_csv(base64.b64decode(payload['content']).decode())), 2)
    def test_unverified_write_not_reported_as_success(self):
        s=GitHubStore('test'); s.get=Mock(return_value=('', None)); s.request=Mock(return_value=Mock(status_code=200))
        with self.assertRaisesRegex(ValueError, 'проверка сохранения'):
            save_predictions(s, [pick()])
    def test_github_denied(self):
        s=GitHubStore('test'); s.request=Mock(return_value=Mock(status_code=403))
        with self.assertRaisesRegex(ValueError, '403'):
            s.read(PATH)
    def test_server_side_path_allowlist(self):
        with self.assertRaises(ValueError):
            GitHubStore('test').append('predictions.csv', [pick()], FIELDS)


class ResultTests(unittest.TestCase):
    def test_khl_uses_existing_assessor(self):
        r=pick(sport='hockey',competition='KHL',event='SKA Saint Petersburg - Sibir Novosibirsk',
               market='SKA team total under 3.5 goals in regulation',line='3.5')
        game={'team_a':{'name':'SKA'},'team_b':{'name':'Sibir'},'game_state_key':'finished','stage_id':407,
              'khl_id':902168,'scores':{'first_period':'4:3','second_period':'1:0','third_period':'1:0'}}
        with patch('tracker.results.events_for_day',return_value=[game]):
            self.assertEqual(KHLProvider().verify(r)['status'], 'LOSS')
        with patch('tracker.results.events_for_day',return_value=[game,game]):
            self.assertIsNone(KHLProvider().verify(r))
    def test_integer_totals_not_settled(self):
        r=pick(sport='hockey',competition='KHL',event='SKA - Sibir',market='SKA team total under 3 goals in regulation',line='3')
        self.assertIsNone(KHLProvider().verify(r))
    def test_missing_date_and_unsupported_market_remain_pending(self):
        self.assertIsNone(KHLProvider().verify(pick(sport='hockey',competition='KHL',event_date='')))
        self.assertIsNone(KHLProvider().verify(pick()))
    def test_settlement_requires_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                save_results(LocalStore(d), [{'id':'fake','status':'WIN'}])
    def test_statistics_excludes_pass_pending_and_void_from_winrate(self):
        rows=[pick(), pick(category='PASS'), pick(), pick(), pick()]
        for r,status in zip(rows,['WIN','WIN','PENDING','LOSS','VOID']): r['status']=status
        s=stats(rows)
        self.assertEqual((s['Прогнозов'],s['Рассчитано'],s['WIN %']), (4,3,50))
    def test_verified_settlement_does_not_change_prediction(self):
        with tempfile.TemporaryDirectory() as d:
            store=LocalStore(d); r=pick(); save_predictions(store,[r]); old=store.read(PATH)
            result={'id':r['id'],'status':'WIN','score':'0:0','source_url':'https://example.org/result',
                    'notes':'Test fixture only','verified_at':'2026-10-24T12:00:00+00:00'}
            self.assertEqual(save_results(store,[result]),1)
            self.assertEqual(save_results(store,[result]),0)
            self.assertEqual(store.read(PATH),old)
            self.assertEqual(journal(store)[0]['status'],'WIN')
    def test_formula_injection_export(self):
        self.assertEqual(safe_export([{'event':'=WEBSERVICE("x")'}])[0]['event'][0], "'")


class ShareTests(unittest.TestCase):
    def test_ssrf_urls_rejected_before_network(self):
        for url in ['http://127.0.0.1', 'https://chatgpt.com.evil/share/12345678',
                    'https://chatgpt.com/share/12345678?x=1', 'https://user@chatgpt.com/share/12345678']:
            with self.assertRaises(ValueError): fetch_share(url)
    def test_no_auth_bypass(self):
        r=Mock(status_code=403); r.__enter__=Mock(return_value=r); r.__exit__=Mock(return_value=False)
        with patch('tracker.share.requests.get', return_value=r) as get:
            with self.assertRaisesRegex(ValueError, 'Вставьте текст'): fetch_share('https://chatgpt.com/share/12345678')
            self.assertFalse(get.call_args.kwargs['allow_redirects'])
    def test_accessible_assistant_only(self):
        r=Mock(status_code=200); r.__enter__=Mock(return_value=r); r.__exit__=Mock(return_value=False)
        r.iter_content.return_value=[b'<div data-message-author-role="user">not a pick</div><div data-message-author-role="assistant">final text</div>']
        with patch('tracker.share.requests.get', return_value=r):
            self.assertEqual(fetch_share('https://chatgpt.com/share/12345678'), 'final text')
