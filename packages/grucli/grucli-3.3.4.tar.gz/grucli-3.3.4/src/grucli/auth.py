import os
import json
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import threading
import requests
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from . import config

OAUTH_CLIENT_ID = '681255809395-oo8ft2oprdrnp9e3aqf6av3hmdib135j.apps.googleusercontent.com'
OAUTH_CLIENT_SECRET = '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'
OAUTH_SCOPES = [
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid',
]

os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

def get_oauth_file_path():
    return os.path.join(config.get_config_dir(), 'google_auth.json')

def get_oauth_credentials():
    creds = None
    oauth_file = get_oauth_file_path()
    if os.path.exists(oauth_file):
        try:
            with open(oauth_file, 'r') as f:
                creds_data = json.load(f)
                
                expiry = None
                if creds_data.get('expiry'):
                    expiry_str = creds_data.get('expiry')
                    if expiry_str.endswith('Z'):
                        expiry_str = expiry_str[:-1] + '+00:00'
                    expiry = datetime.fromisoformat(expiry_str)

                creds = Credentials(
                    token=creds_data.get('access_token'),
                    refresh_token=creds_data.get('refresh_token'),
                    token_uri='https://oauth2.googleapis.com/token',
                    client_id=OAUTH_CLIENT_ID,
                    client_secret=OAUTH_CLIENT_SECRET,
                    scopes=creds_data.get('scope').split() if creds_data.get('scope') else OAUTH_SCOPES,
                    expiry=expiry
                )
        except Exception as e:
            print(f"Error loading credentials: {e}")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                save_oauth_credentials(creds)
            except Exception as e:
                print(f"Error refreshing credentials: {e}")
                creds = None
        else:
            creds = None

    return creds

def save_oauth_credentials(creds):
    oauth_file = get_oauth_file_path()
    os.makedirs(os.path.dirname(oauth_file), exist_ok=True)
    
    creds_data = {
        'access_token': creds.token,
        'refresh_token': creds.refresh_token,
        'scope': ' '.join(creds.scopes) if creds.scopes else None,
        'token_type': 'Bearer',
        'expiry': creds.expiry.isoformat() if creds.expiry else None
    }
    
    with open(oauth_file, 'w') as f:
        json.dump(creds_data, f, indent=2)

def perform_oauth_login():
    client_config = {
        "installed": {
            "client_id": OAUTH_CLIENT_ID,
            "client_secret": OAUTH_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    
    flow = InstalledAppFlow.from_client_config(client_config, OAUTH_SCOPES)
    
    print("\n\033[94m--- Google OAuth Login ---\033[0m")
    print("1. A browser window should open automatically.")
    print("2. If it doesn't, look for a URL in the console below.")
    print("3. Follow the instructions to authorize the application.")
    print("--------------------------\n")
    
    try:
        creds = flow.run_local_server(port=0)
        save_oauth_credentials(creds)
        print("\n\033[92mLogin successful! Credentials saved.\033[0m")
        return creds
    except Exception as e:
        print(f"\n\033[91mOAuth login failed: {e}\033[0m")
        raise e

def get_auth_token():
    creds = get_oauth_credentials()
    if creds:
        return creds.token
    return None
