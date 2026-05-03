from typing import Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from backend.app.db.models import SecurityEvent, Alert


def create_event(db: Session, event: Dict) -> SecurityEvent:
    db_event = SecurityEvent(
        id=event.get("id"),
        log_line=event.get("log_line", ""),
        is_threat=event.get("is_threat", False),
        threat_type=event.get("threat_type", "normal"),
        severity=event.get("severity", "low"),
        score=event.get("score", 0.0),
        rule_score=event.get("rule_score", 0.0),
        ml_score=event.get("ml_score", 0.0),
        rf_score=event.get("rf_score", 0.0),
        isolation_score=event.get("isolation_score", 0.0),
        autoencoder_score=event.get("autoencoder_score", 0.0),
        matched_rules=event.get("matched_rules", []),
        extracted_features=event.get("extracted_features", {}),
        parsed=event.get("parsed", {}),
        detection_mode=event.get("detection_mode", "rules_only"),
        explanation=event.get("explanation", "")
    )

    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    return db_event


def create_alert(db: Session, event: Dict) -> Alert:
    alert = Alert(
        event_id=event.get("id", ""),
        threat_type=event.get("threat_type", "unknown"),
        severity=event.get("severity", "low"),
        score=event.get("score", 0.0),
        payload=event
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    return alert


def list_events(db: Session, limit: int = 100) -> List[SecurityEvent]:
    return (
        db.query(SecurityEvent)
        .order_by(desc(SecurityEvent.created_at))
        .limit(limit)
        .all()
    )


def list_alerts(db: Session, limit: int = 100) -> List[Alert]:
    return (
        db.query(Alert)
        .order_by(desc(Alert.created_at))
        .limit(limit)
        .all()
    )


def review_event(db: Session, event_id: str, reviewed_label: int) -> Optional[SecurityEvent]:
    event = db.query(SecurityEvent).filter(SecurityEvent.id == event_id).first()

    if not event:
        return None

    event.reviewed_label = reviewed_label
    db.commit()
    db.refresh(event)

    return event


def stats(db: Session) -> Dict:
    total_events = db.query(func.count(SecurityEvent.id)).scalar()
    total_alerts = db.query(func.count(Alert.id)).scalar()

    severity_rows = (
        db.query(Alert.severity, func.count(Alert.id))
        .group_by(Alert.severity)
        .all()
    )

    threat_rows = (
        db.query(Alert.threat_type, func.count(Alert.id))
        .group_by(Alert.threat_type)
        .all()
    )

    return {
        "total_events": total_events,
        "total_alerts": total_alerts,
        "benign_events": total_events - total_alerts,
        "severity_count": {severity: count for severity, count in severity_rows},
        "threat_type_count": {threat: count for threat, count in threat_rows}
    }
