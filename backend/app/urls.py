from django.urls import path
from app import views

app_name = "app"

urlpatterns = [
    path("", views.index, name="index"),
    path("upload/", views.upload_document, name="upload_document"),
    path("chat/", views.chat_api, name="chat_api"),
    path("documents/<uuid:doc_id>/", views.document_detail, name="document_detail"),
    path("documents/<uuid:doc_id>/delete/", views.delete_document, name="delete_document"),
    path("chat/clear/", views.clear_chat, name="clear_chat"),
]

