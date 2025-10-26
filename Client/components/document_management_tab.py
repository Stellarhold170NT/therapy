import streamlit as st
import time
from datetime import datetime
from typing import Dict, Any, List
try:
    import PyPDF2
    from PyPDF2 import PdfReader
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False
    PdfReader = None


class DocumentManagementTab:
    """Tab quản lý tài liệu"""

    def __init__(self, document_service):
        self.document_service = document_service

    def render(self):
        """Render UI cho Document Management tab"""
        st.header("Document Management")

        # Create columns for layout
        doc_col1, doc_col2 = st.columns([2, 1])

        with doc_col1:
            self._render_document_list()

        with doc_col2:
            self._render_upload_form()

    def _render_document_list(self):
        """Hiển thị danh sách documents"""
        st.subheader("Document Library")

        # Filter options
        search_term = st.text_input("Search documents", "", key="doc_search")

        # Fetch documents từ backend
        token = st.session_state.get("token", "")

        with st.spinner("Đang tải danh sách documents..."):
            result = self.document_service.list_documents(token, search=search_term if search_term else None)

        if result["success"]:
            documents = result["data"]

            if documents:
                # Prepare data for dataframe
                doc_data = {
                    "ID": [doc["id"] for doc in documents],
                    "File Name": [doc["file_name"] for doc in documents],
                    "Title": [doc.get("title", "") or "" for doc in documents],
                    "Author": [doc.get("author", "") or "" for doc in documents],
                    "Pages": [doc.get("total_pages", "") or "" for doc in documents],
                    "Uploaded": [doc["uploaded_at"][:10] if doc.get("uploaded_at") else "" for doc in documents]
                }

                # Display documents
                st.dataframe(
                    doc_data,
                    use_container_width=True,
                    height=300
                )

                st.info(f"Tổng số documents: {len(documents)}")

                # Document details
                self._render_document_details(documents)
            else:
                st.info("No documents found. Upload your first document!")
        else:
            st.error(f"Không thể tải danh sách documents: {result.get('error', 'Unknown error')}")

    def _render_document_details(self, documents: List[Dict[str, Any]]):
        """Hiển thị chi tiết document"""
        if documents:
            selected_doc_id = st.selectbox(
                "Select document for details",
                options=[doc["id"] for doc in documents],
                format_func=lambda x: next((doc["file_name"] for doc in documents if doc["id"] == x), "")
            )

            selected_doc = next((doc for doc in documents if doc["id"] == selected_doc_id), None)
            if selected_doc:
                with st.expander("Document Details", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**File Name:** {selected_doc['file_name']}")
                        st.markdown(f"**Title:** {selected_doc.get('title', 'N/A')}")
                        st.markdown(f"**Author:** {selected_doc.get('author', 'N/A')}")
                    with col2:
                        st.markdown(f"**Pages:** {selected_doc.get('total_pages', 'N/A')}")
                        st.markdown(f"**Created:** {selected_doc.get('creation_date', 'N/A')}")
                        st.markdown(f"**Uploaded:** {selected_doc.get('uploaded_at', 'N/A')}")

                    st.markdown(f"**File Path:** {selected_doc['file_path']}")

                    # Actions
                    delete_col, view_col = st.columns(2)
                    with delete_col:
                        if st.button("Delete Document", key=f"doc_delete_{selected_doc_id}", type="primary"):
                            self._delete_document(selected_doc_id, selected_doc['file_name'])
                    with view_col:
                        st.button("View Document", key=f"doc_view_{selected_doc_id}", disabled=True)

    def _delete_document(self, doc_id: int, file_name: str):
        """Xóa document qua API backend"""
        token = st.session_state.get("token", "")

        with st.spinner(f"Đang xóa document '{file_name}'..."):
            result = self.document_service.delete_document(doc_id, token)

        if result["success"]:
            st.success(f"Document '{file_name}' deleted successfully!")
            time.sleep(0.5)
            st.rerun()
        else:
            st.error(f"Failed to delete document: {result.get('error', 'Unknown error')}")

    def _extract_pdf_metadata(self, uploaded_file) -> Dict[str, Any]:
        """Extract metadata từ PDF file"""
        if PdfReader is None:
            st.warning("PyPDF2 chưa được cài đặt. Không thể đọc metadata từ PDF.")
            return {"success": False, "pages": 1}

        try:
            # Reset file pointer
            uploaded_file.seek(0)

            # Đọc PDF
            pdf_reader = PdfReader(uploaded_file)

            # Lấy số trang
            num_pages = len(pdf_reader.pages)

            # Lấy metadata
            metadata = pdf_reader.metadata

            result = {
                "success": True,
                "pages": num_pages,
            }

            # Extract title nếu có
            if metadata and metadata.get('/Title'):
                result['title'] = metadata.get('/Title')

            # Extract author nếu có
            if metadata and metadata.get('/Author'):
                result['author'] = metadata.get('/Author')

            # Extract creation date nếu có
            if metadata and metadata.get('/CreationDate'):
                result['creation_date'] = metadata.get('/CreationDate')

            # Reset file pointer lại để upload
            uploaded_file.seek(0)

            return result

        except Exception as e:
            st.warning(f"Không thể đọc PDF: {str(e)}")
            uploaded_file.seek(0)  # Reset file pointer
            return {"success": False, "pages": 1}

    def _render_upload_form(self):
        """Form upload document"""
        st.subheader("Upload Document")

        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf", key="doc_uploader")

        if uploaded_file is not None:
            # Tự động đọc metadata từ PDF
            pdf_metadata = self._extract_pdf_metadata(uploaded_file)

            # Hiển thị thông tin đã extract
            if pdf_metadata.get("success"):
                st.success(f"✓ PDF đã được phân tích: {pdf_metadata['pages']} trang")
                if pdf_metadata.get('title'):
                    st.info(f"Title từ PDF: {pdf_metadata['title']}")
                if pdf_metadata.get('author'):
                    st.info(f"Author từ PDF: {pdf_metadata['author']}")

            # Form nhập thông tin (với giá trị mặc định từ PDF)
            default_title = pdf_metadata.get('title') or uploaded_file.name.replace('.pdf', '')
            default_author = pdf_metadata.get('author', '')
            default_pages = pdf_metadata.get('pages', 1)

            doc_title = st.text_input("Document Title", default_title)
            doc_author = st.text_input("Author", default_author)
            doc_pages = st.number_input("Total Pages", min_value=1, value=default_pages, disabled=True, help="Tự động đọc từ PDF")
            doc_date = st.date_input("Creation Date", datetime.now())

            if st.button("Upload Document", key="save_doc_btn", type="primary"):
                self._save_document(uploaded_file, doc_title, doc_author, doc_pages, doc_date)

    def _save_document(self, file, title: str, author: str, pages: int, date):
        """Upload document lên backend"""
        token = st.session_state.get("token", "")

        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # Read file data
            status_text.text("Reading file...")
            progress_bar.progress(20)
            file_data = file.read()

            # Upload to backend
            status_text.text("Uploading to server...")
            progress_bar.progress(50)

            result = self.document_service.upload_document(
                file_data=file_data,
                filename=file.name,
                title=title if title else None,
                author=author if author else None,
                total_pages=pages,
                creation_date=date.isoformat() if date else None,
                token=token
            )

            progress_bar.progress(80)

            if result["success"]:
                status_text.text("Processing complete!")
                progress_bar.progress(100)
                st.success(f"Document '{title}' uploaded successfully!")
                time.sleep(1)
                st.rerun()
            else:
                status_text.text("")
                progress_bar.empty()
                st.error(f"Upload failed: {result.get('error', 'Unknown error')}")

        except Exception as e:
            status_text.text("")
            progress_bar.empty()
            st.error(f"Upload failed: {str(e)}")
