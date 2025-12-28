# Makefile - Molecule Discovery System
# Docker Compose V2

.PHONY: help setup dev clean build restart logs status test db-init db-upgrade seed health verify

help:
	@echo "🚀 Molecule Discovery System"
	@echo "============================="
	@echo ""
	@echo "Quick Start:"
	@echo "  make setup          - Complete setup (first time)"
	@echo "  make dev            - Start all services"
	@echo "  make test           - Run all tests"
	@echo ""
	@echo "Development:"
	@echo "  make dev            - Start all services"
	@echo "  make dev-backend    - Start backend only"
	@echo "  make build          - Rebuild images"
	@echo "  make rebuild        - Rebuild and restart"
	@echo "  make restart        - Restart services"
	@echo "  make clean          - Stop and remove containers"
	@echo ""
	@echo "Database:"
	@echo "  make db-init        - Initialize database"
	@echo "  make db-upgrade     - Apply migrations"
	@echo "  make db-migrate     - Create migration (msg='...')"
	@echo "  make seed           - Generate seed data"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run all tests in Docker"
	@echo "  make test-backend   - Run backend tests"
	@echo "  make test-integration - Run integration tests"
	@echo "  make test-cov       - Run tests with coverage"
	@echo ""
	@echo "Logs & Status:"
	@echo "  make logs           - View all logs"
	@echo "  make logs-backend   - Backend logs"
	@echo "  make status         - Check services status"
	@echo "  make health         - Health check"
	@echo ""
	@echo "Shell Access:"
	@echo "  make shell-backend  - Backend shell"
	@echo "  make shell-db       - PostgreSQL shell"
	@echo ""

# ========================================
# SETUP & DEVELOPMENT
# ========================================

setup:
	@echo "🚀 Setting up Molecule Discovery System..."
	@docker compose up -d --build
	@echo "⏳ Waiting for services..."
	@sleep 10
	@echo "📦 Initializing database..."
	@docker compose exec -T backend python scripts/init_db.py
	@echo "🔄 Stamping migrations..."
	@docker compose exec -T backend alembic stamp head
	@echo "🌱 Generating seed data..."
	@docker compose exec -T backend python scripts/seed_molecules.py
	@echo ""
	@echo "✅ Setup complete!"
	@echo ""
	@echo "🌐 Services:"
	@echo "   Backend:  http://localhost:8000"
	@echo "   API Docs: http://localhost:8000/docs"

dev:
	@echo "🚀 Starting all services..."
	@docker compose up -d
	@sleep 3
	@docker compose ps
	@echo ""
	@echo "✅ Services running!"
	@echo "   Backend:  http://localhost:8000"
	@echo "   API Docs: http://localhost:8000/docs"

dev-backend:
	@echo "🚀 Starting backend services..."
	@docker compose up -d postgres redis backend celery_worker tests

build:
	@echo "🔨 Building images..."
	@docker compose build

rebuild:
	@echo "🔨 Rebuilding and restarting..."
	@docker compose up -d --build
	@sleep 5
	@docker compose ps

restart:
	@echo "🔄 Restarting services..."
	@docker compose restart
	@docker compose ps

clean:
	@echo "🧹 Stopping and removing containers..."
	@docker compose down -v
	@echo "✅ Cleaned!"

# ========================================
# DATABASE
# ========================================

db-init:
	@echo "📦 Initializing database..."
	@docker compose up -d postgres backend
	@sleep 3
	@docker compose exec -T backend python scripts/init_db.py

db-upgrade:
	@echo "🔄 Applying migrations..."
	@docker compose exec -T backend alembic upgrade head

db-migrate:
	@test -n "$(msg)" || (echo "❌ Usage: make db-migrate msg='description'" && exit 1)
	@docker compose exec -T backend alembic revision --autogenerate -m "$(msg)"

seed:
	@echo "🌱 Generating seed data..."
	@docker compose exec -T backend python scripts/seed_molecules.py

# ========================================
# TESTING
# ========================================

test:
	@echo "🧪 Running all tests..."
	@docker compose up -d tests
	@sleep 2
	@docker compose exec -T tests python -m pytest tests/ -v

test-integration:
	@echo "🧪 Running integration tests..."
	@docker compose up -d tests
	@sleep 2
	@docker compose exec -T tests python -m pytest tests/integration/ -v

test-cov:
	@echo "🧪 Running tests with coverage..."
	@docker compose up -d tests
	@sleep 2
	@docker compose exec -T tests python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html -v

# ========================================
# LOGS & STATUS
# ========================================

logs:
	@docker compose logs -f

logs-backend:
	@docker compose logs -f backend

logs-worker:
	@docker compose logs -f celery_worker

status:
	@docker compose ps

health:
	@echo "🏥 Health Check:"
	@docker compose ps
	@echo ""
	@docker compose exec postgres pg_isready -U moldb || echo "❌ PostgreSQL"
	@docker compose exec redis redis-cli ping || echo "❌ Redis"
	@curl -s http://localhost:8000/docs > /dev/null && echo "✅ Backend API" || echo "❌ Backend API"

# ========================================
# SHELL ACCESS
# ========================================

shell-backend:
	@docker compose exec backend /bin/bash

shell-db:
	@docker compose exec postgres psql -U moldb -d molecule_discovery

# ========================================
# UTILITIES
# ========================================

verify:
	@echo "✅ Verifying setup..."
	@docker compose ps
	@docker compose exec postgres psql -U moldb -d molecule_discovery -c '\dt'

reset:
	@echo "⚠️  Complete reset!"
	@read -p "Continue? (yes/no): " confirm && [ "$$confirm" = "yes" ] || exit 1
	@make clean
	@make setup