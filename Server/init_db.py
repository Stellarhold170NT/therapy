"""
Script để tạo tất cả tables trong database
Chạy: python init_db.py
"""
from database.connection import engine, Base

# Import tất cả models để SQLAlchemy biết cần tạo tables nào
from models.user import User
from models.chat_session import ChatSession
from models.message_store import MessageStore
from models.rag_config import RAGConfig
from models.document import Document
from models.rag_document import RagDocument
from models.model import Model


def init_database():
    """Tạo tất cả tables trong database"""
    print("Đang tạo tables trong database...")
    Base.metadata.create_all(bind=engine)
    print("✓ Hoàn thành! Tất cả tables đã được tạo.")


if __name__ == "__main__":
    init_database()
