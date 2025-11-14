from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import chromadb
from chromadb.config import Settings
import uuid
import re
import time
import json
import os
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv
from rank_bm25 import BM25Okapi
from openai import OpenAI
from urllib.parse import urlparse, unquote
from siglip_embeddings import get_siglip_embeddings
from image_utils import (
    get_document_image_dir,
    download_image_from_url,
    save_uploaded_image,
    get_image_dimensions,
    IMAGE_STORAGE_DIR
)

# Load environment variables
load_dotenv()

# Configure OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    openai_model = "gpt-4.1"
else:
    openai_client = None
    openai_model = None
    print("Warning: OPENAI_API_KEY not found. Query responses will be disabled.")

app = FastAPI(title="SigLIP Embedding Search API with ChromaDB")

# Add CORS middleware to allow Chrome extension requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chunking configuration
CHUNK_SIZE = 800  # characters per chunk
CHUNK_OVERLAP = 150  # overlap between chunks
MIN_CHUNK_SIZE = 100  # minimum chunk size

# ChromaDB configuration
CHROMA_PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "text_embeddings"

# Initialize ChromaDB client (persistent)
chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

# Initialize SigLIP embeddings (singleton)
siglip = get_siglip_embeddings()

# Get embedding dimension
EMBEDDING_DIM = siglip.get_embedding_dimension()


# Custom embedding function for ChromaDB
class SigLIPEmbeddingFunction(chromadb.EmbeddingFunction):
    """ChromaDB-compatible embedding function using SigLIP"""

    def __call__(self, input: chromadb.Documents) -> chromadb.Embeddings:
        # Batch embed texts
        embeddings = siglip.embed_texts(input)
        return embeddings


# Initialize or get collection
try:
    collection = chroma_client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=SigLIPEmbeddingFunction()
    )
    print(f"Loaded existing collection: {COLLECTION_NAME}")
except:
    collection = chroma_client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=SigLIPEmbeddingFunction(),
        metadata={"hnsw:space": "cosine"}  # Use cosine similarity
    )
    print(f"Created new collection: {COLLECTION_NAME}")


# BM25 Index (for keyword-based search)
bm25_index = None
bm25_documents = []
bm25_ids = []


def get_time_of_day(hour: int) -> str:
    """Convert hour to time of day label"""
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 21:
        return "evening"
    else:
        return "night"


def rebuild_bm25_index():
    """Rebuild BM25 index from ChromaDB collection"""
    global bm25_index, bm25_documents, bm25_ids

    try:
        # Get all text documents from ChromaDB
        all_data = collection.get(where={"type": "text"})

        if not all_data['documents']:
            bm25_index = None
            bm25_documents = []
            bm25_ids = []
            return

        # Tokenize documents for BM25
        bm25_documents = all_data['documents']
        bm25_ids = all_data['ids']

        # Simple tokenization (split by whitespace and lowercase)
        tokenized_docs = [doc.lower().split() for doc in bm25_documents]

        # Create BM25 index
        bm25_index = BM25Okapi(tokenized_docs)
        print(f"BM25 index rebuilt with {len(bm25_documents)} documents")

    except Exception as e:
        print(f"Error rebuilding BM25 index: {e}")
        bm25_index = None


def reciprocal_rank_fusion(semantic_results: List[tuple], bm25_results: List[tuple], k: int = 60) -> List[tuple]:
    """
    Combine semantic search and BM25 results using Reciprocal Rank Fusion (RRF)

    Args:
        semantic_results: List of (id, score) tuples from semantic search
        bm25_results: List of (id, score) tuples from BM25
        k: Constant for RRF (default 60)

    Returns:
        List of (id, fused_score) tuples sorted by fused score
    """
    rrf_scores = {}

    # Add semantic search scores
    for rank, (doc_id, _) in enumerate(semantic_results):
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (k + rank + 1)

    # Add BM25 scores
    for rank, (doc_id, _) in enumerate(bm25_results):
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (k + rank + 1)

    # Sort by fused score
    fused_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    return fused_results


