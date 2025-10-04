from pydantic import BaseModel

class UserRegister(BaseModel):
    username: str
    password: str
    role: str = "user"   # default role

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    user_id: int
    username: str
    role: str
    summary: str | None

    class Config:
        orm_mode = True
