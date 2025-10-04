import streamlit as st

# --- Cấu hình trang ---
st.set_page_config(page_title="Chatbot - Trang Chính", page_icon="💬")

# --- Khởi tạo trạng thái ---
for key in ["logged_in", "username", "chat_history", "is_admin"]:
    if key not in st.session_state:
        st.session_state[key] = False if key in ["logged_in", "is_admin"] else "" if key=="username" else []

# --- Khởi tạo dữ liệu mẫu ---
if not st.session_state.chat_history:
    st.session_state.chat_history = [
        "Hello, how are you?",
        "What's the weather today?",
        "Tell me a joke.",
        "How to learn Python?",
        "I love AI",
        "Let's chat",
        "How's your day?",
        "Python or Java?",
        "Good morning",
        "What's up?",
        "Test chat 11",
        "Test chat 12"
    ]

# --- Khởi tạo người dùng mẫu ---
if "users" not in st.session_state:
    st.session_state.users = [
        {"username": "admin", "password": "admin", "is_admin": True},
        {"username": "a", "password": "a", "is_admin": False},
        {"username": "user1", "password": "pass1", "is_admin": False},
        {"username": "user2", "password": "pass2", "is_admin": False},
    ]

# --- Sidebar ---
st.sidebar.title("Chats")

# --- Login / Logout ---
if not st.session_state.logged_in:
    st.sidebar.subheader("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        # Check credentials against user database
        for user in st.session_state.users:
            if user["username"] == username and user["password"] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.is_admin = user["is_admin"]
                st.sidebar.success(f"Welcome, {username}!")
                st.rerun()
                break
        else:
            st.sidebar.error("Invalid username or password")
else:
    st.sidebar.info(f"Logged in as: {st.session_state.username}")
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.is_admin = False
        st.sidebar.success("Logged out!")
        st.rerun()

# --- Main Page ---
st.title("Ngày hôm nay của bạn thế nào")

# Nút bắt đầu cuộc trò chuyện mới
if st.button("Start all new conversation"):
    st.session_state.chat_history = []
    st.rerun()

# Hiển thị chat history
latest_chats = list(reversed(st.session_state.chat_history))[:10]
titles = [msg[:50] + ("..." if len(msg) > 50 else "") for msg in latest_chats]

selected_title_index = st.sidebar.selectbox(
    "Chọn chat để xem:", [""] + list(range(len(titles))),
    format_func=lambda x: "" if x == "" else titles[x]
)

if selected_title_index != "":
    selected_chat = latest_chats[selected_title_index]
    st.subheader("Nội dung chat đầy đủ")
    st.markdown(selected_chat)

# Ô nhập chat mới / search chat
prompt = st.chat_input("Enter your query (gửi hoặc tìm kiếm lịch sử)")
if prompt:
    matches = [msg for msg in reversed(st.session_state.chat_history) if prompt.lower() in msg.lower()]
    if matches:
        st.subheader("Kết quả tìm kiếm trong lịch sử chat")
        for i, msg in enumerate(matches[:10], 1):
            st.markdown(f"{i}. {msg[:50]}{'...' if len(msg) > 50 else ''}")
    else:
        with st.chat_message('user'):
            st.markdown(prompt)
    st.session_state.chat_history.append(prompt)
    st.rerun()