# chat_service.py
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
import ollama
import json
import os
from sqlalchemy.orm import Session
from database.connection import get_db
from models.rag_config import RAGConfig
from models.model import Model
from cachetools import TTLCache
from pathlib import Path
from typing import Optional, Dict, List, Any


router = APIRouter(prefix="/chat", tags=["Chat"])


# --- Session History Management (like Chatbot.py line 42-43) ---
def get_session_history(session_id: str):
    """
    Get chat message history for a session.
    Langchain automatically manages the message_store table.
    """
    return SQLChatMessageHistory(
        session_id=session_id,
        connection_string="mysql+pymysql://root:1001011010010110Ntit!@localhost:3306/chat_message_history"
    )


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"  # Session UUID from client

class TestSearchRequest(BaseModel):
    query: str
    k: Optional[int] = 10

class DebugInfo(BaseModel):
    query: str
    num_docs_retrieved: int
    context_length: int
    similarity_scores: Optional[List[float]] = None
    retrieved_docs: Optional[List[Dict[str, Any]]] = None
    context_text: Optional[str] = None
    rag_config_name: Optional[str] = None
    llm_model_name: Optional[str] = None
    embedding_model_name: Optional[str] = None
    vector_store_path: Optional[str] = None

# --- Cache for RAG config (TTL = 1 day) ---
rag_config_cache = TTLCache(maxsize=1, ttl=86400)  # 1 day = 86400 seconds
CACHE_KEY = "latest_rag_config"

# --- Store debug info per session (in-memory) ---
debug_info_store: Dict[str, Dict] = {}

