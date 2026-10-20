"""One immutable decision per Riga calendar date; settlements are separate."""
import csv
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

FIELDS = ['date_riga','decision_id','decision','sport','competition','event','market','line','reference_odds','estimated_probability_pct','grade','rationale','risks','selected_at_riga']
SETTLEMENT_FIELDS = ['decision_id','result_status','final_score','settled_at_riga','result_source_url','settlement_notes']
SPORTS = {'hockey','basketball','tennis'}
GRADES = {'A','B+','B'}
RESULTS = {'Pending','Win','Loss','Push/Refund','Void/Cancelled','Unable to verify'}


def _read(path, fields):
    if not path.exists():
        return []
    with path.open(newline='', encoding='utf-8') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != fields:
            raise ValueError(f'Unexpected CSV columns in {path.name}')
        return list(reader)


def _write(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def add_decision(path, record):
    """Append one decision for a Riga date, returning 'added' or 'duplicate'."""
    if set(record) - set(FIELDS):
        raise ValueError('Unknown fields')
    for field in ['date_riga','decision_id','decision','selected_at_riga']:
        if not str(record.get(field, '')).strip():
            raise ValueError(f'Missing {field}')
    selected = datetime.fromisoformat(record['selected_at_riga'])
    if selected.tzinfo is None or selected.astimezone(ZoneInfo('Europe/Riga')).date().isoformat() != record['date_riga']:
        raise ValueError('Decision date must match Riga local time')
    if record['decision'] not in {'PICK','PASS'}:
        raise ValueError('Decision must be PICK or PASS')
    if record['decision'] == 'PICK':
        if record.get('sport') not in SPORTS or record.get('grade') not in GRADES:
            raise ValueError('Invalid sport or grade')
        if not all(str(record.get(k, '')).strip() for k in ('competition','event','market','estimated_probability_pct')):
            raise ValueError('Incomplete pick')
        try:
            probability = float(record['estimated_probability_pct'])
        except (ValueError, TypeError) as exc:
            raise ValueError('Invalid probability') from exc
        if not 0 < probability < 100:
            raise ValueError('Invalid probability')
    else:
        if any(str(record.get(k, '')).strip() for k in ('sport','competition','event','market','line','reference_odds','estimated_probability_pct','grade')):
            raise ValueError('PASS cannot include a selected market')
    path = Path(path)
    rows = _read(path, FIELDS)
    existing = [r for r in rows if r['date_riga'] == record['date_riga'] or r['decision_id'] == record['decision_id']]
    if existing:
        expected = {k: str(record.get(k, '')) for k in FIELDS}
        if len(existing) == 1 and existing[0] == expected:
            return 'duplicate'
        raise ValueError('A different decision already exists for this date or ID')
    rows.append({k: str(record.get(k, '')) for k in FIELDS})
    _write(path, FIELDS, rows)
    return 'added'


def settle_decision(decisions_path, settlements_path, record):
    """Settle a known PICK without changing original decision fields."""
    if set(record) - set(SETTLEMENT_FIELDS):
        raise ValueError('Unknown settlement fields')
    if record.get('result_status') not in RESULTS or record['result_status'] == 'Pending':
        raise ValueError('Invalid final status')
    if not record.get('result_source_url') or not record.get('settled_at_riga'):
        raise ValueError('Settlement requires source and timestamp')
    decisions = _read(Path(decisions_path), FIELDS)
    if not any(r['decision_id'] == record.get('decision_id') and r['decision'] == 'PICK' for r in decisions):
        raise ValueError('Unknown PICK decision')
    settlements_path = Path(settlements_path)
    rows = _read(settlements_path, SETTLEMENT_FIELDS)
    new_row = {k: str(record.get(k, '')) for k in SETTLEMENT_FIELDS}
    for old in rows:
        if old['decision_id'] == new_row['decision_id']:
            if old == new_row:
                return 'duplicate'
            raise ValueError('Settlement already exists; review manually')
    rows.append(new_row)
    _write(settlements_path, SETTLEMENT_FIELDS, rows)
    return 'added'
