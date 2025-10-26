import streamlit as st
from typing import Optional


class DebugPanel:
    """Debug panel component for admin users - based on Chatbot.py debug features"""

    def __init__(self, chat_service):
        self.chat_service = chat_service

        # Initialize debug options in session state
        if "debug_show_info" not in st.session_state:
            st.session_state.debug_show_info = False
        if "debug_show_context" not in st.session_state:
            st.session_state.debug_show_context = False
        if "debug_show_similarity" not in st.session_state:
            st.session_state.debug_show_similarity = False
        if "debug_show_full_content" not in st.session_state:
            st.session_state.debug_show_full_content = False

    def render_debug_options_sidebar(self) -> None:
        """Render debug options in sidebar (like Chatbot.py line 48-53)"""
        st.sidebar.divider()
        st.sidebar.subheader("🐛 Debug Options")

        st.session_state.debug_show_info = st.sidebar.checkbox(
            "Show Debug Info",
            value=st.session_state.debug_show_info
        )
        st.session_state.debug_show_context = st.sidebar.checkbox(
            "Show Retrieved Context",
            value=st.session_state.debug_show_context
        )
        st.session_state.debug_show_similarity = st.sidebar.checkbox(
            "Show Similarity Scores",
            value=st.session_state.debug_show_similarity
        )
        st.session_state.debug_show_full_content = st.sidebar.checkbox(
            "Show Full Content (No Truncation)",
            value=st.session_state.debug_show_full_content
        )

    def render_debug_info(self, session_id: str, token: str) -> None:
        """
        Render debug information for the last query in session
        (like Chatbot.py line 162-215)
        """
        if not st.session_state.debug_show_info:
            return

        # Fetch debug info from API
        result = self.chat_service.get_debug_info(session_id, token)

        if not result.get("success"):
            return

        debug_info = result.get("data", {})

        # Skip if no query (empty debug info)
        if not debug_info.get("query"):
            return

        with st.expander("🔍 Debug Information", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Documents Retrieved", debug_info.get("num_docs_retrieved", 0))
                st.metric("Context Length (chars)", debug_info.get("context_length", 0))

            with col2:
                st.write(f"**Query:** {debug_info.get('query', '')}")
                if debug_info.get("rag_config_name"):
                    st.write(f"**RAG Config:** {debug_info['rag_config_name']}")
                if debug_info.get("llm_model_name"):
                    st.write(f"**LLM Model:** {debug_info['llm_model_name']}")

            # Similarity Scores
            if st.session_state.debug_show_similarity and debug_info.get("similarity_scores"):
                st.write("**Similarity Scores:**")
                for i, score in enumerate(debug_info["similarity_scores"]):
                    if score is not None:
                        st.write(f"Document {i+1}: {score:.4f}")

            # Retrieved Context
            if st.session_state.debug_show_context and debug_info.get("retrieved_docs"):
                st.write("**Retrieved Context:**")
                for i, doc in enumerate(debug_info["retrieved_docs"]):
                    # Get similarity score if available
                    score_text = ""
                    if debug_info.get("similarity_scores") and i < len(debug_info["similarity_scores"]):
                        score = debug_info["similarity_scores"][i]
                        if score is not None:
                            score_text = f" (Score: {score:.4f})"

                    with st.expander(f"Document {i+1}{score_text}", expanded=False):
                        page_content = doc.get("page_content", "")

                        # Show full or truncated content
                        if st.session_state.debug_show_full_content:
                            st.text(page_content)
                        else:
                            if len(page_content) > 500:
                                st.text(page_content[:500] + "...")
                                if st.button(f"Show Full Content Doc {i+1}", key=f"show_full_{i}_{session_id}"):
                                    st.text(page_content)
                            else:
                                st.text(page_content)

                        # Show metadata
                        if doc.get("metadata"):
                            st.json(doc["metadata"])

            # Complete Context Sent to LLM
            if st.session_state.debug_show_context and debug_info.get("context_text"):
                st.write("---")
                st.write("**Complete Context Sent to LLM:**")
                with st.expander("Full Context", expanded=False):
                    context_text = debug_info["context_text"]

                    if st.session_state.debug_show_full_content:
                        st.text(context_text)
                    else:
                        if len(context_text) > 1000:
                            st.text(context_text[:1000] + "...")
                            if st.button("Show Complete Context", key=f"show_full_context_{session_id}"):
                                st.text(context_text)
                        else:
                            st.text(context_text)

    def render_vector_store_debug(self, token: str) -> None:
        """
        Render additional debug panel for vector store
        (like Chatbot.py line 217-259)
        """
        if not st.session_state.debug_show_info:
            return

        st.divider()
        st.subheader("🛠️ Vector Store Debug")

        col1, col2, col3 = st.columns(3)

        # Column 1: Vector Store Status
        with col1:
            if st.button("Check Vector Store Status"):
                result = self.chat_service.get_vector_store_status(token)

                if result.get("success"):
                    data = result
                    st.success("✓ Vector Store Active")
                    st.write(f"**Config:** {data.get('rag_config_name', 'N/A')}")
                    st.write(f"**Total Docs:** {data.get('total_documents', 'Unknown')}")
                    st.write(f"**Embedding Model:** {data.get('embedding_model', 'N/A')}")
                    st.write(f"**LLM Model:** {data.get('llm_model', 'N/A')}")
                    st.write(f"**Path:** {data.get('vector_store_path', 'N/A')}")
                    st.write(f"**Cached:** {'Yes' if data.get('cached') else 'No'}")
                else:
                    st.error(f"Error: {result.get('message', 'Unknown error')}")

        # Column 2: Test Search
        with col2:
            test_query = st.text_input("Test Search Query", placeholder="Enter test query...", key="test_search_query")
            test_k = st.number_input("Number of results (k)", min_value=1, max_value=50, value=10, key="test_k")

            if st.button("Test Search") and test_query:
                result = self.chat_service.test_search(test_query, test_k, token)

                if result.get("success"):
                    st.write(f"Found **{result.get('num_results', 0)}** results:")

                    for i, doc_result in enumerate(result.get("results", [])):
                        score = doc_result.get("similarity_score", 0)
                        st.write(f"**Result {i+1}** (Score: {score:.4f})")

                        with st.expander(f"Content Preview", expanded=False, key=f"test_result_{i}"):
                            page_content = doc_result.get("page_content", "")

                            if st.session_state.debug_show_full_content:
                                st.text(page_content)
                            else:
                                if len(page_content) > 200:
                                    st.text(page_content[:200] + "...")
                                    if st.button(f"Show Full Test Result {i+1}", key=f"test_full_{i}"):
                                        st.text(page_content)
                                else:
                                    st.text(page_content)

                            if doc_result.get("metadata"):
                                st.json(doc_result["metadata"])

                        st.write("---")
                else:
                    st.error(f"Search error: {result.get('message', 'Unknown error')}")

        # Column 3: Model Info
        with col3:
            if st.button("Show Model Info"):
                result = self.chat_service.get_vector_store_status(token)

                if result.get("success"):
                    st.write("**Model Configuration:**")
                    st.write(f"- LLM: {result.get('llm_model', 'N/A')}")
                    st.write(f"- Embedding: {result.get('embedding_model', 'N/A')}")
                    st.write(f"- Search Type: {result.get('search_type', 'N/A')}")
                    st.write(f"- K Value: {result.get('k_value', 'N/A')}")
                    st.write(f"- Chunk Size: {result.get('chunk_size', 'N/A')}")
                    st.write(f"- Chunk Overlap: {result.get('chunk_overlap', 'N/A')}")
                else:
                    st.error("No RAG configuration found")
