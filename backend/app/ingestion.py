from pathlib import Path
import pymupdf as fitz

from app.config import CHUNK_SIZE, CHUNK_OVERLAP


def extract_text(file_path):
    """Extract text from each page of a PDF document."""
    file_path = str(file_path)
    document = fitz.open(file_path)
    pages = []

    try:
        total_pages = len(document)
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            if text:
                pages.append({
                    "page_number": page_number,
                    "text": text
                })
    finally:
        document.close()

    return pages, total_pages


def create_chunks(text):
    """Split text into overlapping chunks of words."""
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + CHUNK_SIZE
        chunk_text = " ".join(words[start:end])
        if chunk_text.strip():
            chunks.append(chunk_text)

        if end >= len(words):
            break

        start = end - CHUNK_OVERLAP

    return chunks


def process_document(file_path):
    """Process a PDF file into chunks with metadata."""
    pages, total_pages = extract_text(file_path)
    all_chunks = []

    for page in pages:
        chunks = create_chunks(page["text"])
        for index, chunk in enumerate(chunks):
            all_chunks.append({
                "text": chunk,
                "page_number": page["page_number"],
                "chunk_number": index + 1
            })

    return all_chunks, total_pages
