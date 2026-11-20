import json
from pathlib import Path
from uuid import uuid4

from django.db.models import Sum
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from app.config import (
    DOCUMENT_DIR,
    MAX_FILE_SIZE,
    GROQ_API_KEY,
    GROQ_MODEL,
    GEMINI_API_KEY,
    GEMINI_MODEL,
)
from app.ingestion import process_document
from app.models import Document, ChatMessage
from app.rag import ask_question
from app.retrieval import store_chunks


@ensure_csrf_cookie
def index(request):
    """Main dashboard rendering documents list and interactive chat."""
    documents = Document.objects.all()
    chat_history = ChatMessage.objects.all().order_by("created_at")

    total_docs = documents.count()
    total_chunks = documents.aggregate(total=Sum("chunk_count"))["total"] or 0

    if GROQ_API_KEY:
        llm_provider = f"Groq ({GROQ_MODEL})"
        has_key = True
    elif GEMINI_API_KEY:
        llm_provider = f"Gemini ({GEMINI_MODEL})"
        has_key = True
    else:
        llm_provider = "No API key configured (Context retrieval only)"
        has_key = False

    context = {
        "documents": documents,
        "chat_history": chat_history,
        "total_documents": total_docs,
        "total_chunks": total_chunks,
        "has_api_key": has_key,
        "llm_provider": llm_provider,
    }
    return render(request, "app/index.html", context)


@require_http_methods(["POST"])
def upload_document(request):
    """Handle PDF upload, text chunking, and vector indexing."""
    if "file" not in request.FILES:
        return JsonResponse({"success": False, "error": "No file uploaded."}, status=400)

    uploaded_file = request.FILES["file"]
    filename = uploaded_file.name

    if not filename.lower().endswith(".pdf"):
        return JsonResponse({"success": False, "error": "Only PDF files are supported."}, status=400)

    if uploaded_file.size > MAX_FILE_SIZE:
        return JsonResponse(
            {"success": False, "error": "File size exceeds 20 MB limit."},
            status=400,
        )

    doc_id = uuid4()
    saved_filename = f"{doc_id}.pdf"
    file_path = DOCUMENT_DIR / saved_filename

    try:
        # Write file contents to disk
        with open(file_path, "wb+") as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # Extract text & generate chunks
        chunks, total_pages = process_document(file_path)

        if not chunks:
            if file_path.exists():
                file_path.unlink()
            return JsonResponse(
                {"success": False, "error": "No readable text found in PDF document."},
                status=400,
            )

        # Store chunks in Qdrant vector store
        chunk_count = store_chunks(chunks, doc_id, filename)

        # Save record in Django Database
        relative_storage_path = f"documents/{saved_filename}"
        doc = Document.objects.create(
            id=doc_id,
            name=filename,
            file=relative_storage_path,
            file_size=uploaded_file.size,
            page_count=total_pages,
            chunk_count=chunk_count,
            status="ready",
        )

        return JsonResponse({
            "success": True,
            "document": {
                "id": str(doc.id),
                "name": doc.name,
                "file_size": doc.file_size_display,
                "page_count": doc.page_count,
                "chunk_count": doc.chunk_count,
                "uploaded_at": doc.uploaded_at.strftime("%b %d, %Y %H:%M"),
            }
        })

    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        return JsonResponse(
            {"success": False, "error": f"Document processing failed: {str(e)}"},
            status=500,
        )


@require_http_methods(["POST"])
def chat_api(request):
    """RAG chat endpoint taking a question and returning answer + citations."""
    try:
        if request.content_type == "application/json":
            data = json.loads(request.body.decode("utf-8"))
            question = data.get("question", "").strip()
        else:
            question = request.POST.get("question", "").strip()
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid request body."}, status=400)

    if not question:
        return JsonResponse({"success": False, "error": "Question cannot be empty."}, status=400)

    try:
        # Ask question with RAG pipeline
        result = ask_question(question)

        # Store conversation in SQLite DB
        chat_msg = ChatMessage.objects.create(
            question=question,
            answer=result["answer"],
            sources=result.get("sources", []),
        )

        return JsonResponse({
            "success": True,
            "id": chat_msg.id,
            "question": question,
            "answer": result["answer"],
            "sources": result.get("sources", []),
            "created_at": chat_msg.created_at.strftime("%H:%M"),
        })

    except Exception as e:
        return JsonResponse(
            {"success": False, "error": f"AI response failed: {str(e)}"},
            status=500,
        )


@require_http_methods(["GET"])
def document_detail(request, doc_id):
    """Retrieve details for a specific document."""
    doc = get_object_or_404(Document, id=doc_id)
    return JsonResponse({
        "success": True,
        "document": {
            "id": str(doc.id),
            "name": doc.name,
            "page_count": doc.page_count,
            "chunk_count": doc.chunk_count,
            "file_size": doc.file_size_display,
            "uploaded_at": doc.uploaded_at.strftime("%b %d, %Y %H:%M"),
            "file_url": doc.file.url if doc.file else None,
        }
    })


@require_http_methods(["POST"])
def delete_document(request, doc_id):
    """Delete a document, its file on disk, and its vectors in Qdrant."""
    doc = get_object_or_404(Document, id=doc_id)
    doc.delete()
    return JsonResponse({"success": True, "message": "Document deleted successfully."})


@require_http_methods(["POST"])
def clear_chat(request):
    """Clear conversation history."""
    ChatMessage.objects.all().delete()
    return JsonResponse({"success": True, "message": "Chat history cleared."})


