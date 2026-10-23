"""Run: python -m streamlit run app.py"""
import hmac
import hashlib
import time
import io
import os
from pathlib import Path
import pandas as pd
import streamlit as st
from tracker.parser import parse_text, parse_file
from tracker.share import fetch_share
from tracker.storage import LocalStore, GitHubStore, save_predictions
from tracker.journal import journal, stats, safe_export
from tracker.model import FIELDS, validate
from tracker.results import verify_pending, save_results

LABELS = {'id': 'ID', 'forecast_date': 'Дата прогноза', 'event_date': 'Дата матча (КХЛ: Рига)',
 'sport': 'Вид спорта', 'competition': 'Чемпионат', 'event': 'Матч', 'market': 'Рынок',
 'line': 'Линия', 'odds': 'Коэффициент', 'probability': 'Вероятность, %', 'category': 'Категория',
 'role': 'Тип выбора', 'arguments': 'Аргументы', 'risks': 'Риски', 'source': 'Источник',
 'source_text': 'Исходный фрагмент', 'reported_status': 'Результат со слов источника',
 'status': 'Проверенный статус', 'review_notes': 'Что проверить', 'score': 'Счёт'}

st.set_page_config(page_title='Журнал прогнозов', page_icon='📒', layout='wide')

def secret(key, default=''):
    try:
        return os.environ.get(key) or st.secrets.get(key, default)
    except FileNotFoundError:
        return os.environ.get(key, default)

# A server-wide credential is never exposed to anonymous visitors.
server_token = secret('GITHUB_TOKEN')
app_password = secret('APP_PASSWORD')
if server_token:
    if not app_password:
        st.error('При серверном GITHUB_TOKEN задайте APP_PASSWORD в Secrets. Доступ закрыт.')
        st.stop()
    password = st.text_input('Пароль приложения', type='password')
    if not hmac.compare_digest(password.encode(), str(app_password).encode()):
        st.info('Введите пароль владельца для доступа к журналу.')
        st.stop()

st.title('Журнал спортивных прогнозов')
st.caption('Импорт → проверка → сохранение. Исходные прогнозы не редактируются после записи.')
with st.sidebar:
    mode = st.radio('Хранение', ['GitHub', 'Локально'])
    token = server_token or st.text_input('GitHub token (только для записи)', type='password', help='Fine-grained token: Abrukovs/ChatGPT → Contents: Read and write. Не отправляйте токен в чат.')
    st.caption('Без токена доступно чтение публичного журнала. Локальный режим сохраняет данные на этом компьютере.')
    if st.button('Обновить журнал'):
        st.session_state.pop('loaded_journal', None)
        st.rerun()
    st.markdown('[Инструкция](https://github.com/Abrukovs/ChatGPT/blob/main/APP_GUIDE_RU.md)')

store = GitHubStore(token=token) if mode == 'GitHub' else LocalStore(Path(__file__).parent)
try:
    cache_key = mode + hashlib.sha256(token.encode()).hexdigest()
    cached = st.session_state.get('loaded_journal')
    if not cached or cached[0] != cache_key or time.monotonic() - cached[1] > 60:
        cached = (cache_key, time.monotonic(), journal(store))
        st.session_state['loaded_journal'] = cached
    rows = cached[2]
except Exception as exc:
    st.error(str(exc)); st.stop()

