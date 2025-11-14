# Frontend Data Reference for Synapse

## Query Response Structure

When you call `POST /query`, you'll receive this structure:

```typescript
interface QueryResponse {
  response: string;              // GPT-4.1 generated response
  images: string[];              // Array of image URLs
  sources: SourceDocument[];     // Array of source documents
}

interface SourceDocument {
  document_id: string;           // Unique document identifier
  url: string | null;            // Original webpage URL
  title: string | null;          // Page title
  domain: string | null;         // Domain (e.g., "medium.com")
  favicon: string | null;        // Favicon URL
  timestamp: string | null;      // Human-readable timestamp
  snippet: string;               // First 200 characters
  relevance_score: number;       // 0.0 to 1.0 (how relevant to query)
  structured_content: StructuredContent | null;
  youtube_videos: YouTubeVideo[] | null;
  clean_html: string | null;    // Sanitized HTML for rendering
}

interface StructuredContent {
  headings: Heading[];
  paragraphs: string[];
  lists: List[];
  tables: Table[];
  images?: Image[];              // Added when fetching full source
  images_positions: ImagePosition[];
}

interface Heading {
  level: number;                 // 1-6 (h1-h6)
  text: string;
  position: number;
}

interface List {
  type: "ul" | "ol";
  items: string[];
}

interface Table {
  headers: string[];
  rows: string[][];
}

interface Image {
  url: string;                   // Served from /images/{doc_id}/{filename}
  alt: string;
  width?: number;
  height?: number;
}

interface ImagePosition {
  src: string;
  alt: string;
  position: number;
}

interface YouTubeVideo {
  url: string;                   // https://youtube.com/watch?v=xyz
  embed_url: string;             // https://youtube.com/embed/xyz
  video_id: string;              // xyz
  title: string;
}
```

---

## Example Real Response

### Query Request:
```json
POST /query
{
  "query": "AI trends",
  "top_k": 5,
  "include_images": true
}
```

### Query Response:
```json
{
  "response": "Based on your saved notes, here are the key AI trends: Machine learning adoption is accelerating, with particular focus on transformer models and large language models. Companies are increasingly investing in AI infrastructure...",

  "images": [
    "/images/550e8400-e29b-41d4-a716-446655440000/image_0.jpg",
    "/images/550e8400-e29b-41d4-a716-446655440000/image_1.jpg"
  ],

  "sources": [
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "url": "https://www.example.com/ai-trends-2025",
      "title": "AI Trends 2025: What to Expect",
      "domain": "example.com",
      "favicon": "https://www.example.com/favicon.ico",
      "timestamp": "1/14/2025, 10:30:00 AM",
      "snippet": "The AI landscape is rapidly evolving. In 2025, we expect to see major breakthroughs in natural language processing, computer vision, and robotics. Companies are investing heavily in AI infrastructure...",
      "relevance_score": 0.95,

      "structured_content": {
        "headings": [
          {
            "level": 1,
            "text": "AI Trends 2025: What to Expect",
            "position": 0
          },
          {
            "level": 2,
            "text": "Large Language Models",
            "position": 1
          },
          {
            "level": 2,
            "text": "Computer Vision Advances",
            "position": 2
          }
        ],

        "paragraphs": [
          "The AI landscape is rapidly evolving. In 2025, we expect to see major breakthroughs in natural language processing, computer vision, and robotics.",
          "Large language models like GPT-4 have revolutionized how we interact with AI. These models can understand context, generate human-like text, and even write code.",
          "Computer vision has made significant strides, with applications ranging from autonomous vehicles to medical imaging."
        ],

        "lists": [
          {
            "type": "ul",
            "items": [
              "Natural Language Processing",
              "Computer Vision",
              "Robotics",
              "AI Ethics"
            ]
          }
        ],

        "tables": [
          {
            "headers": ["Technology", "Adoption Rate", "Impact"],
            "rows": [
              ["LLMs", "85%", "High"],
              ["Computer Vision", "70%", "Medium"],
              ["Robotics", "45%", "Growing"]
            ]
          }
        ],

        "images_positions": [
          {
            "src": "https://www.example.com/images/ai-chart.jpg",
            "alt": "AI adoption chart",
            "position": 0
          }
        ]
      },

      "youtube_videos": [
        {
          "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
          "embed_url": "https://www.youtube.com/embed/dQw4w9WgXcQ",
          "video_id": "dQw4w9WgXcQ",
          "title": "AI Trends Explained"
        }
      ],

      "clean_html": "<h1>AI Trends 2025: What to Expect</h1><p>The AI landscape is rapidly evolving...</p><h2>Large Language Models</h2><p>Large language models like GPT-4...</p><ul><li>Natural Language Processing</li><li>Computer Vision</li></ul>"
    }
  ]
}
```

