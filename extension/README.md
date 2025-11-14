# Appointy Chrome Extension

A Chrome extension to capture and query text using your FastAPI backend.

## Setup Instructions

### 1. Create Extension Icons

Since Chrome requires icons, you need to create three PNG images:
- `icon16.png` (16x16 pixels)
- `icon48.png` (48x48 pixels)
- `icon128.png` (128x128 pixels)

You can:
- Create simple colored squares using any image editor
- Use online icon generators
- Download free icons from websites like flaticon.com
- Or temporarily use any PNG images renamed to these names

Save all three icons in the `extension` folder.

### 2. Start Your FastAPI Backend

Make sure your FastAPI backend is running:

```bash
cd backend
python main.py
```

The backend should be running at `http://localhost:8000`

### 3. Install the Extension in Chrome

1. Open Chrome and go to `chrome://extensions/`

2. Enable "Developer mode" by toggling the switch in the top right corner

3. Click "Load unpacked" button

4. Navigate to and select the `extension` folder:
   `C:\Users\ACER\OneDrive\Desktop\appointy\extension`

5. The extension should now appear in your extensions list

6. Pin the extension by clicking the puzzle icon in Chrome toolbar and clicking the pin icon next to "Appointy Text Capture"

### 4. Using the Extension

#### Capture Text:
1. Click the extension icon in your Chrome toolbar
2. Enter text in the "Capture Text" field
3. Click "Capture" button
4. The text will be saved to your backend with timestamp metadata

#### Query Text:
1. Click the extension icon
2. Enter your search query in the "Query Text" field
3. Click "Query" button
4. Results will be displayed below, showing:
   - The matching text
   - Similarity score
   - Timestamp when it was saved

## Features

- Captures text with automatic timestamp (date and time)
- Queries saved text using semantic search
- Shows top 5 most similar results
- Displays similarity scores and timestamps
- Clean, user-friendly interface

## API Endpoints Used

- `POST /save` - Save text with embeddings
- `POST /query` - Query similar texts

## Troubleshooting

- **Extension not loading**: Make sure all files are in the extension folder and icons are present
- **API errors**: Verify the FastAPI backend is running on port 8000
- **CORS errors**: The backend needs to allow requests from Chrome extension origin
- **No results**: Make sure you've saved some text first using the Capture feature
