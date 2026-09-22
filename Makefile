.PHONY: help up down logs ps test-backend lint-backend

help:
	@echo "Comandos disponiveis:"
	@echo "  make help            Exibe esta ajuda"
	@echo "  make up              Inicia os servicos"
	@echo "  make down            Encerra os servicos"
	@echo "  make logs            Acompanha os logs"
	@echo "  make ps              Mostra os servicos"
	@echo "  make test-backend    Executa os testes do backend"
	@echo "  make lint-backend    Verifica o codigo do backend"

up:
	docker compose up -d

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