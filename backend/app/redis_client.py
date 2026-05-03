import json
import os
from typing import Dict

import redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
ALERT_CHANNEL = os.getenv("ALERT_CHANNEL", "ai-threat-alerts")


class RedisPublisher:
    def __init__(self):
        self.ready = False
        self.client = None

        try:
            self.client = redis.from_url(REDIS_URL, decode_responses=True)
            self.client.ping()
            self.ready = True
        except Exception:
            self.ready = False
            self.client = None

    def publish_alert(self, alert: Dict):
        if not self.ready:
            return False

        self.client.publish(ALERT_CHANNEL, json.dumps(alert))
        return True

    def status(self):
        return {
            "ready": self.ready,
            "url": REDIS_URL,
            "channel": ALERT_CHANNEL
        }


redis_publisher = RedisPublisher()