---

## React Component Examples

### 1. Query Interface

```tsx
import { useState } from 'react';

interface QueryResponse {
  response: string;
  images: string[];
  sources: SourceDocument[];
}

function QueryInterface() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const handleQuery = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: 5 })
      });
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Query error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Ask anything..."
      />
      <button onClick={handleQuery} disabled={loading}>
        {loading ? 'Searching...' : 'Search'}
      </button>

      {results && (
        <>
          <div className="response">
            {results.response}
          </div>

          <div className="images">
            {results.images.map(img => (
              <img src={`http://localhost:8000${img}`} alt="" />
            ))}
          </div>

          <div className="sources">
            {results.sources.map(source => (
              <SourceCard key={source.document_id} source={source} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
```

### 2. Source Card

```tsx
function SourceCard({ source }: { source: SourceDocument }) {
  const [showViewer, setShowViewer] = useState(false);

  return (
    <>
      <div className="source-card" onClick={() => setShowViewer(true)}>
        <div className="source-header">
          {source.favicon && (
            <img src={source.favicon} alt="" className="favicon" />
          )}
          <span className="domain">{source.domain}</span>
        </div>

        <h3 className="title">{source.title}</h3>
        <p className="snippet">{source.snippet}</p>

        <div className="meta">
          <span className="timestamp">{source.timestamp}</span>
          <span className="relevance">
            {Math.round(source.relevance_score * 100)}% relevant
          </span>
        </div>
      </div>

      {showViewer && (
        <SourceViewer
          source={source}
          onClose={() => setShowViewer(false)}
        />
      )}
    </>
  );
}
```

### 3. Readonly Source Viewer (Option 1: Structured)

```tsx
import DOMPurify from 'dompurify';

function SourceViewer({ source, onClose }: {
  source: SourceDocument;
  onClose: () => void;
}) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="source-viewer" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="viewer-header">
          {source.favicon && <img src={source.favicon} alt="" />}
          <div>
            <h1>{source.title}</h1>
            <a href={source.url} target="_blank">{source.url}</a>
            <p>{source.timestamp}</p>
          </div>
          <button onClick={onClose}>✕</button>
        </div>

        {/* Content */}
        <div className="viewer-content">
          {source.structured_content?.headings.map((heading, i) => {
            const Tag = `h${heading.level}` as keyof JSX.IntrinsicElements;
            return <Tag key={i}>{heading.text}</Tag>;
          })}

          {source.structured_content?.paragraphs.map((para, i) => (
            <p key={i}>{para}</p>
          ))}

          {source.structured_content?.lists.map((list, i) => {
            const ListTag = list.type === 'ul' ? 'ul' : 'ol';
            return (
              <ListTag key={i}>
                {list.items.map((item, j) => (
                  <li key={j}>{item}</li>
                ))}
              </ListTag>
            );
          })}

          {source.structured_content?.tables.map((table, i) => (
            <table key={i}>
              <thead>
                <tr>
                  {table.headers.map((h, j) => (
                    <th key={j}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {table.rows.map((row, j) => (
                  <tr key={j}>
                    {row.map((cell, k) => (
                      <td key={k}>{cell}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          ))}

          {source.structured_content?.images?.map((img, i) => (
            <img
              key={i}
              src={`http://localhost:8000${img.url}`}
              alt={img.alt}
            />
          ))}
        </div>

        {/* YouTube Videos */}
        {source.youtube_videos && source.youtube_videos.length > 0 && (
          <div className="youtube-section">
            <h2>Videos</h2>
            {source.youtube_videos.map((video, i) => (
              <iframe
                key={i}
                src={video.embed_url}
                title={video.title}
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
```

### 4. Readonly Source Viewer (Option 2: Clean HTML)

```tsx
import DOMPurify from 'dompurify';
import ReactPlayer from 'react-player/youtube';

function SourceViewerHTML({ source, onClose }: {
  source: SourceDocument;
  onClose: () => void;
}) {
  const sanitizedHTML = DOMPurify.sanitize(source.clean_html || '', {
    ALLOWED_TAGS: ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li',
                    'table', 'thead', 'tbody', 'tr', 'th', 'td',
                    'blockquote', 'pre', 'code', 'strong', 'em', 'a'],
    ALLOWED_ATTR: ['href', 'target']
  });

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="source-viewer reading-mode" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <header>
          {source.favicon && <img src={source.favicon} alt="" />}
          <div>
            <h1>{source.title}</h1>
            <a href={source.url} target="_blank">{source.domain}</a>
            <time>{source.timestamp}</time>
          </div>
          <button onClick={onClose}>✕</button>
        </header>

        {/* Clean HTML Content */}
        <article
          dangerouslySetInnerHTML={{ __html: sanitizedHTML }}
        />

        {/* Images */}
        {source.structured_content?.images && (
          <div className="image-gallery">
            {source.structured_content.images.map((img, i) => (
              <figure key={i}>
                <img src={`http://localhost:8000${img.url}`} alt={img.alt} />
                {img.alt && <figcaption>{img.alt}</figcaption>}
              </figure>
            ))}
          </div>
        )}

        {/* YouTube Videos */}
        {source.youtube_videos && source.youtube_videos.length > 0 && (
          <section className="videos">
            <h2>Videos</h2>
            {source.youtube_videos.map((video, i) => (
              <div key={i} className="video-container">
                <ReactPlayer
                  url={video.url}
                  controls
                  width="100%"
                  height="400px"
                />
                <p>{video.title}</p>
              </div>
            ))}
          </section>
        )}
      </div>
    </div>
  );
}
```

---

## CSS for Reading Mode

```css
.source-viewer.reading-mode {
  max-width: 700px;
  margin: 40px auto;
  padding: 40px;
  background: white;
  font-family: Georgia, 'Times New Roman', serif;
  line-height: 1.8;
  color: #333;
}

.source-viewer.reading-mode header {
  border-bottom: 1px solid #ddd;
  padding-bottom: 20px;
  margin-bottom: 30px;
}

.source-viewer.reading-mode header h1 {
  font-size: 36px;
  margin-bottom: 10px;
  font-weight: 700;
  line-height: 1.3;
}

.source-viewer.reading-mode header a {
  color: #666;
  text-decoration: none;
  font-size: 14px;
}

.source-viewer.reading-mode header time {
  display: block;
  color: #999;
  font-size: 13px;
  margin-top: 5px;
}

.source-viewer.reading-mode article h2 {
  font-size: 28px;
  margin-top: 40px;
  margin-bottom: 15px;
  font-weight: 600;
}

.source-viewer.reading-mode article h3 {
  font-size: 22px;
  margin-top: 30px;
  margin-bottom: 12px;
  font-weight: 600;
}

.source-viewer.reading-mode article p {
  margin-bottom: 20px;
  font-size: 18px;
}

.source-viewer.reading-mode article ul,
.source-viewer.reading-mode article ol {
  margin-bottom: 20px;
  padding-left: 30px;
}

.source-viewer.reading-mode article li {
  margin-bottom: 8px;
  font-size: 18px;
}

.source-viewer.reading-mode article table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 20px;
}

.source-viewer.reading-mode article th,
.source-viewer.reading-mode article td {
  padding: 12px;
  border: 1px solid #ddd;
  text-align: left;
}

.source-viewer.reading-mode article th {
  background: #f5f5f5;
  font-weight: 600;
}

.source-viewer.reading-mode .image-gallery {
  margin: 30px 0;
}

.source-viewer.reading-mode .image-gallery figure {
  margin-bottom: 20px;
}

.source-viewer.reading-mode .image-gallery img {
  width: 100%;
  height: auto;
  border-radius: 8px;
}

.source-viewer.reading-mode .image-gallery figcaption {
  margin-top: 8px;
  font-size: 14px;
  color: #666;
  font-style: italic;
}

.source-viewer.reading-mode .videos {
  margin-top: 40px;
  padding-top: 30px;
  border-top: 1px solid #ddd;
}

.source-viewer.reading-mode .video-container {
  margin-bottom: 30px;
}

.source-viewer.reading-mode .video-container p {
  margin-top: 10px;
  font-size: 16px;
  color: #666;
}
```

---

## Installation

### Required Packages:

```bash
npm install dompurify
npm install react-player
npm install @types/dompurify  # If using TypeScript
```

### Or with yarn:

```bash
yarn add dompurify react-player
yarn add -D @types/dompurify
```

---

## Quick Start

1. **Query for data:**
```typescript
const response = await fetch('http://localhost:8000/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'AI trends' })
});
const data = await response.json();
```

2. **Display sources:**
```tsx
{data.sources.map(source => (
  <SourceCard key={source.document_id} source={source} />
))}
```

3. **Open readonly viewer:**
```tsx
<SourceViewer source={selectedSource} onClose={handleClose} />
```

4. **Render YouTube videos:**
```tsx
{source.youtube_videos?.map(video => (
  <ReactPlayer url={video.url} controls />
))}
```

---

That's it! The backend provides all the data you need. Choose your rendering approach (structured content vs clean HTML) and build an amazing reading experience! 🚀
