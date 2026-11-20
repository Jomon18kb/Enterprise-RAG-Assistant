import uuid
from pathlib import Path
from django.db import models


class Document(models.Model):
    """Uploaded PDF document metadata and statistics."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to="documents/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.BigIntegerField(default=0)
    page_count = models.IntegerField(default=0)
    chunk_count = models.IntegerField(default=0)
    status = models.CharField(max_length=32, default="ready")

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.name} ({self.page_count} pages, {self.chunk_count} chunks)"

    @property
    def file_size_display(self):
        """Format file size in human-readable units."""
        size = self.file_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}" if unit != "B" else f"{size} B"
            size /= 1024.0
        return f"{size:.1f} TB"

    def delete(self, *args, **kwargs):
        """Clean up vector storage and file on disk when document is deleted."""
        try:
            from app.retrieval import delete_document_chunks
            delete_document_chunks(str(self.id))
        except Exception as e:
            print(f"Failed to delete Qdrant points for {self.id}: {e}")

        if self.file and self.file.name:
            try:
                storage_file = Path(self.file.path)
                if storage_file.exists():
                    storage_file.unlink()
            except Exception as e:
                print(f"Failed to delete file from disk: {e}")

        super().delete(*args, **kwargs)


class ChatMessage(models.Model):
    """User conversation history and retrieved citations."""
    question = models.TextField()
    answer = models.TextField()
    sources = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Q: {self.question[:40]}..."

