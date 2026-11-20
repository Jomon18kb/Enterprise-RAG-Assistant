# Enterprise RAG Assistant (Django Backend with HTML & CSS)

An Enterprise Retrieval Augmented Generation (RAG) web application powered by **Django**, **Qdrant**, **Sentence-Transformers**, **PyMuPDF**, and **Groq / Google Gemini LLMs**.

---

## 🚀 Features

- **Django Backend**: Fully featured Django architecture (`rag_backend`) with SQLite persistence, migrations, and modular app services.
- **Modern HTML & CSS UI**: Handcrafted responsive UI (`base.html`, `index.html`, and `style.css`) with:
  - Drag-and-drop PDF uploader with real-time chunking progress.
  - Interactive chat workspace with auto-scrolling, quick prompt chips, and message history.
  - Expandable citations drawer displaying exact document names, page numbers, and relevance scores.
  - Real-time document management (upload, delete from DB + disk + vector index).
- **Offline Fast Embeddings**: High-performance lazy-loaded embeddings via `all-MiniLM-L6-v2` with local cache prioritization.
- **Vector Search Engine**: Embedded local Qdrant database storing vectors and rich chunk metadata.
- **Dual LLM Provider Support**: Supports **Groq** (`llama-3.3-70b-versatile`) and **Google Gemini** (`gemini-2.5-flash`), with graceful fallback when no API key is configured.

---

## 🛠️ Project Structure

```
Rag_1/
├── backend/
│   ├── app/
│   │   ├── config.py             # Environment & model configurations
│   │   ├── embedding.py          # Sentence-Transformers vectorizer
│   │   ├── ingestion.py          # PyMuPDF text extractor & chunking
│   │   ├── models.py             # Django models (Document, ChatMessage)
│   │   ├── rag.py                # Retrieval & LLM response generator
│   │   ├── retrieval.py          # Qdrant client & vector search
│   │   ├── views.py              # Web & API controllers
│   │   ├── urls.py               # App routing
│   │   ├── tests.py              # Automated test suite
│   │   ├── templates/app/        # HTML templates (base.html, index.html)
│   │   └── static/               # CSS styles and client JS
│   ├── rag_backend/              # Django project settings & root URLs
│   ├── db.sqlite3                # SQLite database
│   ├── manage.py                 # Backend manage.py
│   └── requirements.txt          # Python dependencies
├── documents/                    # Uploaded PDF document storage
├── qdrant_data/                  # Persistent Qdrant vector storage
├── .env                          # API keys configuration
├── manage.py                     # Root CLI wrapper for manage.py
└── README.md
```

---

## ⚙️ Setup & Running

### 1. Configure API Key
Edit the `.env` file in the root directory and provide your Groq or Gemini API key:

```ini
# Option 1: Groq API Key (Recommended)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Option 2: Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

*(Note: Even without an API key, the app will upload PDFs, chunk text, and perform vector similarity search, presenting the retrieved chunks with relevance scores!)*

### 2. Run Database Migrations
Migrations have already been created and applied. If you make any model changes, run:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Run the Development Server
From the project root:
```bash
python manage.py runserver
```
Or from inside the `backend` folder:
```bash
cd backend
python manage.py runserver
```

Open your browser at:
👉 **`http://127.0.0.1:8000/`**

---

## 🧪 Running Automated Tests

Run the full Django test suite (7 tests):
```bash
python manage.py test app
```

