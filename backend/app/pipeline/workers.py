import uuid

from backend.app.parser import parse_nginx_log
from backend.app.features import extract_features
from backend.app.detector import detect
from backend.app.storage import save_event, save_alert
from backend.app.alerts import broadcast_alert
from backend.app.redis_client import redis_publisher
from backend.app.db.database import SessionLocal
from backend.app.db.repository import create_event, create_alert

from backend.app.pipeline.queue import (
    raw_queue,
    parsed_queue,
    feature_queue,
    detection_queue
)


async def raw_worker():
    while True:
        log_line = await raw_queue.get()

        event = {
            "id": str(uuid.uuid4()),
            "log_line": log_line
        }

        await parsed_queue.put(event)
        raw_queue.task_done()


async def parse_worker():
    while True:
        event = await parsed_queue.get()

        parsed = parse_nginx_log(event["log_line"])
        event["parsed"] = parsed

        await feature_queue.put(event)
        parsed_queue.task_done()


async def feature_worker():
    while True:
        event = await feature_queue.get()

        features = extract_features(event["parsed"])
        event["features"] = features

        await detection_queue.put(event)
        feature_queue.task_done()


async def detection_worker():
    while True:
        event = await detection_queue.get()

        result = detect(event["log_line"])

        full_event = {
            **event,
            **result,
            "extracted_features": result.get("extracted_features", event.get("features", {})),
            "parsed": event.get("parsed", {})
        }

        db = SessionLocal()

        try:
            save_event(full_event)
            create_event(db, full_event)

            if result["is_threat"]:
                save_alert(full_event)
                create_alert(db, full_event)

                published = redis_publisher.publish_alert(full_event)

                if not published:
                    await broadcast_alert(full_event)

        except Exception as e:
            print(f"[Pipeline] Error while saving/dispatching event: {e}")

        finally:
            db.close()
            detection_queue.task_done()
