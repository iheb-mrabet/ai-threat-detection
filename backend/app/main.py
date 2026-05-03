from dotenv import load_dotenv
load_dotenv()

import uuid

from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.app.config import APP_NAME, APP_VERSION
from backend.app.logger import logger
from backend.app.security import verify_api_key
from backend.app.schemas import (
    AnalyzeRequest,
    BatchAnalyzeRequest,
    DetectionResponse,
    BatchDetectionResponse
)


from backend.app.detector import detect
from backend.app.storage import save_alert, save_event, get_alerts, get_stats, get_events
from backend.app.pipeline.queue import raw_queue
from backend.app.pipeline.engine import start_pipeline
from backend.app.alerts import ACTIVE_WEBSOCKETS, broadcast_alert
from backend.app.redis_client import redis_publisher

from backend.app.db.database import get_db, Base, engine
from backend.app.db.repository import (
    create_event,
    create_alert,
    list_events,
    list_alerts,
    review_event,
    stats as db_stats
)

from backend.ml.inference import ml_detector, reload_ml_detector


from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=APP_NAME,
    description="Advanced nginx log threat detection system with rule-based detection, ML ensemble, ONNX inference, and persistent storage.",
    version=APP_VERSION
)

app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)

    # start async pipeline
    await start_pipeline()

    # start Redis subscriber
    from backend.app.redis_subscriber import redis_subscriber
    redis_subscriber.start()

    # start nginx/shared-volume log tailer
    from backend.app.log_tailer import start_log_tailer
    await start_log_tailer()



def build_event(log_line: str, result: dict) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "log_line": log_line,
        **result
    }


async def persist_and_dispatch(event: dict, db: Session):
    save_event(event)

    try:
        create_event(db, event)
    except Exception as e:
        print(f"[DB] Failed to save event: {e}")

    if event["is_threat"]:
        save_alert(event)

        try:
            create_alert(db, event)
        except Exception as e:
            print(f"[DB] Failed to save alert: {e}")

        published = redis_publisher.publish_alert(event)

        if not published:
            await broadcast_alert(event)


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
            "/events",
            "/events/{event_id}/review",
            "/threats",
            "/stats",
            "/models/status",
            "/models/reload",
            "/models/retrain",
            "/infra/status"
        ],
        "websocket": "/ws/alerts"
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": APP_VERSION
    }


