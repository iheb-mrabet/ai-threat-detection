import asyncio

from backend.app.pipeline.workers import (
    raw_worker,
    parse_worker,
    feature_worker,
    detection_worker
)


async def start_pipeline():
    asyncio.create_task(raw_worker())
    asyncio.create_task(parse_worker())
    asyncio.create_task(feature_worker())
    asyncio.create_task(detection_worker())
