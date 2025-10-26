from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from database.connection import get_db
from models.rag_config import RAGConfig
from models.document import Document
from models.rag_document import RagDocument
from models.model import Model
from schemas.rag_config_schema import RAGConfigCreate, RAGConfigUpdate, RAGConfigOut
from schemas.document_schema import DocumentCreate, DocumentUpdate, DocumentOut

# Import RAGProcessor lazily để tránh lỗi nếu langchain chưa cài
try:
    from services.rag_processor import RAGProcessor
    HAS_RAG_PROCESSOR = True
except ImportError as e:
    print(f"Warning: RAGProcessor not available: {e}")
    HAS_RAG_PROCESSOR = False
from schemas.rag_document_schema import RagDocumentCreate, RagDocumentBatchCreate, RagDocumentOut, RagDocumentWithDetails
from schemas.model_schema import ModelCreate, ModelUpdate, ModelOut
from auth.auth import get_current_user
from models.user import User
from typing import List, Optional
from datetime import datetime
import os
import shutil
from pathlib import Path


router = APIRouter(prefix="/rag-configs", tags=["RAG Configurations"])


@router.post("/", response_model=RAGConfigOut)
def create_rag_config(
    config: RAGConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can create RAG configurations")

    new_config = RAGConfig(
        config_name=config.config_name,
        llm_id=config.llm_id,
        embedding_model_id=config.embedding_model_id,
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
        search_type=config.search_type,
        k_value=config.k_value,
        prompt_template=config.prompt_template
    )

    db.add(new_config)
    db.commit()
    db.refresh(new_config)
    return new_config


@router.get("/", response_model=List[RAGConfigOut])
def list_rag_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(RAGConfig).all()


@router.get("/{config_id}", response_model=RAGConfigOut)
def get_rag_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    config = db.query(RAGConfig).filter(RAGConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="RAG configuration not found")
    return config


@router.put("/{config_id}", response_model=RAGConfigOut)
def update_rag_config(
    config_id: int,
    config_update: RAGConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can update RAG configurations")

    config = db.query(RAGConfig).filter(RAGConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="RAG configuration not found")

    update_data = config_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    db.commit()
    db.refresh(config)
    return config


@router.delete("/{config_id}")
def delete_rag_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete RAG configurations")

    config = db.query(RAGConfig).filter(RAGConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="RAG configuration not found")

    db.delete(config)
    db.commit()
    return {"message": f"RAG configuration '{config.config_name}' deleted successfully"}


# ========================= DOCUMENT MANAGEMENT ENDPOINTS =========================

# Thư mục lưu uploaded files
UPLOAD_DIR = Path("uploads/documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/documents/upload", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    total_pages: Optional[int] = Form(None),
    creation_date: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload document file và lưu thông tin vào database"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can upload documents")

    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Tạo unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = UPLOAD_DIR / filename

    # Save file to disk
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Parse creation_date if provided
    parsed_creation_date = None
    if creation_date:
        try:
            parsed_creation_date = datetime.fromisoformat(creation_date)
        except ValueError:
            pass

    # Lưu thông tin vào database
    new_document = Document(
        file_name=file.filename,
        file_path=str(file_path),
        title=title or file.filename.replace('.pdf', ''),
        author=author,
        total_pages=total_pages,
        creation_date=parsed_creation_date
    )

    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    return new_document


@router.get("/documents/", response_model=List[DocumentOut])
def list_documents(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lấy danh sách tất cả documents với optional search"""
    query = db.query(Document)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Document.file_name.like(search_pattern)) |
            (Document.title.like(search_pattern)) |
            (Document.author.like(search_pattern))
        )

    return query.order_by(Document.uploaded_at.desc()).all()


@router.get("/documents/{doc_id}", response_model=DocumentOut)
def get_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lấy thông tin chi tiết document"""
    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.put("/documents/{doc_id}", response_model=DocumentOut)
def update_document(
    doc_id: int,
    document_update: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cập nhật thông tin document"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can update documents")

    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    update_data = document_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(document, field, value)

    db.commit()
    db.refresh(document)
    return document


@router.delete("/documents/{doc_id}")
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Xóa document (cả file và database record)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete documents")

    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Xóa file trên disk nếu tồn tại
    try:
        file_path = Path(document.file_path)
        if file_path.exists():
            os.remove(file_path)
    except Exception as e:
        # Log error nhưng vẫn tiếp tục xóa database record
        print(f"Warning: Could not delete file {document.file_path}: {str(e)}")

    # Xóa database record
    db.delete(document)
    db.commit()

    return {"message": f"Document '{document.file_name}' deleted successfully"}


# ========================= RAG DOCUMENT ASSOCIATIONS =========================

@router.post("/{config_id}/documents")
def add_documents_to_rag_config(
    config_id: int,
    document_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Thêm documents vào RAG configuration và trigger RAG processing.

    Flow:
    1. Lưu document associations vào database
    2. Lấy thông tin embedding model
    3. Load PDFs và process RAG (split, embed, store in Chroma)

    Returns:
        Dict with associations and RAG processing result
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can add documents to RAG config")

    # Kiểm tra RAG config tồn tại
    config = db.query(RAGConfig).filter(RAGConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="RAG configuration not found")

    # Kiểm tra documents tồn tại
    documents = db.query(Document).filter(Document.id.in_(document_ids)).all()
    if len(documents) != len(document_ids):
        raise HTTPException(status_code=404, detail="One or more documents not found")

    # Xóa associations cũ của config này (nếu có)
    db.query(RagDocument).filter(RagDocument.rag_config_id == config_id).delete()

    # Tạo associations mới
    new_associations = []
    for doc_id in document_ids:
        rag_doc = RagDocument(
            rag_config_id=config_id,
            document_id=doc_id
        )
        db.add(rag_doc)
        new_associations.append(rag_doc)

    db.commit()

    # Refresh để lấy ID
    for assoc in new_associations:
        db.refresh(assoc)

    # ===== TRIGGER RAG PROCESSING =====
    try:
        # Kiểm tra RAGProcessor có available không
        if not HAS_RAG_PROCESSOR:
            return {
                "success": False,
                "message": "Documents added but RAG processing unavailable (langchain not installed)",
                "associations": [{"id": a.id, "rag_config_id": a.rag_config_id, "document_id": a.document_id} for a in new_associations]
            }

        # Lấy embedding model name
        embedding_model = db.query(Model).filter(Model.id == config.embedding_model_id).first()
        if not embedding_model:
            return {
                "success": False,
                "message": "Embedding model not found",
                "associations": [{"id": a.id, "rag_config_id": a.rag_config_id, "document_id": a.document_id} for a in new_associations]
            }

        # Lấy file paths của documents
        document_file_paths = [doc.file_path for doc in documents]

        # Initialize RAG processor
        rag_processor = RAGProcessor()

        # Process RAG
        print(f"Starting RAG processing for config: {config.config_name}")
        result = rag_processor.process_rag_config(
            config_name=config.config_name,
            embedding_model_name=embedding_model.model_name,
            document_file_paths=document_file_paths,
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap
        )

        if result["success"]:
            return {
                "success": True,
                "message": f"Successfully added {len(new_associations)} documents and processed RAG",
                "associations": [{"id": a.id, "rag_config_id": a.rag_config_id, "document_id": a.document_id} for a in new_associations],
                "rag_processing": {
                    "vector_store_path": result["vector_store_path"],
                    "num_chunks": result["num_chunks"],
                    "num_documents": result["num_documents"]
                }
            }
        else:
            return {
                "success": False,
                "message": f"Documents added but RAG processing failed: {result['message']}",
                "associations": [{"id": a.id, "rag_config_id": a.rag_config_id, "document_id": a.document_id} for a in new_associations]
            }

    except Exception as e:
        print(f"Error in RAG processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Documents added but RAG processing failed: {str(e)}",
            "associations": [{"id": a.id, "rag_config_id": a.rag_config_id, "document_id": a.document_id} for a in new_associations]
        }


@router.get("/{config_id}/documents", response_model=List[RagDocumentWithDetails])
def get_rag_config_documents(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lấy danh sách documents của một RAG configuration"""
    # Kiểm tra RAG config tồn tại
    config = db.query(RAGConfig).filter(RAGConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="RAG configuration not found")

    # Query với join để lấy thông tin document
    results = db.query(
        RagDocument.id,
        RagDocument.rag_config_id,
        RagDocument.document_id,
        Document.file_name,
        Document.title,
        RagDocument.created_at
    ).join(
        Document, RagDocument.document_id == Document.id
    ).filter(
        RagDocument.rag_config_id == config_id
    ).all()

    # Convert to schema format
    documents_with_details = []
    for result in results:
        documents_with_details.append({
            "id": result.id,
            "rag_config_id": result.rag_config_id,
            "document_id": result.document_id,
            "document_file_name": result.file_name,
            "document_title": result.title or result.file_name,
            "created_at": result.created_at
        })

    return documents_with_details


@router.delete("/{config_id}/documents/{doc_id}")
def remove_document_from_rag_config(
    config_id: int,
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Xóa document khỏi RAG configuration"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can remove documents from RAG config")

    # Tìm association
    rag_doc = db.query(RagDocument).filter(
        RagDocument.rag_config_id == config_id,
        RagDocument.document_id == doc_id
    ).first()

    if not rag_doc:
        raise HTTPException(status_code=404, detail="Document association not found")

    db.delete(rag_doc)
    db.commit()

    return {"message": "Document removed from RAG configuration successfully"}


# ========================= MODEL MANAGEMENT ENDPOINTS =========================

@router.post("/models/", response_model=ModelOut)
def create_model(
    model_data: ModelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Tạo model mới (LLM hoặc Embedding) - chỉ admin"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can create models")

    # Kiểm tra model_type hợp lệ
    if model_data.model_type not in ["llm", "embedding"]:
        raise HTTPException(status_code=400, detail="model_type must be 'llm' or 'embedding'")

    # Kiểm tra model_name đã tồn tại chưa
    existing_model = db.query(Model).filter(Model.model_name == model_data.model_name).first()
    if existing_model:
        raise HTTPException(status_code=400, detail=f"Model '{model_data.model_name}' already exists")

    # Tạo model mới
    new_model = Model(
        model_name=model_data.model_name,
        model_type=model_data.model_type,
        provider=model_data.provider
    )

    db.add(new_model)
    db.commit()
    db.refresh(new_model)

    return new_model


@router.get("/models/", response_model=List[ModelOut])
def list_models(
    model_type: Optional[str] = None,
    provider: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lấy danh sách models - có thể filter theo model_type (llm/embedding) hoặc provider"""
    query = db.query(Model)

    if model_type:
        if model_type not in ["llm", "embedding"]:
            raise HTTPException(status_code=400, detail="model_type must be 'llm' or 'embedding'")
        query = query.filter(Model.model_type == model_type)

    if provider:
        query = query.filter(Model.provider == provider)

    models = query.order_by(Model.added_at.desc()).all()
    return models


@router.get("/models/{model_id}", response_model=ModelOut)
def get_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lấy thông tin model theo ID"""
    model = db.query(Model).filter(Model.id == model_id).first()

    if not model:
        raise HTTPException(status_code=404, detail=f"Model with id {model_id} not found")

    return model


@router.put("/models/{model_id}", response_model=ModelOut)
def update_model(
    model_id: int,
    model_data: ModelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cập nhật thông tin model - chỉ admin"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can update models")

    model = db.query(Model).filter(Model.id == model_id).first()

    if not model:
        raise HTTPException(status_code=404, detail=f"Model with id {model_id} not found")

    # Cập nhật các trường
    if model_data.model_name is not None:
        # Kiểm tra tên mới có trùng không
        existing = db.query(Model).filter(
            Model.model_name == model_data.model_name,
            Model.id != model_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Model '{model_data.model_name}' already exists")
        model.model_name = model_data.model_name

    if model_data.model_type is not None:
        if model_data.model_type not in ["llm", "embedding"]:
            raise HTTPException(status_code=400, detail="model_type must be 'llm' or 'embedding'")
        model.model_type = model_data.model_type

    if model_data.provider is not None:
        model.provider = model_data.provider

    db.commit()
    db.refresh(model)

    return model


@router.delete("/models/{model_id}")
def delete_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Xóa model - chỉ admin"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete models")

    model = db.query(Model).filter(Model.id == model_id).first()

    if not model:
        raise HTTPException(status_code=404, detail=f"Model with id {model_id} not found")

    db.delete(model)
    db.commit()

    return {"message": f"Model '{model.model_name}' deleted successfully"}
