from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import chain
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
import streamlit as st
from langchain_ollama import ChatOllama
from dotenv import load_dotenv

import os
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings

embeddings = OllamaEmbeddings(model="bge-m3")

vector_store = Chroma(
    persist_directory="./chroma_langchain_db",
    embedding_function=embeddings,
)

retriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs= {"k": 10}
)

# Load the env file
load = load_dotenv('./../.env')

print(os.getenv("LANGSMITH_API_KEY"))

# Initialize LLM
llm = ChatOllama(
    base_url="http://localhost:11434",
    model="gpt-oss:20b-cloud",
    temperature=0.5,
    max_tokens=250
)

def get_session_history(session_id):
    return SQLChatMessageHistory(session_id=session_id, connection_string="mysql+pymysql://root:1001011010010110Ntit!@localhost:3306/chat_message_history")

session_id = "Karthik"

# Sidebar cho debug options
st.sidebar.title("Debug Options")
show_debug = st.sidebar.checkbox("Show Debug Info", value=False)
show_context = st.sidebar.checkbox("Show Retrieved Context", value=False)
show_similarity_scores = st.sidebar.checkbox("Show Similarity Scores", value=False)
# THÊM OPTION ĐỂ HIỂN THỊ FULL CONTENT
show_full_content = st.sidebar.checkbox("Show Full Content (No Truncation)", value=False)

st.title("How can I help you today?")
st.write("Enter your query below")

session_id = st.text_input("Enter your name", session_id)

if st.button("Start all new conversation"):
    st.session_state.chat_history = []
    get_session_history(session_id).clear()
    st.rerun()

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

# 1. Định nghĩa prompt template có system message duy nhất
# template = ChatPromptTemplate.from_messages([
#     ("system", 
#      "You are an AI Assistant. Use the provided context to answer the user's question. "
#      "If you don't know the answer, just say 'I don't know'. "
#      "Always summarize the response in Markdown format"),
#     ("placeholder", "{history}"),
#     ("human", "Context:\n{context}\n\nQuestion:\n{question}")
# ])

template = ChatPromptTemplate.from_messages([
    ("system", 
     "You are a helpful AI assistant. You are helping the user understand a book. "
     "The 'context' provided comes from the book, and the user may ask questions about it. "
     "Always answer based on the context from the book. "
     "If the answer is not in the book context, say 'I don't know'. "
     "Summarize your answers in Markdown format, and reference the book context when relevant."),
    ("placeholder", "{history}"),
    ("human", "Book context:\n{context}\n\nQuestion:\n{question}")
])


# template = ChatPromptTemplate.from_messages([
#     ("system",
#      "Bạn là một nhà tư vấn tâm lý thấu hiểu và vui vẻ. "
#      "Sử dụng thông tin được cung cấp để trả lời câu hỏi của người dùng một cách nhẹ nhàng, đồng cảm và dễ tiếp nhận. "
#      "Nếu bạn không biết câu trả lời, hãy chân thành nói 'Mình không biết'. "
#      "Luôn tóm tắt câu trả lời dưới dạng Markdown, và thêm một chút sự ấm áp hoặc khích lệ nếu phù hợp."),
#     ("placeholder", "{history}"),
#     ("human", "Thông tin tham khảo:\n{context}\n\nCâu hỏi của bạn:\n{question}")
# ])

chain = template | llm | StrOutputParser()

# 2. Hàm gọi lịch sử với debug info
def invoke_history_with_debug(chain, session_id, prompt):
    # Retrieve documents với similarity scores nếu có thể
    try:
        # Thử lấy với scores
        retrieved_docs_with_scores = vector_store.similarity_search_with_score(prompt, k=20)
        retrieved_docs = [doc for doc, score in retrieved_docs_with_scores]
        scores = [score for doc, score in retrieved_docs_with_scores]
    except:
        # Fallback về method cũ
        retrieved_docs = retriever.get_relevant_documents(prompt)
        scores = [None] * len(retrieved_docs)
    
    context_text = "\n\n".join([doc.page_content for doc in retrieved_docs])
    
    # Store debug info in session state
    debug_info = {
        "query": prompt,
        "num_docs_retrieved": len(retrieved_docs),
        "context_length": len(context_text),
        "retrieved_docs": retrieved_docs,
        "similarity_scores": scores,
        "context_text": context_text
    }
    
    st.session_state.last_debug_info = debug_info

    history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="question",
        history_messages_key="history"
    )

    for response in history.stream(
        {"question": prompt, "context": context_text},
        config={"configurable": {"session_id": session_id}}
    ):
        yield response