# Initialize BM25 index on startup
rebuild_bm25_index()


# Pydantic models
class TextInput(BaseModel):
    text: str
    metadata: Dict = {}
    enable_chunking: bool = True  # Auto-chunk large texts


class QueryInput(BaseModel):
    query: str
    top_k: int = 5
    top_k_images: int = 3  # Number of image results to return
    include_images: bool = True  # Enable/disable image results
    enable_temporal_decay: bool = True  # Boost recent results (helps with recency bias)
    use_bm25_fusion: bool = True  # Enable BM25 + RRF fusion


class SourceDocument(BaseModel):
    document_id: str
    url: Optional[str] = None
    title: Optional[str] = None
    domain: Optional[str] = None
    favicon: Optional[str] = None
    timestamp: Optional[str] = None
    snippet: str  # First 200 chars
    relevance_score: float
    structured_content: Optional[Dict] = None  # Headings, paragraphs, lists, tables, images
    youtube_videos: Optional[List[Dict]] = None
    clean_html: Optional[str] = None


class QueryResponse(BaseModel):
    response: str  # Tailored response from GPT-4.1
    images: List[str]  # List of image URLs
    sources: List[SourceDocument] = []  # Source attribution with full content


class SearchResult(BaseModel):
    type: str  # "text" or "image"
    text: Optional[str] = None  # For text results
    image_url: Optional[str] = None  # For image results
    similarity: float
    metadata: Dict


# Helper functions
def deserialize_metadata(metadata: Dict) -> Dict:
    """
    Deserialize JSON strings in metadata back to dictionaries/lists

    Args:
        metadata: Metadata dictionary from ChromaDB

    Returns:
        Metadata with deserialized complex fields
    """
    deserialized = {}
    for key, value in metadata.items():
        if isinstance(value, str):
            # Try to parse as JSON
            try:
                deserialized[key] = json.loads(value)
            except (json.JSONDecodeError, ValueError):
                # Not JSON, keep as string
                deserialized[key] = value
        else:
            # Keep non-string values as-is
            deserialized[key] = value
    return deserialized


def get_file_extension_from_url(url: str) -> str:
    """
    Extract file extension from URL, handling query parameters correctly

    Args:
        url: Image URL (may contain query parameters)

    Returns:
        File extension (e.g., '.jpg', '.png') or '.jpg' as default
    """
    try:
        # Parse URL to get path without query parameters
        parsed_url = urlparse(url)
        path = unquote(parsed_url.path)

        # Extract extension from path
        extension = Path(path).suffix.lower()

        # Validate extension is an image format
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg'}
        if extension in valid_extensions:
            return extension

        # Default to .jpg if no valid extension found
        return '.jpg'
    except Exception as e:
        print(f"Error extracting extension from URL {url}: {e}")
        return '.jpg'


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split text into overlapping chunks, trying to preserve sentence boundaries.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())

            if overlap > 0 and len(current_chunk) >= overlap:
                overlap_text = current_chunk[-overlap:].strip()
                current_chunk = overlap_text + " " + sentence
            else:
                current_chunk = sentence
        else:
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    if len(chunks) > 1:
        chunks = [c for c in chunks if len(c) >= MIN_CHUNK_SIZE]

    return chunks if chunks else [text]


