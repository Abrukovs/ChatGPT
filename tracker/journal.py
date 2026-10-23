from .model import prepare
from .storage import PATH, RESULT_PATH, read_csv

STATUS = {'Win': 'WIN', 'Loss': 'LOSS', 'Pending': 'PENDING', 'Push/Refund': 'PUSH',
          'Void/Cancelled': 'VOID', 'NOT_APPLICABLE': 'PENDING'}


def journal(store):
    rows = []
    settlements = {r['decision_id']: r for r in read_csv(store.read('settlements.csv'))}
    for r in read_csv(store.read('predictions.csv')):
        item = prepare({'forecast_date': r.get('selected_at_riga', '')[:10],
            'event_date': r.get('scheduled_start_riga', '')[:10], 'sport': r['sport'],
            'competition': r['competition'], 'event': r['event'], 'market': r['market'],
            'line': r['line'], 'odds': r['reference_odds'], 'probability': r['estimated_probability_pct'],
            'category': r['grade'], 'role': 'final', 'arguments': r['rationale'], 'risks': r['risks'],
            'source': 'predictions.csv'})
        item['id'] = r['prediction_id']
        # Existing verified statuses remain readable; original files are untouched.
        item['status'] = STATUS.get(r['result_status'], r['result_status'].upper() or 'PENDING')
        item['score'] = r.get('final_score', '')
        rows.append(item)
    for r in read_csv(store.read('daily_decisions.csv')):
        item = prepare({'forecast_date': r['date_riga'], 'sport': r['sport'], 'competition': r['competition'],
            'event': r['event'], 'market': r['market'], 'line': r['line'], 'odds': r['reference_odds'],
            'probability': r['estimated_probability_pct'], 'category': r['grade'] if r['decision'] == 'PICK' else 'PASS',
            'arguments': r['rationale'], 'risks': r['risks'], 'role': 'final', 'source': 'daily_decisions.csv'})
        item['id'] = r['decision_id']
        result = settlements.get(r['decision_id'], {})
        item['status'] = STATUS.get(result.get('result_status'), 'PENDING')
        item['score'] = result.get('final_score', '')
        # A decision date is NOT silently promoted to an event date.
        rows.append(item)
    results = {r['id']: r for r in read_csv(store.read(RESULT_PATH))}
    for r in read_csv(store.read(PATH)):
        result = results.get(r['id'], {})
        r['status'] = result.get('status', 'PENDING')
        r['score'] = result.get('score', '')
        rows.append(r)
    return rows


def stats(rows):
    picks = [r for r in rows if r.get('category') != 'PASS' and r.get('role') == 'final']
    settled = [r for r in picks if r['status'] in ('WIN', 'LOSS', 'PUSH', 'VOID')]
    decided = [r for r in settled if r['status'] in ('WIN', 'LOSS')]
    wins = sum(r['status'] == 'WIN' for r in decided)
    priced = []
    for r in settled:
        try:
            odds = float(r.get('odds', ''))
            if odds > 1 and r['status'] != 'VOID':
                priced.append(odds - 1 if r['status'] == 'WIN' else -1 if r['status'] == 'LOSS' else 0)
        except (TypeError, ValueError):
            pass
    return {'Прогнозов': len(picks), 'Рассчитано': len(settled), 'WIN': wins,
            'LOSS': len(decided) - wins, 'WIN %': round(100 * wins / len(decided), 1) if decided else None,
            'ROI модели, %': round(100 * sum(priced) / len(priced), 1) if priced else None,
            'С кэфом для ROI': len(priced)}


def safe_export(rows):
    # Spreadsheet formula injection applies to CSV AND XLSX.
    return [{k: ("'" + v if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@')) else v)
             for k, v in r.items()} for r in rows]
