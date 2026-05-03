from typing import List, Dict
from urllib.parse import unquote


def normalize_path(path: str) -> str:
    decoded = unquote(path).lower()
    decoded = decoded.replace("+", " ")
    return decoded


def apply_rules(parsed_log: Dict[str, str]) -> List[str]:
    path = normalize_path(parsed_log.get("path", ""))
    matched = []

    sql_patterns = [
        "' or 1=1", "\" or 1=1", "or 1=1", "union select",
        "select * from", "drop table", "information_schema",
        "--", "'--", "admin'", "sleep(", "benchmark("
    ]

    xss_patterns = [
        "<script", "</script>", "javascript:", "onerror=",
        "onload=", "alert(", "<img", "document.cookie"
    ]

    traversal_patterns = [
        "../", "..\\", "%2e%2e", "/etc/passwd", "boot.ini",
        "/proc/self/environ", "/windows/win.ini"
    ]

    command_patterns = [
        "cmd=", "exec=", "rm -rf", "wget ", "curl ",
        "/bin/bash", "powershell", "whoami", "cat /etc/passwd",
        ";id", "|id", "&&"
    ]

    ssrf_patterns = [
        "url=http://", "url=https://", "169.254.169.254",
        "localhost", "127.0.0.1", "metadata.google.internal"
    ]

    log4shell_patterns = [
        "${jndi:", "jndi:ldap", "ldap://", "rmi://"
    ]

    scanner_patterns = [
        "wp-admin", "wp-login", "phpmyadmin", ".git/config",
        ".env", "backup.zip", "admin.php"
    ]

    if any(p in path for p in sql_patterns):
        matched.append("SQL Injection")

    if any(p in path for p in xss_patterns):
        matched.append("XSS")

    if any(p in path for p in traversal_patterns):
        matched.append("Path Traversal")

    if any(p in path for p in command_patterns):
        matched.append("Command Injection")

    if any(p in path for p in ssrf_patterns):
        matched.append("SSRF")

    if any(p in path for p in log4shell_patterns):
        matched.append("Log4Shell")

    if any(p in path for p in scanner_patterns):
        matched.append("Scanner / Reconnaissance")

    return matched
