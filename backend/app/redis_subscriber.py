import json
import threading

import redis

from backend.app.redis_client import REDIS_URL, ALERT_CHANNEL
from backend.app.alerts import broadcast_alert


class RedisSubscriber:
    def __init__(self):
        self.client = None
        self.thread = None
        self.running = False

        try:
            self.client = redis.from_url(REDIS_URL, decode_responses=True)
            self.client.ping()
            self.ready = True
        except Exception:
            self.ready = False
            self.client = None

    def start(self):
        if not self.ready:
            print("[RedisSubscriber] Redis not available")
            return

        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()

        print("[RedisSubscriber] Started listening to Redis channel")

    def _listen(self):
        pubsub = self.client.pubsub()
        pubsub.subscribe(ALERT_CHANNEL)

        for message in pubsub.listen():
            if not self.running:
                break

            if message["type"] != "message":
                continue

            try:
                alert = json.loads(message["data"])
                # rebroadcast to WebSocket clients
                import asyncio
                asyncio.run(broadcast_alert(alert))
            except Exception as e:
                print(f"[RedisSubscriber] Error: {e}")


redis_subscriber = RedisSubscriber()
