# phishing_mcp_server/test_gmail.py
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
TOKEN_PATH = 'token.json'

def main():
    creds = None
    # Check if token.json exists
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    # If no valid credentials, run OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            # Save credentials to token.json
            with open(TOKEN_PATH, 'w') as token_file:
                token_file.write(creds.to_json())
    # Build Gmail service
    service = build('gmail', 'v1', credentials=creds)
    # Fetch emails
    results = service.users().messages().list(userId='me', maxResults=10).execute()
    messages = results.get('messages', [])
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        print(msg_data['snippet'])

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