import_tab, journal_tab, result_tab, stats_tab = st.tabs(['Импорт', 'Журнал', 'Результаты', 'Статистика'])
with import_tab:
    st.info('Приложение обрабатывает переданные данные. Оно не читает закрытые чаты автоматически. Загружайте итоговые ответы, чтобы не смешать их с рассуждениями.')
    kind = st.radio('Источник', ['Текст', 'Публичная ссылка', 'Файл'], horizontal=True)
    content = st.text_area('Итоговый ответ нейросети', height=180) if kind == 'Текст' else ''
    url = st.text_input('https://chatgpt.com/share/...') if kind == 'Публичная ссылка' else ''
    uploaded = st.file_uploader('CSV, TSV, JSON, TXT, MD, HTML', type=['csv','tsv','json','txt','md','html','htm']) if kind == 'Файл' else None
    if st.button('Распознать', type='primary'):
        try:
            if kind == 'Файл':
                if uploaded is None:
                    raise ValueError('Выберите файл')
                parsed = parse_file(uploaded.name, uploaded.getvalue())
            else:
                parsed = parse_text(fetch_share(url) if kind == 'Публичная ссылка' else content, url or 'Вставленный текст')
            if not parsed:
                raise ValueError('Прогнозы не найдены')
            st.session_state['preview'] = parsed
            st.session_state.pop('prediction_editor', None)
            st.session_state.pop('ack', None)
        except Exception as exc:
            st.error(str(exc))
    if st.session_state.get('preview'):
        st.subheader('Проверьте распознанные записи')
        st.caption('Исправьте даты, спорт, рынок и категорию. role: final — итог, alternative — альтернатива, preliminary — рассуждение. Спорт: football — футбол, hockey — хоккей, basketball — баскетбол, tennis — теннис. Пустые неизвестные даты и коэффициент допустимы. Все результаты останутся PENDING до проверки.')
        frame = pd.DataFrame(st.session_state['preview'])
        frame.insert(0, 'Сохранить', False)
        edited = st.data_editor(frame, key='prediction_editor', hide_index=True, num_rows='dynamic',
            disabled=['id','status','review_notes','source','source_text','reported_status'],
            column_config={**{k: st.column_config.TextColumn(v) for k,v in LABELS.items()},
                'Сохранить': st.column_config.CheckboxColumn(default=False),
                'sport': st.column_config.SelectboxColumn('Вид спорта', options=['football','hockey','basketball','tennis']),
                'category': st.column_config.SelectboxColumn('Категория', options=['A','B+','B','PASS']),
                'role': st.column_config.SelectboxColumn('Тип выбора', options=['final','alternative','preliminary'])}, width='stretch')
        for i, r in enumerate(edited.to_dict('records')):
            if r.get('Сохранить'):
                issues = validate({k: '' if pd.isna(v) else str(v) for k,v in r.items()})
                if issues:
                    st.warning(f"Строка {i+1}: " + '; '.join(issues))
        with st.expander('Исходные фрагменты'):
            for r in st.session_state['preview']:
                st.text(r.get('source_text', ''))
        ack = st.checkbox('Я проверил выбранные строки. В GitHub будут сохранены также показанные исходные фрагменты.', key='ack')
        if st.button('Подтвердить и сохранить', disabled=not ack):
            try:
                selected = [{k: '' if pd.isna(v) else str(v) for k,v in r.items() if k in FIELDS}
                            for r in edited.to_dict('records') if r.get('Сохранить')]
                if not selected:
                    raise ValueError('Отметьте хотя бы одну строку в столбце «Сохранить»')
                if mode == 'GitHub' and not token:
                    raise ValueError('Для отправки в GitHub введите токен в боковой панели')
                count = save_predictions(store, selected, known=journal(store))
                st.success(f'Сохранение проверено. Новых записей: {count}. Повторы пропущены.')
                st.session_state.pop('preview', None)
                st.session_state.pop('loaded_journal', None)
                st.session_state['saved_message'] = f'Последний импорт: {count} новых записей; сохранение проверено.'
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
    if st.session_state.get('saved_message'):
        st.success(st.session_state['saved_message'])

with journal_tab:
    st.subheader(f'Единый журнал: {len(rows)} записей')
    sport_filter = st.multiselect('Вид спорта', sorted({r['sport'] for r in rows if r['sport']}))
    filtered = [r for r in rows if not sport_filter or r['sport'] in sport_filter]
    st.dataframe(pd.DataFrame(filtered).drop(columns=['source_text'], errors='ignore').rename(columns=LABELS), hide_index=True, width='stretch')
    export = pd.DataFrame(safe_export(filtered))
    st.download_button('Скачать CSV', export.to_csv(index=False).encode('utf-8-sig'), 'predictions_export.csv', 'text/csv')
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        export.to_excel(writer, index=False, sheet_name='Прогнозы')
    st.download_button('Скачать Excel', buf.getvalue(), 'predictions_export.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

with result_tab:
    st.write('Старые записи КХЛ рассчитывает существующий GitHub Action. Для новых импортов доступен тот же Webcaster API: только однозначные индивидуальные тоталы за три периода, линия .5, точные английские названия и дата матча. Остальные рынки остаются PENDING.')
    if st.button('Проверить новые импорты КХЛ'):
        with st.spinner('Проверка счёта и условий рынка…'):
            verified, errors = verify_pending(rows)
        st.session_state['verified'] = verified
        for error in errors:
            st.warning(error)
        if not verified:
            st.info('Новых достоверно подтверждённых результатов нет.')
    verified = st.session_state.get('verified', [])
    if verified:
        st.dataframe(pd.DataFrame(verified), hide_index=True)
        if st.button('Сохранить подтверждённые результаты'):
            try:
                if mode == 'GitHub' and not token:
                    raise ValueError('Для записи нужен GitHub token')
                count = save_results(store, verified)
                st.session_state.pop('verified', None)
                st.session_state.pop('loaded_journal', None)
                st.success(f'Результатов сохранено и проверено: {count}')
            except Exception as exc:
                st.error(str(exc))

with stats_tab:
    st.dataframe(pd.DataFrame([stats(rows)]), hide_index=True)
    st.caption('PASS и альтернативы исключены. WIN % = WIN / (WIN + LOSS). ROI — условная модель по 1 единице на рассчитанный прогноз с известным ориентировочным кэфом; это не фактический доход.')
    for field, label in [('sport', 'По видам спорта'), ('category', 'По категориям'), ('market', 'По рынкам')]:
        st.subheader(label)
        groups = []
        for value in sorted({r[field] for r in rows}):
            groups.append({field: value, **stats([r for r in rows if r[field] == value])})
        st.dataframe(pd.DataFrame(groups), hide_index=True, width='stretch')
