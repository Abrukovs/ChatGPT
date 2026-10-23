import json
import re
from urllib.parse import urlsplit
import requests
from bs4 import BeautifulSoup


def fetch_share(url):
    """Only a public ChatGPT share page; no cookies, redirects or auth bypass."""
    parts = urlsplit(url)
    if (parts.scheme != 'https' or parts.netloc != 'chatgpt.com'
            or not re.fullmatch(r'/share/[A-Za-z0-9-]{8,100}/?', parts.path)
            or parts.query or parts.fragment):
        raise ValueError('Разрешена только ссылка https://chatgpt.com/share/ID без параметров')
    try:
        r = requests.get(url, timeout=(5, 20), allow_redirects=False,
                         headers={'User-Agent': 'SportsJournal/1.0'}, stream=True)
        with r:
            if r.status_code != 200:
                raise ValueError('Публичная ссылка недоступна. Вставьте текст итогового ответа')
            chunks, size = [], 0
            for chunk in r.iter_content(65536):
                size += len(chunk)
                if size > 5 * 1024 * 1024:
                    raise ValueError('Страница слишком большая. Вставьте итоговый текст')
                chunks.append(chunk)
            html = b''.join(chunks).decode('utf-8', errors='replace')
    except requests.RequestException:
        raise ValueError('Не удалось открыть ссылку. Вставьте текст итогового ответа') from None
    soup = BeautifulSoup(html, 'html.parser')
    # Fail closed on app shells/JS: never guess hidden data formats.
    assistant = soup.select('[data-message-author-role="assistant"]')
    if not assistant:
        raise ValueError('На странице нет доступного текста ответов. Вставьте текст или экспорт JSON')
    return '\n\n'.join(node.get_text('\n', strip=True) for node in assistant)
