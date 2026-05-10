import json
import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from redis import Redis

router = APIRouter(prefix="/auth/qr", tags=["QR Authentication"])

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
PUBLIC_FRONTEND_URL = os.getenv("PUBLIC_FRONTEND_URL", "http://127.0.0.1:3000")
QR_SESSION_TTL = int(os.getenv("QR_SESSION_TTL", "120"))

redis_client = Redis.from_url(
    REDIS_URL,
    decode_responses=True
)


@router.post("/start")
def start_qr_login():
    session_id = str(uuid.uuid4())

    session_data = {
        "session_id": session_id,
        "status": "pending",
        "used": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "approved_token": None
    }

    redis_client.setex(
        f"qr_login:{session_id}",
        QR_SESSION_TTL,
        json.dumps(session_data)
    )

    return {
        "session_id": session_id,
        "qr_url": f"{PUBLIC_FRONTEND_URL}/mobile-login/{session_id}",
        "expires_in": QR_SESSION_TTL
    }


@router.get("/status/{session_id}")
def get_qr_status(session_id: str):
    raw_session = redis_client.get(f"qr_login:{session_id}")

    if not raw_session:
        raise HTTPException(
            status_code=404,
            detail="QR session expired or invalid"
        )

    return json.loads(raw_session)


@router.post("/approve-demo/{session_id}")
def approve_qr_demo(session_id: str):
    """
    Temporary demo approval endpoint.
    Later we replace this with real WebAuthn / Face ID verification.
    """
    raw_session = redis_client.get(f"qr_login:{session_id}")

    if not raw_session:
        raise HTTPException(
            status_code=404,
            detail="QR session expired or invalid"
        )

    session_data = json.loads(raw_session)

    if session_data.get("used"):
        raise HTTPException(
            status_code=400,
            detail="QR session already used"
        )

    session_data["status"] = "approved"
    session_data["used"] = True
    session_data["approved_token"] = "DEMO_TOKEN_REPLACE_WITH_JWT_LATER"

    redis_client.setex(
        f"qr_login:{session_id}",
        30,
        json.dumps(session_data)
    )

    return {
        "status": "approved",
        "message": "Demo QR session approved"
    }
