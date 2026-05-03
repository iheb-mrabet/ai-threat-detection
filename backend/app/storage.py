from typing import List, Dict
from backend.app.config import ALERT_LIMIT

ALERTS: List[Dict] = []
EVENTS: List[Dict] = []


def save_event(event: Dict) -> None:
    EVENTS.append(event)


def save_alert(alert: Dict) -> None:
    ALERTS.append(alert)

    if len(ALERTS) > ALERT_LIMIT:
        del ALERTS[0]


def get_alerts(limit: int = 100) -> List[Dict]:
    return ALERTS[-limit:]


def get_events(limit: int = 100) -> List[Dict]:
    return EVENTS[-limit:]


def get_stats() -> Dict:
    total_events = len(EVENTS)
    total_alerts = len(ALERTS)

    severity_count = {}
    threat_type_count = {}

    for alert in ALERTS:
        severity = alert.get("severity", "unknown")
        threat_type = alert.get("threat_type", "unknown")

        severity_count[severity] = severity_count.get(severity, 0) + 1
        threat_type_count[threat_type] = threat_type_count.get(threat_type, 0) + 1

    return {
        "total_events": total_events,
        "total_alerts": total_alerts,
        "benign_events": total_events - total_alerts,
        "severity_count": severity_count,
        "threat_type_count": threat_type_count
    }
