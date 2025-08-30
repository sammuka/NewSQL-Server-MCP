# MCP SQL Server

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Model Context Protocol (MCP) Server para SQL Server** - Um servidor MCP robusto e seguro que fornece acesso controlado a bancos de dados SQL Server através de ferramentas especializadas.

> 🎯 **Usuários do Cursor:** Consulte o [**CURSOR_GUIDE.md**](./docs/CURSOR_GUIDE.md) para configuração rápida em 5 minutos!

## 🚀 Características

- **Dois Modos de Operação**: READ_ONLY e FULL_ACCESS
- **Segurança Robusta**: Validação de queries, prevenção de SQL injection, rate limiting
- **Pool de Conexões**: Gerenciamento eficiente de conexões com SQL Server
- **API REST**: Interface FastAPI com documentação automática
- **Observabilidade**: Logs estruturados, métricas e health checks
- **Docker Ready**: Contêineres otimizados com drivers ODBC
- **Timezone Configurável**: Suporte a America/Sao_Paulo
- **Rate Limiting**: Controle de taxa de requisições por cliente

## 🛠️ Ferramentas Disponíveis

### 📖 READ_ONLY (11 ferramentas)
- `list_tables` - Lista tabelas do banco
- `describe_table` - Estrutura detalhada de tabela
- `list_columns` - Colunas de uma tabela
- `list_indexes` - Índices de uma tabela
- `list_views` - Views do banco
- `list_procedures` - Stored procedures
- `list_functions` - Funções do banco
- `execute_select` - Executa SELECT com validação
- `get_table_data` - Dados paginados de tabela
- `get_database_schema` - Schema completo
- `check_constraints` - Constraints de tabela

### ✏️ FULL_ACCESS (12 ferramentas adicionais)
- `execute_query` - Executa qualquer SQL
- `create_table` - Criar tabelas
- `create_index` - Criar índices
- `insert_data` - Inserir dados
- `update_data` - Atualizar registros
- `delete_data` - Deletar registros
- `backup_table` - Backup de tabelas
- `restore_table` - Restore de backups
- `create_procedure` - Criar stored procedures
- `execute_procedure` - Executar procedures
- `manage_users` - Gerenciar usuários
- `database_maintenance` - Manutenção do banco

## 🎯 Início Rápido

### 1. Clone e Configure
```bash
# Clone do repositório
git clone https://github.com/sammuka/NewSQL-Server-MCP.git
cd NewSQL-Server-MCP

# Configure credenciais
cp config/.env.example .env
# Edite .env com suas credenciais SQL Server
```

### 2. Deploy com Docker (Recomendado)
```bash
# Deploy completo (MCP + SQL Server para desenvolvimento)
docker-compose -f docker/docker-compose.yml up -d

# OU apenas MCP Server (para SQL Server externo)
docker-compose -f docker/docker-compose.mcp-only.yml up -d

# OU usando scripts Windows
scripts\docker-up.bat
```

### 3. Verificar Funcionamento
```bash
# Health check
curl http://localhost:4000/health
# Resposta: {"status":"healthy","database_connection":true}

# Documentação interativa
open http://localhost:4000/docs

# Listar ferramentas disponíveis
curl http://localhost:4000/tools
```

### 4. Teste com Cliente
```bash
# Executar cliente de exemplo
python examples/example_client.py

# OU teste manual
curl -X POST "http://localhost:4000/tools/call" \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "list_tables", "arguments": {}}'
```

## ⚙️ Configuração

### Variáveis de Ambiente (.env)
```bash
# SQL Server Connection
DB_HOST=localhost
DB_PORT=1433
DB_NAME=master
DB_USER=sa
DB_PASSWORD=YourStrongPassword123!

# MCP Server
MCP_MODE=READ_ONLY        # ou FULL_ACCESS
MCP_PORT=4000

# Security
QUERY_TIMEOUT_SECONDS=30
RATE_LIMIT_PER_MINUTE=60
```

### Configuração no Cursor
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

## 📋 Estrutura do Repositório

