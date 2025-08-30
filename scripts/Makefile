# Makefile para MCP SQL Server
# Comandos úteis para desenvolvimento e produção

.PHONY: help install dev test clean build run docker-build docker-run docker-stop logs

# Configurações
PYTHON := python3
PIP := pip3
DOCKER_IMAGE := mcp-sqlserver
DOCKER_CONTAINER := mcp-sqlserver
COMPOSE_FILE := docker/docker-compose.yml
COMPOSE_FILE_MCP_ONLY := docker/docker-compose.mcp-only.yml

help: ## Mostra ajuda
	@echo "MCP SQL Server - Comandos disponíveis:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Instala dependências Python
	$(PIP) install -r requirements.txt

dev: ## Configuração para desenvolvimento
	cp config/.env.example .env
	@echo "✅ Arquivo .env criado"
	@echo "📝 Configure as variáveis de ambiente em .env"
	@echo "🚀 Execute 'make run' para iniciar o servidor"

test: ## Executa testes (placeholder)
	@echo "🧪 Executando testes..."
	# $(PYTHON) -m pytest tests/
	@echo "⚠️ Testes ainda não implementados"

clean: ## Limpa arquivos temporários
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	@echo "🧹 Arquivos temporários removidos"

run: ## Executa servidor local
	$(PYTHON) -m src.main

run-dev: ## Executa servidor em modo desenvolvimento
	ENVIRONMENT=development $(PYTHON) -m src.main

# Docker commands
docker-build: ## Constrói imagem Docker
	docker build -f docker/Dockerfile -t $(DOCKER_IMAGE) .

docker-run: ## Executa container Docker
	docker run -d --name $(DOCKER_CONTAINER) \
		-p 4000:4000 \
		--env-file .env \
		$(DOCKER_IMAGE)

docker-stop: ## Para container Docker
	docker stop $(DOCKER_CONTAINER) || true
	docker rm $(DOCKER_CONTAINER) || true

docker-logs: ## Mostra logs do container
	docker logs -f $(DOCKER_CONTAINER)

# Docker Compose commands
up: ## Inicia com docker-compose (com SQL Server)
	docker-compose -f $(COMPOSE_FILE) up -d

up-mcp-only: ## Inicia apenas MCP Server
	docker-compose -f $(COMPOSE_FILE_MCP_ONLY) up -d

down: ## Para docker-compose
	docker-compose -f $(COMPOSE_FILE) down
	docker-compose -f $(COMPOSE_FILE_MCP_ONLY) down

restart: ## Reinicia docker-compose
	make down
	make up

logs: ## Mostra logs do docker-compose
	docker-compose -f $(COMPOSE_FILE) logs -f mcp-sqlserver

logs-db: ## Mostra logs do SQL Server
	docker-compose -f $(COMPOSE_FILE) logs -f sqlserver

status: ## Mostra status dos containers
	docker-compose -f $(COMPOSE_FILE) ps

# Comandos de desenvolvimento
format: ## Formata código (placeholder)
	@echo "🎨 Formatando código..."
	# black src/
	# isort src/
	@echo "⚠️ Formatadores ainda não configurados"

lint: ## Executa linting (placeholder)
	@echo "🔍 Executando linting..."
	# flake8 src/
	# mypy src/
	@echo "⚠️ Linters ainda não configurados"

# Comandos de utilitários
health: ## Verifica saúde do servidor
	@echo "🏥 Verificando saúde do servidor..."
	@curl -f http://localhost:4000/health || echo "❌ Servidor não está respondendo"

example: ## Executa cliente de exemplo
	$(PYTHON) examples/example_client.py

backup-env: ## Faz backup do arquivo .env
	cp .env .env.backup.$(shell date +%Y%m%d_%H%M%S)
	@echo "💾 Backup do .env criado"

init: ## Inicialização completa do projeto
	make dev
	@echo ""
	@echo "🎉 Projeto inicializado!"
	@echo ""
	@echo "📋 Próximos passos:"
	@echo "   1. Configure .env com suas credenciais"
	@echo "   2. Execute: make run (local) ou make up (Docker)"
	@echo "   3. Acesse: http://localhost:4000/docs"
	@echo ""

# Comandos de produção
deploy: ## Deploy para produção (Docker)
	make clean
	make docker-build
	make docker-stop
	make docker-run
	@echo "🚀 Deploy concluído!"

check-env: ## Verifica se .env existe
	@if [ ! -f .env ]; then \
		echo "❌ Arquivo .env não encontrado"; \
		echo "💡 Execute 'make dev' para criar"; \
		exit 1; \
	fi
	@echo "✅ Arquivo .env encontrado"

# Comandos de monitoramento
monitor: ## Monitora logs em tempo real
	@echo "📊 Monitorando logs..."
	@docker-compose -f $(COMPOSE_FILE) logs -f --tail=50

ps: ## Lista processos relacionados
	@echo "📋 Processos Python relacionados:"
	@ps aux | grep python | grep -v grep || echo "Nenhum processo encontrado"
	@echo ""
	@echo "📋 Containers Docker:"
	@docker ps | grep mcp || echo "Nenhum container encontrado"

# Comandos de debug
debug: ## Informações de debug
	@echo "🐛 Informações de Debug:"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Pip: $(shell $(PIP) --version)"
	@echo "Docker: $(shell docker --version 2>/dev/null || echo 'Não instalado')"
	@echo "Docker Compose: $(shell docker-compose --version 2>/dev/null || echo 'Não instalado')"
	@echo ""
	@echo "📁 Estrutura do projeto:"
	@tree -L 2 -I "__pycache__|*.pyc" || ls -la

shell: ## Acessa shell do container
	docker exec -it $(DOCKER_CONTAINER) /bin/bash

# Meta target
all: clean install dev ## Executa limpeza, instalação e configuração
