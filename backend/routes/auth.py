from click import password_option
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_db
import bcrypt

router = APIRouter(prefix="/auth", tags=["Auth"])

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
def login(req: LoginRequest):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (req.email,))
    user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not bcrypt.checkpw(req.password.encode(), user["password_hash"].encode()):
        print(password_option)
        raise HTTPException(status_code=401, detail="Invalid password")

    return {"message": "Login successful", "user_id": user["user_id"], "name": user["name"]}
