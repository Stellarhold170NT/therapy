import streamlit as st
import streamlit_cookies_manager

# Import services
from services.session_manager import SessionManager
from services.auth_service import AuthService
from services.chat_service import ChatService
from services.history_service import HistoryService

# Import components
from components.auth_ui import AuthUI
from components.chat_ui import ChatUI
from components.debug_panel import DebugPanel


# ========================= MAIN APPLICATION =========================
class TherapyApp:
    """Main application class"""

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
        self.chat_service = ChatService()
        self.history_service = HistoryService()

        # Setup UI components
        self.auth_ui = AuthUI(self.auth_service, self.session_manager)
        self.chat_ui = ChatUI(self.chat_service, self.history_service)
        self.debug_panel = DebugPanel(self.chat_service)

        # Initialize session state
        self.init_session_state()

    def setup_page(self) -> None:
        """Cấu hình trang"""
        st.set_page_config(
            page_title="Therapy Chatbot",
            page_icon="💬"
        )

    def init_session_state(self) -> None:
        """Khởi tạo session state"""
        if "logged_in" not in st.session_state:
            st.session_state.logged_in = False

        if "show_register" not in st.session_state:
            st.session_state.show_register = False

        # Thử load token từ cookies
        if not st.session_state.logged_in:
            session_data = self.session_manager.load_token()
            if session_data:
                token = session_data.get("token")
                # Verify token còn hợp lệ không
                if self.auth_service.verify_token(token):
                    st.session_state.logged_in = True
                    st.session_state.username = session_data.get("username")
                    st.session_state.token = token
                    st.session_state.is_admin = (session_data.get("role") == "admin")
                else:
                    # Token expired, clear it
                    self.session_manager.clear_token()

    def render_sidebar(self) -> None:
        """Render sidebar"""
        st.sidebar.title("💬 Therapy Chatbot")

        if st.session_state.logged_in:
            # User đã đăng nhập
            st.sidebar.success(f"👤 {st.session_state.username}")

            if st.sidebar.button("🚪 Đăng xuất", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username = ""
                st.session_state.token = ""
                st.session_state.messages = []
                self.session_manager.clear_token()
                st.rerun()

            st.sidebar.divider()

            # Chat statistics
            st.sidebar.subheader("📊 Thống kê")
            st.sidebar.metric("Số tin nhắn", len(st.session_state.get("messages", [])))

            # Debug options (only for admin)
            if st.session_state.get("is_admin", False):
                self.debug_panel.render_debug_options_sidebar()
        else:
            # Chưa đăng nhập
            if st.session_state.get("show_register", False):
                self.auth_ui.render_register_form()
            else:
                self.auth_ui.render_login_form()

    def render_main_content(self) -> None:
        """Render nội dung chính"""
        if not st.session_state.logged_in:
            # Chưa đăng nhập - hiển thị welcome screen
            st.title("🌟 Chào mừng đến với Therapy Chatbot")
            st.markdown("""
            ### Hãy đăng nhập hoặc đăng ký để bắt đầu!

            Therapy Chatbot là một ứng dụng trò chuyện thông minh giúp bạn:
            - 💬 Trò chuyện tự nhiên với AI
            - 🔒 Bảo mật thông tin cá nhân
            - 📊 Theo dõi lịch sử trò chuyện

            **Hãy đăng nhập ở sidebar bên trái để bắt đầu!**
            """)
        else:
            # Đã đăng nhập - hiển thị chat interface
            st.title("💬 Ngày hôm nay của bạn thế nào?")

            # New chat button
            self.chat_ui.render_new_chat_button()

            st.divider()

            # Chat history
            self.chat_ui.render_chat_history()

            # Chat input
            self.chat_ui.render_chat_input(st.session_state.token)

            # Debug info (only for admin, after chat interaction)
            if st.session_state.get("is_admin", False) and st.session_state.get("chat_session_id"):
                self.debug_panel.render_debug_info(
                    st.session_state.chat_session_id,
                    st.session_state.token
                )

                # Vector store debug panel
                self.debug_panel.render_vector_store_debug(st.session_state.token)

    def run(self) -> None:
        """Chạy ứng dụng"""
        self.render_sidebar()
        self.render_main_content()


# ========================= RUN APP =========================
if __name__ == "__main__":
    app = TherapyApp()
    app.run()
