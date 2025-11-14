# Quick Start Guide - Appointy Hackathon Project

## What's New

✅ **SigLIP Embeddings** - Replaced Gemini embeddings with local Google SigLIP model
✅ **ChromaDB** - Replaced JSON with persistent vector database
✅ **Time-Based Search** - Accurate timestamp filtering and temporal decay
✅ **Manual Chunking** - Kept for control and transparency
✅ **Ready for Images** - SigLIP supports multimodal embeddings

## Installation (5 minutes)

### 1. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Note:** First run will download SigLIP model (~1.5GB). Be patient!

### 2. Start the Backend

```bash
python main.py
```

Expected output:
```
Loading SigLIP model: google/siglip-so400m-patch14-384...
Using device: cuda  # or cpu
SigLIP model loaded successfully!
Loaded existing collection: text_embeddings
INFO:     Application startup complete.
```

Server runs at: `http://localhost:8000`

### 3. Test the Backend

In another terminal:

```bash
cd backend
python test_chromadb.py
```

This tests all features: chunking, embedding, time-based search, etc.

### 4. Inspect Your Data

```bash
python inspect_chromadb.py
```

View statistics, sample entries, and search by time.

## Using the Chrome Extension

### 1. Create Icons (One-time)

```bash
cd extension
pip install Pillow
python create_icons.py
```

### 2. Load Extension in Chrome

1. Go to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `extension` folder

### 3. Use the Extension

**Capture Text:**
- Click extension icon
- Enter text (can be long - automatic chunking!)
- Click "Capture"
- See success message with chunk count

**Query Text:**
- Click extension icon
- Enter search query
- Click "Query"
- See results with similarity scores and timestamps

## Key Features

### 1. Automatic Chunking

Long texts are automatically split into optimal chunks:
- **Chunk size:** 800 characters
- **Overlap:** 150 characters
- **Sentence-aware:** Won't break mid-sentence

```python
# API automatically handles this
response = requests.post("http://localhost:8000/save", json={
    "text": "Very long text here...",  # Auto-chunked
    "metadata": {"source": "chrome"}
})
```

### 2. Time-Based Search

**Option A: Time Range Filtering**

```python
import time
one_hour_ago = time.time() - 3600

response = requests.post("http://localhost:8000/query", json={
    "query": "machine learning",
    "time_filter": {"start": one_hour_ago}
})
```

**Option B: Temporal Decay (Boost Recent Results)**

```python
response = requests.post("http://localhost:8000/query", json={
    "query": "machine learning",
    "enable_temporal_decay": True  # Recent results boosted
})
```

### 3. ChromaDB Persistence

Your data persists in `backend/chroma_db/` folder:
- Survives server restarts
- Efficient querying
- Built-in indexing

**View your data:**
```bash
python inspect_chromadb.py
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Chrome Extension (frontend)                              │
│  - Text capture                                          │
│  - Query interface                                       │
│  - Results display                                       │
└─────────────────┬───────────────────────────────────────┘
                  │ HTTP (CORS enabled)
┌─────────────────▼───────────────────────────────────────┐
│ FastAPI Backend (main.py)                               │
│  - /save endpoint (captures text)                       │
│  - /query endpoint (searches)                           │
│  - /stats endpoint (statistics)                         │
└─────────────────┬───────────────────────────────────────┘
                  │
     ┌────────────┴────────────┐
     │                         │
┌────▼────────┐       ┌────────▼────────┐
│ SigLIP      │       │ ChromaDB        │
│ Embeddings  │       │ Vector Store    │
│             │       │                 │
│ - Text →    │       │ - Persistence   │
│   Vector    │◄──────┤ - Indexing      │
│ - Image →   │       │ - Metadata      │
│   Vector    │       │ - Time filter   │
└─────────────┘       └─────────────────┘
```

## Time-Based Search: Why It's Accurate

### ✅ What We Do (CORRECT)

**Store timestamps in metadata:**
```python
metadata = {
    "timestamp_unix": 1705234567.89,  # Precise Unix timestamp
    "timestamp_readable": "2025-01-14 10:30:00",  # Human-readable
    # ... other metadata
}
```

