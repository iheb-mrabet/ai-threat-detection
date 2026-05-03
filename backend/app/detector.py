from typing import Dict, List
from backend.app.parser import parse_nginx_log
from backend.app.features import extract_features
from backend.app.rules import apply_rules


def calculate_score(features: Dict[str, float], matched_rules: List[str]) -> float:
    score = 0.0

    score += len(matched_rules) * 0.22
    score += min(features["path_length"] / 350, 0.12)
    score += min(features["num_special_chars"] / 35, 0.12)
    score += min(features["path_entropy"] / 10, 0.08)

    weighted_flags = {
        "contains_sql_keyword": 0.22,
        "contains_script": 0.24,
        "contains_traversal": 0.24,
        "contains_command": 0.25,
        "contains_ssrf": 0.25,
        "contains_log4shell": 0.35,
        "contains_sensitive_file": 0.22,
        "looks_like_scanner": 0.18,
        "suspicious_length": 0.10,
        "many_special_chars": 0.10,
        "parse_error": 0.08,
    }

    for feature_name, weight in weighted_flags.items():
        if features.get(feature_name, 0.0) > 0:
            score += weight

    return round(min(score, 1.0), 4)


def severity_from_score(score: float) -> str:
    if score >= 0.85:
        return "critical"
    if score >= 0.60:
        return "high"
    if score >= 0.35:
        return "medium"
    return "low"


def detect(log_line: str) -> Dict:
    parsed = parse_nginx_log(log_line)
    features = extract_features(parsed)
    matched_rules = apply_rules(parsed)

    score = calculate_score(features, matched_rules)
    is_threat = score >= 0.35 or len(matched_rules) > 0

    threat_type = ", ".join(matched_rules) if matched_rules else "normal"
    severity = severity_from_score(score)

    explanation = (
        f"Detected as {threat_type} with score {score}. "
        f"Severity={severity}. "
        f"Matched rules={matched_rules if matched_rules else 'none'}."
    )

    return {
        "is_threat": is_threat,
        "threat_type": threat_type,
        "severity": severity,
        "score": score,
        "matched_rules": matched_rules,
        "extracted_features": features,
        "explanation": explanation
    }
