# AI Study Assistant 🎓

A RAG-powered study tool — upload your PDFs, ask questions, get answers grounded in your own notes.

---

## Architecture

```
frontend/          ← HTML + CSS + vanilla JS
backend/
  app.py           ← Flask REST API
  utils/
    pdf_processor.py   ← PDF extraction & chunking
    vector_store.py    ← ChromaDB + OpenAI embeddings
  models/__init__.py   ← Pydantic schemas
```

**Stack:** Flask · ChromaDB · OpenAI Embeddings (text-embedding-3-small) · GPT-3.5-turbo · PyMuPDF

---

## Quick Start

### 1. Clone & configure

```bash
git clone <repo>
cd ai-study-assistant/backend
cp .env.example .env
# → Edit .env and add your OPENAI_API_KEY
```

### 2. Install Python dependencies

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run the backend

```bash
python app.py
# API available at http://localhost:8000
```

### 4. Open the frontend

Open `frontend/index.html` in your browser directly, or serve it:

```bash
cd ../frontend
python -m http.server 3000
# → http://localhost:3000
```

---

## Docker (optional)

```bash
# From repo root
echo "OPENAI_API_KEY=sk-..." > .env
docker compose up --build
# Frontend → http://localhost:3000
# API      → http://localhost:8000
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload & index a PDF (`multipart/form-data`: `document`, `user_id`) |
| POST | `/ask` | Ask a question (`JSON`: `question`, `user_id`) |
| GET  | `/documents/{user_id}` | List user's documents |
| DELETE | `/document/{doc_id}` | Delete a document |
| GET  | `/stats/{user_id}` | Library statistics |
| GET  | `/health` | Health check |

---

## Bug Fixes Applied

| File | Issue | Fix |
|------|-------|-----|
| `vector_store.py` | Deprecated `openai.Embedding.create` (v0 API) | Upgraded to `openai>=1.0` `client.embeddings.create()` |
| `vector_store.py` | Deprecated `openai.ChatCompletion.create` | Updated to `client.chat.completions.create()` |
| `vector_store.py` | `ids_exist_ok=True` not a valid ChromaDB param | Replaced `add()` with `upsert()` |
| `app.py` | Mixed Flask + Express route structure | Unified to pure Flask with correct route handlers |
| `app.py` | Hardcoded Ollama LLM | Replaced with OpenAI GPT via VectorStore |
| `pdf_processor.py` | Regex `[^\w\s\.\,\!\?...]` stripped unicode text | Fixed character class to preserve accented characters |
| `script.js` | Template literal in regular string `'...${PORT}...'` | Fixed to backtick template literal |
| `style.css` | `upload-btn:hover` shadow `rgba(79,70,229,0)` (alpha=0) | Fixed alpha to `0.35` |
| `index.html` | Nav buttons had no `data-view` attributes | Added matching `data-view` attributes |
| `index.html` | Stats `id`s (`storageSize`) didn't match JS selectors | Harmonized IDs across HTML and JS |
