from flask import Flask, jsonify, send_from_directory, request
import requests
import csv
import io
import re
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

MAILJET_API_KEY    = os.environ.get('MAILJET_API_KEY', '3b7ed6fa7e4d7e777bb144c487625b06')
MAILJET_SECRET_KEY = os.environ.get('MAILJET_SECRET_KEY', '8a3a0f2e26c51aadaacfcd250b3126cf')
MJ_AUTH = (MAILJET_API_KEY, MAILJET_SECRET_KEY)
MJ_BASE = "https://api.mailjet.com/v3/REST"

SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1N1lO3PdUqX9U4chc1sZXpP_zzfHYwXyfzpEXO4BxYWs"
    "/export?format=csv"
)

APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzoRuw5zraZ_g-g3BioEbReo-m_e_N_glPikd8eJrGmsCe-Pr__cjR4_UX84ZxudQhR/exec"

ALIASES = {
    'name':        ['event name'],
    'month':       ['month'],
    'date':        ['date'],
    'time':        ['time'],
    'desc':        ['description'],
    'signupText1': ['sign up text 1', 'signup text 1'],
    'signupLink1': ['sign up link 1', 'signup link 1', 'sign up link'],
    'signupText2': ['sign up text 2', 'signup text 2'],
    'signupLink2': ['sign up link 2', 'signup link 2'],
    'status':      ['status'],
    'image':       ['image'],
}

def get_col_index(headers):
    col = {}
    for key, alias_list in ALIASES.items():
        for alias in alias_list:
            if alias in headers:
                col[key] = headers.index(alias)
                break
    return col

def get_cell(row, col, key):
    idx = col.get(key)
    if idx is not None and idx < len(row):
        return row[idx].strip()
    return ''

def parse_csv(text):
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return []
    headers = [h.strip().lower() for h in rows[0]]
    col = get_col_index(headers)
    events = []
    for row in rows[1:]:
        if not row or not row[0].strip():
            continue
        events.append({k: get_cell(row, col, k) for k in ALIASES})
    return events

def format_datetime(date, time_str):
    date = re.sub(r'^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s*', '', date, flags=re.IGNORECASE).strip()
    return f"{date} | {time_str}" if time_str else date

def get_base_html():
    res = requests.get(f"{MJ_BASE}/template?Limit=100", auth=MJ_AUTH)
    templates = res.json().get('Data', [])
    base = next((t for t in templates if 'cobysbasetemplate' in t['Name'].lower()), None)
    if not base:
        return None, 'CobysBaseTemplate not found.'
    res2 = requests.get(f"{MJ_BASE}/template/{base['ID']}/detailcontent", auth=MJ_AUTH)
    content = res2.json()
    if 'Data' not in content or not content['Data']:
        return None, 'CobysBaseTemplate has no HTML content.'
    return content['Data'][0].get('Html-part', ''), None

def fill_template(html, event):
    out = html
    out = out.replace('{{var:event_name}}', event['name'])
    out = out.replace('{{var:date}}', format_datetime(event['date'], event['time']))
    out = out.replace('{{var:description}}', event['desc'])
    out = out.replace('{{var:signup_text1}}', event['signupText1'] or 'General Ticket')
    out = out.replace('{{var:signup_link1}}', event['signupLink1'] if event['signupLink1'].startswith('http') else '#')
    out = out.replace('{{var:signup_text2}}', event['signupText2'] or '')
    out = out.replace('{{var:signup_link2}}', event['signupLink2'] if event['signupLink2'].startswith('http') else '#')
    if event['image'] and event['image'].startswith('http'):
        out = out.replace('{{var:image}}', event['image'])
    return out

def mark_done(event_name):
    try:
        requests.post(APPS_SCRIPT_URL, json={'eventName': event_name}, timeout=10)
    except:
        pass

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/api/events', methods=['GET'])
def get_events():
    try:
        res = requests.get(SHEET_CSV_URL, timeout=15)
        res.raise_for_status()
        return jsonify({'success': True, 'events': parse_csv(res.text)})
    except Exception as ex:
        return jsonify({'success': False, 'error': str(ex)}), 500

@app.route('/api/run', methods=['POST'])
def run_automation():
    try:
        res = requests.get(SHEET_CSV_URL, timeout=15)
        res.raise_for_status()
        events = parse_csv(res.text)
        new_events = [e for e in events if e['status'].lower() == 'new']

        if not new_events:
            return jsonify({'success': True, 'results': [], 'message': 'No new events found.'})

        base_html, error = get_base_html()
        if error:
            return jsonify({'success': False, 'error': error}), 500

        results = []
        for event in new_events:
            try:
                filled = fill_template(base_html, event)
                filename = re.sub(r'[^a-zA-Z0-9]+', '_', event['name']) + '.html'
                mark_done(event['name'])
                results.append({
                    'name': event['name'],
                    'status': 'success',
                    'html': filled,
                    'filename': filename
                })
            except Exception as ex:
                results.append({'name': event['name'], 'status': 'error', 'error': str(ex)})

        return jsonify({'success': True, 'results': results})

    except Exception as ex:
        return jsonify({'success': False, 'error': str(ex)}), 500

if __name__ == '__main__':
    app.run(debug=False)
