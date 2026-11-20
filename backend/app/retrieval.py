from uuid import uuid4
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from app.config import (
    QDRANT_PATH,
    COLLECTION_NAME,
    VECTOR_SIZE,
)
from app.embedding import generate_embeddings, generate_query_embedding

_client = None


def get_client():
    """Lazy initialize persistent local Qdrant database."""
    global _client
    if _client is None:
        _client = QdrantClient(path=str(QDRANT_PATH))
    return _client


def create_collection():
    """Ensure the target collection exists in Qdrant."""
    client = get_client()
    try:
        collections = client.get_collections().collections
        exists = any(collection.name == COLLECTION_NAME for collection in collections)
        if not exists:
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=VECTOR_SIZE,
                    distance=Distance.COSINE
                )
            )
    except Exception as e:
        print(f"Collection check/creation error: {e}")


def store_chunks(chunks, document_id, document_name):
    """Store chunk text, vectors, and metadata into Qdrant."""
    if not chunks:
        return 0

    create_collection()
    client = get_client()

    texts = [chunk["text"] for chunk in chunks]
    vectors = generate_embeddings(texts)

    points = []
    for chunk, vector in zip(chunks, vectors):
        points.append(
            PointStruct(
                id=str(uuid4()),
                vector=vector,
                payload={
                    "text": chunk["text"],
                    "document_id": str(document_id),
                    "document_name": document_name,
                    "page_number": chunk["page_number"],
                    "chunk_number": chunk["chunk_number"]
                }
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
        wait=True
    )

    return len(points)


def search_documents(question, limit=5):
    """Retrieve top-k relevant document chunks for a question."""
    create_collection()
    client = get_client()

    try:
        collections = client.get_collections().collections
        if not any(c.name == COLLECTION_NAME for c in collections):
            return []
    except Exception:
        return []

    query_vector = generate_query_embedding(question)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit,
        with_payload=True
    )

    retrieved_documents = []
    for result in results.points:
        retrieved_documents.append({
            "text": result.payload.get("text", ""),
            "document_name": result.payload.get("document_name", "Unknown"),
            "document_id": result.payload.get("document_id", ""),
            "page_number": result.payload.get("page_number", 1),
            "score": float(result.score) if hasattr(result, "score") else 0.0
        })

    return retrieved_documents


def delete_document_chunks(document_id):
    """Delete all vector points belonging to a specific document."""
    client = get_client()
    try:
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=str(document_id))
                    )
                ]
            )
        )
        return True
    except Exception as e:
        print(f"Error deleting chunks for document {document_id}: {e}")
        return False
