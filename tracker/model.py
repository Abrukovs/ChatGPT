import hashlib
import json
import re
import unicodedata
from datetime import datetime

FIELDS = ['id', 'forecast_date', 'event_date', 'sport', 'competition', 'event',
          'market', 'line', 'odds', 'probability', 'category', 'role', 'arguments',
          'risks', 'source', 'source_text', 'reported_status', 'status', 'review_notes']
SPORTS = {'football', 'hockey', 'basketball', 'tennis'}
CATEGORIES = {'A', 'B+', 'B', 'PASS'}
ROLES = {'final', 'alternative', 'preliminary'}
RESULT_FIELDS = ['id', 'status', 'score', 'source_url', 'notes', 'verified_at']


def norm(value):
    value = unicodedata.normalize('NFKC', str(value or '')).casefold().replace('ё', 'е')
    value = value.replace('—', '-').replace('–', '-')
    return re.sub(r'\s+', ' ', value).strip()


def number(value):
    return str(value or '').strip().replace(',', '.')


def identity(row):
    """Category/source never let a revised recommendation overwrite an original."""
    return hashlib.sha256(json.dumps([norm(row.get(k)) for k in
        ('event_date', 'forecast_date', 'sport', 'event', 'market', 'line')] +
        ([norm(row.get('source_text'))] if not row.get('event_date') and not row.get('forecast_date') else []),
        ensure_ascii=False).encode()).hexdigest()[:24]


def validate(row):
    errors = []
    for key in ('forecast_date', 'event_date'):
        value = str(row.get(key, '')).strip()
        if value:
            try:
                datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                errors.append('Дата должна иметь формат ГГГГ-ММ-ДД: ' + key)
    for key, choices in [('sport', SPORTS), ('category', CATEGORIES), ('role', ROLES)]:
        if row.get(key) not in choices:
            errors.append('Проверьте поле ' + key)
    for key in ('event',) + (() if row.get('category') == 'PASS' else ('market',)):
        if not str(row.get(key, '')).strip():
            errors.append('Не заполнено поле ' + key)
    for key, low, high in [('odds', 1, 10000), ('probability', 0, 100)]:
        if str(row.get(key, '')).strip():
            try:
                value = float(number(row[key]))
                if not low < value <= high:
                    raise ValueError()
            except (ValueError, TypeError):
                errors.append('Некорректное число: ' + key)
    if row.get('role') != 'final':
        errors.append('Это альтернатива или рассуждение; подтвердите итоговый выбор вручную')
    return errors


def prepare(row):
    cleaned = {k: str(row.get(k, '') or '').strip() for k in FIELDS}
    for k in ('line', 'odds', 'probability'):
        cleaned[k] = number(cleaned[k])
    cleaned['status'] = 'PENDING'  # Imported claims are not verified results.
    cleaned['id'] = identity(cleaned)
    return cleaned
