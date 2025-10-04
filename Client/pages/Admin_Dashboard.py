import streamlit as st
import sys

# --- Cấu hình trang ---
st.set_page_config(page_title="Admin Dashboard", page_icon="🔧")

# --- Ẩn khỏi sidebar cho người dùng không phải admin ---
# Hack để ẩn trang khỏi sidebar nếu không phải admin
if hasattr(st, '_main_component') and 'Admin_Dashboard' in sys.argv[0]:
    if "is_admin" not in st.session_state or not st.session_state.is_admin:
        # Không hiển thị trong sidebar - chỉ hiển thị riêng khi có url trực tiếp
        st.experimental_set_query_params(
            _pages_hidden=True
        )

# --- Authentication Check ---
# Chỉ admin mới có thể vào trang này
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("Vui lòng đăng nhập để tiếp tục.")
    st.info("Quay lại trang chính và đăng nhập.")
    st.stop()
elif "is_admin" not in st.session_state or not st.session_state.is_admin:
    st.error("Bạn không có quyền truy cập trang quản trị.")
    st.info("Chỉ tài khoản admin mới có thể vào trang này.")
    st.stop()

# --- Admin Page ---
st.title("Admin Dashboard")
st.sidebar.title("Admin Controls")
st.sidebar.info(f"Logged in as: {st.session_state.username} (Admin)")

# --- Admin Tabs ---
tab1, tab2, tab3 = st.tabs(["User Management", "Chat History", "System Settings"])

with tab1:
    st.header("User Management")
    
    # Display users in a table
    if "users" in st.session_state:
        user_data = {
            "Username": [user["username"] for user in st.session_state.users],
            "Is Admin": [user["is_admin"] for user in st.session_state.users]
        }
        st.dataframe(user_data)
    else:
        st.warning("Không tìm thấy dữ liệu người dùng!")
    
    # Add new user form
    st.subheader("Add New User")
    new_username = st.text_input("Username", key="new_user")
    new_password = st.text_input("Password", type="password", key="new_pass")
    new_is_admin = st.checkbox("Is Admin", key="new_is_admin")
    
    if st.button("Add User"):
        if "users" not in st.session_state:
            st.session_state.users = []
            
        # Check if username already exists
        if new_username in [user["username"] for user in st.session_state.users]:
            st.error("Username already exists!")
        elif new_username and new_password:  # Ensure fields aren't empty
            st.session_state.users.append({
                "username": new_username,
                "password": new_password,
                "is_admin": new_is_admin
            })
            st.success(f"User {new_username} added successfully!")
            st.rerun()
        else:
            st.warning("Please fill in all fields.")

with tab2:
    st.header("Chat History")
    
    # Display all chat history
    if "chat_history" in st.session_state and st.session_state.chat_history:
        for i, msg in enumerate(reversed(st.session_state.chat_history), 1):
            st.text(f"{i}. {msg}")
        
        # Option to clear chat history
        if st.button("Clear All Chat History"):
            st.session_state.chat_history = []
            st.success("Chat history cleared!")
            st.rerun()
    else:
        st.info("No chat history available.")

with tab3:
    st.header("System Settings")
    
    # Sample settings
    st.subheader("Chatbot Settings")
    
    # Khởi tạo giá trị mặc định
    if "model" not in st.session_state:
        st.session_state.model = "Llama2"
    if "temperature" not in st.session_state:
        st.session_state.temperature = 0.7
    if "max_tokens" not in st.session_state:
        st.session_state.max_tokens = 500
    
    model = st.selectbox(
        "LLM Model",
        ["GPT-3.5", "GPT-4", "Llama2", "Claude"],
        index=["GPT-3.5", "GPT-4", "Llama2", "Claude"].index(st.session_state.model)
    )
    
    temperature = st.slider("Temperature", 0.0, 1.0, st.session_state.temperature, 0.1)
    max_tokens = st.slider("Max Tokens", 100, 2000, st.session_state.max_tokens, 100)
    
    if st.button("Save Settings"):
        # Lưu cài đặt vào session state
        st.session_state.model = model
        st.session_state.temperature = temperature
        st.session_state.max_tokens = max_tokens
        st.success("Settings saved successfully!")