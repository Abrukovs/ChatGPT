"""Deterministic extraction. Missing information remains empty; every import is reviewed."""
import csv
import io
import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
from .model import FIELDS, prepare, validate

ALIASES = {
 'forecast_date': ['forecast_date', 'дата прогноза', 'selected_at_riga', 'date_riga'],
 'event_date': ['event_date', 'дата матча', 'scheduled_start_riga'],
 'sport': ['sport', 'вид спорта', 'спорт'],
 'competition': ['competition', 'чемпионат', 'турнир'],
 'event': ['event', 'матч', 'команды'],
 'market': ['market', 'рынок', 'лучший рассмотренный рынок', 'ставка', 'прогноз', 'исход'],
 'line': ['line', 'линия'], 'odds': ['odds', 'коэффициент', 'кэф', 'reference_odds'],
 'probability': ['probability', 'вероятность', 'estimated_probability_pct'],
 'category': ['category', 'категория', 'grade'], 'role': ['role', 'тип'],
 'arguments': ['arguments', 'аргументы', 'аргументы за', 'rationale', 'обоснование'],
 'risks': ['risks', 'риски', 'главные риски'],
 'reported_status': ['reported_status', 'status', 'result_status', 'результат'],
 'source_text': ['source_text', 'исходный фрагмент'],
}
KEYS = {a.casefold(): k for k, names in ALIASES.items() for a in names}
SPORT_NAMES = {'футбол': 'football', 'хоккей': 'hockey', 'баскетбол': 'basketball', 'теннис': 'tennis'}


def clean(s):
    return re.sub(r'[*`]', '', str(s)).strip()


def date_only(s):
    s = str(s).strip()
    if re.match(r'^\d{4}-\d{2}-\d{2}(?:$|[T ])', s):
        return s[:10]
    if re.fullmatch(r'\d{2}\.\d{2}\.\d{4}', s):
        return datetime.strptime(s, '%d.%m.%Y').date().isoformat()
    return s  # Never resolve 'today' using the import date.


def from_mapping(obj, source='', context=None):
    row = dict(context or {})
    for key, value in obj.items():
        canonical = KEYS.get(clean(key).casefold())
        if canonical:
            row[canonical] = str(value) if value is not None else ''
    row['sport'] = SPORT_NAMES.get(clean(row.get('sport', '')).casefold(), clean(row.get('sport', '')).lower())
    category = re.search(r'\b(PASS|B\+|B|A)(?!\w)', clean(row.get('category', '')).upper())
    row['category'] = category.group(1) if category else ''
    for key in ('forecast_date', 'event_date'):
        row[key] = date_only(row.get(key, ''))
    row['probability'] = clean(row.get('probability', '')).replace('%', '').strip()
    row['market'] = clean(row.get('market', ''))
    # Only explicit odds markers, never interpret a total line as odds.
    odds = re.search(r'(?:[·@]|к(?:эф|оэфф(?:ициент)?)\.?\s*[:=]?)\s*(\d+[.,]\d+)', row['market'], re.I)
    if odds and not row.get('odds'):
        row['odds'] = odds.group(1)
        row['market'] = row['market'][:odds.start()].strip()
    line = re.search(r'(?:[Тт][БбМм]|[Ии][Тт][БбМм]|[Фф][12]?|(?:тотал|фора)\s*(?:больше|меньше)?)[\s(]*([+-]?\d+(?:[.,]\d+)?)', row['market'])
    if line and not row.get('line'):
        row['line'] = line.group(1)
    role = row.get('role', '')
    row['role'] = {'итог': 'final', 'окончательная': 'final', 'альтернатива': 'alternative', 'предварительная': 'preliminary'}.get(role, role or 'preliminary')
    row['source'] = source
    row['source_text'] = row.get('source_text') or (json.dumps(obj, ensure_ascii=False) if isinstance(obj, dict) else str(obj))
    row = prepare(row)
    row['review_notes'] = '; '.join(validate(row) + ['Дата неизвестна: ' + k for k in ('forecast_date', 'event_date') if not row[k]])
    return row


