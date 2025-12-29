# Makefile for Docker Compose V2
# Project: Molecule Discovery System

.PHONY: help install up down build restart logs status shell-backend shell-db db-init db-upgrade db-migrate seed test clean worker

help:
	@echo "🚀 Molecule Discovery System - Docker Compose V2"
	@echo "================================================"
	@echo ""
	@echo "SETUP (Lần đầu):"
	@echo "  make setup          - Build + Start + Initialize database"
	@echo "  make install        - Install/update dependencies in container"
	@echo ""
	@echo "Development:"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make build          - Rebuild images"
	@echo "  make logs           - View all logs"
	@echo "  make status         - Check services status"
	@echo ""
	@echo "Celery Workflow:"
	@echo "  make worker         - View Celery worker logs"
	@echo "  make worker-restart - Restart Celery worker"
	@echo "  make demo-workflow  - Run workflow demo script"
	@echo ""
	@echo "Database:"
	@echo "  make db-init        - Initialize database"
	@echo "  make db-upgrade     - Apply migrations"
	@echo "  make db-migrate     - Create migration (msg='description')"
	@echo "  make seed           - Generate seed data"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run all tests"
	@echo "  make test-unit      - Run all unit tests"
	@echo "  make test-integration - Run all integration tests"
	@echo "  make test-workflow  - Run workflow tests"
	@echo "  make test-cov       - Run tests with coverage"
	@echo ""
	@echo "Shell Access:"
	@echo "  make shell-backend  - Backend shell"
	@echo "  make shell-db       - PostgreSQL shell"
	@echo "  make shell-redis    - Redis CLI"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          - Stop and remove volumes"
	@echo "  make reset          - Complete reset"
	@echo ""

# ========================================
# SETUP
# ========================================

setup:
	@echo "🚀 Setting up Molecule Discovery System..."
	@docker compose up -d --build
	@echo "⏳ Waiting for services to be ready..."
	@sleep 10
	@echo "📦 Initializing database..."
	@docker compose exec -T backend python scripts/init_db.py
	@echo "🔄 Stamping migrations..."
	@docker compose exec -T backend alembic stamp head
	@echo "🌱 Generating seed data..."
	@docker compose exec -T backend python scripts/seed_molecules.py
	@echo ""
	@echo "✅ Setup complete!"
	@echo "🌐 API Docs: http://localhost:8000/docs"
	@echo "⚙️  Celery Worker: make worker"
	@echo ""

install:
	@echo "📦 Installing/updating dependencies in container..."
	@docker compose exec -T backend pip install --no-cache-dir -r requirements.txt
	@echo "✅ Dependencies installed!"

# ========================================
# DEVELOPMENT
# ========================================

up:
	@echo "🚀 Starting services..."
	@docker compose up -d
	@sleep 5
	@docker compose ps

down:
	@echo "🛑 Stopping services..."
	@docker compose down

restart:
	@echo "🔄 Restarting services..."
	@docker compose restart
	@docker compose ps

build:
	@echo "🔨 Building images..."
	@docker compose build

rebuild:
	@echo "🔨 Rebuilding and starting..."
	@docker compose up -d --build
	@sleep 5
	@docker compose ps

# ========================================
# CELERY WORKFLOW
# ========================================

worker:
	@echo "📊 Celery Worker Logs (Ctrl+C to exit)..."
	@docker compose logs -f celery_worker

worker-restart:
	@echo "🔄 Restarting Celery worker..."
	@docker compose restart celery_worker
	@sleep 2
	@docker compose logs --tail=50 celery_worker

demo-workflow:
	@echo "🎬 Running workflow demo..."
	@docker compose exec -T backend python scripts/workflow_demo.py

# ========================================
# LOGS
# ========================================

logs:
	@docker compose logs -f

logs-backend:
	@docker compose logs -f backend

logs-postgres:
	@docker compose logs -f postgres

logs-redis:
	@docker compose logs -f redis

logs-worker:
	@docker compose logs -f celery_worker

status:
	@docker compose ps

# ========================================
# DATABASE
# ========================================

db-init:
	@echo "📦 Initializing database..."
	@docker compose exec -T backend python scripts/init_db.py

db-upgrade:
	@echo "🔄 Applying migrations..."
	@docker compose exec -T backend alembic upgrade head

db-migrate:
	@test -n "$(msg)" || (echo "❌ Usage: make db-migrate msg='description'" && exit 1)
	@echo "📝 Creating migration: $(msg)"
	@docker compose exec -T backend alembic revision --autogenerate -m "$(msg)"

db-downgrade:
	@echo "⏪ Rolling back migration..."
	@docker compose exec -T backend alembic downgrade -1

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
	@docker compose exec -T tests python -m pytest tests/unit/test_chemistry.py -v
	@docker compose exec -T tests python -m pytest tests/unit/test_agents.py -v
	@docker compose exec -T tests python -m pytest tests/integration/test_database.py -v
	@docker compose exec -T tests python -m pytest tests/integration/test_api_runs.py -v
	@docker compose exec -T tests python -m pytest tests/integration/test_api_celery.py -v
	@docker compose exec -T tests python -m pytest tests/integration/test_api_results.py -v
	@docker compose exec -T tests python -m pytest tests/integration/test_workflow.py -v

