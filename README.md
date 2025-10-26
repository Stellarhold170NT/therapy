# Therapy Chatbot

This is a therapy chatbot application with a client-server architecture. The client is a web-based interface built with Streamlit, and the server is a FastAPI application.

## Project Structure

```
E:\nt170\ChatBot\therapy\
├───.gitignore
├───Client\
│   ├───Home.py                          # Main user interface
│   ├───pages\
│   │   └───Admin_Dashboard.py          # Admin dashboard
│   ├───services\                        # Shared business logic
│   │   ├───session_manager.py          # JWT token management
│   │   ├───auth_service.py             # Authentication API
│   │   ├───chat_service.py             # Chat streaming API
│   │   ├───rag_service.py              # RAG configuration API
│   │   └───document_service.py         # Document management API
│   └───components\                      # UI Components
│       ├───auth_ui.py                  # Login/Register forms
│       ├───chat_ui.py                  # Chat interface
│       ├───user_management_tab.py      # User management UI
│       ├───document_management_tab.py  # Document management UI
│       ├───rag_configuration_tab.py    # RAG config UI
│       ├───rag_versions_tab.py         # RAG versions UI
│       └───analytics_tab.py            # Analytics dashboard
└───Server\
    ├───main.py
    ├───init_db.py                      # Database initialization script
    ├───auth\
    │   └───auth.py
    ├───database\
    │   └───connection.py
    ├───models\
    │   ├───chat_session.py
    │   ├───message_store.py
    │   ├───user.py
    │   ├───rag_config.py               # RAG configuration model
    │   └───document.py                 # Document model
    ├───schemas\
    │   ├───user_schema.py
    │   ├───rag_config_schema.py
    │   └───document_schema.py
    └───services\
        ├───chat_service.py
        ├───history_service.py
        ├───rag_service.py              # RAG + Document endpoints
        └───user_service.py
```

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd therapy
    ```

2.  **Create virtual environment (recommended):**
    ```bash
    # Create venv
    python -m venv venv

    # Activate
    .\venv\Scripts\Activate
    ```

3.  **Install the dependencies:**

    **For Server:**
    ```bash
    pip install fastapi uvicorn pydantic sqlalchemy pymysql python-dotenv "python-jose[cryptography]" "passlib[bcrypt]" langchain-core langchain-ollama python-multipart
    ```

    **For Client:**
    ```bash
    pip install streamlit pandas requests streamlit-cookies-manager PyPDF2 matplotlib
    ```

    **Or install all at once:**
    ```bash
    pip install fastapi uvicorn pydantic sqlalchemy pymysql python-dotenv "python-jose[cryptography]" "passlib[bcrypt]" langchain-core langchain-ollama python-multipart streamlit pandas requests streamlit-cookies-manager PyPDF2 matplotlib
    ```

## Running the project

1.  **Run the server:**
    Navigate to the `Server` directory and run the following command:
    ```bash
    cd Server
    uvicorn main:app --reload
    ```
    The server will be running at `http://127.0.0.1:8000`.

2.  **Run the client:**
    In a new terminal, navigate to the `Client` directory and run the following command:
    ```bash
    cd Client
    streamlit run Home.py
    ```
    The client will be running at `http://localhost:8501`.

