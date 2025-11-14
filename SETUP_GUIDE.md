# Synapse Mind - Complete Setup Guide

This guide will help you set up and run all three components of Synapse Mind:
1. **FastAPI Backend** - Handles embeddings and background processing
2. **React Frontend** - Query interface with black background
3. **Chrome Extension** - Captures web pages

---

## Prerequisites

- Python 3.8+ with virtual environment
- Node.js 16+ and npm
- Google Chrome browser
- OpenAI API key (for GPT-4.1 responses)

---

## 1. Backend Setup (FastAPI)

### Install Dependencies

```bash
# Activate virtual environment
synapsenv\Scripts\activate  # Windows
# source synapsenv/bin/activate  # Mac/Linux

# Install Python dependencies (if not already done)
pip install -r requirements.txt
```

### Configure Environment

Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=your-openai-api-key-here
```

### Start the Backend Server

```bash
cd backend
python main.py
```

The backend will start on `http://localhost:8000`

**Key Features:**
- ✓ Background task processing for `/save` endpoint
- ✓ Parallel image processing
- ✓ Immediate response on data submission
- ✓ Async chunking and embedding

---

## 2. Frontend Setup (React App)

### Install Dependencies

```bash
cd frontend
npm install
```

### Start the Development Server

```bash
npm run dev
```

The React app will start on `http://localhost:3000`

**Key Features:**
- ✓ Black background interface
- ✓ Central query textbox
- ✓ Images displayed horizontally (frameless)
- ✓ Source cards with "View Full Source" buttons
- ✓ Side panel (40% width) with:
  - Structured content (headings, lists, tables)
  - Embedded YouTube player
  - Clean HTML rendering

---

## 3. Extension Setup (Chrome)

### Load the Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top-right)
3. Click "Load unpacked"
4. Select the `extension` folder

**Key Features:**
- ✓ Grey background (instead of bluish)
- ✓ "Capture This Page" button - saves to backend
- ✓ "Open Synapse Mind" button - opens React app

---

## Usage Workflow

### Step 1: Capture Content
1. Navigate to any webpage in Chrome
2. Click the Synapse extension icon
3. Click "Capture This Page"
4. Content is sent to backend and processed in background
5. You'll see: "Content received and queued for processing"

### Step 2: Query Your Knowledge
1. Click "Open Synapse Mind" in the extension (or go to `http://localhost:3000`)
2. Type your query in the central textbox (e.g., "where is best beach I can visit")
3. Press Enter or click the search icon
4. View the AI response, related images, and source cards

### Step 3: View Source Details
1. Click "View Full Source" on any source card
2. A side panel slides in from the right (40% width)
3. View structured content:
   - Headings and paragraphs
   - Lists (ordered and unordered)
   - Tables with proper formatting
   - Embedded YouTube videos
   - Images from the source
4. Click outside or the X button to close

---

## API Endpoints

### POST /save
**Returns immediately** while processing in background:
```json
{
  "status": "success",
  "message": "Content received and queued for processing",
  "document_id": "uuid",
  "processing_status": "queued"
}
```

### POST /query
Query your knowledge base:
```json
{
  "query": "where is best beach I can visit",
  "top_k": 5,
  "top_k_images": 6,
  "include_images": true,
  "enable_temporal_decay": true,
  "use_bm25_fusion": true
}
```

**Response:**
```json
{
  "response": "AI-generated response...",
  "images": ["/images/doc-id/img1.jpg", ...],
  "sources": [
    {
      "document_id": "uuid",
      "url": "https://...",
      "title": "Page Title",
      "domain": "example.com",
      "favicon": "https://.../favicon.ico",
      "timestamp": "Monday afternoon, 02:30 PM",
      "snippet": "First 200 characters...",
      "relevance_score": 0.85,
      "structured_content": { ... },
      "youtube_videos": [ ... ]
    }
  ]
}
```

### GET /source/{document_id}
Get full source document with all structured content

### GET /images/{document_id}/{filename}
Serve stored images

---

## Architecture Highlights

### Backend (FastAPI)
- **Background Tasks**: `/save` returns immediately, processing happens async
- **Parallel Image Processing**: All images downloaded and embedded concurrently
- **Hybrid Search**: BM25 + Semantic embeddings with RRF fusion
- **ChromaDB**: Persistent vector storage
- **SigLIP Embeddings**: Unified text/image vector space (1152-dim)

### Frontend (React + Vite)
- **Black Background**: Modern, distraction-free interface
- **Central Query**: Single-focus search experience
- **Horizontal Images**: Frameless cards, scrollable
- **Side Panel**: 40% width, slides from right, structured content display
- **Responsive**: Adapts to different screen sizes

### Extension (Chrome)
- **Grey Background**: Professional, neutral design
- **Content Extraction**: Structured data (headings, lists, tables, images, videos)
- **Instant Capture**: Quick save with background processing
- **One-Click Access**: Opens React app directly

---

## Development Tips

### Backend
```bash
# Check ChromaDB stats
curl http://localhost:8000/stats

# Clear all data
curl -X DELETE http://localhost:8000/clear
```

### Frontend
```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

### Extension
- Check Console logs in DevTools for debugging
- Reload extension after code changes
- Use `chrome.tabs.create()` for opening new tabs

---

## Troubleshooting

### Backend not starting
- Check if port 8000 is already in use
- Ensure virtual environment is activated
- Verify all dependencies are installed

### Frontend not connecting to backend
- Check CORS settings in `main.py`
- Ensure backend is running on `http://localhost:8000`
- Update `API_BASE_URL` in `App.jsx` if using different port

### Extension not working
- Reload extension in `chrome://extensions/`
- Check if backend is running
- Open DevTools Console for error messages

### Images not displaying
- Check if images are being saved to `./images/` directory
- Verify image URLs in ChromaDB metadata
- Check browser Console for CORS errors

---

## Next Steps

1. **Add more sources**: Capture multiple web pages
2. **Test queries**: Try natural language queries like:
   - "notes from yesterday morning"
   - "articles about AI"
   - "where is best beach I can visit"
3. **Explore sources**: Click "View Full Source" to see structured content
4. **Check backend logs**: Monitor background processing

---

## Tech Stack

- **Backend**: FastAPI, ChromaDB, SigLIP, OpenAI GPT-4.1, BM25
- **Frontend**: React 18, Vite, Axios
- **Extension**: Vanilla JavaScript, Chrome APIs
- **Styling**: Modern CSS with gradients and animations

---

Enjoy using Synapse Mind - your AI-powered second brain!
