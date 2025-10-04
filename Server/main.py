from fastapi import FastAPI
from services import user_service,chat_service

app = FastAPI(title="Backend API")

# Register router của user_service

app.include_router(user_service.router)
app.include_router(chat_service.router)

@app.get("/status")
def get_status():
    return {"status": "ok", "message": "Backend is running!"}

#uvicorn main:app --reload --host 0.0.0.0 --port 8080