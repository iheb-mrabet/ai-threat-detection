from pydantic import BaseModel
from typing import List, Dict


class AnalyzeRequest(BaseModel):
    log_line: str


class BatchAnalyzeRequest(BaseModel):
    log_lines: List[str]


class DetectionResponse(BaseModel):
    is_threat: bool
    threat_type: str
    severity: str
    score: float
    matched_rules: List[str]
    extracted_features: Dict[str, float]
    explanation: str


class BatchDetectionResponse(BaseModel):
    total: int
    threats_detected: int
    results: List[DetectionResponse]
