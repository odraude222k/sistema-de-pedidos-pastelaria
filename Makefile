.PHONY: help up down logs ps install-frontend test-backend lint-backend test-frontend lint-frontend build-frontend

help:
	@echo "Comandos disponiveis:"
	@echo "  make help            Exibe esta ajuda"
	@echo "  make up              Inicia os servicos"
	@echo "  make down            Encerra os servicos"
	@echo "  make logs            Acompanha os logs"
	@echo "  make ps              Mostra os servicos"
	@echo "  make test-backend    Executa os testes do backend"
	@echo "  make lint-backend    Verifica o codigo do backend"
	@echo "  make install-frontend  Instala dependencias do frontend"
	@echo "  make test-frontend    Executa os testes do frontend"
	@echo "  make lint-frontend    Verifica o codigo do frontend"
	@echo "  make build-frontend   Gera o build do frontend"

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

ps:
	docker compose ps

test-backend:
	cd backend && poetry run pytest

lint-backend:
	cd backend && poetry run ruff check .
	cd backend && poetry run ruff format --check .

install-frontend:
	cd frontend && npm ci

test-frontend:
	cd frontend && npm test

lint-frontend:
	cd frontend && npm run lint

build-frontend:
	cd frontend && npm run build

run-backend:
	cd backend && poetry run uvicorn app.main:app --reload
