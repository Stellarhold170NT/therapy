from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

# Load .env nếu có
load_dotenv(dotenv_path=ENV_PATH)


# Lấy config từ environment hoặc fallback
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1001011010010110Ntit!")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "chat_message_history")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 1️⃣ Tạo engine kết nối database
engine = create_engine(DATABASE_URL, echo=True, pool_pre_ping=True)

# 2️⃣ Tạo SessionLocal để thao tác DB
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3️⃣ Base class cho các model kế thừa
Base = declarative_base()

# 4️⃣ Dependency để inject session vào route FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
