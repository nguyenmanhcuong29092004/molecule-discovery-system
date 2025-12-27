.PHONY: help dev test clean

help:
	@echo "Available commands:"
	@echo "  make dev          - Start all services"
	@echo "  make dev-backend  - Start only backend"
	@echo "  make dev-frontend - Start only frontend"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Stop and remove containers"
	@echo "  make logs         - Show logs"

dev:
	docker-compose up -d
	@echo "✅ Services started!"
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "API Docs: http://localhost:8000/docs"

dev-backend:
	docker-compose up -d postgres redis backend celery_worker

dev-frontend:
	cd frontend && npm run dev

logs:
	docker-compose logs -f

test:
	cd backend && pytest tests/ -v
	cd frontend && npm run test

clean:
	docker-compose down -v

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install