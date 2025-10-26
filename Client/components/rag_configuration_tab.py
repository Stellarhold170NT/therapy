import streamlit as st
from datetime import datetime
from typing import List


class RAGConfigurationTab:
    """Tab cấu hình RAG"""

    def __init__(self, rag_service, document_service, model_service):
        self.rag_service = rag_service
        self.document_service = document_service
        self.model_service = model_service

    def render(self):
        """Render UI cho RAG Configuration tab"""
        st.header("RAG Configuration")

        config_col1, config_col2 = st.columns([2, 1])

        with config_col1:
            self._render_config_form()

        with config_col2:
            self._render_existing_configs()

    def _render_config_form(self):
        """Form tạo RAG configuration"""
        st.subheader("Create New RAG Configuration")

        config_name = st.text_input("Configuration Name", "My RAG Config")

        # Fetch models từ backend
        token = st.session_state.get("token", "")

        # Fetch LLM models
        llm_result = self.model_service.list_models(token, model_type="llm")
        llm_options = []
        if llm_result["success"] and llm_result["data"]:
            llm_options = llm_result["data"]

        if not llm_options:
            st.warning("No LLM models available. Please contact admin to add models.")
            return

        llm_id = st.selectbox(
            "Select LLM Model",
            options=[model["id"] for model in llm_options],
            format_func=lambda x: next((f"{model['model_name']} ({model['provider']})"
                                      for model in llm_options if model["id"] == x), "")
        )

        # Fetch Embedding models
        embedding_result = self.model_service.list_models(token, model_type="embedding")
        embedding_options = []
        if embedding_result["success"] and embedding_result["data"]:
            embedding_options = embedding_result["data"]

        if not embedding_options:
            st.warning("No Embedding models available. Please contact admin to add models.")
            return

        embedding_id = st.selectbox(
            "Select Embedding Model",
            options=[model["id"] for model in embedding_options],
            format_func=lambda x: next((f"{model['model_name']} ({model['provider']})"
                                      for model in embedding_options if model["id"] == x), "")
        )

        # RAG parameters
        st.subheader("RAG Parameters")
        col1, col2 = st.columns(2)

        with col1:
            chunk_size = st.slider("Chunk Size", 100, 2000, 1000, 100)
            chunk_overlap = st.slider("Chunk Overlap", 0, 500, 200, 50)

        with col2:
            search_type = st.selectbox(
                "Search Type",
                options=["similarity", "mmr"],
                format_func=lambda x: "Similarity" if x == "similarity" else "Maximum Marginal Relevance"
            )
            k_value = st.slider("K Value (Number of chunks)", 1, 10, 3)

        # Prompt Template
        st.subheader("Prompt Template")
        prompt_template = st.text_area(
            "Template",
            "Answer the following question based on the context:\nContext: {context}\nQuestion: {question}",
            height=150
        )

        # Document selection
        st.subheader("Select Documents")

        # Fetch documents từ backend
        token = st.session_state.get("token", "")
        result = self.document_service.list_documents(token)

        selected_docs = []
        if result["success"] and result["data"]:
            documents = result["data"]
            for doc in documents:
                doc_title = doc.get('title') or doc['file_name']
                if st.checkbox(f"{doc_title} ({doc['file_name']})", key=f"doc_select_{doc['id']}"):
                    selected_docs.append(doc["id"])
        else:
            st.info("No documents available. Please upload documents first.")

        # Save button
        if st.button("Save Configuration", key="save_config_btn"):
            self._save_config(config_name, llm_id, embedding_id, chunk_size,
                            chunk_overlap, search_type, k_value, prompt_template, selected_docs)

    def _save_config(self, name: str, llm_id: int, emb_id: int, chunk_size: int,
                     chunk_overlap: int, search_type: str, k_value: int,
                     prompt_template: str, selected_docs: List[int]):
        """Lưu RAG configuration vào backend"""
        if not name:
            st.error("Please provide a configuration name!")
            return
        elif not selected_docs:
            st.error("Please select at least one document!")
            return

        # Chuẩn bị dữ liệu gửi lên backend
        config_data = {
            "config_name": name,
            "llm_id": llm_id,
            "embedding_model_id": emb_id,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "search_type": search_type,
            "k_value": k_value,
            "prompt_template": prompt_template
        }

        # Gọi API backend
        token = st.session_state.get("token", "")

        with st.spinner("Đang lưu configuration..."):
            result = self.rag_service.create_config(config_data, token)

        if result["success"]:
            saved_config = result["data"]
            config_id = saved_config["id"]

            # Lưu document associations và trigger RAG processing
            with st.spinner("Đang xử lý documents và tạo embeddings... (có thể mất vài phút)"):
                doc_result = self.rag_service.add_documents_to_config(config_id, selected_docs, token)

            if doc_result["success"]:
                # Lưu vào session_state để hiển thị (sync với backend)
                # Kiểm tra xem config đã tồn tại chưa để tránh duplicate
                if not any(c['id'] == saved_config['id'] for c in st.session_state.rag_configs):
                    st.session_state.rag_configs.append(saved_config)

                # Lưu associations vào session_state (để các tab khác dùng)
                for doc_id in selected_docs:
                    new_rag_doc_id = max([item["id"] for item in st.session_state.rag_documents]) + 1 if st.session_state.rag_documents else 1
                    st.session_state.rag_documents.append({
                        "id": new_rag_doc_id,
                        "rag_config_id": config_id,
                        "document_id": doc_id,
                        "created_at": datetime.now().strftime("%Y-%m-%d")
                    })

                # Hiển thị thông tin RAG processing
                st.success(f"RAG Configuration '{name}' và {len(selected_docs)} documents đã được lưu thành công!")

                if "rag_processing" in doc_result:
                    rag_info = doc_result["rag_processing"]
                    st.info(
                        f"📊 RAG Processing: Đã tạo {rag_info.get('num_chunks', 0)} text chunks "
                        f"từ {rag_info.get('num_documents', 0)} documents\n\n"
                        f"💾 Vector store: `{rag_info.get('vector_store_path', 'N/A')}`"
                    )

                st.rerun()
            else:
                st.warning(f"Configuration đã lưu nhưng có lỗi: {doc_result.get('message', 'Unknown error')}")
                st.info("Bạn có thể thử lại hoặc kiểm tra logs của server.")
                # Kiểm tra xem config đã tồn tại chưa để tránh duplicate
                if not any(c['id'] == saved_config['id'] for c in st.session_state.rag_configs):
                    st.session_state.rag_configs.append(saved_config)
                st.rerun()
        else:
            st.error(f"Failed to save configuration: {result.get('error', 'Unknown error')}")

    def _render_existing_configs(self):
        """Hiển thị các config đã có"""
        st.subheader("Existing Configurations")

        if st.session_state.rag_configs:
            # Fetch all models từ backend để hiển thị tên
            token = st.session_state.get("token", "")
            models_result = self.model_service.list_models(token)
            all_models = []
            if models_result["success"] and models_result["data"]:
                all_models = models_result["data"]

            for config in st.session_state.rag_configs:
                with st.expander(f"{config['config_name']} (ID: {config['id']})"):
                    llm_name = next((f"{model['model_name']} ({model['provider']})"
                                  for model in all_models
                                  if model["id"] == config["llm_id"]), "Unknown")

                    emb_name = next((f"{model['model_name']} ({model['provider']})"
                                   for model in all_models
                                   if model["id"] == config["embedding_model_id"]), "Unknown")

                    st.markdown(f"**LLM:** {llm_name}")
                    st.markdown(f"**Embedding:** {emb_name}")
                    st.markdown(f"**Chunk Size:** {config['chunk_size']}")
                    st.markdown(f"**K Value:** {config['k_value']}")
                    st.markdown(f"**Created:** {config['created_at']}")
        else:
            st.info("No configurations found. Create your first one!")
