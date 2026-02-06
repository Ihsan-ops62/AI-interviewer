from datetime import datetime, timedelta
from typing import Dict, Any
import jwt
import bcrypt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from dotenv import load_dotenv

from models import UserCreate, UserLogin
from db import db

# --------------------------------------------------
# ENV + SECURITY
# --------------------------------------------------

load_dotenv()

security = HTTPBearer()

JWT_SECRET = os.getenv("JWT_SECRET", "change-this-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


# --------------------------------------------------
# PASSWORD UTILS
# --------------------------------------------------

def hash_password(password: str) -> str:
    if len(password) > 72:
        raise HTTPException(
            status_code=400,
            detail="Password cannot exceed 72 characters"
        )

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


# --------------------------------------------------
# JWT UTILS
# --------------------------------------------------

def create_token(user_id: int, username: str) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict[str, Any]:
    return verify_token(credentials.credentials)


# --------------------------------------------------
# AUTH SERVICE
# --------------------------------------------------

class AuthService:

    # -------------------------
    # REGISTER
    # -------------------------
    @staticmethod
    async def register_user(user_data: UserCreate) -> Dict[str, Any]:

        if len(user_data.password) < 6:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 6 characters long"
            )

        # Check if user exists
        existing = db.execute(
            "SELECT user_id FROM users WHERE username = %s OR email = %s",
            (user_data.username, user_data.email),
            fetch=True
        )

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Username or email already exists"
            )

        password_hash = hash_password(user_data.password)

        try:
            user = db.execute(
                """
                INSERT INTO users (username, email, password_hash, full_name)
                VALUES (%s, %s, %s, %s)
                RETURNING user_id, username, email, full_name, created_at
                """,
                (
                    user_data.username,
                    user_data.email,
                    password_hash,
                    user_data.full_name
                ),
                fetch=True
            )[0]

            token = create_token(user["user_id"], user["username"])

            return {
                "user": user,
                "token": token
            }

        except Exception as e:
            print("REGISTER ERROR:", e)
            raise HTTPException(
                status_code=500,
                detail="Registration failed"
            )

    # -------------------------
    # LOGIN
    # -------------------------
    @staticmethod
    async def login_user(login_data: UserLogin) -> Dict[str, Any]:

        users = db.execute(
            """
            SELECT user_id, username, email, password_hash, full_name
            FROM users
            WHERE username = %s
            """,
            (login_data.username,),
            fetch=True
        )

        if not users:
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )

        user = users[0]

        if not verify_password(login_data.password, user["password_hash"]):
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )

        db.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = %s",
            (user["user_id"],)
        )

        token = create_token(user["user_id"], user["username"])

        return {
            "user": {
                "user_id": user["user_id"],
                "username": user["username"],
                "email": user["email"],
                "full_name": user["full_name"]
            },
            "token": token
        }

    # -------------------------
    # PROFILE
    # -------------------------
    @staticmethod
    async def get_user_profile(user_id: int) -> Dict[str, Any]:

        users = db.execute(
            """
            SELECT user_id, username, email, full_name, created_at, last_login
            FROM users
            WHERE user_id = %s
            """,
            (user_id,),
            fetch=True
        )

        if not users:
            raise HTTPException(status_code=404, detail="User not found")

        return users[0]
