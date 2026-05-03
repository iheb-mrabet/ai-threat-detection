from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect

from backend.app.config import APP_NAME, APP_VERSION
from backend.app.security import verify_api_key
from backend.app.schemas import (
    AnalyzeRequest,
    BatchAnalyzeRequest,
    DetectionResponse,
    BatchDetectionResponse
)
from backend.app.detector import detect
from backend.app.storage import save_alert, save_event, get_alerts, get_stats
from backend.app.pipeline.queue import raw_queue
from backend.app.pipeline.engine import start_pipeline
from backend.app.alerts import ACTIVE_WEBSOCKETS, broadcast_alert
from backend.ml.inference import ml_detector, reload_ml_detector
from backend.ml.train_classifiers import train as retrain_models

app = FastAPI(
    title=APP_NAME,
    description="Advanced nginx log threat detection system with rule-based and ML ensemble detection.",
    version=APP_VERSION
)


@app.on_event("startup")
async def startup_event():
    await start_pipeline()


@app.get("/")
def root():
    return {
        "message": "AI Threat Detection System API is running",
        "version": APP_VERSION,
        "public_endpoints": ["/", "/health"],
        "protected_endpoints": [
            "/analyze",
            "/ingest/batch",
            "/pipeline/ingest",
            "/pipeline/status",
            "/threats",
            "/stats",
            "/models/status",
            "/models/reload",
            "/models/retrain"
        ],
        "websocket": "/ws/alerts"
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": APP_VERSION
    }


@app.get("/models/status", dependencies=[Depends(verify_api_key)])
def models_status():
    return ml_detector.status()


@app.post("/models/reload", dependencies=[Depends(verify_api_key)])
def models_reload():
    detector = reload_ml_detector()
    return {
        "status": "reloaded",
        "models": detector.status()
    }


@app.post("/models/retrain", dependencies=[Depends(verify_api_key)])
def models_retrain():
    retrain_models()
    detector = reload_ml_detector()

    return {
        "status": "retrained",
        "models": detector.status()
    }


@app.post("/analyze", response_model=DetectionResponse, dependencies=[Depends(verify_api_key)])
async def analyze(request: AnalyzeRequest):
    result = detect(request.log_line)

    event = {
        "log_line": request.log_line,
        **result
    }

    save_event(event)

    if result["is_threat"]:
        save_alert(event)
        await broadcast_alert(event)

    return result


@app.post("/ingest/batch", response_model=BatchDetectionResponse, dependencies=[Depends(verify_api_key)])
async def ingest_batch(request: BatchAnalyzeRequest):
    results = []
    threats_detected = 0

    for log_line in request.log_lines:
        result = detect(log_line)

        event = {
            "log_line": log_line,
            **result
        }

        save_event(event)

        if result["is_threat"]:
            threats_detected += 1
            save_alert(event)
            await broadcast_alert(event)

        results.append(result)

    return {
        "total": len(request.log_lines),
        "threats_detected": threats_detected,
        "results": results
    }


@app.post("/pipeline/ingest", dependencies=[Depends(verify_api_key)])
async def pipeline_ingest(request: AnalyzeRequest):
    await raw_queue.put(request.log_line)

    return {
        "status": "queued",
        "message": "Log submitted to async detection pipeline"
    }


@app.get("/pipeline/status", dependencies=[Depends(verify_api_key)])
def pipeline_status():
    from backend.app.pipeline.queue import (
        raw_queue,
        parsed_queue,
        feature_queue,
        detection_queue
    )

    return {
        "raw_queue": raw_queue.qsize(),
        "parsed_queue": parsed_queue.qsize(),
        "feature_queue": feature_queue.qsize(),
        "detection_queue": detection_queue.qsize()
    }


@app.get("/threats", dependencies=[Depends(verify_api_key)])
def threats(limit: int = 100):
    return {
        "count": len(get_alerts(limit)),
        "alerts": get_alerts(limit)
    }


@app.get("/alerts", dependencies=[Depends(verify_api_key)])
def alerts(limit: int = 100):
    return {
        "count": len(get_alerts(limit)),
        "alerts": get_alerts(limit)
    }


@app.get("/stats", dependencies=[Depends(verify_api_key)])
def stats():
    return get_stats()


@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    await websocket.accept()
    ACTIVE_WEBSOCKETS.append(websocket)

    try:
        await websocket.send_json({
            "type": "connection",
            "message": "Connected to AI Threat Detection alert stream"
        })

        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        if websocket in ACTIVE_WEBSOCKETS:
            ACTIVE_WEBSOCKETS.remove(websocket)
