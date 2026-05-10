# AI Threat Detection Platform

A real-time AI-powered cybersecurity platform that analyzes nginx access logs, detects malicious HTTP behavior, evaluates model performance, and provides a secure dashboard protected by JWT authentication and cross-device biometric QR login using WebAuthn/passkeys.

This project simulates a lightweight SOC/SIEM-style platform for web application security monitoring.

---

## Overview

The platform monitors nginx-style access logs and detects suspicious HTTP requests using a hybrid security engine:

- Rule-based detection for known attack patterns
- Machine learning classification
- Anomaly detection
- ONNX Runtime inference
- PostgreSQL event and alert storage
- Redis-backed temporary authentication sessions
- Real-time WebSocket alerts
- Security evaluation metrics and graphs
- Secure QR login using WebAuthn/passkeys
- iPhone Face ID and Android fingerprint support through passkeys

The project demonstrates both attack detection and secure dashboard access control.

---

## What the Platform Protects

The platform is designed to monitor web applications and APIs placed behind nginx.

    User / Attacker
          |
          v
    HTTP Request
          |
          v
    nginx access.log
          |
          v
    AI Threat Detection Platform
          |
          v
    Alert / Event / Dashboard

The system does not replace nginx. It analyzes nginx logs to detect attacks targeting the backend application.

---

## Main Features

### Threat Detection

- Real-time nginx log analysis
- Rule-based detection
- Machine learning detection
- Anomaly detection
- ONNX inference
- Threat scoring
- Severity classification
- Persistent event storage
- Persistent alert storage
- Live dashboard updates

### Supported Attack Types

- SQL Injection
- Cross-Site Scripting
- Path Traversal
- Command Injection
- SSRF
- Log4Shell
- Suspicious payloads
- Encoded payloads
- Noisy abnormal requests
- ML anomaly detection

### Dashboard

- JWT login
- QR login
- WebAuthn/passkey login
- iPhone Face ID support
- Android fingerprint / screen-lock support
- Real-time WebSocket alerts
- Recent threats
- Recent events
- Model status
- Security metrics
- Confusion matrix
- ROC curve
- Precision-Recall curve
- FAR / FRR / EER curve
- Attack simulation page

### Infrastructure

- FastAPI backend
- React + Vite frontend
- nginx reverse proxy
- PostgreSQL database
- Redis session storage
- Docker Compose deployment
- Prometheus-compatible /metrics endpoint
- ngrok support for HTTPS mobile testing

---

## QR + WebAuthn Biometric Login

The platform supports secure cross-device login.

A user opens the QR login page on a desktop browser, scans the QR code with a smartphone, verifies identity using Face ID, fingerprint, or a passkey, and the desktop browser automatically receives a JWT and redirects to the dashboard.

Authentication flow:

    Desktop opens /login-qr
            |
            v
    FastAPI creates temporary QR session in Redis
            |
            v
    React displays QR code
            |
            v
    Phone scans QR code
            |
            v
    Mobile browser opens /mobile-login/{session_id}
            |
            v
    Phone triggers WebAuthn / passkey authentication
            |
            v
    Face ID / fingerprint verification happens locally on the phone
            |
            v
    Registered passkey signs a cryptographic challenge
            |
            v
    Backend verifies the signature using the stored public key
            |
            v
    Backend creates JWT for user iheb
            |
            v
    Desktop receives token and redirects to dashboard

### Important Security Clarification

The server does not store biometric data.

Face ID or fingerprint verification happens locally on the registered phone. During passkey registration, the backend stores only the credential ID and public key. During login, only the matching registered passkey can sign the WebAuthn challenge.

This means another person cannot simply scan the QR code and log in with their own face or their own phone. Their phone does not have the registered private key, so the backend rejects the authentication.

---

## Tech Stack

### Backend

- Python
- FastAPI
- python-jose JWT
- py_webauthn / webauthn
- scikit-learn
- ONNX Runtime
- PostgreSQL
- Redis

### Frontend

- React
- Vite
- Axios
- react-qr-code
- @simplewebauthn/browser
- nginx

### Infrastructure

- Docker
- Docker Compose
- nginx
- Prometheus
- Grafana
- ngrok

---

