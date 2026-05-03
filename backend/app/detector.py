from typing import Dict, List

from backend.app.parser import parse_nginx_log
from backend.app.features import extract_features
from backend.app.rules import apply_rules
from backend.ml.inference import ml_detector


def calculate_rule_score(features: Dict[str, float], matched_rules: List[str]) -> float:
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
    if score >= 0.90:
        return "critical"
    if score >= 0.70:
        return "high"
    if score >= 0.40:
        return "medium"
    return "low"


def final_decision(rule_score: float, ml_score: float, matched_rules: List[str]) -> float:
    if matched_rules:
        return round(max(rule_score, ml_score), 4)

    return round((0.45 * rule_score) + (0.55 * ml_score), 4)


def detect(log_line: str) -> Dict:
    parsed = parse_nginx_log(log_line)
    features = extract_features(parsed)
    matched_rules = apply_rules(parsed)

    rule_score = calculate_rule_score(features, matched_rules)
    ml_result = ml_detector.predict(features)
    ml_score = ml_result["ml_score"]

    final_score = final_decision(rule_score, ml_score, matched_rules)
    is_threat = final_score >= 0.40 or len(matched_rules) > 0

    threat_type = ", ".join(matched_rules) if matched_rules else "ML Anomaly" if is_threat else "normal"
    severity = severity_from_score(final_score)

    detection_mode = "rules+ml" if ml_result["ml_ready"] == 1.0 else "rules_only"

    explanation = (
        f"Detection mode={detection_mode}. "
        f"Rule score={rule_score}. ML score={ml_score}. Final score={final_score}. "
        f"Threat type={threat_type}. Severity={severity}. "
        f"Matched rules={matched_rules if matched_rules else 'none'}."
    )

    return {
        "is_threat": is_threat,
        "threat_type": threat_type,
        "severity": severity,
        "score": final_score,
        "rule_score": rule_score,
        "ml_score": ml_score,
        "rf_score": ml_result["rf_score"],
        "isolation_score": ml_result["isolation_score"],
        "autoencoder_score": ml_result["autoencoder_score"],
        "detection_mode": detection_mode,
        "matched_rules": matched_rules,
        "extracted_features": features,
        "explanation": explanation
    }
