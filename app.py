from flask import Flask, jsonify, send_from_directory, request
import requests, csv, io, re, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

MJ_AUTH = (
    os.environ.get('MAILJET_API_KEY',    '3b7ed6fa7e4d7e777bb144c487625b06'),
    os.environ.get('MAILJET_SECRET_KEY', '8a3a0f2e26c51aadaacfcd250b3126cf')
)
SHEET_CSV_URL  = "https://docs.google.com/spreadsheets/d/1N1lO3PdUqX9U4chc1sZXpP_zzfHYwXyfzpEXO4BxYWs/export?format=csv"
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzoRuw5zraZ_g-g3BioEbReo-m_e_N_glPikd8eJrGmsCe-Pr__cjR4_UX84ZxudQhR/exec"

FONT   = "'Century Gothic', CenturyGothic, AppleGothic, sans-serif"
LOGO   = "https://sjqzn.mjt.lu/img2/sjqzn/519a4db6-cda9-4e32-8e6f-608386b2fadd/content"
IMG_PH = "https://sjqzn.mjt.lu/img2/sjqzn/1ef5c329-24ef-45e8-9010-9d1d6393531e/content"

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
    'dueDate':     ['due date', 'duedate', 'send date', 'senddate'],
}

MJML_OPEN = f"""<mjml version="4.14.1">
  <mj-head>
    <mj-preview></mj-preview>
    <mj-style inline="inline">
      p, span, td, div, a {{ font-family: {FONT} !important; }}
    </mj-style>
    <mj-style>
      @media only screen and (max-width: 480px) {{
        .event-title {{ font-size: 22px !important; line-height: 30px !important; }}
        .event-date  {{ font-size: 17px !important; line-height: 24px !important; }}
        .event-desc  {{ font-size: 15px !important; line-height: 22px !important; }}
      }}
    </mj-style>
    <mj-attributes>
      <mj-all font-family="{FONT}"></mj-all>
    </mj-attributes>
  </mj-head>
  <mj-body background-color="#ffffff" color="#222222" font-family="{FONT}">
    <mj-section background-color="#ffffff" padding="0px">
      <mj-column>
        <mj-image align="center" alt="" border="none" container-background-color="#e0d3c3" height="auto" padding="10px 25px" src="{LOGO}" width="200px"></mj-image>
      </mj-column>
    </mj-section>"""

MJML_EVENT_SECTION = f"""
    <mj-section background-color="#f4f4f4" padding="5px 0px">
      <mj-column>
        <mj-text padding="0px" passport-element="html" width="100%">
          <p class="event-title" style="font-family:{FONT};font-size:28px;font-weight:bold;text-align:center;color:#000000;line-height:36px;margin:20px 30px 10px 30px;">EVENT_TITLE</p>
        </mj-text>
        <mj-image align="center" alt="" border-radius="10px" border="none" height="auto" padding="10px 25px 15px" src="EVENT_IMAGE" width="350px" fluid-on-mobile="true"></mj-image>
        <mj-text padding="0px" passport-element="html" width="100%">
          <p class="event-date" style="font-family:{FONT};font-size:22px;font-weight:bold;text-align:center;color:#000000;line-height:30px;margin:5px 20px;"><strong>EVENT_DATE</strong></p>
          <p class="event-desc" style="font-family:{FONT};font-size:19px;font-weight:normal;text-align:center;color:#000000;line-height:28px;margin:8px 30px;">EVENT_DESCRIPTION</p>
        </mj-text>
        <mj-text padding="0px" passport-element="html" width="100%">
          <p style="text-align:center;margin:10px 0 5px;">
            <a href="SIGNUP_LINK1" style="background-color:#FFFFFF !important;color:#000000 !important;border:1px solid #000000;border-radius:10px;padding:12px 40px;text-decoration:none !important;font-family:{FONT};font-size:19px;font-weight:bold;display:inline-block;">SIGNUP_TEXT1</a>
          </p>
        </mj-text>
        BUTTON2_PLACEHOLDER
        <mj-divider border-color="#E6E6E6" border-style="solid" border-width="2px" padding="10px 25px"></mj-divider>
      </mj-column>
    </mj-section>"""

