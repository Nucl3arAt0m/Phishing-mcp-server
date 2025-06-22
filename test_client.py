import requests
import json

url = "http://localhost:5000"
payload = {
    "jsonrpc": "2.0",
    "method": "fetch_emails",
    "id": 1
}

try:
    response = requests.post(url, json=payload)
    response_json = response.json()
    print("Full response:", response_json)
    if "result" in response_json:
        print("Result:", response_json["result"])
    elif "error" in response_json:
        print("Error:", response_json["error"])
    else:
        print("Unexpected response:", response_json)
except Exception as e:
    print(f"Client error: {e}")
    