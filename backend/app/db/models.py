import uuid
from datetime import datetime, UTC

from sqlalchemy import Column, String, Float, Boolean, DateTime, Text, Integer
from sqlalchemy.types import JSON

from backend.app.db.database import Base


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    log_line = Column(Text, nullable=False)

    is_threat = Column(Boolean, default=False)
    threat_type = Column(String, default="normal")
    severity = Column(String, default="low")

    score = Column(Float, default=0.0)
    rule_score = Column(Float, default=0.0)
    ml_score = Column(Float, default=0.0)
    rf_score = Column(Float, default=0.0)
    isolation_score = Column(Float, default=0.0)
    autoencoder_score = Column(Float, default=0.0)

    matched_rules = Column(JSON, default=list)
    extracted_features = Column(JSON, default=dict)
    parsed = Column(JSON, default=dict)

    detection_mode = Column(String, default="rules_only")
    explanation = Column(Text, default="")

    reviewed_label = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String, nullable=False)

    threat_type = Column(String, default="unknown")
    severity = Column(String, default="low")
    score = Column(Float, default=0.0)

    payload = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
