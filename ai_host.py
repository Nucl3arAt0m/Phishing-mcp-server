import requests
import json
from transformers import pipeline
import sys
import logging
from datetime import datetime

logging.basicConfig(
    filename="phishing_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

classifier = pipeline("text-classification", model="distilbert-base-uncased")

def run_ai_host():
    url = "http://localhost:5000"
    try:
        fetch_payload = {
            "jsonrpc": "2.0",
            "method": "fetch_emails",
            "id": 1
        }
        logging.info(f"Sending fetch_emails request: {fetch_payload}")
        response = requests.post(url, json=fetch_payload, timeout=15)
        response.raise_for_status()
        response_json = response.json()
        logging.info(f"Received response: {response_json}")

        if "error" in response_json:
            error_msg = f"Error fetching emails: {response_json.get('error', 'Unknown error')}"
            print(error_msg)
            logging.error(error_msg)
            return
        emails = response_json.get("result", [])
        logging.info(f"Fetched {len(emails)} emails")

        if not emails:
            msg = "No emails fetched."
            print(msg)
            logging.info(msg)
            return

        print("\nProcessing emails...")
        for email in emails:

            scan_payload = {
                "jsonrpc": "2.0",
                "method": "scan_phishing",
                "params": {"text": email},
                "id": 2
            }
            logging.info(f"Sending scan_phishing request for email: {email[:50]}...")
            scan_response = requests.post(url, json=scan_payload, timeout=15)
            scan_response.raise_for_status()
            scan_json = scan_response.json()
            logging.info(f"Scan response: {scan_json}")

            if "error" in scan_json:
                error_msg = f"Error scanning email: {scan_json.get('error', 'Unknown error')}"
                print(error_msg)
                logging.error(error_msg)
                continue
            result = scan_json.get("result", {})

            
            print(f"\nEmail: {result['text'][:50]}...")
            print(f"Phishing: {'Yes' if result['is_phishing'] else 'No'} (Score: {result['score']:.2f})")
            log_msg = (
                f"Email: {result['text'][:50]}... "
                f"Phishing: {'Yes' if result['is_phishing'] else 'No'} "
                f"(Score: {result['score']:.2f}, Keywords: {result['keyword_match']})"
            )
            logging.info(log_msg)

    except requests.exceptions.ConnectionError as e:
        error_msg = f"Connection error: Ensure server.py is running on localhost:5000 ({str(e)})"
        print(error_msg)
        logging.error(error_msg)
        sys.exit(1)
    except requests.exceptions.Timeout as e:
        error_msg = f"Timeout error: Request timed out ({str(e)})"
        print(error_msg)
        logging.error(error_msg)
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP error: {str(e)}"
        print(error_msg)
        logging.error(error_msg)
        sys.exit(1)
    except ValueError as e:
        error_msg = f"Invalid JSON response: {str(e)}"
        print(error_msg)
        logging.error(error_msg)
        sys.exit(1)
    except Exception as e:
        error_msg = f"AI host error: {str(e)}"
        print(error_msg)
        logging.error(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    run_ai_host()