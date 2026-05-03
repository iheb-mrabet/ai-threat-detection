from typing import Dict
from urllib.parse import unquote
import math


def normalize_path(path: str) -> str:
    decoded = unquote(path).lower()
    decoded = decoded.replace("+", " ")
    return decoded


def entropy(text: str) -> float:
    if not text:
        return 0.0

    probabilities = [text.count(c) / len(text) for c in set(text)]
    return -sum(p * math.log2(p) for p in probabilities)


def extract_features(parsed_log: Dict[str, str]) -> Dict[str, float]:
    path = normalize_path(parsed_log.get("path", ""))
    method = parsed_log.get("method", "UNKNOWN").upper()

    try:
        status = int(parsed_log.get("status", 0))
    except ValueError:
        status = 0

    try:
        size = int(parsed_log.get("size", 0))
    except ValueError:
        size = 0

    features = {
        "path_length": float(len(path)),
        "num_digits": float(sum(c.isdigit() for c in path)),
        "num_letters": float(sum(c.isalpha() for c in path)),
        "num_special_chars": float(sum(not c.isalnum() and c != "/" for c in path)),
        "num_slashes": float(path.count("/")),
        "num_dots": float(path.count(".")),
        "num_equals": float(path.count("=")),
        "num_quotes": float(path.count("'") + path.count('"')),
        "num_percent": float(path.count("%")),
        "num_ampersand": float(path.count("&")),
        "has_query": 1.0 if "?" in path else 0.0,
        "query_length": float(len(path.split("?", 1)[1])) if "?" in path else 0.0,
        "status_code": float(status),
        "is_2xx": 1.0 if 200 <= status < 300 else 0.0,
        "is_3xx": 1.0 if 300 <= status < 400 else 0.0,
        "is_4xx": 1.0 if 400 <= status < 500 else 0.0,
        "is_5xx": 1.0 if 500 <= status < 600 else 0.0,
        "response_size": float(size),
        "log_response_size": float(math.log1p(size)),
        "parse_error": float(parsed_log.get("parse_error", "0")),
        "method_get": 1.0 if method == "GET" else 0.0,
        "method_post": 1.0 if method == "POST" else 0.0,
        "method_put": 1.0 if method == "PUT" else 0.0,
        "method_delete": 1.0 if method == "DELETE" else 0.0,
        "path_entropy": float(entropy(path)),
        "contains_script": 1.0 if "<script" in path else 0.0,
        "contains_sql_keyword": 1.0 if any(k in path for k in ["union", "select", "or 1=1", "drop", "--"]) else 0.0,
        "contains_traversal": 1.0 if "../" in path or "..\\" in path or "/etc/passwd" in path else 0.0,
        "contains_command": 1.0 if any(k in path for k in ["cmd=", "exec=", "rm -rf", "wget", "curl", "bash", "whoami"]) else 0.0,
        "contains_ssrf": 1.0 if any(k in path for k in ["url=http", "169.254.169.254", "localhost", "127.0.0.1"]) else 0.0,
        "contains_log4shell": 1.0 if "${jndi:" in path or "ldap://" in path else 0.0,
        "contains_sensitive_file": 1.0 if any(k in path for k in ["/etc/passwd", "boot.ini", ".env", "id_rsa"]) else 0.0,
        "looks_like_scanner": 1.0 if any(k in path for k in ["wp-admin", "phpmyadmin", ".git", "admin", "backup"]) else 0.0,
        "suspicious_length": 1.0 if len(path) > 120 else 0.0,
        "many_special_chars": 1.0 if sum(not c.isalnum() and c != "/" for c in path) > 15 else 0.0,
    }

    return features
