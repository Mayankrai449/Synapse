# Gemini Embedding Search API

A FastAPI application that uses Google's Gemini text embedding model to store and search text documents.

## Features

- `/save` - Save text with embeddings to local storage
- `/query` - Search for similar texts using semantic similarity
- `/stats` - View storage statistics
- `/clear` - Clear all stored embeddings

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your Gemini API key:
```bash
cp .env.example .env
```

3. Edit `.env` and add your Gemini API key:
```
GEMINI_API_KEY=your_actual_api_key_here
```

Get your API key from: https://makersuite.google.com/app/apikey

## Running the Application

```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload
```

The API will be available at: http://localhost:8000

## API Usage

### Save Text

```bash
curl -X POST "http://localhost:8000/save" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "FastAPI is a modern web framework for building APIs",
    "metadata": {"category": "technology"}
  }'
```

### Query Similar Texts

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is FastAPI?",
    "top_k": 5
  }'
```

### Get Statistics

```bash
curl "http://localhost:8000/stats"
```

### Clear All Data

```bash
curl -X DELETE "http://localhost:8000/clear"
```

## Interactive Documentation

Visit http://localhost:8000/docs for Swagger UI documentation
