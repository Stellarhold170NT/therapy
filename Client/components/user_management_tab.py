import streamlit as st


class UserManagementTab:
    """Tab quản lý người dùng"""

    def __init__(self, auth_service):
        self.auth_service = auth_service

    def render(self):
        """Render UI cho User Management tab"""
        st.header("User Management")

        # Fetch users từ backend
        token = st.session_state.get("token", "")

        with st.spinner("Đang tải danh sách users..."):
            result = self.auth_service.list_users(token)

        if result["success"]:
            users = result["data"]

            # Hiển thị trong bảng
            if users:
                user_data = {
                    "User ID": [user["user_id"] for user in users],
                    "Username": [user["username"] for user in users],
                    "Role": [user["role"] for user in users],
                    "Summary": [user.get("summary", "")[:50] + "..." if user.get("summary") and len(user.get("summary", "")) > 50 else user.get("summary", "") for user in users]
                }
                st.dataframe(user_data, use_container_width=True)
                st.info(f"Tổng số users: {len(users)}")
            else:
                st.info("Chưa có users nào trong hệ thống.")
        else:
            st.error(f"Không thể tải danh sách users: {result.get('error', 'Unknown error')}")

        st.divider()

        # Add new user form
        st.subheader("Add New User")
        col1, col2, col3 = st.columns(3)

        with col1:
            new_username = st.text_input("Username", key="new_user")
        with col2:
            new_password = st.text_input("Password", type="password", key="new_pass")
        with col3:
            new_role = st.selectbox("Role", options=["user", "admin"], key="new_role")

        if st.button("Add User", key="add_user_btn"):
            self._add_user(new_username, new_password, new_role)

    def _add_user(self, username: str, password: str, role: str):
        """Thêm user mới vào backend"""
        if not username or not password:
            st.error("Please fill in all fields!")
            return

        token = st.session_state.get("token", "")

        with st.spinner("Đang tạo user..."):
            result = self.auth_service.register_user(username, password, role, token)

        if result["success"]:
            st.success(f"User '{username}' created successfully!")
            st.rerun()
        else:
            error_msg = result.get('error', 'Unknown error')
            if "already exists" in error_msg.lower():
                st.error(f"Username '{username}' already exists!")
            else:
                st.error(f"Failed to create user: {error_msg}")
