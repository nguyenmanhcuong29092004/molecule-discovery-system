# Makefile for Docker Compose V2
# Project: Molecule Discovery System

.PHONY: help up down build restart logs status shell-backend shell-db db-init db-upgrade db-migrate seed test clean

help:
	@echo "🚀 Molecule Discovery System - Docker Compose V2"
	@echo "================================================"
	@echo ""
	@echo "SETUP (Lần đầu):"
	@echo "  make setup          - Build + Start + Initialize database"
	@echo ""
	@echo "Development:"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make build          - Rebuild images"
	@echo "  make logs           - View all logs"
	@echo "  make status         - Check services status"
	@echo ""
	@echo "Database:"
	@echo "  make db-init        - Initialize database"
	@echo "  make db-upgrade     - Apply migrations"
	@echo "  make db-migrate     - Create migration (msg='description')"
	@echo "  make seed           - Generate seed data"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run all tests"
	@echo "  make test-cov       - Run tests with coverage"
	@echo ""
	@echo "Shell Access:"
	@echo "  make shell-backend  - Backend shell"
	@echo "  make shell-db       - PostgreSQL shell"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          - Stop and remove volumes"
	@echo "  make reset          - Complete reset"
	@echo ""

# Setup (Lần đầu tiên)
setup:
	@echo "🚀 Setting up Molecule Discovery System..."
	@docker compose up -d --build
	@echo "⏳ Waiting for services to be ready..."
	@sleep 10
	@echo "📦 Initializing database..."
	@docker compose exec -T backend python scripts/init_db.py
	@echo "🔄 Applying migrations..."
	@docker compose exec -T backend alembic upgrade head
	@echo "🌱 Generating seed data..."
	@docker compose exec -T backend python scripts/seed_molecules.py
	@echo ""
	@echo "✅ Setup complete!"
	@echo "🌐 API Docs: http://localhost:8000/docs"
	@echo ""

# Start services
up:
	@echo "🚀 Starting services..."
	@docker compose up -d
	@sleep 5
	@docker compose ps

# Stop services
down:
	@echo "🛑 Stopping services..."
	@docker compose down

# Restart services
restart:
	@echo "🔄 Restarting services..."
	@docker compose restart
	@docker compose ps

# Rebuild images
build:
	@echo "🔨 Building images..."
	@docker compose build

# Rebuild and start
rebuild:
	@echo "🔨 Rebuilding and starting..."
	@docker compose up -d --build
	@sleep 5
	@docker compose ps

# View logs
logs:
	@docker compose logs -f

logs-backend:
	@docker compose logs -f backend

logs-postgres:
	@docker compose logs -f postgres

logs-worker:
	@docker compose logs -f celery_worker

# Check status
status:
	@docker compose ps

# Database operations
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

# Testing
test:
	@echo "🧪 Running tests..."
	@docker compose up -d tests
	@sleep 2
	@docker compose exec -T tests python -m pytest tests/ -v

test-unit-chemistry:
	@echo "🧪 Running tests..."
	@docker compose up -d tests
	@sleep 2
	@docker compose exec -T tests python -m pytest tests/unit/test_chemistry.py -v

test-cov:
	@echo "🧪 Running tests with coverage..."
	@docker compose up -d tests
	@sleep 2
	@docker compose exec -T tests python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

test-integration:
	@echo "🧪 Running integration tests..."
	@docker compose up -d tests
	@sleep 2
	@docker compose exec -T tests python -m pytest tests/integration/ -v

test-integration-database:
	@echo "🧪 Running integration tests..."
	@docker compose up -d tests
	@sleep 2
	@docker compose exec -T tests python -m pytest tests/integration/test_database.py -v

test-integration-api-runs:
	@echo "🧪 Running integration tests..."
	@docker compose up -d tests
	@sleep 2
	@docker compose exec -T tests python -m pytest tests/integration/test_database.py -v

test-unit:
	@echo "🧪 Running unit tests..."
	@docker compose exec -T tests pytest tests/unit/ -v

test-unit-chemistry:
	@echo "🧪 Running unit tests..."
	@docker compose exec -T tests pytest tests/unit/test_chemistry.py -v

test-unit-agents:
	@echo "🧪 Running unit tests..."
	@docker compose exec -T tests pytest tests/unit/test_agents.py -v
	
# Shell access
shell-backend:
	@docker compose exec backend /bin/bash

shell-db:
	@docker compose exec postgres psql -U moldb -d molecule_discovery

shell-redis:
	@docker compose exec redis redis-cli

# Code quality
format:
	@echo "🎨 Formatting code..."
	@docker compose exec -T backend black app/ tests/ scripts/

lint:
	@echo "🔍 Linting code..."
	@docker compose exec -T backend ruff check app/ tests/ scripts/

# Cleanup
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
	@docker compose exec -T backend alembic upgrade head
	@docker compose exec -T backend python scripts/seed_molecules.py
	@echo "✅ Reset complete!"

# Health check
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
	@echo "Backend API:"
	@curl -s http://localhost:8000/docs > /dev/null && echo "✅ Responding" || echo "❌ Not responding"

# Verify setup
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