def load_latest_rag_config(db: Session) -> Optional[dict]:
    """
    Load latest RAG configuration from database with 1-day caching.

    Returns:
        dict with keys: config, vector_store, retriever
        or None if no config found
    """
    # Check cache first
    if CACHE_KEY in rag_config_cache:
        print(f"[Cache HIT] Using cached RAG config")
        return rag_config_cache[CACHE_KEY]

    print(f"[Cache MISS] Loading RAG config from database")

    try:
        # Get latest RAG config from database
        latest_config = db.query(RAGConfig).order_by(RAGConfig.created_at.desc()).first()

        if not latest_config:
            print("No RAG configuration found in database")
            return None

        # Get embedding model info
        embedding_model = db.query(Model).filter(Model.id == latest_config.embedding_model_id).first()

        if not embedding_model:
            print(f"Embedding model {latest_config.embedding_model_id} not found")
            return None

        # Get LLM model info
        llm_model = db.query(Model).filter(Model.id == latest_config.llm_id).first()

        if not llm_model:
            print(f"LLM model {latest_config.llm_id} not found")
            return None

        # Generate vector store path
        safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in latest_config.config_name)
        vector_store_path = Path(f"chroma_db/chroma_langchain_db_{safe_name}")

        if not vector_store_path.exists():
            print(f"Vector store not found at {vector_store_path}")
            return None

        # Load vector store
        embeddings = OllamaEmbeddings(
            base_url="http://localhost:11434",
            model=embedding_model.model_name
        )

        vector_store = Chroma(
            persist_directory=str(vector_store_path),
            embedding_function=embeddings
        )

        # Create retriever
        retriever = vector_store.as_retriever(
            search_type=latest_config.search_type,
            search_kwargs={"k": latest_config.k_value}
        )

        result = {
            "config": latest_config,
            "llm_model": llm_model,
            "embedding_model": embedding_model,
            "vector_store": vector_store,
            "retriever": retriever
        }

        # Cache the result
        rag_config_cache[CACHE_KEY] = result
        print(f"[Cache STORED] RAG config cached for 1 day")

        return result

    except Exception as e:
        print(f"Error loading RAG config: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


# --- Init LLM (will be overridden by RAG config if available) ---
default_llm = ChatOllama(
    base_url="http://localhost:11434",
    model="gpt-oss:20b-cloud",
    temperature=0.5,
    max_tokens=250
)

# --- Streaming endpoint with RAG ---
@router.post("/stream")
def chat_stream(req: ChatRequest, db: Session = Depends(get_db)):
    """
    Chat endpoint with RAG integration.

    Flow:
    1. Load latest RAG config (with 1-day cache)
    2. If RAG available: retrieve relevant documents and add to context
    3. Stream response from LLM
    """
    def event_generator():
        # Load RAG config
        rag_data = load_latest_rag_config(db)
        print(rag_data)

        if rag_data:
            # RAG is available
            config = rag_data["config"]
            llm_model = rag_data["llm_model"]
            vector_store = rag_data["vector_store"]

            # Initialize LLM with model from config
            llm = ChatOllama(
                base_url="http://localhost:11434",
                model=llm_model.model_name,
                temperature=0.5,
                max_tokens=250
            )

            # Retrieve relevant documents with similarity scores
            try:
                # Try to get with scores (like Chatbot.py)
                try:
                    retrieved_docs_with_scores = vector_store.similarity_search_with_score(req.message, k=config.k_value)
                    retrieved_docs = [doc for doc, score in retrieved_docs_with_scores]
                    scores = [float(score) for doc, score in retrieved_docs_with_scores]
                except:
                    # Fallback if similarity_search_with_score not available
                    retrieved_docs = vector_store.similarity_search(req.message, k=config.k_value)
                    scores = None

                context_text = "\n\n".join([doc.page_content for doc in retrieved_docs])

                print(f"[RAG] Retrieved {len(retrieved_docs)} documents, context length: {len(context_text)} chars")

                # Store debug info (like Chatbot.py)
                safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in config.config_name)
                debug_info_store[req.session_id] = {
                    "query": req.message,
                    "num_docs_retrieved": len(retrieved_docs),
                    "context_length": len(context_text),
                    "similarity_scores": scores,
                    "retrieved_docs": [
                        {
                            "page_content": doc.page_content[:500],  # Truncate for API response
                            "metadata": doc.metadata if hasattr(doc, 'metadata') else {}
                        }
                        for doc in retrieved_docs
                    ],
                    "context_text": context_text[:1000],  # Truncate for API response
                    "rag_config_name": config.config_name,
                    "llm_model_name": llm_model.model_name,
                    "embedding_model_name": rag_data["embedding_model"].model_name,
                    "vector_store_path": f"chroma_db/chroma_langchain_db_{safe_name}"
                }
                print(f"[DEBUG] Stored debug info for session: {req.session_id}")

                # Try Ollama native web search with tool calling
                try:
                    # Check if API key is available
                    api_key = os.getenv('OLLAMA_API_KEY')
                    if not api_key:
                        print("[Web Search] No OLLAMA_API_KEY found, skipping web search")
                        raise Exception("No OLLAMA_API_KEY")

                    print(f"[Web Search] Using Ollama web_search tool")

                    # Build messages with RAG context
                    system_message = {
                        'role': 'system',
                        'content': f"""Bạn là chuyên gia tư vấn CV chuyên nghiệp từ Viettel.

Context từ knowledge base:
{context_text}

Hướng dẫn:
1. Ưu tiên sử dụng Context từ knowledge base ở trên để trả lời
2. Nếu Context không đủ hoặc cần thông tin thời gian thực, sử dụng web_search tool
3. Trả lời bằng tiếng Việt một cách chuyên nghiệp"""
                    }

                    messages = [system_message, {'role': 'user', 'content': req.message}]

                    # First call with tools
                    response = ollama.chat(
                        model=llm_model.model_name,
                        messages=messages,
                        tools=[ollama.web_search, ollama.web_fetch]
                    )

                    messages.append(response['message'])

                    # Check if model used tools
                    if response['message'].get('tool_calls'):
                        print(f"[Web Search] Model decided to use tools")

                        # Execute tool calls
                        for tool_call in response['message']['tool_calls']:
                            func_name = tool_call['function']['name']
                            args = tool_call['function']['arguments']

                            print(f"[Web Search] Calling {func_name} with args: {args}")

                            try:
                                if func_name == 'web_search':
                                    result = ollama.web_search(**args)
                                elif func_name == 'web_fetch':
                                    result = ollama.web_fetch(**args)
                                else:
                                    result = f"Unknown tool: {func_name}"

                                print(f"[Web Search] Got {len(str(result))} chars result")

                                # Add tool result to messages
                                messages.append({
                                    'role': 'tool',
                                    'content': str(result)[:8000],  # Limit to 8000 chars
                                })

                            except Exception as tool_error:
                                print(f"[Web Search] Tool error: {str(tool_error)}")
                                messages.append({
                                    'role': 'tool',
                                    'content': f"Error: {str(tool_error)}"
                                })

                        # Second call with tool results
                        print(f"[Web Search] Getting final response with tool results")
                        final_response = ollama.chat(
                            model=llm_model.model_name,
                            messages=messages
                        )
                        output = final_response['message']['content']

                    else:
                        # No tool used
                        print(f"[Web Search] Model did not use tools, answering directly")
                        output = response['message']['content']

                    print(f"[Web Search] Got output length: {len(output) if output else 0}")

                    # Save to history
                    session_history = get_session_history(req.session_id)
                    session_history.add_user_message(req.message)
                    session_history.add_ai_message(output)

                    # Stream the result
                    for char in output:
                        yield char

                except Exception as web_search_error:
                    # Fallback to simple RAG chain
                    print(f"[Web Search] Error: {str(web_search_error)}, falling back to simple RAG chain")
                    import traceback
                    print(f"[Agent] Traceback: {traceback.format_exc()[:500]}")

                    # Simple RAG chain fallback
                    template = ChatPromptTemplate.from_messages([
                        ("system", f"""Bạn là chuyên gia tư vấn CV chuyên nghiệp từ Viettel.

Context từ knowledge base:
{context_text}

Hãy sử dụng context ở trên để trả lời câu hỏi của người dùng."""),
                        ("placeholder", "{{history}}"),
                        ("human", "{question}")
                    ])

                    chain = template | llm | StrOutputParser()
                    history = RunnableWithMessageHistory(
                        chain,
                        get_session_history,
                        input_messages_key="question",
                        history_messages_key="history"
                    )

                    for chunk in history.stream(
                        {"question": req.message},
                        config={"configurable": {"session_id": req.session_id}}
                    ):
                        yield chunk

            except Exception as e:
                print(f"Error in RAG retrieval: {str(e)}")
                # Fallback to non-RAG with history
                template = ChatPromptTemplate.from_messages([
                    ("system", "You are a helpful assistant."),
                    ("placeholder", "{history}"),
                    ("human", "{question}")
                ])
                chain = template | default_llm | StrOutputParser()

                history = RunnableWithMessageHistory(
                    chain,
                    get_session_history,
                    input_messages_key="question",
                    history_messages_key="history"
                )

                for chunk in history.stream(
                    {"question": req.message},
                    config={"configurable": {"session_id": req.session_id}}
                ):
                    yield chunk
        else:
            # No RAG available, use default with history
            print("[No RAG] Using default LLM without context")
            template = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful assistant."),
                ("placeholder", "{history}"),
                ("human", "{question}")
            ])
            chain = template | default_llm | StrOutputParser()

            history = RunnableWithMessageHistory(
                chain,
                get_session_history,
                input_messages_key="question",
                history_messages_key="history"
            )

            for chunk in history.stream(
                {"question": req.message},
                config={"configurable": {"session_id": req.session_id}}
            ):
                yield chunk

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ========================= DEBUG ENDPOINTS =========================

