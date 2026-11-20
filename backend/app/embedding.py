import os
from app.config import EMBEDDING_MODEL

_model = None


def get_embedding_model():
    """Lazy load SentenceTransformer model, prioritizing local cache for maximum speed."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        try:
            # Try loading from local HuggingFace cache without network checks
            _model = SentenceTransformer(EMBEDDING_MODEL, local_files_only=True)
        except Exception:
            # Fallback to standard initialization if not cached yet
            _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def generate_embeddings(texts):
    """Generate dense embeddings for a list of text strings."""
    if not texts:
        return []
    model = get_embedding_model()
    embeddings = model.encode(texts)
    return embeddings.tolist()


def generate_query_embedding(query):
    """Generate a dense embedding vector for a single query string."""
    model = get_embedding_model()
    embedding = model.encode(query)
    return embedding.tolist()
