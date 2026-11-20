import os
from pathlib import Path
from dotenv import load_dotenv

# Project root directory (c:\Users\JOMON\OneDrive\Desktop\Rag_1)
BASE_DIR = Path(__file__).resolve().parents[2]

# Load environment variables from root .env or backend/.env
env_root = BASE_DIR / ".env"
env_backend = BASE_DIR / "backend" / ".env"
if env_backend.exists():
    load_dotenv(env_backend)
elif env_root.exists():
    load_dotenv(env_root)
else:
    load_dotenv()

# Groq API configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()

# Google Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

# Document storage
DOCUMENT_DIR = BASE_DIR / "documents"
DOCUMENT_DIR.mkdir(exist_ok=True)

# Qdrant local database
QDRANT_PATH = BASE_DIR / "qdrant_data"

# Qdrant collection name
COLLECTION_NAME = "enterprise_documents"

# Embedding model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Embedding dimensions
VECTOR_SIZE = 384

# Chunk configuration
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

# Maximum upload size: 20 MB
MAX_FILE_SIZE = 20 * 1024 * 1024
