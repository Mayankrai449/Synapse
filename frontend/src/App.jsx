import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import './App.css'

const API_BASE_URL = 'http://localhost:8000'

function App() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState([]) // Changed from single response to array of messages
  const [selectedSource, setSelectedSource] = useState(null)
  const [sidePanelOpen, setSidePanelOpen] = useState(false)
  const messagesEndRef = useRef(null)

  // Check if query was passed via URL params (from omnibox)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const urlQuery = params.get('q')
    if (urlQuery) {
      setQuery(urlQuery)
      // Auto-execute the query
      setTimeout(() => {
        handleQueryWithText(urlQuery)
      }, 500)
    }
  }, [])

  // Scroll to bottom when new message arrives
  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleQueryWithText = async (queryText) => {
    if (!queryText.trim()) return

    // Add user message
    const userMessage = {
      type: 'user',
      text: queryText,
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMessage])

    setLoading(true)
    try {
      const result = await axios.post(`${API_BASE_URL}/query`, {
        query: queryText,
        top_k: 5,
        top_k_images: 6,
        include_images: true,
        enable_temporal_decay: true,
        use_bm25_fusion: true
      })

      // Add AI response message
      const aiMessage = {
        type: 'ai',
        text: queryText,
        response: result.data.response,
        images: result.data.images,
        sources: result.data.sources,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, aiMessage])
      console.log('Query response:', result.data)
    } catch (error) {
      console.error('Query error:', error)
      const errorMessage = {
        type: 'error',
        text: 'Error: ' + (error.response?.data?.detail || error.message),
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
      setQuery('') // Clear input after sending
    }
  }

  const handleQuery = async (e) => {
    e.preventDefault()
    handleQueryWithText(query)
  }

  const openSourcePanel = async (source) => {
    try {
      // Fetch full source details
      const result = await axios.get(`${API_BASE_URL}/source/${source.document_id}`)
      setSelectedSource(result.data)
      setSidePanelOpen(true)
    } catch (error) {
      console.error('Error fetching source:', error)
      alert('Error loading source: ' + (error.response?.data?.detail || error.message))
    }
  }

  const closeSidePanel = () => {
    setSidePanelOpen(false)
    setSelectedSource(null)
  }

  const renderStructuredContent = (content) => {
    if (!content) return null

    return (
      <div className="structured-content">
        {/* Headings */}
        {content.headings && content.headings.length > 0 && (
          <div className="content-section">
            <h3>Headings</h3>
            {content.headings.map((heading, idx) => (
              <div key={idx} style={{ marginLeft: `${heading.level * 12}px`, marginBottom: '8px' }}>
                <strong>H{heading.level}:</strong> {heading.text}
              </div>
            ))}
          </div>
        )}

        {/* Paragraphs */}
        {content.paragraphs && content.paragraphs.length > 0 && (
          <div className="content-section">
            <h3>Content</h3>
            {content.paragraphs.slice(0, 5).map((para, idx) => (
              <p key={idx} className="paragraph">{para}</p>
            ))}
          </div>
        )}

        {/* Lists */}
        {content.lists && content.lists.length > 0 && (
          <div className="content-section">
            <h3>Lists</h3>
            {content.lists.map((list, idx) => (
              <div key={idx} className="list-container">
                {list.type === 'ul' ? (
                  <ul>
                    {list.items.map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <ol>
                    {list.items.map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ol>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Tables */}
        {content.tables && content.tables.length > 0 && (
          <div className="content-section">
            <h3>Tables</h3>
            {content.tables.map((table, idx) => (
              <div key={idx} className="table-container">
                <table>
                  {table.headers && table.headers.length > 0 && (
                    <thead>
                      <tr>
                        {table.headers.map((header, i) => (
                          <th key={i}>{header}</th>
                        ))}
                      </tr>
                    </thead>
                  )}
                  <tbody>
                    {table.rows.map((row, i) => (
                      <tr key={i}>
                        {row.map((cell, j) => (
                          <td key={j}>{cell}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
          </div>
        )}

        {/* Images */}
        {content.images && content.images.length > 0 && (
          <div className="content-section">
            <h3>Images</h3>
            <div className="images-grid">
              {content.images.map((img, idx) => (
                <img
                  key={idx}
                  src={`${API_BASE_URL}${img.url}`}
                  alt={img.alt || 'Image'}
                  className="content-image"
                />
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderYouTubeVideos = (videos) => {
    if (!videos || videos.length === 0) return null

    return (
      <div className="content-section">
        <h3>YouTube Videos</h3>
        <div className="youtube-videos">
          {videos.map((video, idx) => (
            <div key={idx} className="youtube-container">
              <iframe
                width="100%"
                height="315"
                src={video.embed_url}
                title={video.title}
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              ></iframe>
              <p className="video-title">{video.title}</p>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="app">
      {/* Main Content Area */}
      <div className={`main-content ${sidePanelOpen ? 'with-panel' : ''}`}>
        {/* Header */}
        <div className="header">
          <h1>Synapse Mind</h1>
          <p className="subtitle">Your AI-powered second brain</p>
        </div>

        {/* Messages Container - Scrollable */}
        <div className="messages-container">
          {messages.length === 0 && !loading && (
            <div className="empty-state">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 16v-4M12 8h.01"/>
              </svg>
              <h2>Ask me anything</h2>
              <p>Search through your captured knowledge with natural language</p>
            </div>
          )}

          {messages.map((message, idx) => (
            <div key={idx} className={`message ${message.type}`}>
              {message.type === 'user' && (
                <div className="user-message">
                  <div className="message-bubble">
                    <p>{message.text}</p>
                  </div>
                </div>
              )}

              {message.type === 'ai' && (
                <div className="ai-message">
                  {/* AI Response */}
                  <div className="ai-response">
                    <div className="response-header">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                      </svg>
                      <h2>Response</h2>
                    </div>
                    <p className="response-text">{message.response}</p>
                  </div>

                  {/* Images */}
                  {message.images && message.images.length > 0 && (
                    <div className="images-section">
                      <h3>Related Images</h3>
                      <div className="images-horizontal">
                        {message.images.map((img, imgIdx) => (
                          <div key={imgIdx} className="image-card">
                            <img src={`${API_BASE_URL}${img}`} alt={`Result ${imgIdx + 1}`} />
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Sources */}
                  {message.sources && message.sources.length > 0 && (
                    <div className="sources-section">
                      <h3>Sources</h3>
                      <div className="sources-grid">
                        {message.sources.map((source, srcIdx) => (
                          <div key={srcIdx} className="source-card">
                            <div className="source-header">
                              {source.favicon && (
                                <img src={source.favicon} alt="" className="favicon" />
                              )}
                              <div className="source-info">
                                <h4>{source.title || 'Untitled'}</h4>
                                <p className="source-domain">{source.domain || 'Unknown source'}</p>
                                {source.timestamp && (
                                  <p className="source-timestamp">{source.timestamp}</p>
                                )}
                              </div>
                            </div>
                            <p className="source-snippet">{source.snippet}</p>
                            <div className="source-footer">
                              <span className="relevance-score">
                                Relevance: {(source.relevance_score * 100).toFixed(0)}%
                              </span>
                              <button
                                className="view-source-btn"
                                onClick={() => openSourcePanel(source)}
                              >
                                View Full Source
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {message.type === 'error' && (
                <div className="error-message">
                  <p>{message.text}</p>
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="message ai">
              <div className="ai-message loading">
                <div className="spinner"></div>
                <span>Thinking...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Query Box - Fixed at Bottom */}
        <div className="query-container-bottom">
          <form onSubmit={handleQuery}>
            <div className="query-box">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask me anything..."
                className="query-input"
                disabled={loading}
              />
              <button type="submit" className="query-button" disabled={loading}>
                {loading ? (
                  <div className="spinner"></div>
                ) : (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="11" cy="11" r="8"/>
                    <path d="m21 21-4.35-4.35"/>
                  </svg>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Side Panel */}
      {sidePanelOpen && selectedSource && (
        <>
          <div className="overlay" onClick={closeSidePanel}></div>
          <div className="side-panel">
            <div className="panel-header">
              <div className="panel-title">
                {selectedSource.favicon && (
                  <img src={selectedSource.favicon} alt="" className="favicon" />
                )}
                <div>
                  <h2>{selectedSource.title || 'Source Details'}</h2>
                  {selectedSource.url && (
                    <a href={selectedSource.url} target="_blank" rel="noopener noreferrer" className="source-url">
                      {selectedSource.domain || selectedSource.url}
                    </a>
                  )}
                </div>
              </div>
              <button className="close-btn" onClick={closeSidePanel}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>

            <div className="panel-content">
              {/* YouTube Videos */}
              {renderYouTubeVideos(selectedSource.youtube_videos)}

              {/* Structured Content */}
              {selectedSource.structured_content && Object.keys(selectedSource.structured_content).length > 0 && (
                renderStructuredContent(selectedSource.structured_content)
              )}

              {/* Clean HTML Fallback */}
              {selectedSource.clean_html &&
               (!selectedSource.structured_content || Object.keys(selectedSource.structured_content).length === 0) && (
                <div
                  className="clean-html"
                  dangerouslySetInnerHTML={{ __html: selectedSource.clean_html }}
                />
              )}

              {/* If no content at all, show message */}
              {!selectedSource.youtube_videos &&
               (!selectedSource.structured_content || Object.keys(selectedSource.structured_content).length === 0) &&
               !selectedSource.clean_html && (
                <div className="no-content">
                  <p>No detailed content available for this source.</p>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default App
