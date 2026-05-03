# AI Threat Detection Platform

Real-time nginx log threat detection platform using rules, machine learning, ONNX inference, Redis, PostgreSQL, FastAPI, React, and Docker.

## Features

- Real-time nginx log ingestion
- Rule-based detection for SQLi, XSS, path traversal, command injection, SSRF, Log4Shell, and scanners
- ML ensemble: RandomForest + IsolationForest + Autoencoder
- ONNX Runtime inference for the autoencoder
- FastAPI backend
- React dashboard
- Redis pub/sub live alert streaming
- PostgreSQL event and alert persistence
- WebSocket live alerts
- Docker Compose full-stack deployment
- API key authentication
- Rate limiting
- Structured logging
- Monitoring endpoints

## Architecture

nginx access logs
  -> log tailer
  -> async pipeline
  -> parser + feature extractor + rules + ML ensemble
  -> PostgreSQL + Redis
  -> FastAPI + WebSocket
  -> React dashboard

## Run locally with Docker

cp .env.example .env
docker compose up --build

Frontend: http://localhost:3000
Backend API: http://localhost:8000
Health: http://localhost:8000/health

## API Key

Protected endpoints require:

X-API-Key: dev-secret-key

Change the value in `.env` before deployment.

## Test with a malicious log

echo '10.0.0.5 - - [03/May/2026:10:01:00 +0100] "GET /login?user=admin OR 1=1-- HTTP/1.1" 200 900' >> dev-log/access.log

## Monitoring

curl http://localhost:8000/monitoring/health
curl -H "X-API-Key: dev-secret-key" http://localhost:8000/monitoring/metrics

## Main Stack

- FastAPI
- React + Vite
- PostgreSQL
- Redis
- Docker Compose
- scikit-learn
- ONNX Runtime

## Author

Iheb Mrabet
