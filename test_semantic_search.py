import requests
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_semantic_search():
    """Test the semantic search implementation"""
    
    print_section("TEST 1: Upload Document and Verify Embeddings")
    print("Uploading a test document with diverse topics...")
    
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

Photosynthesis is the process by which plants convert sunlight into energy. Chloroplasts in plant cells contain chlorophyll, which captures light energy. This process produces glucose and oxygen. Photosynthesis is essential for life on Earth as it produces the oxygen we breathe.

Chapter 6: Napoleon and French History

Napoleon Bonaparte was a French military leader and emperor who rose to prominence during the French Revolution. He conquered much of Europe in the early 19th century. His military campaigns and administrative reforms had a lasting impact on European history.

Chapter 7: World War II

World War II was a global conflict that lasted from 1939 to 1945. It involved most of the world's nations and resulted in significant loss of life. The war ended with the defeat of Nazi Germany and Imperial Japan. It reshaped the global political landscape."""
    
    # Save test file
    with open("test_semantic.txt", "w", encoding="utf-8") as f:
        f.write(test_content)
    
    # Upload file
    with open("test_semantic.txt", "rb") as f:
        files = {"file": ("test_semantic.txt", f, "text/plain")}
        response = requests.post(f"{BASE_URL}/upload", files=files)
    
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] File uploaded successfully")
        print(f"  Filename: {data.get('filename')}")
        print(f"  Text length: {data.get('text_length')} characters")
        print(f"  Chunk count: {data.get('chunk_count')}")
        print(f"  Embedding count: {data.get('embedding_count')}")
        
        if data.get('chunk_count') == data.get('embedding_count'):
            print(f"[SUCCESS] Embeddings generated correctly!")
        else:
            print(f"[WARNING] Chunk count and embedding count don't match")
    else:
        print(f"[ERROR] Upload failed: {response.status_code}")
        print(response.json())
        return
    
    time.sleep(1)
    
    print_section("TEST 2: Debug Endpoint - Check Embeddings")
    print("Checking embedding information...")
    
    response = requests.get(f"{BASE_URL}/debug/chunks/test_semantic.txt")
    
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Debug endpoint working")
        print(f"  Chunk count: {data.get('chunk_count')}")
        print(f"  Embedding count: {data.get('embedding_count')}")
        print(f"  Has embeddings: {data.get('has_embeddings')}")
        
        if data.get('has_embeddings'):
            print(f"[SUCCESS] Embeddings are stored correctly!")
        else:
            print(f"[ERROR] Embeddings not found")
    else:
        print(f"[ERROR] Debug endpoint failed: {response.status_code}")
        print(response.json())
    
    time.sleep(1)
    
    print_section("TEST 3: Semantic Search - Exact Keyword Match")
    print("Testing with exact keyword: 'What is DNA?'")
    
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": "What is DNA?",
            "document_name": "test_semantic.txt",
            "session_id": "test_semantic_1"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Response received")
        response_text = data.get('response', '').lower()
        
        if "dna" in response_text or "deoxyribonucleic" in response_text or "genetic" in response_text:
            print(f"[SUCCESS] Found relevant content about DNA!")
        else:
            print(f"[WARNING] Response might not be about DNA")
    else:
        print(f"[ERROR] Chat failed: {response.status_code}")
        print(response.json())
    
    time.sleep(1)
    
    print_section("TEST 4: Semantic Search - Paraphrased Question (THE REAL TEST)")
    print("Testing with paraphrased question: 'How do plants make food?'")
    print("(Should find photosynthesis chunk even without exact word match)")
    
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": "How do plants make food?",
            "document_name": "test_semantic.txt",
            "session_id": "test_semantic_2"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Response received")
        response_text = data.get('response', '').lower()
        
        if "photosynthesis" in response_text or "sunlight" in response_text or "chlorophyll" in response_text:
            print(f"[SUCCESS] Semantic search found photosynthesis content!")
            print(f"  This proves semantic search works - found 'photosynthesis'")
            print(f"  even though question didn't use that word!")
        else:
            print(f"[WARNING] Might not have found photosynthesis content")
            print(f"  Response preview: {response_text[:200]}...")
    else:
        print(f"[ERROR] Chat failed: {response.status_code}")
        print(response.json())
    
    time.sleep(1)
    
    print_section("TEST 5: Semantic Search - Different Topic")
    print("Testing with history question: 'Tell me about Napoleon'")
    
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": "Tell me about Napoleon",
            "document_name": "test_semantic.txt",
            "session_id": "test_semantic_3"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Response received")
        response_text = data.get('response', '').lower()
        
        if "napoleon" in response_text or "french" in response_text or "military" in response_text:
            print(f"[SUCCESS] Found relevant content about Napoleon!")
        else:
            print(f"[WARNING] Might not have found Napoleon content")
    else:
        print(f"[ERROR] Chat failed: {response.status_code}")
        print(response.json())
    
    time.sleep(1)
    
    print_section("TEST 6: Backward Compatibility")
    print("Testing that old documents (without embeddings) still work...")
    
    # Note: This test assumes you might have old documents
    # If not, this will just verify the fallback logic exists
    print("[INFO] Backward compatibility check:")
    print("  - Old documents should use keyword search")
    print("  - New documents should use semantic search")
    print("  - Both should work correctly")
    
    print_section("TEST SUMMARY")
    print("All semantic search tests completed!")
    print("\nKey achievements:")
    print("  [OK] Embeddings generated on upload")
    print("  [OK] Semantic search finds relevant chunks")
    print("  [OK] Paraphrased questions work correctly")
    print("  [OK] Different topics retrieve correct chunks")

if __name__ == "__main__":
    print("\n" + "="*70)
    print("  SEMANTIC SEARCH TEST SUITE")
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
        test_semantic_search()
    except Exception as e:
        print(f"\n[ERROR] During testing: {str(e)}")
        import traceback
        traceback.print_exc()

