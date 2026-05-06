from flask import Flask, jsonify, send_from_directory, request
import requests
import csv
import io
import re
import os
import tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({'success': False, 'error': str(e)}), 500

# Mailjet API
MAILJET_API_KEY    = os.environ.get('MAILJET_API_KEY', '3b7ed6fa7e4d7e777bb144c487625b06')
MAILJET_SECRET_KEY = os.environ.get('MAILJET_SECRET_KEY', '8a3a0f2e26c51aadaacfcd250b3126cf')
MJ_AUTH = (MAILJET_API_KEY, MAILJET_SECRET_KEY)
MJ_BASE = "https://api.mailjet.com/v3/REST"

# Mailjet login
MAILJET_EMAIL    = os.environ.get('MAILJET_EMAIL', 'suepasha@yahoo.com')
MAILJET_PASSWORD = os.environ.get('MAILJET_PASSWORD', 'Suepasha070!')

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
        events.append({
            'name':        get_cell(row, col, 'name'),
            'month':       get_cell(row, col, 'month'),
            'date':        get_cell(row, col, 'date'),
            'time':        get_cell(row, col, 'time'),
            'desc':        get_cell(row, col, 'desc'),
            'signupText1': get_cell(row, col, 'signupText1'),
            'signupLink1': get_cell(row, col, 'signupLink1'),
            'signupText2': get_cell(row, col, 'signupText2'),
            'signupLink2': get_cell(row, col, 'signupLink2'),
            'status':      get_cell(row, col, 'status'),
            'image':       get_cell(row, col, 'image'),
        })
    return events

def format_datetime(date, time):
    date = re.sub(r'^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s*', '', date, flags=re.IGNORECASE).strip()
    if time:
        return f"{date} | {time}"
    return date

def get_base_html():
    res = requests.get(f"{MJ_BASE}/template?Limit=100", auth=MJ_AUTH)
    templates = res.json().get('Data', [])
    base = next((t for t in templates if 'cobysbasetemplate' in t['Name'].lower()), None)
    if not base:
        return None, 'CobysBaseTemplate not found in Mailjet.'
    res2 = requests.get(f"{MJ_BASE}/template/{base['ID']}/detailcontent", auth=MJ_AUTH)
    content = res2.json()
    if 'Data' not in content or not content['Data']:
        return None, 'CobysBaseTemplate has no HTML content.'
    return content['Data'][0].get('Html-part', ''), None

def fill_template(html, event):
    name  = event['name']
    date  = format_datetime(event['date'], event['time'])
    desc  = event['desc']
    txt1  = event['signupText1'] or 'General Ticket'
    lnk1  = event['signupLink1'] if event['signupLink1'].startswith('http') else '#'
    txt2  = event['signupText2']
    lnk2  = event['signupLink2'] if event['signupLink2'].startswith('http') else ''
    image = event['image']

    out = html
    out = out.replace('{{var:event_name}}', name)
    out = out.replace('{{var:date}}', date)
    out = out.replace('{{var:description}}', desc)
    out = out.replace('{{var:signup_text1}}', txt1)
    out = out.replace('{{var:signup_link1}}', lnk1)
    out = out.replace('{{var:signup_text2}}', txt2)
    out = out.replace('{{var:signup_link2}}', lnk2)
    if image and image.startswith('http'):
        out = out.replace('{{var:image}}', image)

    return out

def mark_done(event_name):
    try:
        requests.post(APPS_SCRIPT_URL, json={'eventName': event_name}, timeout=10)
    except Exception:
        pass

def import_template_to_mailjet(html_content, template_name):
    """Use Playwright to log into Mailjet and import HTML as a template."""
    from playwright.sync_api import sync_playwright
    log = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        try:
            log.append('Going to signin page...')
            page.goto('https://app.mailjet.com/signin', timeout=30000)
            page.wait_for_load_state('networkidle', timeout=30000)
            log.append(f'Page title: {page.title()}')
            log.append('Filling email...')
            page.fill('input[type="email"]', MAILJET_EMAIL, timeout=10000)
            log.append('Filling password...')
            page.fill('input[type="password"]', MAILJET_PASSWORD, timeout=10000)
            log.append('Clicking submit...')
            page.click('button[type="submit"]', timeout=10000)
            page.wait_for_load_state('networkidle', timeout=30000)
            log.append(f'After login title: {page.title()}')
            log.append('Going to templates page...')
            page.goto('https://app.mailjet.com/templates/marketing', timeout=30000)
            page.wait_for_load_state('networkidle', timeout=30000)
            log.append(f'Templates page title: {page.title()}')
            log.append('Clicking Create a template...')
            page.click('text=Create a template', timeout=15000)
            page.wait_for_load_state('networkidle', timeout=30000)
            log.append('Clicking By coding it in HTML...')
            page.click('text=By coding it in HTML', timeout=15000)
            page.wait_for_load_state('networkidle', timeout=30000)
            log.append('Clicking Import HTML from a file...')
            page.click('text=Import HTML from a file', timeout=15000)
            page.wait_for_load_state('networkidle', timeout=30000)
            log.append('Uploading file...')
            with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w') as f:
                f.write(html_content)
                tmp_path = f.name
            page.set_input_files('input[type="file"]', tmp_path, timeout=10000)
            os.unlink(tmp_path)
            log.append('Entering template name...')
            name_input = page.query_selector('input[placeholder*="name"], input[name*="name"], #template-name')
            if name_input:
                name_input.fill(template_name)
            log.append('Clicking Continue...')
            page.click('text=Continue', timeout=10000)
            page.wait_for_load_state('networkidle', timeout=30000)
            log.append('Done!')
            browser.close()
            return True, ' | '.join(log)
        except Exception as e:
            log.append(f'ERROR: {str(e)}')
            try:
                browser.close()
            except:
                pass
            return False, ' | '.join(log)


