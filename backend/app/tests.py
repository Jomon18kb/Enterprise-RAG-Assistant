import io
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

import pymupdf as fitz
from app.models import Document, ChatMessage


def create_sample_pdf(content_text="This is an enterprise test report. Antigravity AI provides automated solutions."):
    """Generate in-memory PDF file for testing."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), content_text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


class RagAppTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_homepage_loads(self):
        """Test homepage renders 200 OK with proper HTML and CSS links."""
        response = self.client.get(reverse('app:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enterprise RAG")
        self.assertContains(response, "Knowledge Base")
        self.assertContains(response, "style.css")
        self.assertContains(response, "main.js")

    def test_upload_non_pdf_fails(self):
        """Test uploading a non-PDF file returns a 400 bad request."""
        fake_file = SimpleUploadedFile("notes.txt", b"plain text", content_type="text/plain")
        response = self.client.post(reverse('app:upload_document'), {'file': fake_file})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("Only PDF files are supported", data["error"])

    def test_upload_pdf_success(self):
        """Test uploading a valid PDF processes chunks and creates Document record."""
        pdf_bytes = create_sample_pdf("Enterprise security guidelines. Employees must rotate credentials every 90 days.")
        uploaded_pdf = SimpleUploadedFile("guidelines.pdf", pdf_bytes, content_type="application/pdf")

        response = self.client.post(reverse('app:upload_document'), {'file': uploaded_pdf})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["document"]["name"], "guidelines.pdf")
        self.assertGreater(data["document"]["chunk_count"], 0)

        # Check DB
        self.assertEqual(Document.objects.count(), 1)
        doc = Document.objects.first()
        self.assertEqual(doc.name, "guidelines.pdf")

    def test_chat_empty_question(self):
        """Test submitting empty question returns 400."""
        response = self.client.post(reverse('app:chat_api'), {'question': '   '})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["success"])

    def test_chat_with_question(self):
        """Test chat returns response and stores ChatMessage in DB."""
        response = self.client.post(
            reverse('app:chat_api'),
            data={'question': 'What are the security guidelines?'},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("answer", data)
        self.assertIsInstance(data.get("sources"), list)

        # Verify chat message recorded
        self.assertEqual(ChatMessage.objects.count(), 1)
        msg = ChatMessage.objects.first()
        self.assertEqual(msg.question, "What are the security guidelines?")

    def test_clear_chat(self):
        """Test clearing chat history removes all messages."""
        ChatMessage.objects.create(question="Q1", answer="A1")
        ChatMessage.objects.create(question="Q2", answer="A2")
        self.assertEqual(ChatMessage.objects.count(), 2)

        response = self.client.post(reverse('app:clear_chat'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ChatMessage.objects.count(), 0)

    def test_delete_document(self):
        """Test deleting a document removes it from database."""
        pdf_bytes = create_sample_pdf("Deletable document content.")
        uploaded_pdf = SimpleUploadedFile("delete_me.pdf", pdf_bytes, content_type="application/pdf")
        upload_resp = self.client.post(reverse('app:upload_document'), {'file': uploaded_pdf})
        doc_id = upload_resp.json()["document"]["id"]

        self.assertEqual(Document.objects.filter(id=doc_id).count(), 1)

        del_resp = self.client.post(reverse('app:delete_document', args=[doc_id]))
        self.assertEqual(del_resp.status_code, 200)
        self.assertEqual(Document.objects.filter(id=doc_id).count(), 0)