# 3. UI
prompt = st.chat_input("Enter your query")

if prompt:
    st.session_state.chat_history.append({'role': 'user', "content": prompt})
    
    with st.chat_message('user'):
        st.markdown(prompt)

    with st.chat_message('assistant'):
        streamResponse = st.write_stream(invoke_history_with_debug(chain, session_id, prompt))

    st.session_state.chat_history.append({'role': 'assistant', 'content': streamResponse})

    # Display debug information
    if show_debug and 'last_debug_info' in st.session_state:
        debug_info = st.session_state.last_debug_info
        
        with st.expander("🔍 Debug Information", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Documents Retrieved", debug_info["num_docs_retrieved"])
                st.metric("Context Length (chars)", debug_info["context_length"])
            
            with col2:
                st.write(f"**Query:** {debug_info['query']}")
            
            if show_similarity_scores and any(score is not None for score in debug_info["similarity_scores"]):
                st.write("**Similarity Scores:**")
                for i, score in enumerate(debug_info["similarity_scores"]):
                    if score is not None:
                        st.write(f"Document {i+1}: {score:.4f}")
            
            if show_context:
                st.write("**Retrieved Context:**")
                for i, doc in enumerate(debug_info["retrieved_docs"]):
                    score_text = f" (Score: {debug_info['similarity_scores'][i]:.4f})" if debug_info['similarity_scores'][i] is not None else ""
                    with st.expander(f"Document {i+1}{score_text}", expanded=False):
                        # SỬA TẠI ĐÂY: Hiển thị full content thay vì cắt ở 500 ký tự
                        if show_full_content:
                            st.text(doc.page_content)  # Hiển thị toàn bộ nội dung
                        else:
                            # Hiển thị với option cắt nhưng cho phép expand
                            if len(doc.page_content) > 500:
                                st.text(doc.page_content[:500] + "...")
                                if st.button(f"Show Full Content Doc {i+1}", key=f"show_full_{i}"):
                                    st.text(doc.page_content)
                            else:
                                st.text(doc.page_content)
                        
                        if hasattr(doc, 'metadata') and doc.metadata:
                            st.json(doc.metadata)
            
            # THÊM PHẦN HIỂN THỊ CONTEXT HOÀN CHỈNH
            if show_context:
                st.write("---")
                st.write("**Complete Context Sent to LLM:**")
                with st.expander("Full Context", expanded=False):
                    if show_full_content:
                        st.text(debug_info["context_text"])
                    else:
                        # Hiển thị preview và cho phép xem full
                        if len(debug_info["context_text"]) > 1000:
                            st.text(debug_info["context_text"][:1000] + "...")
                            if st.button("Show Complete Context", key="show_full_context"):
                                st.text(debug_info["context_text"])
                        else:
                            st.text(debug_info["context_text"])

# Additional debug panel ở bottom
if show_debug:
    st.divider()
    st.subheader("🛠️ Vector Store Debug")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Check Vector Store Status"):
            try:
                # Kiểm tra số lượng documents
                total_docs = vector_store._collection.count()
                st.success(f"Vector store contains {total_docs} documents")
            except Exception as e:
                st.error(f"Error checking vector store: {e}")
    
    with col2:
        test_query = st.text_input("Test Search Query", placeholder="Enter test query...")
        if st.button("Test Search") and test_query:
            try:
                test_results = vector_store.similarity_search_with_score(test_query, k=10)
                st.write(f"Found {len(test_results)} results:")
                for i, (doc, score) in enumerate(test_results):
                    st.write(f"**Result {i+1}** (Score: {score:.4f})")
                    # SỬA TẠI ĐÂY: Không cắt content trong test search
                    with st.expander(f"Content Preview", expanded=False):
                        if show_full_content:
                            st.text(doc.page_content)
                        else:
                            if len(doc.page_content) > 200:
                                st.text(doc.page_content[:200] + "...")
                                if st.button(f"Show Full Test Result {i+1}", key=f"test_full_{i}"):
                                    st.text(doc.page_content)
                            else:
                                st.text(doc.page_content)
                    st.write("---")
            except Exception as e:
                st.error(f"Search error: {e}")
    
    with col3:
        if st.button("Show Embedding Model Info"):
            st.write(f"**Embedding Model:** {embeddings.model}")
            st.write(f"**Vector Store Path:** ./chroma_langchain_db")