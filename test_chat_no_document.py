import requests

BASE_URL = "http://localhost:8000"

# Test chat without document
print("Testing chat endpoint without document...")
print("="*60)

chat_data = {
    "message": "What are the key skills I should focus on learning in the next 2-3 months to prepare for a software engineering internship? Give me a practical learning roadmap."
}

print("Sending message:", chat_data["message"])
print("\nWaiting for Claude's response...\n")

response = requests.post(f"{BASE_URL}/chat", json=chat_data)

if response.status_code == 200:
    print("="*60)
    print("CLAUDE'S RESPONSE:")
    print("="*60)
    print(response.json()["response"])
    print("="*60)
else:
    print(f"\nError: {response.status_code}")
    print(response.json())


