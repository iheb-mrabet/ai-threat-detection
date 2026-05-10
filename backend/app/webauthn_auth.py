import base64
import json
import os

from fastapi import APIRouter, HTTPException, Request
from redis import Redis

from backend.app.auth import create_access_token

from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
)

from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    ResidentKeyRequirement,
    UserVerificationRequirement,
    PublicKeyCredentialDescriptor,
)

router = APIRouter(prefix="/auth/webauthn", tags=["WebAuthn Passkeys"])

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

RP_ID = os.getenv("WEBAUTHN_RP_ID", "localhost")
RP_NAME = os.getenv("WEBAUTHN_RP_NAME", "AI Threat Detection Platform")
EXPECTED_ORIGIN = os.getenv("WEBAUTHN_EXPECTED_ORIGIN", "http://localhost:3000")

DEMO_USER_ID = os.getenv("WEBAUTHN_DEMO_USER_ID", "iheb-demo-user")
DEMO_USERNAME = os.getenv("WEBAUTHN_DEMO_USERNAME", "iheb")

redis_client = Redis.from_url(
    REDIS_URL,
    decode_responses=True
)


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _credential_key(username: str) -> str:
    return f"webauthn:credential:{username}"


def _registration_challenge_key(username: str) -> str:
    return f"webauthn:registration_challenge:{username}"


def _auth_challenge_key(session_id: str) -> str:
    return f"webauthn:auth_challenge:{session_id}"


@router.get("/debug")
def webauthn_debug():
    return {
        "rp_id": RP_ID,
        "rp_name": RP_NAME,
        "expected_origin": EXPECTED_ORIGIN,
        "demo_username": DEMO_USERNAME,
        "has_registered_credential": bool(redis_client.get(_credential_key(DEMO_USERNAME)))
    }


@router.post("/register/options")
def register_options():
    try:
        options = generate_registration_options(
            rp_id=RP_ID,
            rp_name=RP_NAME,
            user_id=DEMO_USER_ID.encode("utf-8"),
            user_name=DEMO_USERNAME,
            user_display_name="Iheb Demo User",
            authenticator_selection=AuthenticatorSelectionCriteria(
                resident_key=ResidentKeyRequirement.PREFERRED,
                user_verification=UserVerificationRequirement.REQUIRED,
            ),
        )

        redis_client.setex(
            _registration_challenge_key(DEMO_USERNAME),
            300,
            _b64url_encode(options.challenge)
        )

        return json.loads(options_to_json(options))

    except Exception as e:
        print("[WEBAUTHN_REGISTER_OPTIONS_ERROR]", repr(e))
        raise HTTPException(
            status_code=500,
            detail=f"Registration options failed: {str(e)}"
        )


@router.post("/register/verify")
async def register_verify(request: Request):
    body = await request.json()

    expected_challenge_b64 = redis_client.get(
        _registration_challenge_key(DEMO_USERNAME)
    )

    if not expected_challenge_b64:
        raise HTTPException(
            status_code=400,
            detail="Registration challenge expired"
        )

    try:
        verification = verify_registration_response(
            credential=body,
            expected_challenge=_b64url_decode(expected_challenge_b64),
            expected_origin=EXPECTED_ORIGIN,
            expected_rp_id=RP_ID,
            require_user_verification=True,
        )

        credential_data = {
            "credential_id": _b64url_encode(verification.credential_id),
            "credential_public_key": _b64url_encode(verification.credential_public_key),
            "sign_count": verification.sign_count,
            "username": DEMO_USERNAME,
        }

        redis_client.set(
            _credential_key(DEMO_USERNAME),
            json.dumps(credential_data)
        )

        redis_client.delete(_registration_challenge_key(DEMO_USERNAME))

        return {
            "status": "registered",
            "username": DEMO_USERNAME,
            "credential_id": credential_data["credential_id"]
        }

    except Exception as e:
        print("[WEBAUTHN_REGISTER_VERIFY_ERROR]", repr(e))
        raise HTTPException(
            status_code=400,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login/options/{session_id}")
def login_options(session_id: str):
    try:
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

        raw_credential = redis_client.get(_credential_key(DEMO_USERNAME))

        if not raw_credential:
            raise HTTPException(
                status_code=404,
                detail="No passkey registered yet. Register your phone first."
            )

        credential_data = json.loads(raw_credential)

        options = generate_authentication_options(
            rp_id=RP_ID,
            allow_credentials=[
                PublicKeyCredentialDescriptor(
                    id=_b64url_decode(credential_data["credential_id"])
                )
            ],
            user_verification=UserVerificationRequirement.REQUIRED,
        )

        redis_client.setex(
            _auth_challenge_key(session_id),
            120,
            _b64url_encode(options.challenge)
        )

        return json.loads(options_to_json(options))

    except HTTPException:
        raise

    except Exception as e:
        print("[WEBAUTHN_LOGIN_OPTIONS_ERROR]", repr(e))
        raise HTTPException(
            status_code=500,
            detail=f"Login options failed: {str(e)}"
        )


@router.post("/login/verify/{session_id}")
async def login_verify(session_id: str, request: Request):
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

    raw_credential = redis_client.get(_credential_key(DEMO_USERNAME))

    if not raw_credential:
        raise HTTPException(
            status_code=404,
            detail="No passkey registered yet"
        )

    expected_challenge_b64 = redis_client.get(_auth_challenge_key(session_id))

    if not expected_challenge_b64:
        raise HTTPException(
            status_code=400,
            detail="Authentication challenge expired"
        )

    credential_data = json.loads(raw_credential)
    body = await request.json()

    try:
        verification = verify_authentication_response(
            credential=body,
            expected_challenge=_b64url_decode(expected_challenge_b64),
            expected_origin=EXPECTED_ORIGIN,
            expected_rp_id=RP_ID,
            credential_public_key=_b64url_decode(
                credential_data["credential_public_key"]
            ),
            credential_current_sign_count=int(
                credential_data.get("sign_count", 0)
            ),
            require_user_verification=True,
        )

        credential_data["sign_count"] = verification.new_sign_count

        redis_client.set(
            _credential_key(DEMO_USERNAME),
            json.dumps(credential_data)
        )

        session_data["status"] = "approved"
        session_data["used"] = True
        token = create_access_token({"sub": DEMO_USERNAME})
        session_data["approved_token"] = token

        redis_client.setex(
            f"qr_login:{session_id}",
            30,
            json.dumps(session_data)
        )

        redis_client.delete(_auth_challenge_key(session_id))

        return {
            "status": "approved",
            "message": "WebAuthn login approved"
        }

    except Exception as e:
        print("[WEBAUTHN_LOGIN_VERIFY_ERROR]", repr(e))
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )
