from pydantic import BaseModel
from typing import List, Dict, Optional


class AnalyzeRequest(BaseModel):
    log_line: str


class BatchAnalyzeRequest(BaseModel):
    log_lines: List[str]


class DetectionResponse(BaseModel):
    is_threat: bool
    threat_type: str
    severity: str
    score: float

    rule_score: Optional[float] = None
    ml_score: Optional[float] = None
    rf_score: Optional[float] = None
    isolation_score: Optional[float] = None
    autoencoder_score: Optional[float] = None
    detection_mode: Optional[str] = None

    matched_rules: List[str]
    extracted_features: Dict[str, float]
    explanation: str


class BatchDetectionResponse(BaseModel):
    total: int
    threats_detected: int
    results: List[DetectionResponse]
