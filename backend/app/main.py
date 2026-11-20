
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import DOCUMENT_DIR, MAX_FILE_SIZE
from app.retrieval import create_collection, store_chunks
from app.ingestion import process_document
from app.rag import ask_question


# Initialize Qdrant when the application starts
@asynccontextmanager
async def lifespan(app: FastAPI):

    create_collection()

    yield


app = FastAPI(
    title="Enterprise AI Knowledge Assistant",
    description="Advanced Retrieval Augmented Generation API",
    version="1.0.0",
    lifespan=lifespan
)


# Allow React frontend to access FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Request model
class ChatRequest(BaseModel):
    question: str


# Home endpoint
@app.get("/")
def home():

    return {
        "message": "Enterprise RAG API is running"
    }


# Health endpoint
@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# PDF upload endpoint
@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    file_content = await file.read(MAX_FILE_SIZE + 1)

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size exceeds 20 MB."
        )

    document_id = str(uuid4())

    file_path = DOCUMENT_DIR / f"{document_id}.pdf"

    try:

        file_path.write_bytes(file_content)

        # Extract and chunk document
        chunks = process_document(file_path)

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="No readable text found in PDF."
            )

        # Generate embeddings and store in Qdrant
        total_chunks = store_chunks(
            chunks,
            document_id,
            file.filename
        )

        return {
            "message": "Document uploaded successfully",
            "document_id": document_id,
            "document_name": file.filename,
            "total_chunks": total_chunks
        }

    except HTTPException:
        raise

    except Exception as error:

        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed: {str(error)}"
        )


# Chat endpoint
@app.post("/chat")
def chat(request: ChatRequest):

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    try:

        result = ask_question(question)

        return result

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"AI response failed: {str(error)}"
        )

