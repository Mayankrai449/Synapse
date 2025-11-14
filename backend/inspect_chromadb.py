"""
ChromaDB Inspector - View and analyze data in ChromaDB
Run this script to inspect the contents of your ChromaDB collection
"""

import chromadb
from chromadb.config import Settings
import json
from datetime import datetime

# Configuration
CHROMA_PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "text_embeddings"


def inspect_chromadb():
    """Inspect ChromaDB collection and display statistics"""

    print("=" * 80)
    print("ChromaDB Inspector")
    print("=" * 80)

    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

        # Get collection
        collection = client.get_collection(name=COLLECTION_NAME)

        print(f"\nCollection: {COLLECTION_NAME}")
        print(f"Total entries: {collection.count()}")

        if collection.count() == 0:
            print("\n⚠ Collection is empty. Add some data first using the /save endpoint.")
            return

        # Get all data
        print("\n📊 Fetching all data...")
        all_data = collection.get(
            include=['documents', 'metadatas', 'embeddings']
        )

        print(f"Retrieved {len(all_data['ids'])} entries")

        # Statistics
        print("\n" + "=" * 80)
        print("STATISTICS")
        print("=" * 80)

        # Document statistics
        document_ids = set()
        chunked_docs = 0
        chunk_sizes = []
        timestamps = []

        for i, metadata in enumerate(all_data['metadatas']):
            doc_id = metadata.get('document_id')
            if doc_id:
                document_ids.add(doc_id)

            if metadata.get('is_chunked'):
                if metadata.get('chunk_index', 0) == 0:
                    chunked_docs += 1

            chunk_size = metadata.get('chunk_size', 0)
            if chunk_size:
                chunk_sizes.append(chunk_size)

            timestamp = metadata.get('timestamp_unix')
            if timestamp:
                timestamps.append(timestamp)

        print(f"Unique documents: {len(document_ids)}")
        print(f"Chunked documents: {chunked_docs}")

        if chunk_sizes:
            print(f"Average chunk size: {sum(chunk_sizes) / len(chunk_sizes):.0f} characters")
            print(f"Min chunk size: {min(chunk_sizes)} characters")
            print(f"Max chunk size: {max(chunk_sizes)} characters")

        if timestamps:
            oldest = min(timestamps)
            newest = max(timestamps)
            print(f"\nOldest entry: {datetime.fromtimestamp(oldest).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Newest entry: {datetime.fromtimestamp(newest).strftime('%Y-%m-%d %H:%M:%S')}")

        # Embedding statistics
        if all_data['embeddings'] is not None and len(all_data['embeddings']) > 0:
            embedding_dim = len(all_data['embeddings'][0])
            print(f"\nEmbedding dimension: {embedding_dim}")

        # Display sample entries
        print("\n" + "=" * 80)
        print("SAMPLE ENTRIES (First 5)")
        print("=" * 80)

        num_samples = min(5, len(all_data['ids']))

        for i in range(num_samples):
            print(f"\n--- Entry {i + 1} ---")
            print(f"ID: {all_data['ids'][i]}")
            print(f"Text: {all_data['documents'][i][:200]}..." if len(all_data['documents'][i]) > 200 else f"Text: {all_data['documents'][i]}")

            metadata = all_data['metadatas'][i]
            print(f"Metadata:")
            for key, value in metadata.items():
                if key == 'timestamp_unix':
                    readable_time = datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"  {key}: {value} ({readable_time})")
                elif key == 'embedding':
                    continue  # Skip embedding in display
                else:
                    print(f"  {key}: {value}")

        # Search by document ID
        print("\n" + "=" * 80)
        print("DOCUMENTS")
        print("=" * 80)

        for doc_id in list(document_ids)[:3]:  # Show first 3 documents
            # Get all chunks for this document
            doc_data = collection.get(
                where={"document_id": doc_id},
                include=['documents', 'metadatas']
            )

            if doc_data['ids']:
                metadata = doc_data['metadatas'][0]
                print(f"\nDocument ID: {doc_id}")
                print(f"Total chunks: {metadata.get('total_chunks', 1)}")
                print(f"Timestamp: {metadata.get('timestamp_readable', 'N/A')}")

                for i, (chunk_id, text, meta) in enumerate(zip(doc_data['ids'], doc_data['documents'], doc_data['metadatas'])):
                    chunk_idx = meta.get('chunk_index', 0)
                    print(f"  Chunk {chunk_idx}: {text[:100]}...")

        print("\n" + "=" * 80)
        print("✓ Inspection complete!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("1. ChromaDB is initialized (run the FastAPI server once)")
        print("2. The collection exists and has data")


def search_by_time(start_time=None, end_time=None):
    """Search entries by time range"""

    print("\n" + "=" * 80)
    print("TIME-BASED SEARCH")
    print("=" * 80)

    try:
        client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        collection = client.get_collection(name=COLLECTION_NAME)

        # Build where filter
        where_filter = {}

        if start_time or end_time:
            time_conditions = {}
            if start_time:
                time_conditions["$gte"] = start_time
            if end_time:
                time_conditions["$lte"] = end_time

            where_filter = {"timestamp_unix": time_conditions}

        # Get filtered data
        results = collection.get(
            where=where_filter,
            include=['documents', 'metadatas']
        )

        print(f"\nFound {len(results['ids'])} entries")

        for i, (id, text, metadata) in enumerate(zip(results['ids'][:5], results['documents'][:5], results['metadatas'][:5])):
            timestamp = metadata.get('timestamp_unix', 0)
            readable_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n{i+1}. {readable_time}")
            print(f"   {text[:100]}...")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # Inspect the database
    inspect_chromadb()

    # Example: Search for entries from the last hour
    # Uncomment to use:
    # import time
    # one_hour_ago = time.time() - 3600
    # search_by_time(start_time=one_hour_ago)
