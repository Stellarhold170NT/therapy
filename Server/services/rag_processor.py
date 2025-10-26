"""
RAG Processor Service
Xử lý việc load PDFs, split text, embedding và lưu vào Chroma vector store
"""

from pathlib import Path
from typing import List
import os

try:
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_ollama import OllamaEmbeddings
    from langchain_chroma import Chroma
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False


class RAGProcessor:
    """Xử lý RAG: load PDFs, split, embed và lưu vào Chroma"""

    def __init__(self, ollama_base_url: str = "http://localhost:11434"):
        if not HAS_LANGCHAIN:
            raise ImportError(
                "Langchain dependencies not installed. "
                "Please install: pip install langchain langchain-community langchain-text-splitters langchain-ollama langchain-chroma"
            )
        self.ollama_base_url = ollama_base_url
        self.chroma_base_dir = Path("chroma_db")
        self.chroma_base_dir.mkdir(exist_ok=True)

    def get_vector_store_path(self, config_name: str) -> str:
        """Generate vector store path từ config name"""
        safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in config_name)
        return str(self.chroma_base_dir / f"chroma_langchain_db_{safe_name}")

    def process_rag_config(
        self,
        config_name: str,
        embedding_model_name: str,
        document_file_paths: List[str],
        chunk_size: int,
        chunk_overlap: int
    ) -> dict:
        """
        Xử lý RAG configuration:
        1. Load PDFs
        2. Split text
        3. Create embeddings
        4. Store in Chroma

        Returns:
            dict với keys: success, message, vector_store_path, num_chunks
        """
        try:
            # 1. Load PDFs
            print(f"Loading {len(document_file_paths)} PDF files...")
            documents = []
            for pdf_path in document_file_paths:
                if not os.path.exists(pdf_path):
                    print(f"Warning: File not found: {pdf_path}")
                    continue

                try:
                    loader = PyPDFLoader(pdf_path)
                    docs = loader.load()
                    documents.extend(docs)
                    print(f"Loaded {len(docs)} pages from {Path(pdf_path).name}")
                except Exception as e:
                    print(f"Error loading {pdf_path}: {str(e)}")
                    continue

            if not documents:
                return {
                    "success": False,
                    "message": "No documents loaded successfully"
                }

            print(f"Total pages loaded: {len(documents)}")

            # 2. Split text
            print(f"Splitting text with chunk_size={chunk_size}, chunk_overlap={chunk_overlap}...")
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                add_start_index=True
            )
            all_splits = text_splitter.split_documents(documents)
            print(f"Created {len(all_splits)} text chunks")

            if not all_splits:
                return {
                    "success": False,
                    "message": "No text chunks created from documents"
                }

            # 3. Create embeddings và store in Chroma
            print(f"Creating embeddings with model: {embedding_model_name}...")
            embeddings = OllamaEmbeddings(
                base_url=self.ollama_base_url,
                model=embedding_model_name
            )

            vector_store_path = self.get_vector_store_path(config_name)
            print(f"Storing vectors in: {vector_store_path}")

            # Xóa thư mục cũ nếu tồn tại (để tránh duplicate data)
            if os.path.exists(vector_store_path):
                import shutil
                shutil.rmtree(vector_store_path)
                print(f"Removed existing vector store at {vector_store_path}")

            # Tạo vector store mới
            vector_store = Chroma.from_documents(
                documents=all_splits,
                embedding=embeddings,
                persist_directory=vector_store_path
            )

            print(f"Successfully created vector store with {len(all_splits)} chunks")

            return {
                "success": True,
                "message": f"RAG processing completed successfully",
                "vector_store_path": vector_store_path,
                "num_chunks": len(all_splits),
                "num_documents": len(documents)
            }

        except Exception as e:
            print(f"Error in RAG processing: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"RAG processing failed: {str(e)}"
            }

    def load_vector_store(self, config_name: str, embedding_model_name: str):
        """Load existing vector store"""
        try:
            vector_store_path = self.get_vector_store_path(config_name)

            if not os.path.exists(vector_store_path):
                raise FileNotFoundError(f"Vector store not found at {vector_store_path}")

            embeddings = OllamaEmbeddings(
                base_url=self.ollama_base_url,
                model=embedding_model_name
            )

            vector_store = Chroma(
                persist_directory=vector_store_path,
                embedding_function=embeddings
            )

            return vector_store

        except Exception as e:
            print(f"Error loading vector store: {str(e)}")
            raise
