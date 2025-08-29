# MCP SQL Server

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Model Context Protocol (MCP) Server para SQL Server** - Um servidor MCP robusto e seguro que fornece acesso controlado a bancos de dados SQL Server através de ferramentas especializadas.

> 🎯 **Usuários do Cursor**: Consulte o [**CURSOR_GUIDE.md**](docs/CURSOR_GUIDE.md) para configuração rápida em 5 minutos!

## 📋 Índice

- [Características](#-características)
- [Modos de Operação](#-modos-de-operação)
- [Instalação](#-instalação)
- [Configuração no Cursor](#-configuração-no-cursor)
- [Configuração](#-configuração)
- [Uso](#-uso)
- [Ferramentas Disponíveis](#-ferramentas-disponíveis)
- [Docker](#-docker)
- [Exemplos](#-exemplos)
- [Segurança](#-segurança)
- [Troubleshooting](#-troubleshooting)
- [Contribuição](#-contribuição)

## 🚀 Características

- **Dois Modos de Operação**: READ_ONLY e FULL_ACCESS
- **Segurança Robusta**: Validação de queries, prevenção de SQL injection, rate limiting
- **Pool de Conexões**: Gerenciamento eficiente de conexões com SQL Server
- **API REST**: Interface FastAPI com documentação automática
- **Observabilidade**: Logs estruturados, métricas e health checks
- **Docker Ready**: Contêineres otimizados com drivers ODBC
- **Timezone Configurável**: Suporte a America/Sao_Paulo
- **Rate Limiting**: Controle de taxa de requisições por cliente

## 🔧 Modos de Operação

### READ_ONLY
Modo seguro para operações somente leitura:
- ✅ Listar tabelas, views, procedures e funções
- ✅ Descrever estruturas de tabelas
- ✅ Executar queries SELECT com validação
- ✅ Obter dados com paginação
- ✅ Verificar constraints e índices
- ❌ Modificar dados ou estruturas

### FULL_ACCESS
Modo completo com todas as operações:
- ✅ Todas as funcionalidades do READ_ONLY
- ✅ Executar qualquer query SQL
- ✅ Criar, alterar e remover tabelas
- ✅ Inserir, atualizar e deletar dados
- ✅ Gerenciar índices
- ✅ Executar stored procedures
- ✅ Fazer backup de tabelas

## 💿 Instalação

### Pré-requisitos
- Python 3.11+
- SQL Server (local ou remoto)
- Docker (opcional)

### Instalação Local

1. **Clone o repositório**:
```bash
git clone <repository-url>
cd mcp-sqlserver
```

2. **Crie ambiente virtual**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Instale dependências**:
```bash
pip install -r requirements.txt
```

4. **Configure variáveis de ambiente**:
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

5. **Execute o servidor**:
```bash
python -m src.main
```

### Instalação via Docker

1. **Clone e configure**:
```bash
git clone <repository-url>
cd mcp-sqlserver
cp config/.env.example .env
# Configure o arquivo .env
```

2. **Execute com Docker Compose**:
```bash
# Com SQL Server incluso (desenvolvimento)
docker-compose -f docker/docker-compose.yml up -d

# Apenas MCP Server (SQL Server externo)
docker-compose -f docker/docker-compose.mcp-only.yml up -d
```

## 🔧 Configuração no Cursor

### Pré-requisitos

Antes de configurar no Cursor, certifique-se de ter:
- **Cursor Editor** instalado
- **Docker Desktop** instalado e rodando
- **Git** configurado
- Acesso a um **SQL Server** (local ou remoto)

### Passo a Passo Completo

#### 1. Clone e Abra o Projeto

```bash
# 1. Clone o repositório
git clone <repository-url>
cd mcp-sqlserver

# 2. Abra no Cursor
cursor .
```

#### 2. Configuração Inicial

**No terminal integrado do Cursor:**

```bash
# 1. Copie o arquivo de exemplo
cp config/.env.example .env

# 2. Edite as configurações (use Ctrl+` para abrir terminal)
# Configure as variáveis no arquivo .env
```

**Configure o arquivo `.env`:**
```bash
# SQL Server Configuration
DB_HOST=localhost                    # ou IP do seu SQL Server
DB_PORT=1433
DB_NAME=master                       # ou nome do seu banco
DB_USER=sa                          # seu usuário SQL Server
DB_PASSWORD=YourStrongPassword123!   # sua senha SQL Server

# MCP Server Configuration
MCP_MODE=READ_ONLY                   # ou FULL_ACCESS se precisar de escrita
MCP_PORT=4000
```

#### 3. Deploy com Docker Compose

**Escolha um dos cenários:**

##### Cenário 1: Desenvolvimento Completo (Recomendado)
```bash
# Inicia MCP Server + SQL Server local
docker-compose -f docker/docker-compose.yml up -d

# Verifica status
docker-compose -f docker/docker-compose.yml ps

# Acompanha logs
docker-compose -f docker/docker-compose.yml logs -f mcp-sqlserver
```

##### Cenário 2: SQL Server Externo
```bash
# Apenas MCP Server (SQL Server já existe)
docker-compose -f docker/docker-compose.mcp-only.yml up -d

# Verifica conexão
curl http://localhost:4000/health
```

#### 4. Verificação e Testes

**No terminal do Cursor:**

```bash
# 1. Verificar se está rodando
curl http://localhost:4000/health

# 2. Ver documentação interativa
# Abra: http://localhost:4000/docs

# 3. Testar com cliente de exemplo
python examples/example_client.py
```

#### 5. Configuração do MCP no Cursor

**Para integrar com o Cursor como MCP Server:**

1. **Configure o MCP Client no Cursor:**
   ```json
   {
     "mcpServers": {
       "sqlserver": {
         "command": "python",
         "args": ["-m", "src.main"],
         "env": {
           "DB_HOST": "localhost",
           "DB_PASSWORD": "YourPassword",
           "MCP_MODE": "READ_ONLY"
         }
       }
     }
   }
   ```

2. **Ou use via HTTP:**
   ```json
   {
     "mcpServers": {
       "sqlserver": {
         "transport": {
           "type": "http",
           "url": "http://localhost:4000"
         }
       }
     }
   }
   ```

#### 6. Scripts de Automação (Windows)

**Use os scripts incluídos:**

```bash
# Setup inicial completo
scripts/setup.bat

# Executar servidor rapidamente
scripts/run.bat

# Deploy com Docker
scripts/docker-up.bat

# Deploy standalone (sem docker-compose)
scripts/deploy-standalone.bat
```

#### 7. Comandos Make (Linux/Mac)

```bash
# Setup inicial
make -f scripts/Makefile init

# Executar local
make -f scripts/Makefile run

# Deploy Docker
make -f scripts/Makefile up

# Apenas MCP Server
make -f scripts/Makefile up-mcp-only

# Ver logs
make -f scripts/Makefile logs

# Health check
make -f scripts/Makefile health

# Testar cliente
make -f scripts/Makefile example
```

### Troubleshooting no Cursor

#### Problema: Erro de Conexão
```bash
# Verificar se Docker está rodando
docker ps

# Verificar logs
docker-compose -f docker/docker-compose.yml logs mcp-sqlserver

# Restart completo
docker-compose -f docker/docker-compose.yml down
docker-compose -f docker/docker-compose.yml up -d
```

#### Problema: SQL Server não conecta
```bash
# Testar conexão direta
telnet <DB_HOST> <DB_PORT>

# Verificar variáveis de ambiente
docker-compose -f docker/docker-compose.yml exec mcp-sqlserver env | grep DB_
```

#### Problema: MCP não responde
```bash
# Verificar health check
curl http://localhost:4000/health

# Ver logs detalhados
docker-compose -f docker/docker-compose.yml logs -f --tail=50 mcp-sqlserver
```

### Desenvolvimento no Cursor

#### Estrutura para Development

```bash
# 1. Crie ambiente virtual local para desenvolvimento
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# 2. Instale dependências
pip install -r requirements.txt

# 3. Execute em modo desenvolvimento
python -m src.main
```

#### Configuração do Cursor

**Configure `config/.vscode/settings.json` (funciona no Cursor):**
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "python.linting.enabled": true,
  "files.associations": {
    "*.env": "properties"
  }
}
```

#### Tasks.json para Cursor

**Configure `config/.vscode/tasks.json`:**
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Start MCP Server",
      "type": "shell",
      "command": "python -m src.main",
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "new"
      }
    },
    {
      "label": "Docker Up",
      "type": "shell",
      "command": "docker-compose -f docker/docker-compose.yml up -d",
      "group": "build"
    },
    {
      "label": "Test Client",
      "type": "shell",
      "command": "python examples/example_client.py",
      "group": "test"
    }
  ]
}
```

### Monitoramento no Cursor

**Terminal integrado para monitoramento:**
```bash
# Terminal 1: Logs do servidor
docker-compose -f docker/docker-compose.yml logs -f mcp-sqlserver

# Terminal 2: Monitoramento de health
watch -n 10 'curl -s http://localhost:4000/health | jq'

# Terminal 3: Desenvolvimento/testes
python examples/example_client.py
```

## ⚙️ Configuração

### Variáveis de Ambiente

Copie `config/.env.example` para `.env` e configure:

```bash
# SQL Server Database Configuration
DB_HOST=localhost
DB_PORT=1433
DB_NAME=master
DB_USER=sa
DB_PASSWORD=YourStrongPassword123!

# MCP Server Configuration
MCP_MODE=READ_ONLY              # READ_ONLY ou FULL_ACCESS
MCP_PORT=4000                   # Porta do servidor
MCP_HOST=0.0.0.0

# Security Settings
QUERY_TIMEOUT=30                # Timeout de queries em segundos
MAX_RESULT_ROWS=1000           # Máximo de linhas retornadas
RATE_LIMIT_PER_MINUTE=60       # Limite de requisições por minuto
CONNECTION_POOL_SIZE=10        # Tamanho do pool de conexões
CONNECTION_POOL_MAX_OVERFLOW=20 # Overflow máximo do pool

# Logging Configuration
LOG_LEVEL=INFO                 # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json                # json ou console

# Performance Settings
ASYNC_POOL_SIZE=5              # Tamanho do pool assíncrono
MAX_CONCURRENT_QUERIES=10      # Queries concorrentes máximas

# Timezone
TZ=America/Sao_Paulo
```

### Configuração de Banco de Dados

Certifique-se de que:
- SQL Server esteja rodando e acessível
- Usuário tenha permissões adequadas
- Firewall permita conexões na porta configurada
- Drivers ODBC estejam instalados (automático no Docker)

## 🎯 Uso

### Inicialização

```bash
# Desenvolvimento
python -m src.main

# Produção
python -m src.main

# Docker
docker-compose up -d
```

### API REST

Acesse a documentação interativa:
- **Swagger UI**: `http://localhost:4000/docs`
- **ReDoc**: `http://localhost:4000/redoc`

### Endpoints Principais

- `GET /health` - Health check
- `GET /info` - Informações do servidor
- `GET /tools` - Lista de ferramentas disponíveis
- `POST /tools/call` - Executar ferramenta
- `GET /database/tables` - Listar tabelas
- `GET /database/schema` - Esquema do banco

## 🛠️ Ferramentas Disponíveis

### Ferramentas READ_ONLY

#### `list_tables`
Lista todas as tabelas do banco de dados.
```json
{
  "tool_name": "list_tables",
  "arguments": {
    "schema": "dbo"  // opcional
  }
}
```

#### `describe_table`
Obtém estrutura detalhada de uma tabela.
```json
{
  "tool_name": "describe_table",
  "arguments": {
    "table_name": "users",
    "schema": "dbo"  // opcional
  }
}
```

#### `execute_select`
Executa queries SELECT com validação.
```json
{
  "tool_name": "execute_select",
  "arguments": {
    "query": "SELECT TOP 10 * FROM users WHERE active = 1",
    "limit": 100  // opcional
  }
}
```

#### `get_table_data`
Obtém dados com paginação.
```json
{
  "tool_name": "get_table_data",
  "arguments": {
    "table_name": "users",
    "limit": 50,
    "offset": 0,
    "schema": "dbo"  // opcional
  }
}
```

### Ferramentas FULL_ACCESS

#### `execute_query`
Executa qualquer query SQL.
```json
{
  "tool_name": "execute_query",
  "arguments": {
    "query": "INSERT INTO users (name, email) VALUES (?, ?)",
    "params": ["João Silva", "joao@email.com"]
  }
}
```

#### `create_table`
Cria nova tabela.
```json
{
  "tool_name": "create_table",
  "arguments": {
    "table_name": "products",
    "columns": [
      {
        "name": "id",
        "type": "INT IDENTITY(1,1)",
        "primary_key": true,
        "nullable": false
      },
      {
        "name": "name",
        "type": "NVARCHAR(255)",
        "nullable": false
      },
      {
        "name": "price",
        "type": "DECIMAL(10,2)",
        "nullable": true,
        "default": "0.00"
      }
    ],
    "schema": "dbo"
  }
}
```

#### `insert_data`
Insere dados em lote.
```json
{
  "tool_name": "insert_data",
  "arguments": {
    "table_name": "products",
    "data": [
      {"name": "Produto 1", "price": 10.99},
      {"name": "Produto 2", "price": 25.50}
    ],
    "schema": "dbo"
  }
}
```

## 🐳 Docker

### Cenários de Uso

#### 1. Desenvolvimento (com SQL Server)
```bash
docker-compose -f docker/docker-compose.yml up -d
```
Inclui SQL Server para desenvolvimento local.

#### 2. Produção (SQL Server externo)
```bash
docker-compose -f docker/docker-compose.mcp-only.yml up -d
```
Apenas o MCP Server, conecta a SQL Server externo.

#### 3. Build personalizado
```bash
docker build -f docker/Dockerfile -t mcp-sqlserver:final .
docker run -d --name mcp-server \
  -p 4000:4000 \
  -e DB_HOST=your-sql-server \
  -e DB_PASSWORD=your-password \
  -e MCP_MODE=READ_ONLY \
  mcp-sqlserver:final
```

#### 4. Deploy standalone (sem docker-compose)
```bash
# Use o script automatizado
scripts/deploy-standalone.bat

# Ou manualmente
docker run -d \
  --name mcp-sqlserver \
  -p 4000:4000 \
  -e DB_HOST=host.docker.internal \
  -e DB_PASSWORD=YourPassword123! \
  -e MCP_MODE=READ_ONLY \
  mcp-sqlserver:final
```

### Volumes

- `mcp-logs`: Logs da aplicação
- `mcp-config`: Configurações
- `sqlserver-data`: Dados do SQL Server (se usando o compose completo)

## 📝 Exemplos

### Exemplo 1: Listar Tabelas via cURL
```bash
curl -X GET "http://localhost:4000/database/tables" \
     -H "accept: application/json"
```

### Exemplo 2: Executar Query via Python
```python
import requests

response = requests.post("http://localhost:4000/tools/call", json={
    "tool_name": "execute_select",
    "arguments": {
        "query": "SELECT name, email FROM users WHERE created_date > '2024-01-01'"
    }
})

print(response.json())
```

### Exemplo 3: Criar Tabela (FULL_ACCESS)
```bash
curl -X POST "http://localhost:4000/tools/call" \
     -H "Content-Type: application/json" \
     -d '{
       "tool_name": "create_table",
       "arguments": {
         "table_name": "logs",
         "columns": [
           {
             "name": "id",
             "type": "BIGINT IDENTITY(1,1)",
             "primary_key": true
           },
           {
             "name": "message",
             "type": "NVARCHAR(MAX)"
           },
           {
             "name": "created_at",
             "type": "DATETIME2",
             "default": "GETDATE()"
           }
         ]
       }
     }'
```

## 🔒 Segurança

### Validação de Queries
- **READ_ONLY**: Apenas queries SELECT são permitidas
- **Sanitização**: Remove caracteres perigosos
- **Blacklist**: Bloqueia palavras-chave perigosas
- **Timeout**: Limite de tempo para execução

### Rate Limiting
- Limite configurável por minuto por cliente
- Baseado em token bucket
- Headers informativos na resposta

### Pool de Conexões
- Gerenciamento seguro de conexões
- Timeout automático
- Reconexão automática em falhas

### Logs de Auditoria
- Todas as operações são logadas
- Formato JSON estruturado
- Informações de performance

## 🔧 Troubleshooting

### Problemas Comuns

#### 1. Erro de Conexão com SQL Server
```
Erro: ('08001', '[08001] [Microsoft][ODBC Driver 17 for SQL Server]...)
```
**Solução**:
- Verifique se SQL Server está rodando
- Confirme host, porta e credenciais no `.env`
- Teste conectividade: `telnet <host> <port>`

#### 2. Driver ODBC não encontrado
```
Erro: ('01000', "[01000] [unixODBC][Driver Manager]Can't open lib...")
```
**Solução**:
- Use Docker (drivers inclusos)
- Instale manualmente: `apt-get install msodbcsql17`

#### 3. Rate Limit Excedido
```
{"error": "Rate limit excedido", "error_code": "RATE_LIMIT_EXCEEDED"}
```
**Solução**:
- Aguarde antes de nova requisição
- Aumente `RATE_LIMIT_PER_MINUTE` no `.env`

#### 4. Query Inválida em READ_ONLY
```
{"error": "Query inválida: Apenas queries SELECT são permitidas"}
```
**Solução**:
- Use apenas SELECT em modo READ_ONLY
- Mude para FULL_ACCESS se necessário
- Verifique sintaxe da query

### Health Check

```bash
# Verificar saúde do servidor
curl http://localhost:4000/health

# Resposta esperada
{
  "status": "healthy",
  "database_connection": true,
  "server_running": true,
  "mode": "READ_ONLY",
  "timestamp": "2024-01-01T12:00:00"
}
```

### Logs

```bash
# Docker logs
docker logs mcp-sqlserver

# Logs em arquivo (se configurado)
tail -f ./logs/mcp-server.log
```

### Performance

#### Monitoramento
- Use endpoint `/health` para status
- Monitore logs para tempo de execução
- Observe uso de memória e CPU

#### Otimização
- Ajuste `CONNECTION_POOL_SIZE` conforme carga
- Configure `MAX_RESULT_ROWS` adequadamente
- Use índices nas tabelas consultadas

## 📊 Monitoramento

### Métricas Disponíveis
- Tempo de execução de queries
- Número de conexões ativas
- Taxa de erro por ferramenta
- Uso de rate limiting

### Configuração de Alertas
```bash
# Exemplo com curl para monitoramento
while true; do
  status=$(curl -s http://localhost:4000/health | jq -r '.status')
  if [ "$status" != "healthy" ]; then
    echo "ALERT: MCP Server unhealthy at $(date)"
  fi
  sleep 60
done
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

### Desenvolvimento

```bash
# Setup para desenvolvimento
git clone <repo>
cd mcp-sqlserver
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # se existir

# Executar testes
python -m pytest

# Executar com reload
python -m src.main --reload
```

## 📄 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📞 Suporte

- **Issues**: Abra uma issue no GitHub
- **Discussões**: Use GitHub Discussions
- **Wiki**: Consulte a wiki do projeto

## 🔄 Changelog

### v1.0.0
- ✅ Implementação inicial do servidor MCP
- ✅ Suporte a modos READ_ONLY e FULL_ACCESS
- ✅ API REST com FastAPI
- ✅ Pool de conexões com SQL Server
- ✅ Validação de segurança
- ✅ Docker support
- ✅ Documentação completa

---

**MCP SQL Server** - Desenvolvido com ❤️ para a comunidade Python e SQL Server.
