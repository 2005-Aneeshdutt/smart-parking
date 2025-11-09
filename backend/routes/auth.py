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
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = db.cursor(dictionary=True)
    try:
        # Trim email to handle any whitespace issues
        email = req.email.strip()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        # Check password
        password_hash = user["password_hash"]
        if isinstance(password_hash, bytes):
            password_hash = password_hash.decode()
        
        if not bcrypt.checkpw(req.password.encode(), password_hash.encode()):
            raise HTTPException(status_code=401, detail="Invalid password")

        return {
            "message": "Login successful", 
            "user_id": user["user_id"], 
            "name": user["name"],
            "email": user["email"],
            "role": user.get("role", "driver")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")
    finally:
        cursor.close()
        db.close()