@app.get("/infra/status", dependencies=[Depends(verify_api_key)])
def infra_status():
    return {
        "database": "enabled",
        "redis": redis_publisher.status()
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
@limiter.limit("100/minute")
async def analyze(request: Request, payload: AnalyzeRequest, db: Session = Depends(get_db)):
    result = detect(payload.log_line)
    event = build_event(payload.log_line, result)

    await persist_and_dispatch(event, db)
    from backend.app.notifier import send_alert
    if event['is_threat']:
        send_alert(event)
    logger.info("event_processed", event_id=event["id"], threat=event["is_threat"], score=event["score"])

    return result


@app.post("/ingest/batch", response_model=BatchDetectionResponse, dependencies=[Depends(verify_api_key)])
async def ingest_batch(request: BatchAnalyzeRequest, db: Session = Depends(get_db)):
    results = []
    threats_detected = 0

    for log_line in request.log_lines:
        result = detect(log_line)
        event = build_event(log_line, result)

        await persist_and_dispatch(event, db)
    from backend.app.notifier import send_alert
    if event['is_threat']:
        send_alert(event)

        if result["is_threat"]:
            threats_detected += 1

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


@app.get("/events", dependencies=[Depends(verify_api_key)])
def events(limit: int = 100, db: Session = Depends(get_db)):
    try:
        db_events = list_events(db, limit)

        return {
            "count": len(db_events),
            "events": [
                {
                    "id": e.id,
                    "log_line": e.log_line,
                    "is_threat": e.is_threat,
                    "threat_type": e.threat_type,
                    "severity": e.severity,
                    "score": e.score,
                    "rule_score": e.rule_score,
                    "ml_score": e.ml_score,
                    "matched_rules": e.matched_rules,
                    "extracted_features": e.extracted_features,
                    "detection_mode": e.detection_mode,
                    "reviewed_label": e.reviewed_label,
                    "created_at": str(e.created_at)
                }
                for e in db_events
            ]
        }

    except Exception as e:
        return {
            "count": len(get_events(limit)),
            "events": get_events(limit),
            "fallback": "memory",
            "error": str(e)
        }


@app.post("/events/{event_id}/review", dependencies=[Depends(verify_api_key)])
def review(event_id: str, reviewed_label: int, db: Session = Depends(get_db)):
    if reviewed_label not in [0, 1]:
        raise HTTPException(status_code=400, detail="reviewed_label must be 0 or 1")

    event = review_event(db, event_id, reviewed_label)

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return {
        "status": "reviewed",
        "event_id": event.id,
        "reviewed_label": event.reviewed_label
    }


@app.get("/threats", dependencies=[Depends(verify_api_key)])
def threats(limit: int = 100, db: Session = Depends(get_db)):
    try:
        db_alerts = list_alerts(db, limit)

        return {
            "count": len(db_alerts),
            "alerts": [
                {
                    "id": a.id,
                    "event_id": a.event_id,
                    "threat_type": a.threat_type,
                    "severity": a.severity,
                    "score": a.score,
                    "payload": a.payload,
                    "created_at": str(a.created_at)
                }
                for a in db_alerts
            ]
        }

    except Exception as e:
        return {
            "count": len(get_alerts(limit)),
            "alerts": get_alerts(limit),
            "fallback": "memory",
            "error": str(e)
        }


@app.get("/alerts", dependencies=[Depends(verify_api_key)])
def alerts(limit: int = 100, db: Session = Depends(get_db)):
    return threats(limit, db)


@app.get("/stats", dependencies=[Depends(verify_api_key)])
def stats(db: Session = Depends(get_db)):
    try:
        return db_stats(db)
    except Exception as e:
        memory_stats = get_stats()
        memory_stats["fallback"] = "memory"
        memory_stats["error"] = str(e)
        return memory_stats


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


from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request, exc):
    return JSONResponse({"error": "rate limit exceeded"}, status_code=429)


@app.get("/monitoring/health")
def monitoring_health():
    return {"status": "ok", "service": "ai-threat-detection"}

@app.get("/monitoring/metrics", dependencies=[Depends(verify_api_key)])
def monitoring_metrics(db: Session = Depends(get_db)):
    return {
        "service": "ai-threat-detection",
        "status": "running",
        "stats": db_stats(db),
        "model_ready": ml_detector.status().get("ready"),
        "redis": redis_publisher.status()
    }

@app.get("/monitoring/health")
def monitoring_health():
    return {"status": "ok", "service": "ai-threat-detection"}

@app.get("/monitoring/metrics", dependencies=[Depends(verify_api_key)])
def monitoring_metrics(db: Session = Depends(get_db)):
    return {
        "service": "ai-threat-detection",
        "status": "running",
        "stats": db_stats(db),
        "model_ready": ml_detector.status().get("ready"),
        "redis": redis_publisher.status()
    }

from fastapi import Form
from backend.app.auth import authenticate_user, create_access_token

@app.post("/auth/login")
def login(username: str = Form(...), password: str = Form(...)):
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": username})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/models/metrics-graphs", dependencies=[Depends(verify_api_key)])
def get_metrics_graphs():
    import json
    import os

    path = "reports/metrics_graphs_summary.json"

    if not os.path.exists(path):
        return {
            "ready": False,
            "message": "Graphs not generated yet. Run: python -m backend.ml.metrics_graphs"
        }

    with open(path, "r") as f:
        return {
            "ready": True,
            "summary": json.load(f)
        }

@app.get("/models/security-metrics", dependencies=[Depends(verify_api_key)])
def get_security_metrics():
    import json
    import os

    path = "models/security_metrics.json"

    if not os.path.exists(path):
        return {
            "ready": False,
            "message": "Security metrics not computed yet. Run: python -m backend.ml.security_metrics"
        }

    with open(path, "r") as f:
        return {
            "ready": True,
            "metrics": json.load(f)
        }