MJML_BUTTON2 = f"""<mj-text padding="0px" passport-element="html" width="100%">
          <p style="text-align:center;margin:8px 0 5px;">
            <a href="SIGNUP_LINK2" style="background-color:#FFFFFF !important;color:#000000 !important;border:1px solid #000000;border-radius:10px;padding:12px 40px;text-decoration:none !important;font-family:{FONT};font-size:19px;font-weight:bold;display:inline-block;">SIGNUP_TEXT2</a>
          </p>
        </mj-text>"""

MJML_CLOSE = f"""
    <mj-section background-color="#e0d3c3" padding="15px 25px 5px">
      <mj-column>
        <mj-text padding="0px" passport-element="html" width="100%">
          <p style="text-align:center;margin-top:5px;"><a href="mailto:info@cobyscafe.com?subject=An%20idea%20for%20meetups%2Fevents" style="display:inline-block;font-family:{FONT};font-size:15px;font-weight:bold;text-decoration:none;padding:5px 10px;border-radius:8px;border:1px solid #2D2D2D;color:#2D2D2D;background-color:#ffffff;">Submit an Event Idea</a></p>
          <p style="text-align:center;margin-top:0;"><a href="https://www.cobyscafe.com/membership" style="display:inline-block;font-family:{FONT};font-size:15px;font-weight:bold;text-decoration:none;padding:5px 10px;border-radius:8px;border:1px solid #2D2D2D;color:#2D2D2D;background-color:#ffffff;">Become a Member</a></p>
          <p style="text-align:center;margin-top:0;"><a href="https://www.cobyscafe.com/parties" style="display:inline-block;font-family:{FONT};font-size:15px;font-weight:bold;text-decoration:none;padding:5px 10px;border-radius:8px;border:1px solid #2D2D2D;color:#2D2D2D;background-color:#ffffff;">Host a Party</a></p>
          <p style="text-align:center;margin-top:0;"><a href="https://www.google.com/maps/search/?api=1&query=Coby's+Cafe+101+Nickerson+St+Seattle+WA" style="display:inline-block;font-family:{FONT};font-size:15px;font-weight:bold;text-decoration:none;padding:5px 10px;border-radius:8px;border:1px solid #2D2D2D;color:#2D2D2D;background-color:#ffffff;" target="_blank">Leave a Google Review</a></p>
        </mj-text>
        <mj-social align="center" border-radius="25px" container-background-color="transparent" icon-size="28px" mode="horizontal" text-mode="false">
          <mj-social-element background-color="#3B5998" href="https://www.facebook.com/people/Cobys-Cafe/61553537724188/" name="facebook-noshare" src="https://static.mailjet.com/ico-social/facebook.png"></mj-social-element>
          <mj-social-element background-color="#9585F4" href="https://www.instagram.com/cobys.dog.cafe/" name="instagram-noshare" src="https://static.mailjet.com/ico-social/instagram-colored.png"></mj-social-element>
        </mj-social>
        <mj-text padding="0px 5px">
          <p style="text-align:center;margin:10px 0;"><span style="font-size:12px;font-family:{FONT};color:#131B20;">Coby's Cafe<br>101 Nickerson Street Building B Ste 200<br>Seattle, Washington 98109<br>www.cobyscafe.com</span></p>
        </mj-text>
        <mj-text padding="10px 25px">
          <p style="text-align:center;margin:10px 0;"><span style="font-size:12px;font-family:{FONT};color:#000000;">If you do not wish to receive further communication like this, </span><a href="[[UNSUB_LINK_EN]]" target="_blank"><span style="font-size:12px;font-family:{FONT};color:#ffffff;"><u>unsubscribe here</u></span></a></p>
        </mj-text>
      </mj-column>
    </mj-section>
  </mj-body>
</mjml>"""


