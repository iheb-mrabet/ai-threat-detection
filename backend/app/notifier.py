import os
import requests

WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")

def send_alert(event):
    if not WEBHOOK:
        return

    data = {
        "content": f"🚨 Threat Detected!\nType: {event['threat_type']}\nScore: {event['score']}"
    }

    try:
        requests.post(WEBHOOK, json=data, timeout=2)
    except:
        pass