## Project Structure

    ai-threat-detection/
    ├── backend/
    │   ├── app/
    │   │   ├── main.py
    │   │   ├── auth.py
    │   │   ├── qr_auth.py
    │   │   ├── qr_ws.py
    │   │   ├── webauthn_auth.py
    │   │   ├── detector.py
    │   │   ├── security.py
    │   │   ├── redis_client.py
    │   │   └── ...
    │   └── requirements.txt
    ├── frontend/
    │   ├── src/
    │   │   ├── App.jsx
    │   │   ├── LoginQR.jsx
    │   │   ├── MobileLogin.jsx
    │   │   ├── RegisterPasskey.jsx
    │   │   └── ...
    │   ├── nginx.conf
    │   └── package.json
    ├── models/
    ├── reports/
    ├── data/
    ├── docker-compose.yml
    ├── prometheus.yml
    ├── .env.example
    └── README.md

---

## Environment Setup

Create a local .env file:

    cp .env.example .env

Example .env values:

    API_KEY=change-me
    JWT_SECRET=change-me
    DATABASE_URL=postgresql://threat_user:threat_pass@postgres:5432/threat_db
    REDIS_URL=redis://redis:6379/0
    ALERT_CHANNEL=ai-threat-alerts
    LOG_TAIL_ENABLED=true
    LOG_FILE_PATH=/logs/access.log
    RATE_LIMIT=100/minute

    PUBLIC_FRONTEND_URL=http://127.0.0.1:3000
    QR_SESSION_TTL=120

    WEBAUTHN_RP_ID=your-domain.ngrok-free.dev
    WEBAUTHN_EXPECTED_ORIGIN=https://your-domain.ngrok-free.dev
    WEBAUTHN_RP_NAME=AI Threat Detection Platform
    WEBAUTHN_DEMO_USER_ID=iheb-demo-user
    WEBAUTHN_DEMO_USERNAME=iheb

Never commit .env.

---

## Running the Project Locally

Start the full stack:

    docker compose up -d --build

Check containers:

    docker compose ps

Backend API:

    http://127.0.0.1:8000

Frontend dashboard:

    http://127.0.0.1:3000

Attack simulation page:

    http://127.0.0.1:3000/attacks

QR login page:

    http://127.0.0.1:3000/login-qr

Passkey registration page:

    http://127.0.0.1:3000/register-passkey

---

## Default Credentials

    Username: iheb
    Password: iheb

After successful login, the JWT is stored in browser local storage as:

    jwt_token

---

## Using QR + Face ID Login with ngrok

WebAuthn/passkeys require HTTPS. For real mobile testing, expose the frontend through ngrok.

### 1. Start Docker

    docker compose up -d --build

### 2. Start ngrok

    ngrok http 3000

or:

    /usr/local/bin/ngrok http 3000

You will receive a public HTTPS URL such as:

    https://your-domain.ngrok-free.dev

### 3. Update .env

Set the WebAuthn values to match your current ngrok domain:

    WEBAUTHN_RP_ID=your-domain.ngrok-free.dev
    WEBAUTHN_EXPECTED_ORIGIN=https://your-domain.ngrok-free.dev
    WEBAUTHN_RP_NAME=AI Threat Detection Platform
    WEBAUTHN_DEMO_USER_ID=iheb-demo-user
    WEBAUTHN_DEMO_USERNAME=iheb

Restart the backend:

    docker compose up -d --build backend

### 4. Verify WebAuthn Configuration

    curl https://your-domain.ngrok-free.dev/api/auth/webauthn/debug

Expected example:

    {
      "rp_id": "your-domain.ngrok-free.dev",
      "rp_name": "AI Threat Detection Platform",
      "expected_origin": "https://your-domain.ngrok-free.dev",
      "demo_username": "iheb",
      "has_registered_credential": false
    }

### 5. Register the Phone Passkey

Open on the phone:

    https://your-domain.ngrok-free.dev/register-passkey

Tap:

    Register this phone

The phone should trigger Face ID, fingerprint, or screen-lock passkey creation.

After successful registration, check again:

    curl https://your-domain.ngrok-free.dev/api/auth/webauthn/debug

Expected:

    "has_registered_credential": true

### 6. Login with QR + Face ID

Open on desktop:

    https://your-domain.ngrok-free.dev/login-qr

Then:

1. Scan the QR code with the registered phone.
2. Open the mobile authentication page.
3. Tap Verify with Face ID / Passkey.
4. Approve with Face ID, fingerprint, or screen lock.
5. The desktop browser receives the JWT and redirects to the dashboard.

---

## API Endpoints

Public:

    GET  /
    GET  /health
    GET  /metrics

