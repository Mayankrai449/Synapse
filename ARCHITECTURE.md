# Synapse Mind - Architecture Overview

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SYNAPSE MIND ECOSYSTEM                       │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│                  │      │                  │      │                  │
│  Chrome          │      │  React App       │      │  FastAPI         │
│  Extension       │      │  (Frontend)      │      │  Backend         │
│                  │      │                  │      │                  │
│  ┌────────────┐  │      │  ┌────────────┐  │      │  ┌────────────┐  │
│  │ Popup UI   │  │      │  │ Query Box  │  │      │  │ /save      │  │
│  │ (Grey BG)  │  │      │  │ (Central)  │  │      │  │ (Immediate)│  │
│  └────────────┘  │      │  └────────────┘  │      │  └────────────┘  │
│        │         │      │        │         │      │        │         │
│        ├─────────┼──────┼────────┤         │      │        │         │
│        │         │      │        │         │      │        ▼         │
│  ┌────────────┐  │      │  ┌────────────┐  │      │  ┌────────────┐  │
│  │ Capture    │  │      │  │ Response   │  │      │  │ Background │  │
│  │ Button     │──┼──────┼─▶│ Display    │◀─┼──────┼──│ Tasks      │  │
│  └────────────┘  │      │  └────────────┘  │      │  └────────────┘  │
│        │         │      │        │         │      │        │         │
│  ┌────────────┐  │      │  ┌────────────┐  │      │  ┌────────────┐  │
│  │ Open Mind  │  │      │  │ Images     │  │      │  │ ChromaDB   │  │
│  │ Button     │──┼──────┼─▶│ Horizontal │◀─┼──────┼──│ (Vectors)  │  │
│  └────────────┘  │      │  └────────────┘  │      │  └────────────┘  │
│                  │      │        │         │      │        │         │
│  Port: N/A       │      │  ┌────────────┐  │      │  ┌────────────┐  │
│  Color: Grey     │      │  │ Side Panel │  │      │  │ SigLIP     │  │
│                  │      │  │ (40% width)│  │      │  │ Embeddings │  │
│                  │      │  └────────────┘  │      │  └────────────┘  │
│                  │      │                  │      │                  │
│                  │      │  Port: 3000      │      │  Port: 8000      │
│                  │      │  Color: Black    │      │  CORS: Enabled   │
└──────────────────┘      └──────────────────┘      └──────────────────┘
```

---

## Data Flow

### 1. Content Capture Flow

```
User Action: Click "Capture This Page" on Extension
    │
    ▼
Extract Page Content (structured)
    ├─ Text content
    ├─ Images (URLs)
    ├─ Headings, Lists, Tables
    ├─ YouTube videos
    └─ Metadata (title, URL, timestamp)
    │
    ▼
POST /save (FormData)
    │
    ▼
Backend receives data
    │
    ├─ Generate UUID
    ├─ Parse metadata
    ├─ Read uploaded images into memory
    └─ Return IMMEDIATELY ✅
    │
    ▼
Background Task Starts (async)
    │
    ├─ Chunk text (800 chars, 150 overlap)
    ├─ Generate embeddings for each chunk
    │   └─ SigLIP (1152-dim vectors)
    │
    ├─ Process images IN PARALLEL 🚀
    │   ├─ Download from URLs
    │   ├─ Save to filesystem
    │   └─ Generate image embeddings (SigLIP)
    │
    └─ Save all to ChromaDB
        ├─ Text chunks with metadata
        ├─ Image embeddings with metadata
        └─ Rebuild BM25 index
```

### 2. Query Flow

```
User Action: Type query and press Enter
    │
    ▼
POST /query
    {
      "query": "where is best beach I can visit",
      "top_k": 5,
      "top_k_images": 6
    }
    │
    ▼
Hybrid Search (Backend)
    │
    ├─ Semantic Search (SigLIP embeddings)
    │   └─ ChromaDB vector similarity
    │
    ├─ BM25 Keyword Search
    │   └─ Full-text search
    │
    └─ RRF Fusion
        └─ Combine results (Reciprocal Rank Fusion)
    │
    ▼
