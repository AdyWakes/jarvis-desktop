.PHONY: help install backend frontend dev test lint format docker docker-down clean

help:
	@echo "Targets:"
	@echo "  install      Install backend (.venv) and frontend dependencies"
	@echo "  backend      Run the FastAPI dev server"
	@echo "  frontend     Run the Vite dev server"
	@echo "  dev          Run both (requires foreman or two terminals)"
	@echo "  test         Run backend pytest suite"
	@echo "  lint         Lint backend + frontend"
	@echo "  format       Auto-format backend + frontend"
	@echo "  docker       docker compose up --build"
	@echo "  docker-down  docker compose down"
	@echo "  clean        Remove build artifacts and caches"

install:
	cd backend && python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
	cd frontend && npm install

backend:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload

frontend:
	cd frontend && npm run dev

dev:
	@echo "Run 'make backend' in one terminal and 'make frontend' in another."

test:
	cd backend && . .venv/bin/activate && pytest

lint:
	cd backend && . .venv/bin/activate && ruff check . && ruff format --check . && mypy app
	cd frontend && npm run lint && npm run typecheck

format:
	cd backend && . .venv/bin/activate && ruff check --fix . && ruff format .

docker:
	docker compose up --build

docker-down:
	docker compose down

clean:
	rm -rf backend/.venv backend/.ruff_cache backend/.mypy_cache backend/.pytest_cache backend/**/__pycache__
	rm -rf frontend/node_modules frontend/dist frontend/.vite
