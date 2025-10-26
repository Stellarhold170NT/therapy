import streamlit as st
import uuid
from datetime import datetime


class ChatUI:
    """Component giao diện chat"""

    def __init__(self, chat_service, history_service):
        self.chat_service = chat_service
        self.history_service = history_service

        # Khởi tạo chat history trong session_state
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Khởi tạo session_id trong session_state
        if "chat_session_id" not in st.session_state:
            st.session_state.chat_session_id = None

        # Khởi tạo session_created flag
        if "session_created" not in st.session_state:
            st.session_state.session_created = False

    def _init_chat_session(self, token: str) -> None:
        """
        Khởi tạo chat session mới nếu chưa có.
        Gọi khi bắt đầu chat lần đầu (messages rỗng)
        """
        if st.session_state.chat_session_id is None:
            # Generate UUID mới
            session_id = str(uuid.uuid4())
            st.session_state.chat_session_id = session_id

            # Tạo session name mặc định
            session_name = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"

            # Gọi API tạo chat session
            result = self.history_service.create_chat_session(
                session_id=session_id,
                session_name=session_name,
                token=token
            )

            if result["success"]:
                st.session_state.session_created = True
                print(f"[Chat Session] Created: {session_id}")
            else:
                print(f"[Chat Session] Error creating session: {result.get('message')}")

    def render_chat_history(self) -> None:
        """Hiển thị lịch sử chat"""
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    def render_chat_input(self, token: str) -> None:
        """Render input chat và xử lý message"""
        if prompt := st.chat_input("Nhập tin nhắn của bạn..."):
            # Khởi tạo chat session nếu chưa có (khi bắt đầu chat)
            self._init_chat_session(token)

            # Thêm user message
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Hiển thị user message
            with st.chat_message("user"):
                st.markdown(prompt)

            # Hiển thị assistant response với streaming
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""

                # Truyền session_id khi gọi API
                session_id = st.session_state.chat_session_id or "default"
                for chunk in self.chat_service.send_message_stream(prompt, token, session_id):
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")

                message_placeholder.markdown(full_response)

            # Lưu assistant response
            st.session_state.messages.append({"role": "assistant", "content": full_response})

            # Touch session để cập nhật timestamp
            if st.session_state.chat_session_id:
                self.history_service.touch_chat_session(
                    st.session_state.chat_session_id,
                    token
                )

    def render_new_chat_button(self) -> None:
        """Render nút bắt đầu chat mới"""
        if st.button("🔄 Bắt đầu cuộc trò chuyện mới", use_container_width=True):
            # Reset messages và session
            st.session_state.messages = []
            st.session_state.chat_session_id = None
            st.session_state.session_created = False
            st.rerun()