Authentication:

    POST /auth/login
    POST /auth/qr/start
    GET  /auth/qr/status/{session_id}
    WS   /auth/qr/ws/{session_id}

WebAuthn / Passkeys:

    GET  /auth/webauthn/debug
    POST /auth/webauthn/register/options
    POST /auth/webauthn/register/verify
    POST /auth/webauthn/login/options/{session_id}
    POST /auth/webauthn/login/verify/{session_id}

Detection:

    POST /analyze
    POST /ingest/batch
    POST /pipeline/ingest
    GET  /pipeline/status

Dashboard data:

    GET /stats
    GET /events
    GET /threats
    GET /alerts
    GET /models/status
    GET /models/security-metrics
    GET /models/metrics-graphs

WebSocket:

    WS /ws/alerts

---

## Prometheus Metrics

The backend exposes a lightweight Prometheus-compatible endpoint:

    curl http://127.0.0.1:8000/metrics

Example output:

    # HELP ai_threat_up AI Threat Detection backend status
    # TYPE ai_threat_up gauge
    ai_threat_up 1

---

## Demo Workflow

### Standard Login

1. Start the Docker stack.
2. Open the dashboard.
3. Login with iheb / iheb.
4. Open the attack simulation page.
5. Trigger an attack.
6. Watch dashboard alerts update in real time.

### Biometric QR Login

1. Start Docker.
2. Start ngrok.
3. Update .env with the ngrok WebAuthn origin.
4. Register the phone passkey from /register-passkey.
5. Open /login-qr on desktop.
6. Scan QR with the registered phone.
7. Approve with Face ID / passkey.
8. Desktop redirects automatically to the dashboard.

---

## Detection Engine

The detection engine uses a hybrid approach.

Rule-based detection identifies known attack patterns such as SQL keywords, script tags, path traversal, SSRF indicators, Log4Shell payloads, and suspicious command patterns.

The ML layer combines:

- Random Forest for supervised classification
- Isolation Forest for anomaly detection
- Autoencoder for reconstruction-based anomaly scoring
- ONNX Runtime for portable inference

Examples of extracted features:

- Path length
- Number of digits
- Number of special characters
- Query length
- HTTP status code
- Response size
- Path entropy
- SQL keyword presence
- Script tag presence
- SSRF indicator
- Log4Shell indicator

---

## Security Evaluation

The system evaluates itself using labeled data and model predictions.

Displayed metrics include:

- FAR: False Acceptance Rate
- FRR: False Rejection Rate
- EER: Equal Error Rate
- Precision
- Recall
- F1-score
- ROC-AUC
- PR-AUC
- TP, FP, FN, TN confusion matrix values

The dashboard also displays generated graphs:

- ROC Curve
- Precision-Recall Curve
- FAR / FRR / EER Curve

---

## Security Notes

- The platform does not store Face ID, fingerprint, or biometric images.
- Biometric verification happens locally on the registered phone.
- The backend stores only a passkey credential ID and public key.
- Only the matching registered passkey can approve the WebAuthn challenge.
- Another phone or another person's face cannot approve the login.
- QR login sessions are temporary.
- QR sessions are stored in Redis.
- QR sessions expire automatically.
- A QR session can only be used once.
- The desktop receives the JWT only after successful WebAuthn verification.
- .env must never be committed.

---

## Useful Commands

Start stack:

    docker compose up -d --build

Stop stack:

    docker compose down

View backend logs:

    docker compose logs backend --tail=100

Test backend health:

    curl http://127.0.0.1:8000/health

Test Prometheus metrics:

    curl http://127.0.0.1:8000/metrics

Create QR session:

    curl -X POST http://127.0.0.1:3000/api/auth/qr/start

Check WebAuthn config:

    curl https://your-domain.ngrok-free.dev/api/auth/webauthn/debug

Check latest commits:

    git log --oneline -5

---

## Future Improvements

- Store WebAuthn credentials in PostgreSQL instead of Redis
- Add multi-user passkey registration
- Add device management page
- Add user roles and RBAC
- Add richer Prometheus metrics
- Add Grafana dashboards
- Add Slack, Discord, or email alert notifications
- Add Kafka for scalable streaming
- Add Kubernetes deployment
- Add CI/CD deployment pipeline

---

## Author

Iheb Mrabet

---

## Note

This project is a realistic simulation environment for learning, demonstration, and portfolio purposes.

It can be extended to monitor real nginx logs from production applications.
