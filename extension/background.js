// Background service worker for Synapse extension
// Handles omnibox (address bar) search functionality

// Listen for when the user starts typing in the omnibox (after 'synapse' keyword)
chrome.omnibox.onInputChanged.addListener((text, suggest) => {
  // Provide search suggestions
  if (text.length > 0) {
    suggest([
      {
        content: text,
        description: `Search Synapse Mind for: <match>${text}</match>`
      }
    ]);
  }
});

// Listen for when the user accepts a suggestion or presses Enter
chrome.omnibox.onInputEntered.addListener((text, disposition) => {
  // URL encode the query text
  const encodedQuery = encodeURIComponent(text);
  const url = `http://localhost:3000?q=${encodedQuery}`;

  // Open in current tab or new tab based on disposition
  if (disposition === 'currentTab') {
    chrome.tabs.update({ url: url });
  } else {
    chrome.tabs.create({ url: url });
  }
});

// Set default suggestion when user types 'synapse'
chrome.omnibox.setDefaultSuggestion({
  description: 'Search your Synapse Mind knowledge base - Type your query and press Enter'
});
