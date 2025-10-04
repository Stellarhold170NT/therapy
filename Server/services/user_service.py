from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from models.user import User
from models.chat_session import ChatSession
from schemas.user_schema import UserRegister, UserLogin, UserOut
from auth.auth import create_access_token, get_current_user


from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/register", response_model=UserOut)
def register_user(user: UserRegister, db: Session = Depends(get_db)):
    # Kiểm tra username đã tồn tại chưa
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Hash password trước khi lưu
    new_user = User(
        username=user.username,
        password=hash_password(user.password),
        role=user.role if user.role else "user",  # gán mặc định "user" nếu không truyền
        summary=""
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login")
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user.username).first()
    if not existing or not verify_password(user.password, existing.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # ✅ Tạo JWT token
    token = create_access_token(data={"sub": existing.username})
    return {
        "access_token": token,
        "token_type": "bearer"
    }

@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(User).all()
