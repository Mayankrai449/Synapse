// API Base URL
const API_BASE_URL = 'http://localhost:8000';

// Get DOM elements
const captureBtn = document.getElementById('captureBtn');
const openMindBtn = document.getElementById('openMindBtn');
const status = document.getElementById('status');

// Capture button click handler
captureBtn.addEventListener('click', async () => {
  try {
    captureBtn.disabled = true;
    showStatus('Capturing page...', 'info');

    // Get active tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    // Inject content script to extract page data
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      function: extractPageContent
    });

    const pageData = results[0].result;

    if (!pageData || !pageData.text) {
      throw new Error('Could not extract page content');
    }

    // Prepare metadata with full page data
    const now = new Date();
    const metadata = {
      url: pageData.url,
      title: pageData.title,
      domain: pageData.domain,
      favicon: pageData.favicon,
      timestamp: now.toISOString(),
      timestamp_readable: now.toLocaleString(),
      date: now.toLocaleDateString(),
      time: now.toLocaleTimeString(),
      structured_content: pageData.structured_content,
      youtube_videos: pageData.youtube_videos,
      clean_html: pageData.clean_html
    };

    console.log('Sending data to backend:');
    console.log('- Text length:', pageData.text.length);
    console.log('- Images:', pageData.image_urls.length);
    console.log('- YouTube videos:', pageData.youtube_videos.length);
    console.log('- Metadata:', metadata);

    // Create FormData for multipart request
    const formData = new FormData();
    formData.append('text', pageData.text || '');
    formData.append('metadata', JSON.stringify(metadata));
    formData.append('enable_chunking', 'true');
    formData.append('image_urls', JSON.stringify(pageData.image_urls || []));

    // Send to /save endpoint
    const response = await fetch(`${API_BASE_URL}/save`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    console.log('Backend response:', data);

    // Show success message
    let message = `✓ Captured! ${data.text_chunks_created} chunks, ${data.images_saved} images`;

    // Add warning if some images failed
    if (data.warning) {
      message += ` (${data.warning})`;
    }

    showStatus(message, data.warning ? 'info' : 'success');

    // Auto-hide after 4 seconds (longer if there's a warning)
    setTimeout(() => {
      showStatus('', '');
    }, data.warning ? 5000 : 3000);

  } catch (error) {
    console.error('Capture error:', error);
    showStatus(`✗ Error: ${error.message}`, 'error');
  } finally {
    captureBtn.disabled = false;
  }
});

// Open Synapse Mind button - opens React app
openMindBtn.addEventListener('click', () => {
  chrome.tabs.create({ url: 'http://localhost:3000' });
  showStatus('Opening Synapse Mind...', 'info');
  setTimeout(() => {
    window.close();
  }, 500);
});

