import json
import os
import base64
import time

SESSION_FILE = os.path.expanduser("~/.gentool_session")

def get_session():
    if not os.path.exists(SESSION_FILE):
        return None
    with open(SESSION_FILE) as f:
        return json.load(f)

def save_session(user):
    with open(SESSION_FILE, "w") as f:
        json.dump(user, f)

def is_token_expired(id_token):
    payload = id_token.split('.')[1]
    payload += '=' * (4 - len(payload) % 4)
    decoded = json.loads(base64.b64decode(payload))
    return time.time() > decoded['exp']

def get_valid_user(firebase):
    session = get_session()
    if not session:
        return None
    
    if not is_token_expired(session['idToken']):
        return session
    
    auth = firebase.auth()
    try:
        user = auth.refresh(session['refreshToken'])
        save_session(user)
        return user
    except:
        return None