def parse_text(text, source='Вставленный текст', context=None):
    text = BeautifulSoup(text, 'html.parser').get_text('\n') if '<html' in text.lower() else text
    lines = text.splitlines()
    output, headers, block = [], None, {}
    section_role = 'preliminary'
    table_context = dict(context or {})
    def flush():
        nonlocal block
        if block and ('event' in block or 'market' in block):
            output.append(from_mapping(block, source, context))
        block = {}
    # Markdown tables plus explicit labeled blocks are supported without a language model.
    for line in lines:
        if re.search(r'альтернатив|предварительн|рассуждени', line, re.I) and ':' not in line and '|' not in line:
            section_role = 'alternative' if 'альтернатив' in line.lower() else 'preliminary'
        elif re.search(r'итоговая таблица|итоговая сравнительная таблица|окончательные ставки|финальный выбор', line, re.I) and '|' not in line:
            section_role = 'final'
        if line.strip().startswith('|'):
            cells = [clean(c) for c in line.strip().strip('|').split('|')]
            mapped = [KEYS.get(c.casefold(), '') for c in cells]
            if 'event' in mapped and 'market' in mapped:
                table_context.update({k: v for k, v in block.items() if k in ('forecast_date', 'event_date', 'sport', 'competition')})
                flush(); headers = mapped; continue
            if headers and len(cells) == len(headers) and not all(re.fullmatch(r'[:\-\s]*', c) for c in cells):
                obj = {k: v for k, v in zip(headers, cells) if k}
                obj.setdefault('role', section_role)
                output.append(from_mapping(obj, source, table_context))
            continue
        headers = None
        m = re.match(r'^\s*(?:[-•]\s*)?([^:]{1,55}):\s*(.*)$', clean(line))
        if m:
            key = KEYS.get(m.group(1).casefold())
            if key:
                if (key == 'event' and 'event' in block) or (key == 'forecast_date' and 'event' in block):
                    flush()
                block[key] = m.group(2)
    flush()
    if not output and text.strip():
        row = from_mapping({}, source, context)
        row['source_text'] = text
        row['review_notes'] = 'Формат не распознан. Заполните запись вручную. ' + row['review_notes']
        output.append(row)
    return output


def conversation_messages(conv):
    """Follow current branch only; user messages are never treated as assistant picks."""
    mapping = conv.get('mapping', {})
    current = conv.get('current_node')
    if not current or current not in mapping:
        raise ValueError('В экспорте не указана текущая ветка беседы; вставьте итоговый ответ текстом')
    nodes, seen = [], set()
    while current:
        if current in seen or current not in mapping:
            raise ValueError('Повреждённая цепочка сообщений экспорта')
        seen.add(current); node = mapping[current]; nodes.append(node)
        current = node.get('parent')
    for node in reversed(nodes):
        msg = node.get('message') or {}
        if msg.get('author', {}).get('role') != 'assistant':
            continue
        parts = msg.get('content', {}).get('parts', [])
        body = '\n'.join(p for p in parts if isinstance(p, str))
        stamp = msg.get('create_time')
        day = datetime.fromtimestamp(stamp, ZoneInfo('Europe/Moscow')).date().isoformat() if isinstance(stamp, (int, float)) else ''
        yield body, day


def parse_file(name, data):
    if len(data) > 25 * 1024 * 1024:
        raise ValueError('Файл больше 25 МБ. Разделите экспорт на части')
    text = data.decode('utf-8-sig')
    suffix = name.lower().rsplit('.', 1)[-1]
    if suffix in ('csv', 'tsv'):
        sample = text[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=',;\t')
        except csv.Error:
            dialect = csv.excel_tab if suffix == 'tsv' else csv.excel
        return [from_mapping(r, name) for r in csv.DictReader(io.StringIO(text), dialect=dialect)]
    if suffix == 'json':
        obj = json.loads(text)
        items = obj if isinstance(obj, list) else [obj]
        if any(not isinstance(i, dict) for i in items):
            raise ValueError('JSON должен содержать объект или список объектов')
        rows = []
        for item in items:
            if 'mapping' in item:
                for body, day in conversation_messages(item):
                    rows.extend(parse_text(body, name + ': ' + item.get('title', ''), {'forecast_date': day}))
            elif 'messages' in item:
                for msg in item['messages']:
                    if msg.get('role') == 'assistant' and isinstance(msg.get('content'), str):
                        rows.extend(parse_text(msg['content'], name))
            else:
                rows.append(from_mapping(item, name))
        return rows
    if suffix in ('txt', 'md', 'html', 'htm'):
        return parse_text(text, name)
    raise ValueError('Поддерживаются CSV, TSV, JSON, TXT, MD, HTML; ZIP сначала распакуйте')