async def process_content_background(
    doc_id: str,
    text: str,
    metadata_dict: Dict,
    enable_chunking: bool,
    image_url_list: List[str],
    uploaded_images: List[tuple]  # List of (filename, file_content) tuples
):
    """
    Background task to process text chunking and image embedding.
    Processes images in parallel for better performance.
    """
    try:
        print(f"\n=== Background processing started for {doc_id} ===")
        current_time = time.time()

        # Serialize complex metadata fields to JSON strings for ChromaDB
        serialized_metadata = {}
        for key, value in metadata_dict.items():
            if isinstance(value, (dict, list)):
                serialized_metadata[key] = json.dumps(value)
            elif isinstance(value, (str, int, float, bool)) or value is None:
                serialized_metadata[key] = value
            else:
                serialized_metadata[key] = str(value)

        # Prepare lists for batch ChromaDB insert
        all_ids = []
        all_documents = []
        all_metadatas = []
        all_embeddings = []

        # ===== PROCESS TEXT =====
        text_chunks_count = 0
        if text.strip():
            try:
                print(f"Processing text content in background...")
                if enable_chunking:
                    chunks = chunk_text(text)
                else:
                    chunks = [text]

                text_chunks_count = len(chunks)
                print(f"✓ Created {text_chunks_count} text chunks")

                # Get readable timestamp with time-of-day
                timestamp_readable = metadata_dict.get("timestamp", "")
                enhanced_timestamp = timestamp_readable
                if timestamp_readable:
                    try:
                        dt = datetime.fromisoformat(timestamp_readable.replace("T", " ").split(".")[0])
                        day_name = dt.strftime("%A")
                        time_str = dt.strftime("%I:%M %p")
                        time_of_day = get_time_of_day(dt.hour)
                        enhanced_timestamp = f"{day_name} {time_of_day}, {time_str}"
                    except Exception as e:
                        print(f"Warning: Could not parse timestamp: {e}")
                        enhanced_timestamp = timestamp_readable

                for idx, chunk in enumerate(chunks):
                    try:
                        chunk_id = f"{doc_id}_chunk_{idx}"
                        chunk_with_timestamp = chunk
                        if enhanced_timestamp:
                            chunk_with_timestamp = f"{chunk}\n[Saved: {enhanced_timestamp}]"

                        text_embedding = siglip.embed_text(chunk_with_timestamp)

                        chunk_metadata = {
                            **serialized_metadata,
                            "type": "text",
                            "document_id": doc_id,
                            "chunk_index": idx,
                            "total_chunks": text_chunks_count,
                            "is_chunked": text_chunks_count > 1,
                            "chunk_size": len(chunk),
                            "timestamp_unix": current_time,
                            "timestamp_readable": timestamp_readable,
                        }

                        all_ids.append(chunk_id)
                        all_documents.append(chunk_with_timestamp)
                        all_metadatas.append(chunk_metadata)
                        all_embeddings.append(text_embedding)

                    except Exception as e:
                        print(f"✗ Error processing text chunk {idx} in background: {e}")

            except Exception as e:
                print(f"✗ Error in background text processing: {e}")

        # ===== PROCESS IMAGES IN PARALLEL =====
        images_saved = 0
        image_dir = None

        if uploaded_images or image_url_list:
            image_dir = get_document_image_dir(doc_id)
            print(f"✓ Created image directory: {image_dir}")

        # Create async tasks for parallel image processing
        async def process_uploaded_image(idx: int, filename: str, file_content: bytes):
            try:
                print(f"Processing uploaded image {idx + 1} in background")
                file_extension = Path(filename).suffix or ".jpg"
                save_filename = f"image_{idx}{file_extension}"
                file_path = str(Path(image_dir) / save_filename)

                if save_uploaded_image(file_content, file_path):
                    dimensions = None
                    try:
                        dimensions = get_image_dimensions(file_path)
                    except Exception as e:
                        print(f"Warning: Could not get dimensions: {e}")

                    image_embedding = siglip.embed_image(file_path)
                    image_id = f"{doc_id}_image_{idx}"
                    alt_text = serialized_metadata.get(f"image_{idx}_alt", "")
                    image_document = f"[IMAGE] {alt_text}" if alt_text else f"[IMAGE] Uploaded image {idx}"

                    image_metadata = {
                        "type": "image",
                        "document_id": doc_id,
                        "image_index": idx,
                        "file_path": file_path,
                        "filename": save_filename,
                        "alt_text": alt_text,
                        "source": "upload",
                        "timestamp_unix": current_time,
                        **serialized_metadata,
                        **(dimensions or {})
                    }

                    return (image_id, image_document, image_metadata, image_embedding, save_filename)
            except Exception as e:
                print(f"✗ Error processing uploaded image {idx} in background: {e}")
                return None

        async def process_image_url(idx: int, img_url: str):
            try:
                print(f"Processing image URL {idx + 1} in background")
                file_extension = get_file_extension_from_url(img_url)
                filename = f"image_url_{idx}{file_extension}"
                file_path = str(Path(image_dir) / filename)

                try:
                    download_success = await download_image_from_url(img_url, file_path)
                except Exception as e:
                    print(f"Download failed: {e}")
                    download_success = False

                if download_success:
                    dimensions = None
                    try:
                        dimensions = get_image_dimensions(file_path)
                    except Exception as e:
                        print(f"Warning: Could not get dimensions: {e}")

                    image_embedding = siglip.embed_image(file_path)
                    image_id = f"{doc_id}_image_url_{idx}"
                    alt_text = serialized_metadata.get(f"image_url_{idx}_alt", "")
                    image_document = f"[IMAGE] {alt_text}" if alt_text else f"[IMAGE] Image from {img_url}"

                    image_metadata = {
                        "type": "image",
                        "document_id": doc_id,
                        "image_index": len(uploaded_images) + idx,
                        "file_path": file_path,
                        "filename": filename,
                        "source_url": img_url,
                        "alt_text": alt_text,
                        "source": "url",
                        "timestamp_unix": current_time,
                        **serialized_metadata,
                        **(dimensions or {})
                    }

                    return (image_id, image_document, image_metadata, image_embedding, filename)
            except Exception as e:
                print(f"✗ Error processing image URL {idx} in background: {e}")
                return None

        # Process all images in parallel
        image_tasks = []

        # Add uploaded image tasks
        for idx, (filename, file_content) in enumerate(uploaded_images):
            image_tasks.append(process_uploaded_image(idx, filename, file_content))

        # Add URL image tasks
        for idx, img_url in enumerate(image_url_list):
            image_tasks.append(process_image_url(idx, img_url))

        # Wait for all image tasks to complete
        if image_tasks:
            print(f"Processing {len(image_tasks)} images in parallel...")
            image_results = await asyncio.gather(*image_tasks, return_exceptions=True)

            for result in image_results:
                if result and not isinstance(result, Exception):
                    image_id, image_document, image_metadata, image_embedding, filename = result
                    all_ids.append(image_id)
                    all_documents.append(image_document)
                    all_metadatas.append(image_metadata)
                    all_embeddings.append(image_embedding)
                    images_saved += 1

        # ===== SAVE TO CHROMADB =====
        if all_ids:
            try:
                print(f"Saving {len(all_ids)} entries to ChromaDB in background...")
                collection.add(
                    ids=all_ids,
                    documents=all_documents,
                    metadatas=all_metadatas,
                    embeddings=all_embeddings
                )
                print(f"✓ Saved to ChromaDB successfully")

                if text_chunks_count > 0:
                    try:
                        rebuild_bm25_index()
                        print(f"✓ BM25 index rebuilt")
                    except Exception as e:
                        print(f"Warning: Could not rebuild BM25 index: {e}")

            except Exception as e:
                print(f"✗ Error saving to ChromaDB in background: {e}")

        print(f"✓ Background processing completed for {doc_id}: {text_chunks_count} chunks, {images_saved} images")

    except Exception as e:
        print(f"✗ CRITICAL ERROR in background processing: {e}")
        import traceback
        traceback.print_exc()


