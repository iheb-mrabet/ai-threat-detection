from fastapi import Header, HTTPException
from backend.app.config import API_KEY


def verify_api_key(x_api_key: str = Header(default="")):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
