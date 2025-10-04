# chat_service.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama
import json


router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    message: str

# --- Init LLM + Prompt ---
llm = ChatOllama(
    base_url="http://localhost:11434",
    model="gpt-oss:20b-cloud",
    temperature=0.5,
    max_tokens=250
)

template = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{question}")
])

chain = template | llm | StrOutputParser()

# --- Streaming endpoint ---
@router.post("/stream")
def chat_stream(req: ChatRequest):
    def event_generator():
        for chunk in chain.stream({"question": req.message}):
            # giữ nguyên format JSON
            yield chunk
    return StreamingResponse(event_generator(), media_type="text/event-stream")