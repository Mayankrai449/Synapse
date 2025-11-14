"""
Test script to demonstrate chunking functionality
Run this after starting the FastAPI server
"""

import requests
import json

API_BASE = "http://localhost:8000"

def test_chunking():
    print("=" * 60)
    print("Testing Text Chunking Feature")
    print("=" * 60)

    # Test 1: Short text (no chunking needed)
    print("\n1. Testing short text (should create 1 chunk)...")
    short_text = "This is a short text that doesn't need chunking."

    response = requests.post(f"{API_BASE}/save", json={
        "text": short_text,
        "metadata": {"test": "short_text"}
    })

    result = response.json()
    print(f"   Status: {result['status']}")
    print(f"   Chunks created: {result['chunks_created']}")
    print(f"   Document ID: {result['document_id']}")

    # Test 2: Long text (will be chunked)
    print("\n2. Testing long text (should create multiple chunks)...")

    long_text = """
    Artificial Intelligence has transformed the way we interact with technology.
    Machine learning algorithms can now recognize patterns in vast amounts of data.
    Deep learning networks have revolutionized computer vision and natural language processing.

    Neural networks are inspired by the structure of the human brain. They consist of
    interconnected nodes that process information in layers. Each layer extracts
    increasingly complex features from the input data. This hierarchical approach
    has proven remarkably effective for many tasks.

    Natural language processing enables computers to understand human language.
    Modern NLP models can translate between languages, summarize documents, and
    answer questions with impressive accuracy. These capabilities are powered by
    transformer architectures that use attention mechanisms to process text.

    Computer vision systems can now identify objects, detect faces, and even
    generate realistic images. Convolutional neural networks are particularly
    well-suited for processing visual data. They automatically learn to recognize
    edges, shapes, and complex patterns through training on large datasets.

    The future of AI holds immense potential. As models become more sophisticated
    and computational resources more abundant, we can expect AI to tackle
    increasingly complex problems. However, this progress also raises important
    ethical considerations about fairness, transparency, and the societal impact
    of automated decision-making systems.
    """

    response = requests.post(f"{API_BASE}/save", json={
        "text": long_text,
        "metadata": {"test": "long_text", "topic": "AI"}
    })

    result = response.json()
    print(f"   Status: {result['status']}")
    print(f"   Chunks created: {result['chunks_created']}")
    print(f"   Document ID: {result['document_id']}")
    print(f"   Total entries in store: {result['total_entries']}")

    # Test 3: Query the chunked data
    print("\n3. Testing query with chunked data...")

    query_response = requests.post(f"{API_BASE}/query", json={
        "query": "How do neural networks work?",
        "top_k": 3
    })

    results = query_response.json()
    print(f"   Found {len(results)} results:")

    for i, result in enumerate(results, 1):
        print(f"\n   Result {i}:")
        print(f"   Similarity: {result['similarity']:.4f}")
        print(f"   Text preview: {result['text'][:100]}...")
        metadata = result['metadata']
        if metadata.get('is_chunked'):
            print(f"   Chunk {metadata['chunk_index'] + 1} of {metadata['total_chunks']}")
            print(f"   Document ID: {metadata['document_id']}")

    # Test 4: Get statistics
    print("\n4. Getting storage statistics...")

    stats_response = requests.get(f"{API_BASE}/stats")
    stats = stats_response.json()

    print(f"   Total entries: {stats['total_entries']}")
    print(f"   Unique documents: {stats['unique_documents']}")
    print(f"   Chunked documents: {stats['chunked_documents']}")
    print(f"   Total chunks: {stats['total_chunks']}")
    print(f"   Chunk size: {stats['chunking_config']['chunk_size']} chars")
    print(f"   Overlap: {stats['chunking_config']['overlap']} chars")

    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_chunking()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API server.")
        print("Make sure the FastAPI server is running on http://localhost:8000")
    except Exception as e:
        print(f"Error: {e}")
