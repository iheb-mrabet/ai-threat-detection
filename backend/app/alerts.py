from typing import List
from fastapi import WebSocket

ACTIVE_WEBSOCKETS: List[WebSocket] = []


async def broadcast_alert(alert: dict):
    disconnected = []

    for websocket in ACTIVE_WEBSOCKETS:
        try:
            await websocket.send_json(alert)
        except Exception:
            disconnected.append(websocket)

    for websocket in disconnected:
        if websocket in ACTIVE_WEBSOCKETS:
            ACTIVE_WEBSOCKETS.remove(websocket)
