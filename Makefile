.PHONY: help install dev start stop restart clean test lint format docker-build docker-run

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make dev          - Run server in development mode with auto-reload"
	@echo "  make start        - Start server in background"
	@echo "  make stop         - Stop running server"
	@echo "  make restart      - Restart server"
	@echo "  make clean        - Clean up temporary files"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run in Docker"

install:
	python3 -m venv venv
	./venv/bin/pip install -r requirements.txt
	@echo "✓ Dependencies installed. Activate with: source venv/bin/activate"

dev:
	@echo "Starting server in development mode..."
	./venv/bin/uvicorn server:app --reload --host 0.0.0.0 --port ${PORT:-8000}

start:
	@echo "Starting server in background..."
	@./scripts/start.sh

stop:
	@echo "Stopping server..."
	@./scripts/stop.sh

restart: stop
	@sleep 2
	@make start

clean:
	@echo "Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf .pytest_cache htmlcov .coverage
	@echo "✓ Cleaned up temporary files"

test:
	@echo "Running tests..."
	./venv/bin/pytest tests/ -v

lint:
	@echo "Running linters..."
	./venv/bin/ruff check . || true
	./venv/bin/mypy server.py || true

format:
	@echo "Formatting code..."
	./venv/bin/black .
	./venv/bin/ruff check --fix .

docker-build:
	@echo "Building Docker image..."
	docker build -t elevenlabs-openai-proxy .

docker-run:
	@echo "Running in Docker..."
	docker run -p 8000:8000 --env-file .env elevenlabs-openai-proxy
