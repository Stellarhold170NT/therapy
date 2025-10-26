import streamlit as st


class AuthUI:
    """Component giao diện đăng nhập/đăng ký"""

    def __init__(self, auth_service, session_manager):
        self.auth_service = auth_service
        self.session_manager = session_manager

    def render_login_form(self) -> None:
        """Render form đăng nhập"""
        st.sidebar.subheader("Đăng nhập")

        username = st.sidebar.text_input("Username", key="login_username")
        password = st.sidebar.text_input("Password", type="password", key="login_password")

        col1, col2 = st.sidebar.columns(2)

        if col1.button("Đăng nhập", use_container_width=True):
            if not username or not password:
                st.sidebar.error("Vui lòng nhập đầy đủ thông tin")
                return

            with st.spinner("Đang đăng nhập..."):
                result = self.auth_service.login(username, password)

            if result["success"]:
                # Lưu token vào cookies
                self.session_manager.save_token(
                    token=result["token"],
                    username=result["username"],
                    role=result.get("role", "user")
                )
                # Lưu vào session_state
                st.session_state.logged_in = True
                st.session_state.username = result["username"]
                st.session_state.token = result["token"]
                st.session_state.is_admin = (result.get("role") == "admin")

                st.sidebar.success(f"Chào mừng, {username}!")
                st.rerun()
            else:
                st.sidebar.error(f"Đăng nhập thất bại: {result.get('error', 'Unknown error')}")

        if col2.button("Đăng ký", use_container_width=True):
            st.session_state.show_register = True
            st.rerun()

    def render_register_form(self) -> None:
        """Render form đăng ký"""
        st.sidebar.subheader("Đăng ký tài khoản")

        username = st.sidebar.text_input("Username", key="register_username")
        password = st.sidebar.text_input("Password", type="password", key="register_password")
        password_confirm = st.sidebar.text_input("Xác nhận Password", type="password", key="register_password_confirm")

        col1, col2 = st.sidebar.columns(2)

        if col1.button("Đăng ký", use_container_width=True):
            if not username or not password:
                st.sidebar.error("Vui lòng nhập đầy đủ thông tin")
                return

            if password != password_confirm:
                st.sidebar.error("Mật khẩu không khớp")
                return

            with st.spinner("Đang đăng ký..."):
                result = self.auth_service.register(username, password)

            if result["success"]:
                st.sidebar.success("Đăng ký thành công! Vui lòng đăng nhập.")
                st.session_state.show_register = False
                st.rerun()
            else:
                error_msg = result.get('error', 'Unknown error')
                if "already exists" in error_msg:
                    st.sidebar.error("Username đã tồn tại")
                else:
                    st.sidebar.error(f"Đăng ký thất bại: {error_msg}")

        if col2.button("Quay lại", use_container_width=True):
            st.session_state.show_register = False
            st.rerun()
