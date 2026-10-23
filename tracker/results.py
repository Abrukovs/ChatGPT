"""Provider extension point. No imported result claim can settle a prediction."""
from datetime import datetime, timezone
from typing import Protocol
from khl_auto_settle import events_for_day, assess, parse_market, MARKET_RE
from .model import RESULT_FIELDS
from .storage import RESULT_PATH, PATH, read_csv


class ResultProvider(Protocol):
    def verify(self, row: dict) -> dict | None: ...


class KHLProvider:
    def __init__(self):
        self.cache = {}
    def verify(self, row):
        if row.get('sport') != 'hockey' or not row.get('competition', '').upper().startswith(('KHL', 'КХЛ')):
            return None
        if row.get('category') == 'PASS' or row.get('role') != 'final' or not row.get('event_date'):
            return None
        decision = {'decision_id': row['id'], 'event': row['event'], 'market': row['market'], 'line': row['line']}
        match = MARKET_RE.fullmatch(row['market'].strip())
        names = row['event'].split(' - ')
        if not match or len(names) != 2:
            return None
        team = match.group(1).lower()
        if sum(team in (name.strip().lower(), name.strip().split()[0].lower()) for name in names if name.strip()) != 1:
            return None
        parsed = parse_market(decision)
        # Existing assessor is safe for half-lines. Integer equality is PUSH and must not be called a LOSS.
        if not parsed or parsed[2] % 1 != .5:
            return None
        day = row['event_date']
        if day not in self.cache:
            self.cache[day] = events_for_day(day)
        candidate = assess(decision, self.cache[day])
        if not candidate:
            return None
        return {'id': row['id'], 'status': candidate['result_status'].upper(), 'score': candidate['final_score'],
                'source_url': candidate['result_source_url'], 'notes': candidate['settlement_notes'],
                'verified_at': datetime.now(timezone.utc).isoformat()}


def verify_pending(rows, providers=None):
    verified, errors = [], []
    providers = providers if providers is not None else [KHLProvider()]
    for row in rows:
        if row.get('status') != 'PENDING' or row.get('source') in ('predictions.csv', 'daily_decisions.csv'):
            continue
        for provider in providers:
            try:
                result = provider.verify(row)
                if result:
                    verified.append(result); break
            except Exception:
                errors.append(f"{row['id']}: источник не подтвердил результат; запись оставлена PENDING")
    return verified, errors


def save_results(store, results):
    predictions = {r['id']: r for r in read_csv(store.read(PATH))}
    for r in results:
        original = predictions.get(r.get('id'), {})
        if not original or original.get('category') == 'PASS' or original.get('role') != 'final':
            raise ValueError('Результат не соответствует сохранённому итоговому прогнозу')
        if (r.get('status') not in ('WIN', 'LOSS', 'PUSH', 'VOID') or not r.get('score')
                or not r.get('source_url', '').startswith('https://') or not r.get('verified_at') or not r.get('notes')):
            raise ValueError('Результат не имеет достаточных подтверждений')
    return store.append(RESULT_PATH, results, RESULT_FIELDS)
