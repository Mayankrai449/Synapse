# Synapse - Source Attribution Design

## Overview
Synapse captures full webpage content and provides an intelligent query interface with source attribution, similar to browser reading mode.

## Architecture

### 1. Extension Capture Flow
When user clicks "Capture" button, extension extracts:

#### Content to Extract:
- **Page Metadata:**
  - URL
  - Page title
  - Domain
  - Favicon URL
  - Timestamp

- **Text Content:**
  - All visible text from DOM
  - Preserve structure (headings, paragraphs, lists, tables)

- **Images:**
  - All img src URLs
  - Alt text for each image
  - Image positions/context

- **Media:**
  - YouTube video embeds (iframe src)
  - YouTube links in content
  - Other video sources

- **Structured Content (for readonly view):**
  - HTML structure with:
    - Headings (h1-h6)
    - Paragraphs
    - Lists (ul, ol)
    - Tables
    - Blockquotes
    - Code blocks
  - Simplified/cleaned HTML (remove scripts, ads, navigation)

### 2. Backend Storage

#### Updated /save API Request Format:
```javascript
{
  text: "Full page text content",
  metadata: {
    url: "https://example.com/article",
    title: "Article Title",
    domain: "example.com",
    favicon: "https://example.com/favicon.ico",
    timestamp: "2025-01-14 10:30:00",

    // Structured content for readonly view
    structured_content: {
      headings: [
        {level: 1, text: "Main Title", position: 0},
        {level: 2, text: "Section 1", position: 5}
      ],
      paragraphs: ["Para 1 text", "Para 2 text"],
      lists: [
        {type: "ul", items: ["item1", "item2"]},
      ],
      tables: [
        {headers: ["Col1", "Col2"], rows: [["A", "B"]]}
      ],
      images_positions: [
        {src: "url", alt: "alt text", position: 3}
      ]
    },

    // Media content
    youtube_videos: [
      {url: "https://youtube.com/watch?v=xyz", embed_url: "...", title: "Video Title"}
    ],

    // Clean HTML for readonly view
    clean_html: "<article>...</article>"
  },

  // Images (existing format)
  image_urls: ["url1", "url2"],
  images: [uploaded files]
}
```

#### Backend Storage Strategy:
- Store all metadata in ChromaDB document metadata
- Store structured_content as JSON in metadata
- Store images in file system (existing approach)
- Each document has unique document_id for retrieval

### 3. Query Response with Sources

#### Updated /query API Response Format:
```javascript
{
  response: "GPT-4.1 tailored response",
  images: ["/images/doc1/img1.jpg"],

  // NEW: Source attribution
  sources: [
    {
      document_id: "uuid-1234",
      url: "https://example.com/article",
      title: "Article Title",
      domain: "example.com",
      favicon: "https://example.com/favicon.ico",
      timestamp: "2025-01-14 10:30:00",
      snippet: "First 200 chars of content...",
      relevance_score: 0.95,

      // Full content for readonly view
      structured_content: {
        headings: [...],
        paragraphs: [...],
        lists: [...],
        tables: [...],
        images: [
          {url: "/images/doc1/img1.jpg", alt: "..."}
        ]
      },

      youtube_videos: [...],
      clean_html: "<article>...</article>"
    }
  ]
}
```

### 4. Frontend Requirements (Not implementing yet)

#### Components Needed:
1. **Query Interface:**
   - Search input
   - GPT-4.1 response display
   - Image gallery

2. **Source List:**
   - Clickable source cards showing:
     - Favicon + Domain
     - Title
     - Timestamp
     - Snippet
     - Relevance score

3. **Readonly Source Viewer (Modal/Panel):**
   - Full article view with:
     - Original formatting (headings, lists, tables)
     - All images displayed
     - YouTube video embeds (conditionally rendered)
     - Clean, readable layout (like Firefox/Edge reading mode)

4. **YouTube Video Player:**
   - Conditional rendering of YouTube embeds
   - iframe or react-player component

## Implementation Plan

### Phase 1: Backend Updates (Now)
✅ Update /save endpoint to accept full page data
✅ Update response models to include source attribution
✅ Update /query endpoint to return sources with full content
✅ Create new endpoint /source/{document_id} to get full source

### Phase 2: Extension Updates (Now)
✅ Rename to Synapse
✅ Simplify UI (single capture button + "Open Synapse Mind" button)
✅ Implement full DOM extraction
✅ Extract structured content
✅ Detect and extract YouTube videos
✅ Clean HTML generation
✅ Better styling with mind.png logo

### Phase 3: Frontend (Later)
- Source list component
- Readonly viewer component
- YouTube video player
- Image gallery

## Data Flow Example

1. **User visits article on Medium.com**
2. **Clicks "Capture" in extension**
   - Extension extracts all content
   - Sends to /save API with full metadata
   - Backend stores in ChromaDB + file system

3. **User queries "AI trends"**
   - Backend performs hybrid search
   - Returns GPT-4.1 response + images + sources list
   - Each source includes full structured content

4. **User clicks source card**
   - Frontend opens readonly viewer
   - Displays full article with formatting
   - Renders YouTube videos if present
   - Shows all images

## Key Features

### Extension:
- Single-click capture of entire page
- Automatic content extraction
- No manual input required
- Beautiful, minimal UI

### Backend:
- Stores full page content
- Provides source attribution
- Returns structured data for readonly view
- Supports YouTube video metadata

### Frontend (Future):
- Reading mode view of sources
- YouTube video playback
- Image galleries
- Clean, focused interface

## Technical Considerations

1. **HTML Cleaning:**
   - Remove scripts, styles, ads, navigation
   - Keep only content elements
   - Preserve semantic structure

2. **YouTube Detection:**
   - Detect iframe embeds
   - Detect youtube.com/watch links
   - Extract video IDs
   - Generate embed URLs

3. **Image Handling:**
   - Download and store all images
   - Preserve alt text
   - Track image positions in content

4. **Storage Efficiency:**
   - Store clean HTML (not full page)
   - Store structured content as JSON
   - Use ChromaDB metadata efficiently

5. **Performance:**
   - Lazy load source content
   - Cache structured content
   - Optimize image loading