```
NewSQL-Server-MCP/                    # 🏠 Repositório MCP SQL Server
├── README.md                         # 📋 Documentação principal
├── requirements.txt                  # 🐍 Dependências Python
├── .dockerignore                     # 🐳 Docker exclusions
├── .gitignore                        # 📝 Git exclusions
│
├── config/                           # ⚙️ Configurações
│   ├── .env.example                 # 📝 Template de ambiente
│   └── .vscode/                      # 🎯 Configurações Cursor/VS Code
│
├── docker/                           # 🐳 Containerização
│   ├── Dockerfile                   # 📦 Imagem otimizada
│   ├── docker-compose.yml           # 🏗️ Stack completa
│   └── docker-compose.mcp-only.yml  # 🎯 Apenas MCP
│
├── docs/                             # 📚 Documentação
│   ├── CURSOR_GUIDE.md              # 🎯 Guia para Cursor
│   └── TECHNICAL.md                 # 🔧 Documentação técnica
│
├── examples/                         # 🧪 Exemplos
│   └── example_client.py            # 🐍 Cliente demonstrativo
│
├── scripts/                          # 🛠️ Automação
│   ├── setup.bat                    # 🪟 Setup Windows
│   ├── run.bat                      # 🪟 Execução Windows
│   ├── docker-up.bat                # 🪟 Deploy Windows
│   ├── deploy-standalone.bat        # 🪟 Deploy standalone
│   └── Makefile                     # 🐧 Comandos Linux/Mac
│
└── src/                              # 💻 Código fonte
    ├── main.py                      # 🚀 FastAPI app
    ├── mcp_server.py               # 🧠 MCP server core
    ├── database/                    # 🗄️ Camada de dados
    └── tools/                       # 🔧 Ferramentas MCP
```

## 🛠️ Build e Deploy

### 📋 Pré-requisitos

#### Obrigatórios
- **Git** (para clone do repositório)
- **Docker Desktop** (recomendado)
- **Python 3.11+** (para execução local)

#### Opcionais
- **SQL Server** (local ou remoto)
- **Cursor/VS Code** (para desenvolvimento)

### 🚀 Deploy Rápido (Docker)

#### 1. Clone e Configuração
```bash
# Clone do repositório
git clone https://github.com/sammuka/NewSQL-Server-MCP.git
cd NewSQL-Server-MCP/mcp-sqlserver

# Configurar credenciais
cp config/.env.example .env
# Editar .env com suas credenciais SQL Server
```

#### 2. Deploy Automático (Windows)
```bash
# Setup completo + Deploy
scripts\setup.bat

# Deploy apenas
scripts\docker-up.bat

# Deploy standalone (sem docker-compose)
scripts\deploy-standalone.bat
```

#### 3. Deploy Manual (Linux/Mac/Windows)
```bash
# Desenvolvimento completo (MCP + SQL Server)
docker-compose -f docker/docker-compose.yml up -d

# Produção (apenas MCP, SQL Server externo)
docker-compose -f docker/docker-compose.mcp-only.yml up -d

# Standalone (container único)
docker run -d \
  --name mcp-sqlserver \
  -p 4000:4000 \
  -e DB_HOST=host.docker.internal \
  -e DB_PASSWORD=YourPassword123! \
  -e MCP_MODE=READ_ONLY \
  mcp-sqlserver:final
```

### 🔧 Build Personalizado

#### 1. Build da Imagem Docker
```bash
# Build da imagem otimizada
docker build -f docker/Dockerfile -t mcp-sqlserver:final .

# Verificar build
docker images | grep mcp-sqlserver
```

#### 2. Execução Local (Desenvolvimento)
```bash
# Configurar ambiente Python
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar ambiente
cp config/.env.example .env
# Editar .env

# Executar servidor
python -m src.main
```

#### 3. Deploy Customizado
```bash
# Docker com configurações específicas
docker run -d \
  --name mcp-sqlserver \
  -p 4000:4000 \
  -e DB_HOST=seu-sql-server \
  -e DB_PORT=1433 \
  -e DB_NAME=sua-database \
  -e DB_USER=seu-usuario \
  -e DB_PASSWORD=sua-senha \
  -e MCP_MODE=READ_ONLY \
  -e QUERY_TIMEOUT=30 \
  -e RATE_LIMIT_PER_MINUTE=60 \
  --restart unless-stopped \
  mcp-sqlserver:final

# Docker Compose customizado
# Edite docker/docker-compose.yml conforme necessário
docker-compose -f docker/docker-compose.yml up -d
```

### ⚡ Comandos por Plataforma

#### Windows (PowerShell/CMD)
```bash
# Navegue até o projeto
cd NewSQL-Server-MCP

# Setup automático
scripts\setup.bat

# Deploy Docker
scripts\docker-up.bat

# Deploy standalone
scripts\deploy-standalone.bat

# Execução local
scripts\run.bat
```

