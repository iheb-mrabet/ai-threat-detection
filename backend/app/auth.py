import os
import hashlib
from datetime import datetime, timedelta, timezone
from jose import jwt

SECRET_KEY = os.getenv("JWT_SECRET", "super-secure-jwt-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "iheb")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "iheb")


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


ADMIN_PASSWORD_HASH = hash_password(ADMIN_PASSWORD)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password


def authenticate_user(username: str, password: str):
    if username != ADMIN_USERNAME:
        return None

    if not verify_password(password, ADMIN_PASSWORD_HASH):
        return None

    return {"username": username, "role": "admin"}


def create_access_token(data: dict):
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
