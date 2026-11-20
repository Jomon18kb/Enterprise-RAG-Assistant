from django.contrib import admin
from app.models import Document, ChatMessage


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("name", "page_count", "chunk_count", "file_size_display", "status", "uploaded_at")
    search_fields = ("name",)
    list_filter = ("status", "uploaded_at")


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("short_question", "created_at")
    search_fields = ("question", "answer")

    def short_question(self, obj):
        return obj.question[:60]
    short_question.short_description = "Question"