# API Routes
@app.get("/")
def root():
    return {
        "message": "SigLIP Embedding Search API with ChromaDB - Hybrid Search with BM25 + RRF Fusion",
        "models": {
            "embedding": "google/siglip-so400m-patch14-384",
            "llm": "gpt-4.1"
        },
        "vector_db": "ChromaDB",
        "embedding_dim": EMBEDDING_DIM,
        "features": [
            "Hybrid search: BM25 keyword search + Semantic embeddings with RRF fusion",
            "Cross-modal search: Text queries find images, image queries find text",
            "Unified vector space for text and images (1152-dim)",
            "Natural language time queries with enhanced timestamps (e.g., 'notes from yesterday morning')",
            "Time-of-day labels: morning, afternoon, evening, night",
            "Temporal decay for recency bias",
            "Automatic text chunking",
            "Image embedding and storage",
            "GPT-4.1 for tailored query responses"
        ],
        "endpoints": {
            "/save": "POST - Save text and/or images with embeddings (multipart/form-data)",
            "/query": "POST - Query with natural language, returns GPT-4.1 response + images + sources",
            "/source/{document_id}": "GET - Get full source document with structured content for readonly view",
            "/images/{document_id}/{filename}": "GET - Serve stored images",
            "/stats": "GET - Get collection statistics",
            "/clear": "DELETE - Clear all embeddings and images"
        }
    }


