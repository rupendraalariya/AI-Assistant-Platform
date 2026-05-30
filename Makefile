.PHONY: help install dev test lint build docker-up docker-down clean

help: ## Show this help message
	@echo Available commands:
	@echo   install     - Install all dependencies
	@echo   dev         - Start development servers
	@echo   test        - Run all tests
	@echo   lint        - Run linters
	@echo   build       - Build for production
	@echo   docker-up   - Start Docker services
	@echo   docker-down - Stop Docker services
	@echo   clean       - Clean generated files

install: ## Install all dependencies
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

dev-backend: ## Start backend development server
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start frontend development server
	cd frontend && npm run dev

test: ## Run all tests
	cd backend && pytest tests/ -v --cov=app --cov-report=term-missing

test-unit: ## Run unit tests only
	cd backend && pytest tests/unit/ -v

test-api: ## Run API tests only
	cd backend && pytest tests/api/ -v

lint: ## Run linters
	cd backend && ruff check . && black --check . && mypy app/ --ignore-missing-imports
	cd frontend && npm run lint

format: ## Format code
	cd backend && black . && ruff check --fix .

build: ## Build for production
	cd frontend && npm run build

docker-up: ## Start all Docker services
	docker-compose up -d --build

docker-down: ## Stop all Docker services
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

clean: ## Clean generated files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/htmlcov backend/.coverage
	rm -rf frontend/dist frontend/node_modules
