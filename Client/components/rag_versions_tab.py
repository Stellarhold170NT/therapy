import streamlit as st
from typing import Dict


class RAGVersionsTab:
    """Tab xem các phiên bản RAG"""

    def __init__(self, model_service):
        self.model_service = model_service

    def render(self):
        """Render UI cho RAG Versions tab"""
        st.header("RAG Versions")

        # Fetch models từ backend
        token = st.session_state.get("token", "")
        models_result = self.model_service.list_models(token)
        models = []
        if models_result["success"] and models_result["data"]:
            models = models_result["data"]

        if st.session_state.rag_configs:
            for idx, config in enumerate(st.session_state.rag_configs):
                self._render_version_details(config, models, idx)

            # Compare versions
            self._render_version_comparison()
        else:
            st.info("No RAG versions found. Create a new RAG configuration first!")

    def _render_version_details(self, config: Dict, models: list, idx: int):
        """Hiển thị chi tiết 1 version"""
        with st.expander(f"RAG Version: {config['config_name']} (Created: {config['created_at']})", expanded=True):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader("Configuration Details")

                llm = next((model for model in models if model["id"] == config["llm_id"]), None)
                emb = next((model for model in models if model["id"] == config["embedding_model_id"]), None)

                details_cols = st.columns(2)
                with details_cols[0]:
                    st.markdown(f"**LLM Model:** {llm['model_name'] if llm else 'Unknown'}")
                    st.markdown(f"**LLM Provider:** {llm['provider'] if llm else 'Unknown'}")
                    st.markdown(f"**Embedding Model:** {emb['model_name'] if emb else 'Unknown'}")
                    st.markdown(f"**Embedding Provider:** {emb['provider'] if emb else 'Unknown'}")

                with details_cols[1]:
                    st.markdown(f"**Chunk Size:** {config['chunk_size']}")
                    st.markdown(f"**Chunk Overlap:** {config['chunk_overlap']}")
                    st.markdown(f"**Search Type:** {config['search_type']}")
                    st.markdown(f"**K Value:** {config['k_value']}")

                st.subheader("Prompt Template")
                st.text_area("", config['prompt_template'], height=100, key=f"prompt_view_{idx}_{config['id']}", disabled=True)

            with col2:
                st.subheader("Associated Documents")
                # TODO: Implement document associations API
                st.info("Document associations feature coming soon...")

            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Clone & Edit", key=f"rag_clone_{idx}_{config['id']}"):
                    st.info("This would clone the configuration for editing.")
            with col2:
                if st.button("Download Config", key=f"rag_download_{idx}_{config['id']}"):
                    st.info("This would download the configuration.")
            with col3:
                if st.button("Delete Version", key=f"rag_delete_{idx}_{config['id']}"):
                    st.info("This would delete the RAG version.")

    def _render_version_comparison(self):
        """So sánh các versions"""
        st.subheader("Compare RAG Versions")

        if len(st.session_state.rag_configs) >= 2:
            col1, col2 = st.columns(2)

            with col1:
                version1 = st.selectbox(
                    "Select first version",
                    options=[config["id"] for config in st.session_state.rag_configs],
                    format_func=lambda x: next((config["config_name"] for config in st.session_state.rag_configs if config["id"] == x), ""),
                    key="compare_version1"
                )

            with col2:
                version2 = st.selectbox(
                    "Select second version",
                    options=[config["id"] for config in st.session_state.rag_configs],
                    format_func=lambda x: next((config["config_name"] for config in st.session_state.rag_configs if config["id"] == x), ""),
                    index=1 if len(st.session_state.rag_configs) > 1 else 0,
                    key="compare_version2"
                )

            if st.button("Compare Versions", key="compare_versions_btn"):
                if version1 == version2:
                    st.warning("Please select different versions to compare.")
                else:
                    st.info("This would show a detailed comparison of the selected versions.")
        else:
            st.info("Need at least 2 RAG configurations to compare.")
