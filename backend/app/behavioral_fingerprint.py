import hashlib
import math
import re


def entropy(text: str) -> float:
    if not text:
        return 0.0

    probs = [text.count(c) / len(text) for c in set(text)]
    return -sum(p * math.log2(p) for p in probs)


def extract_behavioral_fingerprint(log_line: str) -> dict:
    """
    Behavioral fingerprinting = biométrie comportementale adaptée aux logs.
    Instead of human fingerprints/face/iris, we fingerprint request behavior:
    method, path structure, suspicious symbols, entropy, query behavior.
    """

    request_match = re.search(r'"([A-Z]+)\s+([^"]+)\s+HTTP/[0-9.]+"', log_line)

    method = "UNKNOWN"
    path = ""

    if request_match:
        method = request_match.group(1)
        path = request_match.group(2)

    fingerprint_source = f"{method}|{path[:80]}|len={len(path)}|entropy={round(entropy(path), 3)}"
    fingerprint_hash = hashlib.sha256(fingerprint_source.encode()).hexdigest()[:16]

    return {
        "behavioral_fingerprint": fingerprint_hash,
        "method": method,
        "path_length": len(path),
        "path_entropy": round(entropy(path), 4),
        "has_query": "?" in path,
        "special_char_count": sum(1 for c in path if not c.isalnum() and c not in "/_-?.=&"),
        "fingerprint_explanation": "Behavioral biometric-style fingerprint extracted from request behavior, not from human biometrics."
    }