def mark_done(event_name):
    try:
        requests.post(APPS_SCRIPT_URL, json={'eventName': event_name}, timeout=10)
    except Exception:
        pass

def import_template_to_mailjet(html_content, template_name):
    """Use Playwright to log into Mailjet and import HTML as a template."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            # Login to Mailjet
            page.goto('https://app.mailjet.com/signin')
            page.wait_for_load_state('networkidle')
            page.fill('input[type="email"], input[name="email"], #email', MAILJET_EMAIL)
            page.fill('input[type="password"], input[name="password"], #password', MAILJET_PASSWORD)
            page.click('button[type="submit"], input[type="submit"], .btn-primary')
            page.wait_for_load_state('networkidle')

            # Go to Email Templates
            page.goto('https://app.mailjet.com/templates/marketing')
            page.wait_for_load_state('networkidle')

            # Click Create a template
            page.click('text=Create a template', timeout=10000)
            page.wait_for_load_state('networkidle')

            # Click By coding it in HTML
            page.click('text=By coding it in HTML', timeout=10000)
            page.wait_for_load_state('networkidle')

            # Click Import HTML from a file
            page.click('text=Import HTML from a file', timeout=10000)
            page.wait_for_load_state('networkidle')

            # Save HTML to temp file and upload
            with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w') as f:
                f.write(html_content)
                tmp_path = f.name

            # Upload the file
            page.set_input_files('input[type="file"]', tmp_path)
            os.unlink(tmp_path)

            # Enter template name
            name_input = page.query_selector('input[placeholder*="name"], input[name*="name"], #template-name')
            if name_input:
                name_input.fill(template_name)

            # Click Continue or Save
            page.click('text=Continue, text=Save, button[type="submit"]', timeout=10000)
            page.wait_for_load_state('networkidle')

            browser.close()
            return True, None

        except Exception as e:
            browser.close()
            return False, str(e)

@app.route('/api/test', methods=['GET'])
def test_playwright():
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto('https://example.com')
            title = page.title()
            browser.close()
            return jsonify({'success': True, 'title': title})
    except Exception as ex:
        return jsonify({'success': False, 'error': str(ex)})

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/api/events', methods=['GET'])
def get_events():
    try:
        res = requests.get(SHEET_CSV_URL, timeout=15)
        res.raise_for_status()
        events = parse_csv(res.text)
        return jsonify({'success': True, 'events': events})
    except Exception as ex:
        return jsonify({'success': False, 'error': str(ex)}), 500

@app.route('/api/run', methods=['POST'])
def run_automation():
    try:
        # Load sheet
        res = requests.get(SHEET_CSV_URL, timeout=15)
        res.raise_for_status()
        events = parse_csv(res.text)
        new_events = [e for e in events if e['status'].lower() == 'new']

        if not new_events:
            return jsonify({'success': True, 'results': [], 'message': 'No new events found.'})

        # Get base HTML
        base_html, error = get_base_html()
        if error:
            return jsonify({'success': False, 'error': error}), 500

        results = []
        for event in new_events:
            event_name = event['name']
            try:
                filled = fill_template(base_html, event)

                # Use Playwright to import into Mailjet
                success, err = import_template_to_mailjet(filled, event_name)

                if not success:
                    results.append({'name': event_name, 'status': 'error', 'error': err})
                    continue

                # Mark as Done in Google Sheet
                mark_done(event_name)
                results.append({'name': event_name, 'status': 'success'})

            except Exception as ex:
                results.append({'name': event_name, 'status': 'error', 'error': str(ex)})

        return jsonify({'success': True, 'results': results})

    except Exception as ex:
        return jsonify({'success': False, 'error': str(ex)}), 500

if __name__ == '__main__':
    app.run(debug=False)