**Filter at database level:**
```python
# ChromaDB filters efficiently
where = {"timestamp_unix": {"$gte": start_time}}
results = collection.query(query, where=where)
```

**Benefits:**
- Clean semantic embeddings
- Fast metadata filtering
- Accurate time ranges
- Flexible combination with similarity

### ❌ What NOT to Do

**DON'T append timestamps to text:**
```python
# BAD - pollutes embeddings
text = "Machine learning is great. Saved on 2025-01-14"
```

**Problems:**
- Corrupts semantic space
- Reduces search accuracy
- Wastes embedding dimensions
- Similar content becomes dissimilar

## API Reference

### POST /save
```python
{
    "text": "Your text here",
    "metadata": {"source": "chrome"},
    "enable_chunking": True  # Optional, default True
}
```

Returns:
```python
{
    "status": "success",
    "document_id": "uuid",
    "chunks_created": 3,
    "total_entries": 42
}
```

### POST /query
```python
{
    "query": "search term",
    "top_k": 5,  # Number of results
    "time_filter": {  # Optional
        "start": 1705234567,  # Unix timestamp
        "end": 1705238167
    },
    "enable_temporal_decay": False  # Optional
}
```

Returns:
```python
[
    {
        "text": "Matching chunk",
        "similarity": 0.87,
        "metadata": {
            "chunk_index": 0,
            "total_chunks": 3,
            "timestamp_unix": 1705234567,
            ...
        }
    }
]
```

### GET /stats
```python
{
    "total_entries": 42,
    "unique_documents": 15,
    "embedding_model": "google/siglip-so400m-patch14-384",
    "embedding_dimension": 1152,
    ...
}
```

## Troubleshooting

### "Could not connect to server"
```bash
# Make sure server is running
cd backend
python main.py
```

### "Module not found"
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### "Model download stuck"
```bash
# Check internet connection
# Model is ~1.5GB, takes time on first run
# Subsequent runs use cached model
```

### "Out of memory"
```bash
# SigLIP will use CPU if GPU unavailable
# Slower but works everywhere
```

### "ChromaDB locked"
```bash
# Only run one server instance
# Kill existing: Ctrl+C, then restart
```

## Next Steps for Hackathon

### Phase 1: Polish Current Features (1 hour)
- [ ] Test with real data
- [ ] Tune chunk size if needed
- [ ] Test Chrome extension thoroughly

### Phase 2: Add Image Support (2-3 hours)
- [ ] Add image upload endpoint
- [ ] Use SigLIP for image embeddings
- [ ] Update Chrome extension UI
- [ ] Test multimodal search

### Phase 3: Add Structured Responses (1-2 hours)
- [ ] Integrate Gemini 2.5 Flash
- [ ] Format responses for extension
- [ ] Add markdown rendering

### Phase 4: (Optional) BM25 Hybrid Search (2-3 hours)
- [ ] Add BM25 indexing
- [ ] Implement RRF fusion
- [ ] Combine with vector search

## Files Overview

```
appointy/
├── backend/
│   ├── main.py                    # FastAPI server (ChromaDB + SigLIP)
│   ├── siglip_embeddings.py      # SigLIP wrapper
│   ├── test_chromadb.py          # Test script
│   ├── inspect_chromadb.py       # Data viewer
│   ├── requirements.txt          # Dependencies
│   ├── SETUP_CHROMADB.md         # Detailed setup guide
│   └── chroma_db/                # ChromaDB storage (auto-created)
│
├── extension/
│   ├── manifest.json             # Extension config
│   ├── popup.html                # UI
│   ├── popup.js                  # Logic
│   ├── popup.css                 # Styling
│   ├── create_icons.py           # Icon generator
│   └── README.md                 # Extension guide
│
└── QUICK_START.md                # This file
```

## Support

For issues or questions:
1. Check `SETUP_CHROMADB.md` for detailed docs
2. Run `python inspect_chromadb.py` to debug data
3. Check server logs for errors

Good luck with your hackathon! 🚀
