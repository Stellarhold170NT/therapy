# Therapy Chatbot

This is a therapy chatbot application with a client-server architecture. The client is a web-based interface built with Streamlit, and the server is a FastAPI application.

## Project Structure

```
E:\nt170\ChatBot\therapy\
├───.gitignore
├───Client\
│   ├───Home.py
│   └───pages\
│       └───Admin_Dashboard.py
└───Server\
    ├───main.py
    ├───auth\
    │   └───auth.py
    ├───database\
    │   └───connection.py
    ├───models\
    │   ├───chat_session.py
    │   ├───message_store.py
    │   └───user.py
    ├───schemas\
    │   └───user_schema.py
    └───services\
        ├───chat_service.py
        ├───history_service.py
        ├───rag_service.py
        └───user_service.py
```

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd therapy
    ```

2.  **Install the dependencies:**
    ```bash
    pip install streamlit fastapi uvicorn python-dotenv pymongo bcrypt pyjwt pandas langchain llama-index
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

