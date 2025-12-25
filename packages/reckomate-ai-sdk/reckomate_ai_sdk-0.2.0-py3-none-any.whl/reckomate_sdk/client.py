# Entry point for Reckomate SDK

from .services.admin import AdminService
from .services.user import UserService
from .services.upload import UploadService
from .services.rag import RAGService
from .services.chat import ChatService
from .services.ingest import IngestService


class ReckomateClient:
    def __init__(self):
        self.admin_service = AdminService()
        self.user_service = UserService()
        self.upload_service = UploadService()
        self.rag_service = RAGService()
        self.chat_service = ChatService()
        self.ingest_service = IngestService()

    def get_admin_service(self):
        return self.admin_service

    def get_user_service(self):
        return self.user_service

    def get_upload_service(self):
        return self.upload_service

    def get_rag_service(self):
        return self.rag_service

    def get_chat_service(self):
        return self.chat_service

    def get_ingest_service(self):
        return self.ingest_service