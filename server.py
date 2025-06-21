# phishing_mcp_server/server.py
from jsonrpcserver import method, dispatch, Success
from http.server import BaseHTTPRequestHandler, HTTPServer
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    creds = None
    # Load token if it exists
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save credentials for reuse
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

@method
def fetch_emails():
    try:
        service = get_gmail_service()
        results = service.users().messages().list(userId='me', maxResults=5).execute()
        messages = results.get('messages', [])
        emails = []
        for msg in messages:
            msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
            emails.append(msg_data['snippet'])
        return Success(emails)
    except Exception as e:
        return {"error": f"Failed to fetch emails: {str(e)}"}

@method
def scan_phishing(text):
    return Success(f"Placeholder: Scan text for phishing - {text}")

class JsonRpcHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        request_data = self.rfile.read(content_length).decode('utf-8')
        response = dispatch(request_data)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(str(response).encode('utf-8'))

if __name__ == "__main__":
    server_address = ('localhost', 5000)
    httpd = HTTPServer(server_address, JsonRpcHandler)
    print("MCP server running on localhost:5000")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down server")
        httpd.server_close()