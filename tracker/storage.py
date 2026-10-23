"""Append-only local/GitHub storage with content-SHA compare and swap."""
import base64
import csv
import io
import json
import os
from pathlib import Path
from filelock import FileLock
import requests
from .model import FIELDS, RESULT_FIELDS, identity, prepare, validate

PATH = 'data/imported_predictions.csv'
RESULT_PATH = 'data/imported_results.csv'


def read_csv(text):
    return list(csv.DictReader(io.StringIO(text.lstrip('\ufeff')))) if text.strip() else []


def encode_csv(rows, fields):
    f = io.StringIO(newline='')
    w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    return f.getvalue()


def append_text(old, rows, fields):
    if old and next(csv.reader(io.StringIO(old.lstrip('\ufeff'))), []) != fields:
        raise ValueError('Неожиданные столбцы журнала; запись остановлена')
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=fields, extrasaction='ignore')
    if not old:
        writer.writeheader()
    writer.writerows(rows)
    return old + ('' if not old or old.endswith('\n') else '\n') + out.getvalue()


class LocalStore:
    def __init__(self, root):
        self.root = Path(root)
    def read(self, path):
        p = self.root / path
        return p.read_bytes().decode('utf-8') if p.exists() else ''
    def append(self, path, records, fields):
        p = self.root / path; p.parent.mkdir(parents=True, exist_ok=True)
        with FileLock(str(p) + '.lock', timeout=10):
            old = self.read(path); existing = {r['id'] for r in read_csv(old)}
            new = []
            for row in records:
                if row['id'] not in existing:
                    new.append(row); existing.add(row['id'])
            if not new:
                return 0
            text = append_text(old, new, fields)
            tmp = p.with_suffix('.tmp'); tmp.write_bytes(text.encode('utf-8')); os.replace(tmp, p)
            if self.read(path) != text:
                raise ValueError('Не удалось подтвердить локальное сохранение')
            return len(new)


class GitHubStore:
    def __init__(self, token='', repo='Abrukovs/ChatGPT', branch='main'):
        if repo != 'Abrukovs/ChatGPT':
            raise ValueError('Эта версия настроена только на Abrukovs/ChatGPT')
        self.repo, self.branch = repo, branch
        self.session = requests.Session()
        self.session.headers.update({'Accept': 'application/vnd.github+json', 'User-Agent': 'SportsJournal/1.0'})
        if token:
            self.session.headers['Authorization'] = 'Bearer ' + token
    def request(self, method, path, **kwargs):
        try:
            return self.session.request(method, f'https://api.github.com/repos/{self.repo}/contents/{path}',
                                        timeout=(5, 25), **kwargs)
        except requests.RequestException:
            raise ValueError('Сеть GitHub недоступна. Повторите позже; токен не выводится в ошибки') from None
    def get(self, path):
        r = self.request('GET', path, params={'ref': self.branch})
        if r.status_code == 404:
            return '', None
        if r.status_code != 200:
            raise ValueError(f'GitHub: код {r.status_code}. Проверьте доступ, лимит запросов и ветку')
        try:
            obj = r.json()
            if obj.get('encoding') != 'base64':
                raise ValueError()
            return base64.b64decode(obj['content']).decode('utf-8'), obj['sha']
        except (KeyError, ValueError, TypeError):
            raise ValueError('GitHub вернул неподдерживаемый файл (возможно, больше 1 МБ)') from None
    def read(self, path):
        return self.get(path)[0]
    def append(self, path, records, fields):
        if path not in (PATH, RESULT_PATH):
            raise ValueError('Запись разрешена только в новые журналы импорта')
        for attempt in range(3):
            old, sha = self.get(path)
            existing = {r['id'] for r in read_csv(old)}
            new = []
            for row in records:
                if row['id'] not in existing:
                    new.append(row); existing.add(row['id'])
            if not new:
                return 0
            content = append_text(old, new, fields)
            payload = {'message': f'Append {len(new)} reviewed journal records', 'branch': self.branch,
                       'content': base64.b64encode(content.encode()).decode()}
            if sha:
                payload['sha'] = sha
            r = self.request('PUT', path, json=payload)
            if r.status_code in (409, 422):
                continue  # Fetch fresh SHA before retry; never overwrite a racing writer.
            if r.status_code not in (200, 201):
                raise ValueError(f'GitHub не сохранил файл: код {r.status_code}. Нужен Contents: Read and write')
            verified = {v['id']: v for v in read_csv(self.read(path))}
            if not all(verified.get(v['id']) == {k: str(v.get(k, '')) for k in fields} for v in new):
                raise ValueError('Запрос принят, но проверка сохранения не пройдена. Обновите журнал перед повтором')
            return len(new)
        raise ValueError('Конфликт параллельной записи. Данные не перезаписаны; обновите журнал и повторите')


def save_predictions(store, rows, known=()):
    clean, seen = [], {identity(r) for r in known}
    for row in rows:
        row = prepare(row)
        errors = validate(row)
        if errors:
            raise ValueError('; '.join(errors))
        if row['id'] not in seen:
            clean.append(row); seen.add(row['id'])
    return store.append(PATH, clean, FIELDS) if clean else 0
