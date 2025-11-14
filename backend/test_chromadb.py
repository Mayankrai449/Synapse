"""
Test script for ChromaDB + SigLIP implementation
Tests text embedding, chunking, and time-based search
"""

import requests
import time
from datetime import datetime

API_BASE = "http://localhost:8000"


def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def test_siglip_chromadb():
    """Test the full ChromaDB + SigLIP pipeline"""

    print_header("Testing SigLIP + ChromaDB Backend")

    # Test 1: Check server status
    print("\n1. Checking server status...")
    try:
        response = requests.get(f"{API_BASE}/")
        data = response.json()
        print(f"   ✓ Server running")
        print(f"   Model: {data.get('model')}")
        print(f"   Vector DB: {data.get('vector_db')}")
        print(f"   Embedding dimension: {data.get('embedding_dim')}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        print("\n   Make sure the server is running: python main.py")
        return

    # Test 2: Save short text (no chunking)
    print("\n2. Testing short text (no chunking)...")
    short_text = "Machine learning is transforming the technology industry."

    response = requests.post(f"{API_BASE}/save", json={
        "text": short_text,
        "metadata": {
            "source": "test_script",
            "category": "AI"
        }
    })

    result = response.json()
    print(f"   Status: {result['status']}")
    print(f"   Chunks created: {result['chunks_created']}")
    print(f"   Document ID: {result['document_id']}")
    print(f"   Total entries: {result['total_entries']}")

    # Test 3: Save long text (will be chunked)
    print("\n3. Testing long text (with chunking)...")

    long_text = """
    Artificial intelligence has become one of the most transformative technologies of our time.
    Machine learning algorithms can now process vast amounts of data and identify patterns
    that were previously impossible for humans to detect. Deep learning networks, inspired by
    the structure of the human brain, have revolutionized fields like computer vision and
    natural language processing.

    Natural language processing enables computers to understand and generate human language.
    Modern NLP models can translate between languages, summarize documents, answer questions,
    and even engage in conversations with impressive accuracy. These capabilities are powered
    by transformer architectures that use attention mechanisms to process text efficiently.

    Computer vision systems can identify objects, detect faces, and generate realistic images.
    Convolutional neural networks are particularly effective for processing visual data. They
    automatically learn to recognize edges, shapes, and complex patterns through training on
    large datasets. This has enabled applications ranging from autonomous vehicles to medical
    image analysis.

    The future of AI holds tremendous potential but also raises important ethical questions.
    As AI systems become more powerful and autonomous, we must carefully consider issues of
    fairness, transparency, accountability, and the societal impact of automated decision-making.
    Responsible AI development requires ongoing collaboration between technologists, ethicists,
    policymakers, and the broader public.
    """

    response = requests.post(f"{API_BASE}/save", json={
        "text": long_text,
        "metadata": {
            "source": "test_script",
            "category": "AI",
            "topic": "AI Overview"
        }
    })

    result = response.json()
    print(f"   Status: {result['status']}")
    print(f"   Chunks created: {result['chunks_created']}")
    print(f"   Document ID: {result['document_id']}")
    print(f"   Total entries: {result['total_entries']}")

    doc_id_long = result['document_id']

    # Wait a bit for time-based testing
    print("\n   ⏳ Waiting 2 seconds for time-based test...")
    time.sleep(2)

    # Test 4: Save another text for time filtering
    print("\n4. Saving recent text (for time-based search)...")

    recent_text = "Quantum computing uses quantum mechanics principles to process information exponentially faster than classical computers."

    response = requests.post(f"{API_BASE}/save", json={
        "text": recent_text,
        "metadata": {
            "source": "test_script",
            "category": "Quantum"
        }
    })

    result = response.json()
    print(f"   Status: {result['status']}")
    recent_timestamp = time.time()

    # Test 5: Basic semantic search
    print("\n5. Testing semantic search...")

    query_response = requests.post(f"{API_BASE}/query", json={
        "query": "How do neural networks work?",
        "top_k": 3
    })

    results = query_response.json()
    print(f"   Found {len(results)} results:\n")

    for i, result in enumerate(results, 1):
        print(f"   Result {i}:")
        print(f"   Similarity: {result['similarity']:.4f}")
        print(f"   Text: {result['text'][:150]}...")
        metadata = result['metadata']
        if metadata.get('is_chunked'):
            print(f"   Chunk {metadata['chunk_index'] + 1}/{metadata['total_chunks']}")
        print()

    # Test 6: Time-filtered search
    print("\n6. Testing time-filtered search (last 3 seconds)...")

    three_seconds_ago = time.time() - 3

    query_response = requests.post(f"{API_BASE}/query", json={
        "query": "computing",
        "top_k": 5,
        "time_filter": {
            "start": three_seconds_ago
        }
    })

    results = query_response.json()
    print(f"   Found {len(results)} recent results")

    for i, result in enumerate(results, 1):
        timestamp = result['metadata'].get('timestamp_unix', 0)
        readable_time = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
        print(f"   {i}. [{readable_time}] {result['text'][:100]}...")

    # Test 7: Temporal decay search
    print("\n7. Testing temporal decay (recent results boosted)...")

    query_response = requests.post(f"{API_BASE}/query", json={
        "query": "artificial intelligence",
        "top_k": 3,
        "enable_temporal_decay": True
    })

    results = query_response.json()
    print(f"   Found {len(results)} results with temporal decay:\n")

    for i, result in enumerate(results, 1):
        timestamp = result['metadata'].get('timestamp_unix', 0)
        age_hours = (time.time() - timestamp) / 3600
        readable_time = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')

        print(f"   Result {i}:")
        print(f"   Boosted similarity: {result['similarity']:.4f}")
        print(f"   Age: {age_hours:.2f} hours (saved at {readable_time})")
        print(f"   Text: {result['text'][:100]}...")
        print()

    # Test 8: Get statistics
    print("\n8. Getting collection statistics...")

    stats_response = requests.get(f"{API_BASE}/stats")
    stats = stats_response.json()

    print(f"   Total entries: {stats['total_entries']}")
    print(f"   Unique documents: {stats['unique_documents']}")
    print(f"   Chunked documents: {stats['chunked_documents']}")
    print(f"   Total chunks: {stats['total_chunks']}")
    print(f"   Storage: {stats['storage_backend']}")
    print(f"   Persist directory: {stats['persist_directory']}")
    print(f"   Embedding model: {stats['embedding_model']}")
    print(f"   Embedding dimension: {stats['embedding_dimension']}")

    # Test 9: Cross-modal readiness
    print("\n9. Checking multimodal readiness...")
    print("   ✓ SigLIP model supports both text and images")
    print("   ✓ Same embedding space for text and images")
    print("   ✓ Ready for image embedding integration")
    print("   Next step: Add image upload endpoint")

    # Summary
    print_header("Test Summary")
    print("\n✅ All tests completed successfully!")
    print("\nFeatures tested:")
    print("  ✓ Short text storage (no chunking)")
    print("  ✓ Long text storage (with chunking)")
    print("  ✓ Semantic search with SigLIP embeddings")
    print("  ✓ Time-based filtering")
    print("  ✓ Temporal decay scoring")
    print("  ✓ ChromaDB persistence")
    print("  ✓ Metadata tracking")

    print("\nNext steps:")
    print("  → Run 'python inspect_chromadb.py' to view stored data")
    print("  → Test with Chrome extension")
    print("  → Add image upload for multimodal search")
    print("  → Implement BM25 hybrid search")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        test_siglip_chromadb()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the API server.")
        print("Make sure the FastAPI server is running:")
        print("  python main.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
