.PHONY: help up down logs ps

help:
	@echo "Comandos disponiveis:"
	@echo "  make help    Exibe esta ajuda"
	@echo "  make up      Inicia os servicos"
	@echo "  make down    Encerra os servicos"
	@echo "  make logs    Acompanha os logs"
	@echo "  make ps      Mostra os servicos"

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

ps:
	docker compose ps