@app.post("/save")
async def save_content(
    background_tasks: BackgroundTasks,
    text: str = Form(default=""),
    metadata: str = Form(default="{}"),
    enable_chunking: bool = Form(default=True),
    image_urls: str = Form(default="[]"),  # JSON array of image URLs
    images: List[UploadFile] = File(default=[])  # Uploaded image files
):
    """
    Save text and images with embeddings to ChromaDB using background tasks.
    Returns immediately while processing happens asynchronously.

    Supports both text chunking and image embeddings in the same vector space.
    Images are processed in parallel for better performance.

    Args:
        background_tasks: FastAPI background tasks
        text: Text content to save
        metadata: JSON string with metadata
        enable_chunking: Whether to chunk large text
        image_urls: JSON array of image URLs to download and embed
        images: Uploaded image files (multipart/form-data)

    Returns:
        Immediate success response with document_id while processing continues in background
    """
    try:
        # Log received data for debugging
        print(f"\n=== /save endpoint called ===")
        print(f"Text length: {len(text)} chars")
        print(f"Metadata length: {len(metadata)} chars")
        print(f"Image URLs: {image_urls[:200]}..." if len(image_urls) > 200 else f"Image URLs: {image_urls}")
        print(f"Uploaded images: {len(images)}")
        print(f"Enable chunking: {enable_chunking}")

        # Generate unique document ID
        doc_id = str(uuid.uuid4())
        print(f"Generated document ID: {doc_id}")

        # Parse metadata
        try:
            metadata_dict = json.loads(metadata)
            print(f"✓ Metadata parsed successfully")
        except Exception as e:
            print(f"✗ Error parsing metadata: {e}")
            metadata_dict = {}

        # Parse image URLs
        try:
            image_url_list = json.loads(image_urls)
            print(f"✓ Parsed {len(image_url_list)} image URLs")
        except Exception as e:
            print(f"✗ Error parsing image URLs: {e}")
            image_url_list = []

        # Read uploaded images into memory (so background task can access them)
        uploaded_images = []
        for uploaded_file in images:
            file_content = await uploaded_file.read()
            uploaded_images.append((uploaded_file.filename, file_content))

        print(f"✓ Read {len(uploaded_images)} uploaded images into memory")

        # Add background task
        background_tasks.add_task(
            process_content_background,
            doc_id=doc_id,
            text=text,
            metadata_dict=metadata_dict,
            enable_chunking=enable_chunking,
            image_url_list=image_url_list,
            uploaded_images=uploaded_images
        )

        print(f"✓ Background task queued for document {doc_id}")

        # Return immediately with success
        return {
            "status": "success",
            "message": "Content received and queued for processing",
            "document_id": doc_id,
            "processing_status": "queued",
            "text_length": len(text),
            "image_urls_count": len(image_url_list),
            "uploaded_images_count": len(uploaded_images)
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ CRITICAL ERROR in /save endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error saving content: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def query_content(query_input: QueryInput):
    """
    Query for similar content using hybrid search (BM25 + Semantic + RRF fusion).

    Returns a tailored response from GPT-4.1 and relevant images.

    Cross-modal search: Text queries can find relevant images and vice versa!

    Natural language time queries work because timestamps are embedded in chunk text.
    Examples: "notes from yesterday", "this morning's ideas", "last week about AI"
    """
    try:
        import math

        # ===== GET TEXT RESULTS WITH HYBRID SEARCH =====
        text_chunks = []

        if query_input.use_bm25_fusion and bm25_index:
            # HYBRID SEARCH: BM25 + Semantic + RRF Fusion

            # 1. Semantic search
            semantic_results_raw = collection.query(
                query_texts=[query_input.query],
                n_results=query_input.top_k * 3,  # Get more candidates
                where={"type": "text"}
            )

            # Convert to (id, score) tuples for RRF
            semantic_results = []
            if semantic_results_raw['ids'] and len(semantic_results_raw['ids'][0]) > 0:
                for i in range(len(semantic_results_raw['ids'][0])):
                    doc_id = semantic_results_raw['ids'][0][i]
                    distance = semantic_results_raw['distances'][0][i]
                    similarity = 1 - distance
                    semantic_results.append((doc_id, similarity))

            # 2. BM25 search
            query_tokens = query_input.query.lower().split()
            bm25_scores = bm25_index.get_scores(query_tokens)

            # Get top BM25 results
            bm25_results = []
            top_bm25_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)
            for idx in top_bm25_indices[:query_input.top_k * 3]:
                bm25_results.append((bm25_ids[idx], bm25_scores[idx]))

            # 3. RRF Fusion
            fused_results = reciprocal_rank_fusion(semantic_results, bm25_results)

            # Apply temporal decay to fused results
            if query_input.enable_temporal_decay:
                reranked_results = []
                for doc_id, rrf_score in fused_results[:query_input.top_k * 2]:
                    # Get metadata from ChromaDB
                    doc_data = collection.get(ids=[doc_id])
                    if doc_data['metadatas'] and len(doc_data['metadatas']) > 0:
                        metadata = doc_data['metadatas'][0]
                        timestamp_unix = metadata.get('timestamp_unix', time.time())
                        age_hours = (time.time() - timestamp_unix) / 3600

                        # Temporal decay
                        decay_factor = math.exp(-age_hours / 24)
                        final_score = 0.7 * rrf_score + 0.3 * decay_factor

                        reranked_results.append((doc_id, final_score))

                reranked_results.sort(key=lambda x: x[1], reverse=True)
                fused_results = reranked_results

            # Get top K document IDs
            top_doc_ids = [doc_id for doc_id, _ in fused_results[:query_input.top_k]]

            # Fetch full documents
            if top_doc_ids:
                top_docs_data = collection.get(ids=top_doc_ids)
                text_chunks = top_docs_data['documents'] if top_docs_data['documents'] else []

        else:
            # SEMANTIC SEARCH ONLY (fallback)
            text_results_raw = collection.query(
                query_texts=[query_input.query],
                n_results=query_input.top_k,
                where={"type": "text"}
            )

            if text_results_raw['documents'] and len(text_results_raw['documents'][0]) > 0:
                text_chunks = text_results_raw['documents'][0]

        # ===== GET IMAGE RESULTS =====
        image_urls = []
        if query_input.include_images:
            image_results_raw = collection.query(
                query_texts=[query_input.query],
                n_results=query_input.top_k_images,
                where={"type": "image"}
            )

            if image_results_raw['ids'] and len(image_results_raw['ids'][0]) > 0:
                for i in range(len(image_results_raw['ids'][0])):
                    metadata = image_results_raw['metadatas'][0][i]
                    doc_id = metadata.get('document_id', '')
                    filename = metadata.get('filename', '')
                    if doc_id and filename:
                        image_urls.append(f"/images/{doc_id}/{filename}")

        # ===== BUILD SOURCE ATTRIBUTION =====
        sources = []
        seen_documents = set()  # Track unique documents

        # Get source documents from text results
        if text_chunks:
            # Get full data for text chunks to access metadata
            if query_input.use_bm25_fusion and bm25_index:
                # For hybrid search, we already have top_doc_ids
                source_ids = top_doc_ids[:query_input.top_k]
            else:
                # For semantic-only search
                if text_results_raw['ids'] and len(text_results_raw['ids'][0]) > 0:
                    source_ids = text_results_raw['ids'][0]
                else:
                    source_ids = []

            # Fetch metadata for each source chunk
            for chunk_id in source_ids:
                chunk_data = collection.get(ids=[chunk_id])
                if chunk_data['metadatas'] and len(chunk_data['metadatas']) > 0:
                    raw_metadata = chunk_data['metadatas'][0]
                    # Deserialize JSON strings back to dicts/lists
                    metadata = deserialize_metadata(raw_metadata)
                    doc_id = metadata.get('document_id')

                    # Only include each document once
                    if doc_id and doc_id not in seen_documents:
                        seen_documents.add(doc_id)

                        # Get snippet (first chunk of the document)
                        snippet_text = chunk_data['documents'][0] if chunk_data['documents'] else ""
                        snippet = snippet_text[:200] + ("..." if len(snippet_text) > 200 else "")

                        # Calculate relevance score (from distance/similarity)
                        relevance_score = 0.0
                        if query_input.use_bm25_fusion and fused_results:
                            # Find this doc in fused results
                            for fused_id, score in fused_results:
                                if chunk_id == fused_id:
                                    relevance_score = float(score)
                                    break
                        elif text_results_raw.get('distances'):
                            # Use semantic similarity
                            try:
                                idx = source_ids.index(chunk_id)
                                distance = text_results_raw['distances'][0][idx]
                                relevance_score = 1 - distance
                            except (IndexError, ValueError):
                                relevance_score = 0.5

                        # Build source document
                        source = SourceDocument(
                            document_id=doc_id,
                            url=metadata.get('url'),
                            title=metadata.get('title'),
                            domain=metadata.get('domain'),
                            favicon=metadata.get('favicon'),
                            timestamp=metadata.get('timestamp_readable'),
                            snippet=snippet,
                            relevance_score=relevance_score,
                            structured_content=metadata.get('structured_content'),
                            youtube_videos=metadata.get('youtube_videos'),
                            clean_html=metadata.get('clean_html')
                        )
                        sources.append(source)

        # ===== GENERATE OPENAI RESPONSE =====
        openai_response = ""

        if openai_client and text_chunks:
            # Prepare context from top K chunks
            context = "\n\n".join([f"Chunk {i+1}:\n{chunk}" for i, chunk in enumerate(text_chunks)])

            # Create prompt for OpenAI
            prompt = f"""Based on the following context chunks from the user's saved notes, provide a clear, concise, and helpful response to their query.

Query: {query_input.query}

Context:
{context}

Instructions:
- Provide a direct, tailored answer based on the context
- If the context doesn't contain relevant information, say so briefly
- Keep the response concise and natural
- Don't mention "chunks" or technical details

Response:"""

            try:
                completion = openai_client.chat.completions.create(
                    model=openai_model,
                    max_tokens=1024,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                openai_response = completion.choices[0].message.content
            except Exception as e:
                print(f"OpenAI API error: {e}")
                openai_response = "I found relevant information but couldn't generate a response. Please check the results."

        elif not openai_client:
            openai_response = "OpenAI API key not configured. Please add OPENAI_API_KEY to your .env file."
        else:
            openai_response = "No relevant text chunks found for your query."

        return QueryResponse(
            response=openai_response,
            images=image_urls,
            sources=sources
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying content: {str(e)}")


@app.get("/source/{document_id}")
async def get_source(document_id: str):
    """
    Get full source document by ID including all structured content for readonly view

    Args:
        document_id: Document identifier

    Returns:
        Full source document with structured content, images, and YouTube videos
    """
    try:
        # Get all chunks for this document
        results = collection.get(where={"document_id": document_id})

        if not results['metadatas'] or len(results['metadatas']) == 0:
            raise HTTPException(status_code=404, detail="Source document not found")

        # Get metadata from first chunk (contains full document metadata)
        raw_metadata = results['metadatas'][0]
        # Deserialize JSON strings back to dicts/lists
        metadata = deserialize_metadata(raw_metadata)

        # Get all images for this document
        image_results = collection.get(where={
            "$and": [
                {"document_id": document_id},
                {"type": "image"}
            ]
        })

        images = []
        if image_results['metadatas']:
            for img_meta in image_results['metadatas']:
                doc_id = img_meta.get('document_id', '')
                filename = img_meta.get('filename', '')
                if doc_id and filename:
                    images.append({
                        "url": f"/images/{doc_id}/{filename}",
                        "alt": img_meta.get('alt_text', ''),
                        "width": img_meta.get('width'),
                        "height": img_meta.get('height')
                    })

        # Get structured content or initialize empty dict
        structured_content = metadata.get('structured_content')
        if structured_content and not isinstance(structured_content, dict):
            structured_content = {}
        elif not structured_content:
            structured_content = {}

        # Add images to structured content if we have any
        if images:
            if not isinstance(structured_content, dict):
                structured_content = {}
            structured_content['images'] = images

        # Build full source document
        source = SourceDocument(
            document_id=document_id,
            url=metadata.get('url'),
            title=metadata.get('title'),
            domain=metadata.get('domain'),
            favicon=metadata.get('favicon'),
            timestamp=metadata.get('timestamp_readable'),
            snippet=results['documents'][0][:200] if results['documents'] else "",
            relevance_score=1.0,
            structured_content=structured_content,
            youtube_videos=metadata.get('youtube_videos'),
            clean_html=metadata.get('clean_html')
        )

        return source

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving source: {str(e)}")


@app.get("/images/{document_id}/{filename}")
async def serve_image(document_id: str, filename: str):
    """
    Serve stored images by document ID and filename

    Args:
        document_id: Document identifier
        filename: Image filename

    Returns:
        Image file
    """
    try:
        file_path = Path(IMAGE_STORAGE_DIR) / document_id / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Image not found")

        return FileResponse(str(file_path))

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Image not found: {str(e)}")


@app.get("/stats")
def get_stats():
    """Get statistics about stored embeddings, chunks, and images"""

    # Get all data to calculate stats
    all_data = collection.get()

    document_ids = set()
    chunked_docs = 0
    total_chunks = 0
    total_images = 0
    total_text_entries = 0

    if all_data['metadatas']:
        for metadata in all_data['metadatas']:
            if 'document_id' in metadata:
                document_ids.add(metadata['document_id'])

            entry_type = metadata.get('type', 'text')

            if entry_type == 'image':
                total_images += 1
            else:
                total_text_entries += 1
                if metadata.get('is_chunked', False):
                    total_chunks += 1
                    if metadata.get('chunk_index', 0) == 0:
                        chunked_docs += 1

    return {
        "total_entries": collection.count(),
        "total_text_entries": total_text_entries,
        "total_images": total_images,
        "unique_documents": len(document_ids),
        "chunked_documents": chunked_docs,
        "total_chunks": total_chunks,
        "storage_backend": "ChromaDB",
        "persist_directory": CHROMA_PERSIST_DIR,
        "collection_name": COLLECTION_NAME,
        "embedding_model": "google/siglip-so400m-patch14-384",
        "embedding_dimension": EMBEDDING_DIM,
        "chunking_config": {
            "chunk_size": CHUNK_SIZE,
            "overlap": CHUNK_OVERLAP,
            "min_chunk_size": MIN_CHUNK_SIZE
        }
    }


@app.delete("/clear")
def clear_store():
    """Clear all stored embeddings and images"""
    try:
        # Delete and recreate collection
        chroma_client.delete_collection(name=COLLECTION_NAME)

        global collection
        collection = chroma_client.create_collection(
            name=COLLECTION_NAME,
            embedding_function=SigLIPEmbeddingFunction(),
            metadata={"hnsw:space": "cosine"}
        )

        # Clear BM25 index
        rebuild_bm25_index()

        # Clear all stored images
        import shutil
        image_storage_path = Path(IMAGE_STORAGE_DIR)
        if image_storage_path.exists():
            # Remove all subdirectories (document image folders)
            for item in image_storage_path.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)

        return {
            "status": "success",
            "message": "All embeddings and images cleared"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing store: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