// Content extraction function (runs in page context)
function extractPageContent() {
  const data = {
    url: window.location.href,
    title: document.title,
    domain: window.location.hostname,
    favicon: '',
    text: '',
    image_urls: [],
    youtube_videos: [],
    structured_content: {
      headings: [],
      paragraphs: [],
      lists: [],
      tables: [],
      images_positions: []
    },
    clean_html: ''
  };

  // Extract favicon
  const faviconLink = document.querySelector('link[rel~="icon"]') ||
                      document.querySelector('link[rel~="shortcut icon"]');
  if (faviconLink) {
    data.favicon = new URL(faviconLink.href, window.location.origin).href;
  } else {
    data.favicon = `${window.location.origin}/favicon.ico`;
  }

  // Extract main content area (try common selectors)
  const contentSelectors = [
    'article',
    'main',
    '[role="main"]',
    '.content',
    '.post-content',
    '.article-content',
    '#content',
    'body'
  ];

  let contentRoot = null;
  for (const selector of contentSelectors) {
    contentRoot = document.querySelector(selector);
    if (contentRoot) break;
  }

  if (!contentRoot) {
    contentRoot = document.body;
  }

  // Extract text content
  const textNodes = [];
  const walker = document.createTreeWalker(
    contentRoot,
    NodeFilter.SHOW_TEXT,
    {
      acceptNode: (node) => {
        // Skip script, style, and hidden elements
        const parent = node.parentElement;
        if (!parent) return NodeFilter.FILTER_REJECT;

        const tagName = parent.tagName.toLowerCase();
        if (['script', 'style', 'noscript', 'iframe'].includes(tagName)) {
          return NodeFilter.FILTER_REJECT;
        }

        const style = window.getComputedStyle(parent);
        if (style.display === 'none' || style.visibility === 'hidden') {
          return NodeFilter.FILTER_REJECT;
        }

        const text = node.textContent.trim();
        if (text.length > 0) {
          return NodeFilter.FILTER_ACCEPT;
        }

        return NodeFilter.FILTER_REJECT;
      }
    }
  );

  while (walker.nextNode()) {
    textNodes.push(walker.currentNode.textContent.trim());
  }

  data.text = textNodes.join(' ').replace(/\s+/g, ' ').trim();

  // Extract headings
  const headings = contentRoot.querySelectorAll('h1, h2, h3, h4, h5, h6');
  headings.forEach((heading, index) => {
    data.structured_content.headings.push({
      level: parseInt(heading.tagName[1]),
      text: heading.textContent.trim(),
      position: index
    });
  });

  // Extract paragraphs
  const paragraphs = contentRoot.querySelectorAll('p');
  paragraphs.forEach(p => {
    const text = p.textContent.trim();
    if (text.length > 20) {  // Skip very short paragraphs
      data.structured_content.paragraphs.push(text);
    }
  });

  // Extract lists
  const lists = contentRoot.querySelectorAll('ul, ol');
  lists.forEach(list => {
    const items = Array.from(list.querySelectorAll('li')).map(li => li.textContent.trim());
    if (items.length > 0) {
      data.structured_content.lists.push({
        type: list.tagName.toLowerCase(),
        items: items
      });
    }
  });

  // Extract tables
  const tables = contentRoot.querySelectorAll('table');
  tables.forEach(table => {
    const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent.trim());
    const rows = Array.from(table.querySelectorAll('tr')).map(tr => {
      return Array.from(tr.querySelectorAll('td')).map(td => td.textContent.trim());
    }).filter(row => row.length > 0);

    if (rows.length > 0) {
      data.structured_content.tables.push({
        headers: headers,
        rows: rows
      });
    }
  });

  // Extract images
  const images = contentRoot.querySelectorAll('img');
  images.forEach((img, index) => {
    const src = img.src;
    const alt = img.alt || '';

    if (src && !src.startsWith('data:')) {  // Skip data URLs
      data.image_urls.push(src);
      data.structured_content.images_positions.push({
        src: src,
        alt: alt,
        position: index
      });
    }
  });

  // Extract YouTube videos
  const youtubeIframes = contentRoot.querySelectorAll('iframe[src*="youtube.com"], iframe[src*="youtu.be"]');
  youtubeIframes.forEach(iframe => {
    const src = iframe.src;
    const match = src.match(/(?:youtube\.com\/embed\/|youtu\.be\/)([a-zA-Z0-9_-]+)/);
    if (match) {
      const videoId = match[1];
      data.youtube_videos.push({
        url: `https://www.youtube.com/watch?v=${videoId}`,
        embed_url: `https://www.youtube.com/embed/${videoId}`,
        video_id: videoId,
        title: iframe.title || 'YouTube Video'
      });
    }
  });

  // Also check for YouTube links
  const youtubeLinks = contentRoot.querySelectorAll('a[href*="youtube.com/watch"], a[href*="youtu.be/"]');
  youtubeLinks.forEach(link => {
    const href = link.href;
    const match = href.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]+)/);
    if (match) {
      const videoId = match[1];
      // Check if not already added
      if (!data.youtube_videos.some(v => v.video_id === videoId)) {
        data.youtube_videos.push({
          url: `https://www.youtube.com/watch?v=${videoId}`,
          embed_url: `https://www.youtube.com/embed/${videoId}`,
          video_id: videoId,
          title: link.textContent.trim() || 'YouTube Video'
        });
      }
    }
  });

  // Create clean HTML
  const cleanHTML = document.createElement('article');

  // Add headings and paragraphs in order
  contentRoot.querySelectorAll('h1, h2, h3, h4, h5, h6, p, ul, ol, table, blockquote, pre').forEach(el => {
    const clone = el.cloneNode(true);
    // Remove scripts and event handlers
    clone.querySelectorAll('script, style').forEach(s => s.remove());
    Array.from(clone.attributes).forEach(attr => {
      if (attr.name.startsWith('on')) {
        clone.removeAttribute(attr.name);
      }
    });
    cleanHTML.appendChild(clone);
  });

  data.clean_html = cleanHTML.innerHTML;

  return data;
}

// Helper function to show status messages
function showStatus(message, type) {
  status.textContent = message;
  status.className = `status ${type}`;
}
