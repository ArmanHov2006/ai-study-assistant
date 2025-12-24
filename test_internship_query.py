import requests

BASE_URL = "http://localhost:8000"

# Step 1: Upload PDF (if not already uploaded)
print("1. Uploading test.pdf...")
try:
    with open("test.pdf", "rb") as f:
        files = {"file": ("test.pdf", f, "application/pdf")}
        response = requests.post(f"{BASE_URL}/upload", files=files)
        if response.status_code == 200:
            print("PDF uploaded successfully")
            filename = response.json()["filename"]
            print(f"  Filename: {filename}")
        else:
            print(f"Upload failed: {response.text}")
            # Try to use existing file
            filename = "test.pdf"
except FileNotFoundError:
    print("test.pdf not found, using existing upload")
    filename = "test.pdf"
except Exception as e:
    print(f"Error uploading: {e}")
    filename = "test.pdf"

# Step 2: Ask about best project for internship
print("\n2. Asking Claude about best project for internship...")
chat_data = {
    "message": "I have no finished projects on GitHub and need to apply for an internship in 2-3 months (around February). From the projects in this document, pick the one that: 1) I can learn and complete in 2-3 months, 2) will get the most attention from recruiters, 3) gives me the highest chance of getting selected for an internship. Explain why this project is the best choice for my situation and what makes it stand out to recruiters.",
    "document_name": filename
}

response = requests.post(f"{BASE_URL}/chat", json=chat_data)

if response.status_code == 200:
    print("\n" + "="*60)
    print("CLAUDE'S RECOMMENDATION:")
    print("="*60)
    print(response.json()["response"])
    print("="*60)
else:
    print(f"\nError: {response.status_code}")
    print(response.json())

