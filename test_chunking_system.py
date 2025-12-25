import requests
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_chunking_system():
    """Test the complete chunking and retrieval system"""
    
    print_section("TEST 1: Upload Document and Verify Chunking")
    print("Uploading a test document...")
    
    # Create a test document with multiple topics
    test_content = """Chapter 1: Introduction to Biology

Biology is the study of life. It encompasses everything from tiny microorganisms to massive ecosystems. Life exists in many forms, from single-celled bacteria to complex multicellular organisms like humans.

Chapter 2: Cell Structure

Cells are the basic building blocks of life. There are two main types: prokaryotic and eukaryotic cells. Prokaryotic cells are simpler and lack a nucleus. Examples include bacteria. Eukaryotic cells are more complex and have a nucleus. Examples include animal and plant cells.

Chapter 3: DNA and Genetics

DNA (deoxyribonucleic acid) carries genetic information. It's found in the nucleus of eukaryotic cells. DNA is a double helix structure made of nucleotides. Genes are segments of DNA that code for specific proteins. The genetic code determines an organism's traits and characteristics.

Chapter 4: Evolution

Evolution is the process by which species change over time through natural selection. Charles Darwin proposed the theory of evolution in his book "On the Origin of Species." Natural selection favors traits that help organisms survive and reproduce. Over millions of years, this leads to new species forming.

Chapter 5: Photosynthesis

Photosynthesis is the process by which plants convert sunlight into energy. Chloroplasts in plant cells contain chlorophyll, which captures light energy. This process produces glucose and oxygen. Photosynthesis is essential for life on Earth as it produces the oxygen we breathe."""
    
    # Save test file
    with open("test_biology.txt", "w", encoding="utf-8") as f:
        f.write(test_content)
    
    # Upload file
    with open("test_biology.txt", "rb") as f:
        files = {"file": ("test_biology.txt", f, "text/plain")}
        response = requests.post(f"{BASE_URL}/upload", files=files)
    
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] File uploaded successfully")
        print(f"  Filename: {data.get('filename')}")
        print(f"  Text length: {data.get('text_length')} characters")
        print(f"  Chunk count: {data.get('chunk_count')}")
        
        if data.get('chunk_count', 0) > 0:
            print(f"[SUCCESS] Document was chunked into {data.get('chunk_count')} pieces!")
        else:
            print(f"[WARNING] No chunks created - document might be too short")
    else:
        print(f"[ERROR] Upload failed: {response.status_code}")
        print(response.json())
        return
    
    time.sleep(1)
    
    print_section("TEST 2: Debug Endpoint - Inspect Chunks")
    print("Checking chunk details...")
    
    response = requests.get(f"{BASE_URL}/debug/chunks/test_biology.txt")
    
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Debug endpoint working")
        print(f"  Filename: {data.get('filename')}")
        print(f"  Chunk count: {data.get('chunk_count')}")
        print(f"  Total length: {data.get('total_length')} characters")
        print(f"  First chunk preview: {data.get('first_chunk_preview', '')[:100]}...")
    else:
        print(f"[ERROR] Debug endpoint failed: {response.status_code}")
        print(response.json())
    
    time.sleep(1)
    
    print_section("TEST 3: Smart Retrieval - DNA Question")
    print("Testing if only relevant chunks are retrieved for DNA question...")
    
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": "What is DNA?",
            "document_name": "test_biology.txt",
            "session_id": "test_session_1"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Chat response received")
        print(f"  Session ID: {data.get('session_id')}")
        print(f"  Message count: {data.get('message_count')}")
        print(f"  Response preview: {data.get('response', '')[:200]}...")
        
        # Check if response mentions DNA
        if "dna" in data.get('response', '').lower() or "deoxyribonucleic" in data.get('response', '').lower():
            print(f"[SUCCESS] Response correctly mentions DNA!")
        else:
            print(f"[WARNING] Response might not be about DNA")
    else:
        print(f"[ERROR] Chat failed: {response.status_code}")
        print(response.json())
    
    time.sleep(1)
    
    print_section("TEST 4: Smart Retrieval - Photosynthesis Question")
    print("Testing retrieval for different topic (photosynthesis)...")
    
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": "How does photosynthesis work?",
            "document_name": "test_biology.txt",
            "session_id": "test_session_2"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Chat response received")
        print(f"  Response preview: {data.get('response', '')[:200]}...")
        
        if "photosynthesis" in data.get('response', '').lower() or "chlorophyll" in data.get('response', '').lower():
            print(f"[SUCCESS] Response correctly mentions photosynthesis!")
        else:
            print(f"[WARNING] Response might not be about photosynthesis")
    else:
        print(f"[ERROR] Chat failed: {response.status_code}")
        print(response.json())
    
    time.sleep(1)
    
    print_section("TEST 5: Conversation Memory with Chunks")
    print("Testing if conversation memory works with chunked documents...")
    
    session_id = "test_session_3"
    
    # First message
    response1 = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": "Tell me about cells",
            "document_name": "test_biology.txt",
            "session_id": session_id
        }
    )
    
    if response1.status_code == 200:
        print(f"[OK] First message sent")
        time.sleep(1)
        
        # Follow-up question
        response2 = requests.post(
            f"{BASE_URL}/chat",
            json={
                "message": "What did you tell me about cells?",
                "document_name": "test_biology.txt",
                "session_id": session_id
            }
        )
        
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"[OK] Follow-up response received")
            print(f"  Message count: {data2.get('message_count')}")
            print(f"  Response preview: {data2.get('response', '')[:200]}...")
            
            if "cell" in data2.get('response', '').lower():
                print(f"[SUCCESS] Conversation memory works with chunks!")
            else:
                print(f"[WARNING] Might not be remembering previous context")
        else:
            print(f"[ERROR] Follow-up failed: {response.status_code}")
    else:
        print(f"[ERROR] First message failed: {response1.status_code}")
    
    print_section("TEST SUMMARY")
    print("All tests completed! Review results above.")

if __name__ == "__main__":
    print("\n" + "="*70)
    print("  CHUNKING SYSTEM TEST SUITE")
    print("="*70)
    print("\nWaiting for server to be ready...")
    
    # Wait for server
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/")
            if response.status_code == 200:
                print("[OK] Server is ready!\n")
                break
        except requests.exceptions.ConnectionError:
            if i < max_retries - 1:
                print(f"  Waiting... ({i+1}/{max_retries})")
                time.sleep(2)
            else:
                print("\n[ERROR] Could not connect to server!")
                print("   Make sure the server is running: uvicorn main:app --reload")
                exit(1)
    
    try:
        test_chunking_system()
    except Exception as e:
        print(f"\n[ERROR] During testing: {str(e)}")
        import traceback
        traceback.print_exc()

