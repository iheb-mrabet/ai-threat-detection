# AI Threat Detection Platform

A real-time web threat detection system that analyzes nginx access logs and detects malicious HTTP behavior using both rule-based logic and machine learning.

The project simulates how a security monitoring platform can protect web applications and APIs by observing incoming traffic, detecting attacks, storing events, and showing live alerts in a dashboard.

## What is being protected?

The system is designed to protect web applications and APIs exposed over HTTP.

In practice, it monitors nginx access logs. These logs represent requests reaching a backend service such as Flask, Django, Node.js, or any API.

Protection model:

User / Attacker -> HTTP Request -> nginx -> Detection System -> Application

The system does not replace nginx. It analyzes nginx logs to detect attacks targeting the application behind it.

## Main Features

- Real-time nginx log analysis
- Hybrid detection using rules and machine learning
- SQL Injection detection
- XSS detection
- Path Traversal detection
- Command Injection detection
- SSRF detection
- Log4Shell detection
- Noisy and encoded payload detection
- WebSocket live alerts
- PostgreSQL event storage
- Redis pub/sub streaming
- React dashboard
- Separate attack simulation page
- JWT login authentication
- API key support
- FAR, FRR, EER security metrics
- ROC, Precision-Recall, and FAR/FRR/EER graphs
- Docker Compose deployment

## Detection Engine

The detection engine combines several methods:

- Rule-based detection for known attack signatures
- Random Forest for supervised classification
- Isolation Forest for anomaly detection
- Autoencoder exported to ONNX for anomaly scoring

Each request is converted into numerical features before being analyzed.

Examples of extracted features:

- Path length
- Number of special characters
- Query length
- HTTP status code
- Response size
- Path entropy
- SQL keyword presence
- Script tag presence
- SSRF indicator
- Log4Shell indicator

## Security Evaluation

The system evaluates itself using labeled data and real model predictions.

The dashboard displays:

- FAR: False Acceptance Rate
- FRR: False Rejection Rate
- EER: Equal Error Rate
- Precision
- Recall
- F1-score
- ROC-AUC
- PR-AUC
- Confusion matrix

These values are calculated from TP, TN, FP, and FN. They are not hardcoded.

The dashboard also displays generated evaluation graphs:

- ROC Curve
- Precision-Recall Curve
- FAR / FRR / EER Curve

## Architecture

nginx access logs  
-> parser  
-> feature extraction  
-> rules + ML ensemble  
-> PostgreSQL + Redis  
-> FastAPI backend  
-> WebSocket  
-> React dashboard  

## Tech Stack

Backend:

- FastAPI
- Python
- scikit-learn
- ONNX Runtime

Frontend:

- React
- Vite
- Nginx

Infrastructure:

- PostgreSQL
- Redis
- Docker Compose

## Authentication

The platform includes JWT login authentication and API key support.

Default login:

Username: iheb  
Password: iheb  

After login, the dashboard uses a JWT token to access protected backend endpoints.

## Running the Project

Start the full stack with:

`docker compose up --build`

Dashboard: http://127.0.0.1:3000

Attack simulation page: http://127.0.0.1:3000/attacks

API: http://127.0.0.1:8000

## Demo Workflow

1. Start the Docker stack.
2. Open the dashboard.
3. Login with the default credentials.
4. Open the attack simulation page.
5. Trigger attacks such as SQL Injection, XSS, SSRF, Log4Shell, noise, or encoded payloads.
6. Watch the dashboard update in real time.
7. Review alerts, metrics, confusion matrix, and evaluation graphs.

## Author

Iheb Mrabet

## Note

This project is a realistic simulation environment for learning, demonstration, and portfolio purposes. It can be extended to monitor real nginx logs from production applications.
