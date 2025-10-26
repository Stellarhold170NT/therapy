from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database.connection import get_db
from models.user import User
from models.chat_session import ChatSession
from schemas.chat_session_schema import ChatSessionCreate, ChatSessionUpdate, ChatSessionOut
from auth.auth import get_current_user

router = APIRouter(prefix="/history", tags=["Chat History"])


@router.post("/chat-sessions/", response_model=ChatSessionOut, status_code=status.HTTP_201_CREATED)
def create_chat_session(
    session_data: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create new chat session with UUID from client
    """
    # Check if session_id already exists
    existing_session = db.query(ChatSession).filter(
        ChatSession.session_id == session_data.session_id
    ).first()

    if existing_session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session ID already exists"
        )

    # Create new chat session
    new_session = ChatSession(
        user_id=current_user.user_id,
        session_id=session_data.session_id,
        session_name=session_data.session_name
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return new_session


@router.get("/chat-sessions/", response_model=List[ChatSessionOut])
def get_user_chat_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all chat sessions for current user
    Sorted by updated_at descending (newest first)
    """
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.user_id
    ).order_by(ChatSession.updated_at.desc()).all()

    return sessions


@router.get("/chat-sessions/{session_id}", response_model=ChatSessionOut)
def get_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get details of a specific chat session
    """
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.user_id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )

    return session


@router.put("/chat-sessions/{session_id}", response_model=ChatSessionOut)
def update_chat_session(
    session_id: str,
    session_data: ChatSessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update chat session name
    """
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.user_id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )

    # Update session name
    if session_data.session_name is not None:
        session.session_name = session_data.session_name

    session.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(session)

    return session


@router.delete("/chat-sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete chat session
    """
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.user_id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )

    db.delete(session)
    db.commit()

    return None


@router.post("/chat-sessions/{session_id}/touch", response_model=ChatSessionOut)
def touch_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update timestamp of chat session (when there is new activity)
    """
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.user_id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )

    session.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(session)

    return session
