import json
from jsonrpcserver import method, dispatch, Success
from http.server import BaseHTTPRequestHandler, HTTPServer
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle
import logging
from transformers import pipeline
import socketserver
import re

logging.basicConfig(
    filename="server_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

classifier = pipeline("text-classification", model="distilbert-base-uncased")

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    try:
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
                logging.info("Loaded token.pickle")
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                logging.info("Refreshed expired token")
            else:
                if not os.path.exists('credentials.json'):
                    logging.error("credentials.json not found")
                    raise FileNotFoundError("credentials.json not found")
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
                logging.info("Authenticated via OAuth")
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
                logging.info("Saved new token.pickle")
        service = build('gmail', 'v1', credentials=creds)
        logging.info("Gmail service initialized")
        return service
    except Exception as e:
        logging.error(f"Failed to initialize Gmail service: {str(e)}")
        raise

@method
def fetch_emails():
    try:
        service = get_gmail_service()
        results = service.users().messages().list(userId='me', maxResults=10).execute()
        messages = results.get('messages', [])
        logging.info(f"Fetched {len(messages)} messages")
        emails = []
        for msg in messages:
            msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
            emails.append(msg_data['snippet'])
            logging.info(f"Retrieved email snippet: {msg_data['snippet'][:50]}...")
        return Success(emails)
    except Exception as e:
        logging.error(f"Failed to fetch emails: {str(e)}")
        return {"error": f"Failed to fetch emails: {str(e)}"}

@method
def scan_phishing(text):
    try:
        result = classifier(text)
        distilbert_score = result[0]["score"]
        distilbert_label = result[0]["label"] == "POSITIVE" and distilbert_score > 0.55
        phishing_keywords = [
            r'\burgent\b', r'\blocked\b', r'\breset your password\b',
            r'\bclick this link\b', r'\bverify your account\b',
            r'\bdata will be erased\b', r'\baccount is locked\b'
        ]
        keyword_match = any(re.search(pattern, text, re.IGNORECASE) for pattern in phishing_keywords)
        is_phishing = distilbert_label or keyword_match  

        logging.info(f"Scanned text: {text[:50]}... Phishing: {is_phishing} (Score: {distilbert_score:.2f}, Keywords: {keyword_match})")
        return Success({
            "text": text,
            "is_phishing": is_phishing,
            "score": distilbert_score,
            "keyword_match": keyword_match
        })
    except Exception as e:
        logging.error(f"Phishing scan failed: {str(e)}")
        return {"error": f"Phishing scan failed: {str(e)}"}

class JsonRpcHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            request_data = self.rfile.read(content_length).decode('utf-8')
            logging.info(f"Received request: {request_data}")
            response = dispatch(request_data)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(str(response).encode('utf-8'))
        except BrokenPipeError as e:
            logging.error(f"Broken pipe error: {str(e)}")
            return
        except Exception as e:
            logging.error(f"Server error: {str(e)}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            try:
                self.wfile.write(json.dumps({"jsonrpc": "2.0", "error": {"code": -32000, "message": str(e)}, "id": None}).encode('utf-8'))
            except BrokenPipeError:
                logging.error("Broken pipe error during error response")
                return

if __name__ == "__main__":
    server_address = ('localhost', 5000)
    httpd = HTTPServer(server_address, JsonRpcHandler)
    print("MCP server running on localhost:5000")
    logging.info("MCP server started")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down server")
        logging.info("MCP server stopped")
        httpd.server_close()