@router.get("/debug/{session_id}", response_model=DebugInfo)
def get_debug_info(session_id: str):
    """
    Get debug information for a specific session.
    Returns debug info from the last query in that session.
    """
    if session_id not in debug_info_store:
        return {
            "query": "",
            "num_docs_retrieved": 0,
            "context_length": 0,
            "similarity_scores": None,
            "retrieved_docs": None,
            "context_text": None,
            "rag_config_name": None,
            "llm_model_name": None,
            "embedding_model_name": None,
            "vector_store_path": None
        }

    return debug_info_store[session_id]


@router.post("/test-search")
def test_search(req: TestSearchRequest, db: Session = Depends(get_db)):
    """
    Test search on vector store.
    Similar to the test search feature in Chatbot.py sidebar.

    Returns search results with similarity scores.
    """
    try:
        rag_data = load_latest_rag_config(db)

        if not rag_data:
            return {
                "success": False,
                "message": "No RAG configuration found"
            }

        vector_store = rag_data["vector_store"]
        config = rag_data["config"]

        # Perform search with scores
        try:
            results_with_scores = vector_store.similarity_search_with_score(req.query, k=req.k)

            results = [
                {
                    "page_content": doc.page_content,
                    "metadata": doc.metadata if hasattr(doc, 'metadata') else {},
                    "similarity_score": float(score)
                }
                for doc, score in results_with_scores
            ]

            return {
                "success": True,
                "query": req.query,
                "num_results": len(results),
                "results": results,
                "rag_config_name": config.config_name
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Search error: {str(e)}"
            }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error loading RAG config: {str(e)}"
        }


