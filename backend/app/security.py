import os
from fastapi import Header, HTTPException
from jose import jwt

API_KEY = os.getenv("API_KEY", "dev-secret-key")
JWT_SECRET = os.getenv("JWT_SECRET", "super-secure-jwt-key")
ALGORITHM = "HS256"


def verify_api_key(x_api_key: str = Header(None)):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API key not configured")

    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return {"auth_type": "api_key"}


def verify_auth(
    authorization: str = Header(None),
    x_api_key: str = Header(None)
):
    if x_api_key == API_KEY:
        return {"auth_type": "api_key"}

    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
            return {
                "auth_type": "jwt",
                "user": payload.get("sub"),
                "role": payload.get("role", "admin")
            }
        except Exception:
            pass

    raise HTTPException(status_code=401, detail="Unauthorized")