def fetch_events():
    res = requests.get(SHEET_CSV_URL, timeout=15)
    res.raise_for_status()
    reader = csv.reader(io.StringIO(res.text))
    rows = list(reader)
    if not rows:
        return []
    headers = [h.strip().lower() for h in rows[0]]
    col = {key: next((headers.index(a) for a in aliases if a in headers), None)
           for key, aliases in ALIASES.items()}
    def cell(row, k):
        i = col.get(k)
        return row[i].strip() if i is not None and i < len(row) else ''
    return [{k: cell(row, k) for k in ALIASES} for row in rows[1:] if row and row[0].strip()]

def format_datetime(date, time_str):
    date = re.sub(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\w*,?\s*', '', date, flags=re.IGNORECASE).strip()
    return f"{date} | {time_str}" if time_str else date

def fill_event_section(event):
    lnk1 = event['signupLink1'] if event['signupLink1'].startswith('http') else '#'
    lnk2 = event['signupLink2'] if event['signupLink2'].startswith('http') else ''
    btn2 = MJML_BUTTON2.replace('SIGNUP_LINK2', lnk2).replace('SIGNUP_TEXT2', event['signupText2']) \
           if event['signupText2'] and lnk2 else ''
    return (MJML_EVENT_SECTION
        .replace('EVENT_TITLE',       event['name'])
        .replace('EVENT_DATE',        format_datetime(event['date'], event['time']))
        .replace('EVENT_DESCRIPTION', event['desc'])
        .replace('EVENT_IMAGE',       event['image'] if event['image'].startswith('http') else IMG_PH)
        .replace('SIGNUP_LINK1',      lnk1)
        .replace('SIGNUP_TEXT1',      event['signupText1'] or 'General Ticket')
        .replace('BUTTON2_PLACEHOLDER', btn2))

def build_mjml(events):
    return MJML_OPEN + ''.join(fill_event_section(e) for e in events) + MJML_CLOSE

def mark_done(event_name):
    try:
        requests.post(APPS_SCRIPT_URL, json={'eventName': event_name}, timeout=10)
    except Exception:
        pass

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/api/events')
def get_events():
    try:
        return jsonify({'success': True, 'events': fetch_events()})
    except Exception as ex:
        return jsonify({'success': False, 'error': str(ex)}), 500

@app.route('/api/run', methods=['POST'])
def run_automation():
    try:
        selected = set((request.json or {}).get('selected', []))
        events   = fetch_events()
        to_process = [e for e in events if e['status'].lower() == 'new' and e['name'] in selected]

        if not to_process:
            return jsonify({'success': True, 'results': [], 'message': 'No events selected.'})

        # Group by Due Date
        groups = {}
        for e in to_process:
            key = e['dueDate'].strip() or 'no_due_date'
            groups.setdefault(key, []).append(e)

        results = []
        for due_date, group in groups.items():
            try:
                mjml     = build_mjml(group)
                has_due  = due_date != 'no_due_date'
                filename = re.sub(r'[^a-zA-Z0-9]+', '_', due_date if has_due else group[0]['name']) + '.mjml'
                label    = f"{due_date} ({len(group)} event{'s' if len(group)>1 else ''})" if has_due else group[0]['name']
                for e in group:
                    mark_done(e['name'])
                results.append({'name': label, 'events': [e['name'] for e in group], 'status': 'success', 'mjml': mjml, 'filename': filename})
            except Exception as ex:
                results.append({'name': due_date, 'events': [e['name'] for e in group], 'status': 'error', 'error': str(ex)})

        return jsonify({'success': True, 'results': results})
    except Exception as ex:
        return jsonify({'success': False, 'error': str(ex)}), 500

if __name__ == '__main__':
    app.run(debug=False)
