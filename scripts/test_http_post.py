import requests
import json
from datetime import datetime

Token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyIiwidHlwZSI6ImFwaV9rZXkiLCJleHAiOjE4MDEyMDcxOTR9.2VSKocb7Isg-QaNBcbPiV1YZ-PFyafFVIypjH0wWfvA"

# Configuration
BASE_URL = "http://localhost:8000"
API_ENDPOINT = "/api/transactions/parse"

def test_transaction_parse():
    url = f"{BASE_URL}{API_ENDPOINT}"
    
    headers = {
        "Authorization": f"Bearer {Token}",
        "Content-Type": "application/json"
    }

    # Example payload matching TransactionParseRequest schema
    payload = {
        "bank_message": "A transaction of SGD 3.64 was made with your UOB Card ending 1234 on 28/01/26 at BUS/MRT. If unauthorised, call 24/7 Fraud Hotline now",
        "bank_name": "UOB",
        "timestamp": datetime.now().isoformat(),
        "remarks": "Bus to CDC"
    }

    print(f"Sending POST request to {url}")
    print("Payload:")
    print(json.dumps(payload, indent=2))
    print("-" * 50)

    try:
        response = requests.post(url, headers=headers, json=payload)
        
        print(f"Status Code: {response.status_code}")
        print("-" * 50)
        print("Response:")
        
        try:
            response_data = response.json()
            print(json.dumps(response_data, indent=2))
        except json.JSONDecodeError:
            print("Raw response (not JSON):")
            print(response.text)

    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure the API is running.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_transaction_parse()