#### Linux/Mac (Terminal)
```bash
# Navegue até o projeto
cd NewSQL-Server-MCP

# Setup inicial
make -f scripts/Makefile init

# Deploy Docker completo
make -f scripts/Makefile up

# Deploy apenas MCP
make -f scripts/Makefile up-mcp-only

# Execução local
make -f scripts/Makefile run

# Health check
make -f scripts/Makefile health

# Ver logs
make -f scripts/Makefile logs
```

### 🔍 Verificação e Testes

#### 1. Verificar Status
```bash
# Health check
curl http://localhost:4000/health

# Listar ferramentas
curl http://localhost:4000/tools

# Status dos containers
docker ps | grep mcp-sqlserver
```

#### 2. Executar Testes
```bash
# Cliente de exemplo
python examples/example_client.py

# Documentação interativa
# Abra: http://localhost:4000/docs
```

#### 3. Debug e Logs
```bash
# Logs do container
docker logs mcp-sqlserver --tail=50

# Logs em tempo real
docker logs mcp-sqlserver --follow

# Acessar container
docker exec -it mcp-sqlserver /bin/bash
```

### 🛑 Problemas Comuns

#### Docker Build Falha
```bash
# Limpar cache Docker
docker system prune -f

# Build sem cache
docker build --no-cache -f docker/Dockerfile -t mcp-sqlserver:final .
```

#### Container Não Inicia
```bash
# Verificar logs
docker logs mcp-sqlserver

# Verificar porta ocupada
netstat -an | grep :4000

# Parar containers conflitantes
docker stop mcp-sqlserver
docker rm mcp-sqlserver
```

#### SQL Server Não Conecta
```bash
# Testar conectividade
telnet seu-sql-server 1433

# Verificar variáveis de ambiente
docker exec mcp-sqlserver env | grep DB_
```

## 🎯 Integração com Cursor

### Configuração Rápida
1. **Clone e abra no Cursor:**
   ```bash
   git clone https://github.com/sammuka/NewSQL-Server-MCP.git
   cd NewSQL-Server-MCP/mcp-sqlserver
   cursor .
   ```

2. **Execute setup automático:**
   ```bash
   scripts/setup.bat     # Windows
   # ou
   make init            # Linux/Mac
   ```

3. **Configure MCP no Cursor:**
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

### Guia Detalhado
📖 **Consulte:** [docs/CURSOR_GUIDE.md](./docs/CURSOR_GUIDE.md)

## 🧪 Teste Rápido

```bash
# 1. Health check
curl http://localhost:4000/health

# 2. Listar ferramentas disponíveis
curl http://localhost:4000/tools

# 3. Executar cliente de exemplo
cd mcp-sqlserver
python examples/example_client.py
```

## 🔗 Links Úteis

- 📚 **Documentação Completa:** [mcp-sqlserver/README.md](./mcp-sqlserver/README.md)
- 🎯 **Guia Cursor:** [mcp-sqlserver/docs/CURSOR_GUIDE.md](./mcp-sqlserver/docs/CURSOR_GUIDE.md)
- 🧪 **Cliente Exemplo:** [mcp-sqlserver/examples/example_client.py](./mcp-sqlserver/examples/example_client.py)
- 🐳 **Docker Configs:** [mcp-sqlserver/docker/](./mcp-sqlserver/docker/)

## 🤝 Contribuição

1. Fork o repositório
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add: AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📚 Documentação Adicional

- 🎯 **Guia Cursor:** [docs/CURSOR_GUIDE.md](./docs/CURSOR_GUIDE.md)
- 📖 **Documentação Técnica:** [docs/TECHNICAL.md](./docs/TECHNICAL.md)
- 🧪 **Cliente Exemplo:** [examples/example_client.py](./examples/example_client.py)
- 🐳 **Configs Docker:** [docker/](./docker/)

## 📞 Suporte

- 🐛 **Issues:** [GitHub Issues](https://github.com/sammuka/NewSQL-Server-MCP/issues)
- 💬 **Discussões:** [GitHub Discussions](https://github.com/sammuka/NewSQL-Server-MCP/discussions)
- 📧 **Email:** suporte@newsql-mcp.com

---

⭐ **Se este projeto foi útil, considere dar uma estrela!** ⭐