@router.get("/vector-store-status")
def get_vector_store_status(db: Session = Depends(get_db)):
    """
    Check vector store status.
    Returns information about the current vector store.
    """
    try:
        rag_data = load_latest_rag_config(db)

        if not rag_data:
            return {
                "success": False,
                "message": "No RAG configuration found"
            }

        config = rag_data["config"]
        vector_store = rag_data["vector_store"]

        # Try to get document count
        try:
            total_docs = vector_store._collection.count()
        except:
            total_docs = "Unknown"

        safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in config.config_name)

        return {
            "success": True,
            "rag_config_name": config.config_name,
            "llm_model": rag_data["llm_model"].model_name,
            "embedding_model": rag_data["embedding_model"].model_name,
            "vector_store_path": f"chroma_db/chroma_langchain_db_{safe_name}",
            "total_documents": total_docs,
            "search_type": config.search_type,
            "k_value": config.k_value,
            "chunk_size": config.chunk_size,
            "chunk_overlap": config.chunk_overlap,
            "cached": CACHE_KEY in rag_config_cache
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


@router.get("/test-rag")
def test_rag(db: Session = Depends(get_db)):
    """
    Test RAG with fixed query "CV" to debug if RAG is working
    """
    try:
        # Load RAG config
        rag_data = load_latest_rag_config(db)

        if not rag_data:
            return {
                "success": False,
                "message": "No RAG configuration found"
            }

        config = rag_data["config"]
        vector_store = rag_data["vector_store"]

        # Test query
        test_query = "CV"

        # Retrieve documents
        try:
            retrieved_docs_with_scores = vector_store.similarity_search_with_score(test_query, k=config.k_value)
            retrieved_docs = [doc for doc, score in retrieved_docs_with_scores]
            scores = [float(score) for doc, score in retrieved_docs_with_scores]
        except:
            retrieved_docs = vector_store.similarity_search(test_query, k=config.k_value)
            scores = None

        context_text = "\n\n".join([doc.page_content for doc in retrieved_docs])

        return {
            "success": True,
            "query": test_query,
            "rag_config": config.config_name,
            "num_docs_retrieved": len(retrieved_docs),
            "context_length": len(context_text),
            "similarity_scores": scores,
            "context_preview": context_text[:500] + "..." if len(context_text) > 500 else context_text,
            "full_context": context_text,
            "documents": [
                {
                    "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "metadata": doc.metadata if hasattr(doc, 'metadata') else {}
                }
                for doc in retrieved_docs
            ]
        }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "message": str(e),
            "traceback": traceback.format_exc()
        }