import os.path
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Global Config Path
CONFIG_DIR = Path.home() / '.gmailsweep'
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# Scope for full mail access (needed for permanent delete)
SCOPES = ['https://mail.google.com/']

def get_gmail_service():
    """Authenticates the user and returns the Gmail API service instance."""
    creds = None
    token_path = CONFIG_DIR / 'token.json'
    creds_path = CONFIG_DIR / 'credentials.json'

    # Load existing token if available
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # Refresh or re-authenticate if invalid
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                # If refresh fails, force re-auth
                os.remove(token_path)
                return get_gmail_service()
        else:
            if not os.path.exists(creds_path):
                raise FileNotFoundError("credentials.json not found. Please add it to the project root.")
            
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the new token
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)