test-unit:
	@echo "🧪 Running unit tests..."
	@docker compose up -d tests
	@sleep 2
	@docker compose exec -T tests python -m pytest tests/unit/test_chemistry.py -v
	@docker compose exec -T tests python -m pytest tests/unit/test_agents.py -v

test-unit-chemistry:
	@echo "🧪 Running chemistry tests..."
	@docker compose up -d tests
	@sleep 2
	@docker compose exec -T tests python -m pytest tests/unit/test_chemistry.py -v

test-unit-agents:
	@echo "🧪 Running agents tests..."
	@docker compose up -d tests
	@sleep 2
	@docker compose exec -T tests python -m pytest tests/unit/test_agents.py -v


test-integration:
	@echo "🧪 Running integration tests..."
	@docker compose up -d tests
	@sleep 2
	@docker compose exec -T tests python -m pytest tests/integration/test_database.py -v
	@docker compose exec -T tests python -m pytest tests/integration/test_api_runs.py -v
	@docker compose exec -T tests python -m pytest tests/integration/test_api_celery.py -v
	@docker compose exec -T tests python -m pytest tests/integration/test_api_results.py -v
	@docker compose exec -T tests python -m pytest tests/integration/test_workflow.py -v

test-integration-database:
	@echo "🧪 Running database tests..."
	@docker compose up -d tests
	@sleep 2
	@docker compose exec -T tests python -m pytest tests/integration/test_database.py -v

test-integration-api:
	@echo "🧪 Running API tests..."
	@docker compose up -d tests
	@sleep 2
	@docker compose exec -T tests python -m pytest tests/integration/test_api_runs.py -v

test-integration-api-celery:
	@echo "🧪 Running API tests..."
	@docker compose up -d tests
	@sleep 2
	@docker compose exec -T tests python -m pytest tests/integration/test_api_celery.py -v

test-integration-api-results:
	@echo "🧪 Running API tests..."
	@docker compose up -d tests
	@sleep 2
	@docker compose exec -T tests python -m pytest tests/integration/test_api_results.py -v

test-integration-workflow:
	@echo "🧪 Running workflow tests..."
	@docker compose up -d tests celery_worker
	@sleep 3
	@docker compose exec -T tests python -m pytest tests/integration/test_workflow.py -v

test-cov:
	@echo "🧪 Running tests with coverage..."
	@docker compose up -d tests
	@sleep 2
	@docker compose exec -T tests python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html
	@echo "📊 Coverage report: backend/htmlcov/index.html"

# ========================================
# SHELL ACCESS
# ========================================

shell-backend:
	@docker compose exec backend /bin/bash

shell-db:
	@docker compose exec postgres psql -U moldb -d molecule_discovery

shell-redis:
	@docker compose exec redis redis-cli

shell-worker:
	@docker compose exec celery_worker /bin/bash

# ========================================
# CODE QUALITY
# ========================================

format:
	@echo "🎨 Formatting code..."
	@docker compose exec -T backend black app/ tests/ scripts/

lint:
	@echo "🔍 Linting code..."
	@docker compose exec -T backend ruff check app/ tests/ scripts/

# ========================================
# CLEANUP
# ========================================

clean:
	@echo "🧹 Cleaning up..."
	@docker compose down -v

reset:
	@echo "⚠️  This will delete ALL data!"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ] || exit 1
	@docker compose down -v
	@docker compose up -d --build
	@sleep 10
	@docker compose exec -T backend python scripts/init_db.py
	@docker compose exec -T backend alembic stamp head
	@docker compose exec -T backend python scripts/seed_molecules.py
	@echo "✅ Reset complete!"

# ========================================
# HEALTH & VERIFICATION
# ========================================

health:
	@echo "🏥 Checking system health..."
	@echo ""
	@echo "Services:"
	@docker compose ps
	@echo ""
	@echo "PostgreSQL:"
	@docker compose exec postgres pg_isready -U moldb || echo "❌ Not ready"
	@echo ""
	@echo "Redis:"
	@docker compose exec redis redis-cli ping || echo "❌ Not ready"
	@echo ""
	@echo "Celery Worker:"
	@docker compose exec celery_worker celery -A app.celery_app inspect ping 2>/dev/null || echo "❌ Not responding"
	@echo ""
	@echo "Backend API:"
	@curl -s http://localhost:8000/docs > /dev/null && echo "✅ Responding" || echo "❌ Not responding"

verify:
	@echo "✅ Verifying setup..."
	@echo ""
	@echo "1. Services status:"
	@docker compose ps
	@echo ""
	@echo "2. Database tables:"
	@docker compose exec postgres psql -U moldb -d molecule_discovery -c '\dt'
	@echo ""
	@echo "3. API health:"
	@curl -s http://localhost:8000/docs > /dev/null && echo "   ✅ API is up" || echo "   ❌ API is down"
	@echo ""
	@echo "4. Celery worker:"
	@docker compose exec celery_worker celery -A app.celery_app inspect active 2>/dev/null && echo "   ✅ Worker active" || echo "   ❌ Worker not responding"
	@echo ""