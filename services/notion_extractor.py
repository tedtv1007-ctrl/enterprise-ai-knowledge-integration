import os
import requests

NOTION_KEY = os.environ.get('NOTION_KEY')
NOTION_VERSION = os.environ.get('NOTION_VERSION','2025-09-03')

headers = {
    'Authorization': f'Bearer {NOTION_KEY}',
    'Notion-Version': NOTION_VERSION,
    'Content-Type':'application/json'
}


def fetch_page_text(page_id):
    if not NOTION_KEY:
        return ''
    # Retrieve blocks for page and concatenate plain text
    url = f'https://api.notion.com/v1/blocks/{page_id}/children?page_size=100'
    texts = []
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        for blk in data.get('results',[]):
            typ = blk.get('type')
            if typ and 'text' in blk.get(typ, {}):
                for rt in blk[typ].get('rich_text',[]):
                    texts.append(rt.get('plain_text',''))
        return '\n'.join(texts)
    except Exception:
        return ''
