from flask import Flask, request, jsonify
import hmac
import hashlib
import os
from .notion_extractor import fetch_page_text

app = Flask(__name__)

NOTION_SECRET = os.environ.get('NOTION_WEBHOOK_SECRET', '')

def verify_signature(req):
    # Notion may send a signature header; this is a placeholder HMAC-SHA256 verification
    signature = req.headers.get('Notion-Signature', '')
    if not NOTION_SECRET:
        return True
    computed = hmac.new(NOTION_SECRET.encode('utf-8'), req.data, hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, signature)

@app.route('/notion-webhook', methods=['POST'])
def notion_webhook():
    if not verify_signature(request):
        return jsonify({'error':'invalid signature'}), 401
    payload = request.get_json(silent=True)
    # Minimal handling: extract page id and fetch content
    page_id = None
    try:
        # Notion event payload varies; look for page id in common locations
        page_id = payload.get('page_id') or payload.get('resource') or (payload.get('event') or {}).get('page_id')
    except Exception:
        page_id = None
    if not page_id:
        # attempt to parse blocks
        page_id = payload.get('data',{}).get('page',{}).get('id')
    if not page_id:
        # fallback: log and ack
        app.logger.info('no page id in payload')
        return jsonify({'status':'no_page'}), 202
    text = fetch_page_text(page_id)
    # Here we would enqueue text for vectorization; placeholder response
    app.logger.info(f'Fetched text for page {page_id}: {len(text)} chars')
    return jsonify({'status':'queued','page_id':page_id}), 202

if __name__=='__main__':
    app.run(port=int(os.environ.get('PORT',3000)))
