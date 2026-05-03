import re
from typing import Dict


LOG_PATTERN = re.compile(
    r'(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] '
    r'"(?P<request>[^"]+)" '
    r'(?P<status>\d+) (?P<size>\d+)'
)


def parse_nginx_log(log_line: str) -> Dict[str, str]:
    match = LOG_PATTERN.match(log_line)

    if not match:
        return {
            "ip": "unknown",
            "time": "unknown",
            "method": "UNKNOWN",
            "path": log_line,
            "protocol": "unknown",
            "status": "0",
            "size": "0",
            "parse_error": "1"
        }

    data = match.groupdict()
    request = data.get("request", "")
    parts = request.split(" ")

    if len(parts) >= 3:
        method = parts[0]
        protocol = parts[-1]
        path = " ".join(parts[1:-1])
    elif len(parts) == 2:
        method = parts[0]
        path = parts[1]
        protocol = "unknown"
    else:
        method = "UNKNOWN"
        path = request
        protocol = "unknown"

    return {
        "ip": data["ip"],
        "time": data["time"],
        "method": method,
        "path": path,
        "protocol": protocol,
        "status": data["status"],
        "size": data["size"],
        "parse_error": "0"
    }
