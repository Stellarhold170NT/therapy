import streamlit as st
import streamlit_cookies_manager

# Import services
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.session_manager import SessionManager
from services.auth_service import AuthService
from services.rag_service import RAGService
from services.document_service import DocumentService
from services.model_service import ModelService

# Import components
from components.user_management_tab import UserManagementTab
from components.document_management_tab import DocumentManagementTab
from components.rag_configuration_tab import RAGConfigurationTab
from components.rag_versions_tab import RAGVersionsTab
from components.analytics_tab import AnalyticsTab


# ========================= MAIN ADMIN DASHBOARD APP =========================
class AdminDashboardApp:
    """Main Admin Dashboard Application"""

    def __init__(self):
        # Setup page config (phải gọi đầu tiên)
        self.setup_page()

        # Initialize cookies manager
        self.cookies = streamlit_cookies_manager.CookieManager()

        # Wait for cookies to be ready
        if not self.cookies.ready():
            st.stop()

        # Setup services
        self.session_manager = SessionManager(self.cookies)
        self.auth_service = AuthService()
        self.rag_service = RAGService()
        self.document_service = DocumentService()
        self.model_service = ModelService()

        # Setup tabs
        self.user_tab = UserManagementTab(self.auth_service)
        self.document_tab = DocumentManagementTab(self.document_service)
        self.rag_config_tab = RAGConfigurationTab(self.rag_service, self.document_service, self.model_service)
        self.rag_versions_tab = RAGVersionsTab(self.model_service)
        self.analytics_tab = AnalyticsTab()

        # Initialize session state and check auth
        self.init_session_state()
        self.check_authentication()

    def setup_page(self) -> None:
        """Cấu hình trang"""
        st.set_page_config(page_title="Admin Dashboard", page_icon="🔧", layout="wide")

    def init_session_state(self) -> None:
        """Khởi tạo session state"""
        # Try to load token from cookies
        if "logged_in" not in st.session_state:
            st.session_state.logged_in = False

        if not st.session_state.logged_in:
            session_data = self.session_manager.load_token()
            if session_data:
                token = session_data.get("token")
                if self.auth_service.verify_token(token):
                    st.session_state.logged_in = True
                    st.session_state.username = session_data.get("username")
                    st.session_state.token = token
                    st.session_state.is_admin = session_data.get("role") == "admin"

        # Initialize mock data
        self._init_mock_data()

    def _init_mock_data(self):
        """Khởi tạo dữ liệu mẫu"""
        # Documents và models giờ fetch từ backend, không cần mock data

        if "rag_configs" not in st.session_state:
            st.session_state.rag_configs = [
                {"id": 1, "config_name": "Standard RAG", "llm_id": 1, "embedding_model_id": 5,
                 "chunk_size": 1000, "chunk_overlap": 200, "search_type": "similarity", "k_value": 3,
                 "prompt_template": "Answer the following question based on the context:\nContext: {context}\nQuestion: {question}",
                 "created_at": "2023-08-10"},
                {"id": 2, "config_name": "High Precision RAG", "llm_id": 2, "embedding_model_id": 6,
                 "chunk_size": 500, "chunk_overlap": 100, "search_type": "mmr", "k_value": 5,
                 "prompt_template": "Given the context information, answer the question accurately:\nContext: {context}\nQuestion: {question}",
                 "created_at": "2023-09-22"}
            ]

        if "rag_documents" not in st.session_state:
            st.session_state.rag_documents = [
                {"id": 1, "rag_config_id": 1, "document_id": 1, "created_at": "2023-08-10"},
                {"id": 2, "rag_config_id": 1, "document_id": 2, "created_at": "2023-08-10"},
                {"id": 3, "rag_config_id": 2, "document_id": 1, "created_at": "2023-09-22"},
                {"id": 4, "rag_config_id": 2, "document_id": 3, "created_at": "2023-09-22"}
            ]

        if "users" not in st.session_state:
            st.session_state.users = [
                {"username": "admin", "password": "admin", "is_admin": True},
                {"username": "user1", "password": "pass1", "is_admin": False},
            ]

    def check_authentication(self) -> None:
        """Kiểm tra authentication"""
        if not st.session_state.logged_in:
            st.error("Vui lòng đăng nhập để tiếp tục.")
            st.info("Quay lại trang chính và đăng nhập.")
            st.stop()
        elif not st.session_state.get("is_admin", False):
            st.error("Bạn không có quyền truy cập trang quản trị.")
            st.info("Chỉ tài khoản admin mới có thể vào trang này.")
            st.stop()

    def render_sidebar(self) -> None:
        """Render sidebar"""
        st.sidebar.title("Admin Controls")
        st.sidebar.info(f"Logged in as: {st.session_state.username} (Admin)")

        # Hiển thị token (có thể comment out trong production)
        with st.sidebar.expander("Debug Info"):
            st.code(f"Token: {st.session_state.get('token', 'N/A')[:50]}...")

    def render_main_content(self) -> None:
        """Render nội dung chính"""
        st.title("Admin Dashboard")

        # Render tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "User Management",
            "Document Management",
            "RAG Configuration",
            "RAG Versions",
            "Analytics"
        ])

        with tab1:
            self.user_tab.render()

        with tab2:
            self.document_tab.render()

        with tab3:
            self.rag_config_tab.render()

        with tab4:
            self.rag_versions_tab.render()

        with tab5:
            self.analytics_tab.render()

    def run(self) -> None:
        """Chạy ứng dụng"""
        self.render_sidebar()
        self.render_main_content()


# ========================= RUN APP =========================
if __name__ == "__main__":
    app = AdminDashboardApp()
    app.run()
