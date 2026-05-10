import asyncio
import json
import os

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from redis import Redis

router = APIRouter(prefix="/auth/qr", tags=["QR Login WebSocket"])

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

redis_client = Redis.from_url(
    REDIS_URL,
    decode_responses=True
)


@router.websocket("/ws/{session_id}")
async def qr_login_websocket(websocket: WebSocket, session_id: str):
    """
    Non-blocking WebSocket listener.

    The desktop browser connects here while waiting for phone/mobile approval.
    Redis pub/sub is checked without blocking the whole FastAPI server.
    """
    await websocket.accept()

    pubsub = redis_client.pubsub()
    channel = f"qr_login_channel:{session_id}"

    try:
        pubsub.subscribe(channel)

        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "message": "Waiting for mobile authentication..."
        })

        while True:
            message = pubsub.get_message(ignore_subscribe_messages=True)

            if message and message.get("type") == "message":
                data = json.loads(message["data"])

                await websocket.send_json(data)

                if data.get("status") == "approved":
                    break

            await asyncio.sleep(0.2)

    except WebSocketDisconnect:
        pass

    finally:
        try:
            pubsub.unsubscribe(channel)
            pubsub.close()
        except Exception:
            pass