Generate Response
    │
    ├─ Get top K text chunks
    ├─ Get top K images
    │
    └─ OpenAI GPT-4.1
        ├─ Context: Top chunks
        ├─ Query: User question
        └─ Generate tailored response
    │
    ▼
Return Response
    {
      "response": "AI answer...",
      "images": [...],
      "sources": [...]
    }
    │
    ▼
React App Displays
    │
    ├─ AI Response (top)
    ├─ Images (horizontal scroll)
    └─ Source Cards (grid)
```

### 3. Source Detail Flow

```
User Action: Click "View Full Source" button
    │
    ▼
GET /source/{document_id}
    │
    ▼
Backend fetches from ChromaDB
    ├─ All chunks for document
    ├─ All images for document
    └─ Full metadata
    │
    ▼
Return Structured Content
    {
      "structured_content": {
        "headings": [...],
        "paragraphs": [...],
        "lists": [...],
        "tables": [...],
        "images": [...]
      },
      "youtube_videos": [...]
    }
    │
    ▼
React Side Panel Opens (40% width)
    │
    ├─ Display headings (hierarchical)
    ├─ Display paragraphs (readable)
    ├─ Display lists (ordered/unordered)
    ├─ Display tables (formatted)
    ├─ Display images (grid)
    └─ Embed YouTube videos (iframe)
```

---

## Component Communication

```
┌─────────────┐
│  Extension  │
└──────┬──────┘
       │
       │ Opens new tab
       │ chrome.tabs.create()
       ▼
┌─────────────┐
│ React App   │
│ localhost:3000│
└──────┬──────┘
       │
       │ HTTP Requests
       │ (Axios)
       ▼
┌─────────────┐
│ FastAPI     │
│ localhost:8000│
└──────┬──────┘
       │
       ├─────────────┐
       │             │
       ▼             ▼
┌────────────┐  ┌────────────┐
│ ChromaDB   │  │ Background │
│ (Vectors)  │  │ Tasks      │
└────────────┘  └────────────┘
```

---

## Background Task Processing

```
/save endpoint receives request
│
├─ Parse and validate data (sync)
├─ Generate UUID (sync)
├─ Read uploaded files into memory (async)
└─ Queue background task (async)
│
Return IMMEDIATELY ✅
{
  "status": "success",
  "processing_status": "queued"
}

Meanwhile, in background:
│
├─ Text Processing
│   ├─ Chunk text
│   ├─ Generate embeddings
│   └─ Prepare metadata
│
├─ Image Processing (PARALLEL) 🚀
│   │
│   ├─ Task 1: Process uploaded image 1
│   ├─ Task 2: Process uploaded image 2
│   ├─ Task 3: Download image URL 1
│   ├─ Task 4: Download image URL 2
│   └─ ... all run concurrently
│
│   └─ asyncio.gather() waits for all
│
└─ Save to ChromaDB
    ├─ Batch insert (all chunks + images)
    └─ Rebuild BM25 index

Processing complete (user already moved on)
```

---

## Side Panel Layout

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Main Content Area (60%)     │  Side Panel (40%)           │
│                               │                             │
│  ┌─────────────────────┐     │  ┌────────────────────┐    │
│  │  Query Box          │     │  │  Header            │    │
│  └─────────────────────┘     │  │  ┌──────────────┐  │    │
│                               │  │  │ Close Button │  │    │
│  ┌─────────────────────┐     │  │  └──────────────┘  │    │
│  │  AI Response        │     │  └────────────────────┘    │
│  └─────────────────────┘     │                             │
│                               │  ┌────────────────────┐    │
│  ┌─────────────────────┐     │  │  YouTube Videos    │    │
│  │  Images (Horizontal)│     │  │  ┌──────────────┐  │    │
│  │  ┌───┐ ┌───┐ ┌───┐ │     │  │  │  Embed Player │  │    │
│  │  │   │ │   │ │   │ │     │  │  └──────────────┘  │    │
│  │  └───┘ └───┘ └───┘ │     │  └────────────────────┘    │
│  └─────────────────────┘     │                             │
│                               │  ┌────────────────────┐    │
│  ┌─────────────────────┐     │  │  Headings          │    │
│  │  Sources (Grid)     │     │  │  H1: Title         │    │
│  │  ┌─────┐  ┌─────┐  │     │  │  H2: Section       │    │
│  │  │Card │  │Card │  │     │  └────────────────────┘    │
│  │  └─────┘  └─────┘  │     │                             │
│  │  ┌─────┐  ┌─────┐  │     │  ┌────────────────────┐    │
│  │  │Card │  │Card │  │     │  │  Lists             │    │
│  │  └─────┘  └─────┘  │     │  │  • Item 1          │    │
│  └─────────────────────┘     │  │  • Item 2          │    │
│                               │  └────────────────────┘    │
│                               │                             │
│                               │  ┌────────────────────┐    │
│                               │  │  Tables            │    │
│                               │  │  ┌───────┬──────┐  │    │
│                               │  │  │ Head  │ Head │  │    │
│                               │  │  ├───────┼──────┤  │    │
│                               │  │  │ Data  │ Data │  │    │
│                               │  │  └───────┴──────┘  │    │
│                               │  └────────────────────┘    │
│                               │                             │
└───────────────────────────────┴─────────────────────────────┘
```

---

## Tech Stack Details

### Backend Stack
```
FastAPI (async framework)
├─ BackgroundTasks (async processing)
├─ CORS Middleware (allow extension)
└─ Pydantic (data validation)

ChromaDB (vector database)
├─ Persistent storage
├─ Cosine similarity search
└─ Metadata filtering

SigLIP (embedding model)
├─ Text embeddings (1152-dim)
├─ Image embeddings (1152-dim)
└─ Unified vector space

BM25 (keyword search)
├─ Full-text indexing
├─ TF-IDF scoring
└─ RRF fusion with semantic

OpenAI GPT-4.1 (LLM)
└─ Tailored response generation
```

### Frontend Stack
```
React 18
├─ Functional components
├─ Hooks (useState)
└─ JSX

Vite (build tool)
├─ Fast HMR
├─ Modern bundling
└─ Development server

Axios (HTTP client)
├─ POST /query
├─ GET /source
└─ Error handling

CSS (styling)
├─ Black background (#000)
├─ Flexbox layout
├─ Animations (slideIn, fadeIn)
└─ Responsive design
```

### Extension Stack
```
Chrome Extension Manifest V3
├─ Popup UI (HTML/CSS/JS)
├─ Content Scripts (extraction)
└─ Chrome APIs

JavaScript (vanilla)
├─ chrome.tabs.create()
├─ chrome.scripting.executeScript()
└─ FormData (multipart/form-data)

Content Extraction
├─ TreeWalker (text nodes)
├─ querySelector (structured data)
└─ Metadata (favicon, title, URL)
```

---

## Performance Optimizations

1. **Background Tasks**: No blocking on `/save`
2. **Parallel Processing**: All images processed concurrently
3. **Batch Insert**: Single ChromaDB operation for all chunks
4. **Lazy Loading**: Side panel content loaded on demand
5. **Horizontal Scroll**: Efficient image display
6. **Vector Search**: Fast approximate nearest neighbor
7. **BM25 Index**: In-memory keyword search
8. **RRF Fusion**: Best of both worlds (semantic + keyword)

---

## Security Considerations

- ✅ CORS configured for extension/frontend
- ✅ Input validation (Pydantic models)
- ✅ Error handling (try/catch blocks)
- ✅ File path sanitization
- ⚠️ Production: Use specific CORS origins
- ⚠️ Production: Add authentication
- ⚠️ Production: Rate limiting

---

This architecture enables:
- Fast content capture (immediate response)
- Smart search (hybrid BM25 + semantic)
- Beautiful visualization (black UI, side panel)
- Seamless integration (extension → app → backend)
