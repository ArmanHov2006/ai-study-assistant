import requests
import json

BASE_URL = "http://localhost:8000"

print("="*60)
print("EDGE CASE TESTING")
print("="*60)

# Test 1: Document that doesn't exist
print("\n1. Testing with non-existent document...")
print("-" * 60)
chat_data = {
    "message": "Test question",
    "document_name": "nonexistent.pdf"
}

response = requests.post(f"{BASE_URL}/chat", json=chat_data)
print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code == 200:
    print("[PASS] Test 1: Handled gracefully (normal chat)")
else:
    print("[FAIL] Test 1: Unexpected error")

# Test 2: Question not in document
print("\n\n2. Testing with question not in document...")
print("-" * 60)

# First, make sure test.pdf is uploaded
try:
    with open("test.pdf", "rb") as f:
        files = {"file": ("test.pdf", f, "application/pdf")}
        upload_response = requests.post(f"{BASE_URL}/upload", files=files)
        if upload_response.status_code == 200:
            print("[OK] test.pdf uploaded for testing")
except:
    print("Note: Using existing test.pdf upload")

chat_data = {
    "message": "What is quantum physics?",
    "document_name": "test.pdf"
}

response = requests.post(f"{BASE_URL}/chat", json=chat_data)
print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code == 200:
    response_text = response.json()["response"].lower()
    if "quantum" in response_text or "physics" in response_text:
        print("[PASS] Test 2: Claude responded (may or may not reference document)")
    else:
        print("[INFO] Test 2: Claude responded but may not have addressed the question")
else:
    print("[FAIL] Test 2: Unexpected error")

print("\n" + "="*60)
print("EDGE CASE TESTING COMPLETE")
print("="*60)

