import urllib.request, pathlib, sys

base = pathlib.Path(r"C:\Users\kmato\OneDrive\Documents\GitHub\portfolio-challenge\ai-bootcamp-assignments\module-06")

API = r"""
import requests

API_BASE = 'http://localhost:8000'

def _h(token):
    return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

def _get(path, token, params=None):
    try:
        r = requests.get(f'{API_BASE}{path}', headers=_h(token), params=params, timeout=10)
        if r.status_code == 401: return None, 'Session expired.'
        if not r.ok: return None, str(r.json().get('detail', r.text))
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, 'Cannot reach API at localhost:8000. Is the backend running?'
    except Exception as e:
        return None, str(e)

def _post(path, token, payload):
    try:
        r = requests.post(f'{API_BASE}{path}', headers=_h(token), json=payload, timeout=10)
        if r.status_code == 401: return None, 'Session expired.'
        if not r.ok: return None, str(r.json().get('detail', r.text))
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, 'Cannot reach API at localhost:8000. Is the backend running?'
    except Exception as e:
        return None, str(e)

def _patch(path, token, payload):
    try:
        r = requests.patch(f'{API_BASE}{path}', headers=_h(token), json=payload, timeout=10)
        if r.status_code == 401: return None, 'Session expired.'
        if r.status_code == 403: return None, 'You can only modify your own decisions.'
        if not r.ok: return None, str(r.json().get('detail', r.text))
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, 'Cannot reach API at localhost:8000. Is the backend running?'
    except Exception as e:
        return None, str(e)

def login(email, password):
    try:
        r = requests.post(f'{API_BASE}/auth/login',
                          json={'email': email, 'password': password}, timeout=10)
        if not r.ok: return None, 'Invalid email or password.'
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, 'Cannot reach API at localhost:8000. Is the backend running?'
    except Exception as e:
        return None, str(e)

def register(name, email, password, role='analyst'):
    try:
        r = requests.post(f'{API_BASE}/auth/register',
                          json={'name': name, 'email': email,
                                'password': password, 'role': role}, timeout=10)
        if not r.ok: return None, str(r.json().get('detail', 'Registration failed.'))
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, 'Cannot reach API at localhost:8000. Is the backend running?'
    except Exception as e:
        return None, str(e)

def get_me(token):
    return _get('/auth/users/me', token)

def get_decisions(token, ticker=None, outcome=None, status=None):
    p = {}
    if ticker: p['ticker'] = ticker
    if outcome: p['outcome'] = outcome
    if status: p['status'] = status
    return _get('/decisions', token, p)

def create_decision(token, payload):
    return _post('/decisions', token, payload)

def set_outcome(token, decision_id, outcome, notes=None):
    p = {'outcome': outcome}
    if notes: p['outcome_notes'] = notes
    return _patch(f'/decisions/{decision_id}/outcome', token, p)

def get_ai_suggestion(token, decision_id):
    return _post(f'/decisions/{decision_id}/suggest', token, {})

def get_securities(token):
    return _get('/securities', token)

def mock_copilot(scope, prompt, context):
    ctx = ', '.join(context) if context else 'general'
    return (f'[Caduceus Copilot · {scope}] Context: {ctx}\n\n'
            f'Regarding: "{prompt[:80]}"\n\n'
            f'In production this retrieves EDGAR filings and earnings transcripts '
            f'via pgvector similarity search, then synthesizes a response via Claude '
            f'with source citations. RAG pipeline wired in Modules 7-8.')

def get_copilot_response(api_key, scope, messages, context):
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        system = (f'You are the Caduceus copilot for a healthcare equity analyst at '
                  f'Rhenman and Partners. Surface: {scope}. '
                  f'Context: {", ".join(context)}. Be concise and institutionally precise.')
        resp = client.messages.create(
            model='claude-sonnet-4-20250514', max_tokens=600,
            system=system, messages=messages)
        return resp.content[0].text, None
    except Exception as e:
        return None, str(e)
"""

(base / 'api_client.py').write_text(API, encoding='utf-8')
print(f"api_client.py written: {len(API.splitlines())} lines")
print("Done - now run: streamlit run app.py")
