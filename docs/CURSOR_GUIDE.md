# 🎯 Guia Rápido para Cursor

**Configuração em 5 minutos do MCP SQL Server no Cursor**

> 📚 **Documentação Técnica Completa:** [TECHNICAL.md](./TECHNICAL.md)

## 🚀 Início Rápido

### 1. Abrir Projeto
```bash
# Clone e abra no Cursor
git clone https://github.com/sammuka/NewSQL-Server-MCP.git
cd NewSQL-Server-MCP
cursor .
```

### 2. Setup Automático (Windows)
```bash
# Execute no terminal do Cursor
./setup.bat
```

### 3. Setup Manual (Linux/Mac)
```bash
# No terminal do Cursor (Ctrl+`)
cp config/.env.example .env
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configurar .env
Edite `.env` com suas credenciais SQL Server:
```bash
DB_HOST=localhost
DB_PASSWORD=YourStrongPassword123!
MCP_MODE=READ_ONLY  # ou FULL_ACCESS
```

### 5. Executar

**Opção A: Docker (Recomendado)**
```bash
# Terminal do Cursor
docker-compose -f docker/docker-compose.yml up -d

# Ou use o script Windows
scripts/docker-up.bat
```

**Opção B: Local**
```bash
# Terminal do Cursor
python -m src.main

# Ou use o script Windows  
scripts/run.bat
```

### 6. Testar
```bash
# Verificar saúde
curl http://localhost:4000/health

# Testar cliente
python examples/example_client.py

# Ou use o script Windows
scripts/test-client.bat
```

## 🎮 Comandos Úteis no Cursor

### Terminal Integrado (Ctrl+`)
```bash
# Desenvolvimento
python -m src.main                                              # Executar local
docker-compose -f docker/docker-compose.yml up -d              # Executar Docker
docker-compose -f docker/docker-compose.yml logs -f mcp-sqlserver  # Ver logs
curl http://localhost:4000/docs                                # Abrir docs

# Monitoramento  
docker-compose -f docker/docker-compose.yml ps                 # Status containers
curl http://localhost:4000/health                              # Health check
python examples/example_client.py                              # Testar cliente
```

### Tasks (Ctrl+Shift+P → "Tasks: Run Task")
- **MCP Server: Start Local** - Executa servidor local
- **Docker: Up (Full Stack)** - Docker com SQL Server
- **Docker: Up (MCP Only)** - Apenas MCP Server
- **Test: Client Example** - Testa cliente
- **Docker: Logs** - Mostra logs em tempo real

### Debug (F5)
- **MCP Server: Debug Local** - Debug modo desenvolvimento
- **MCP Server: Debug READ_ONLY** - Debug modo somente leitura
- **MCP Server: Debug FULL_ACCESS** - Debug modo completo
- **Test: Example Client** - Debug cliente de exemplo

## 🔧 Configuração MCP no Cursor

### 1. Arquivo de Configuração
Crie/edite `.cursor/mcp-config.json`:
```json
{
  "mcpServers": {
    "sqlserver": {
      "command": "python",
      "args": ["-m", "src.main"],
      "cwd": "./",
      "env": {
        "DB_HOST": "localhost",
        "DB_PASSWORD": "YourPassword",
        "MCP_MODE": "READ_ONLY"
      }
    }
  }
}
```

### 2. Via HTTP (Docker)
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

## 📊 URLs Importantes

- **API Docs**: http://localhost:4000/docs
- **Health Check**: http://localhost:4000/health
- **Server Info**: http://localhost:4000/info
- **Tools List**: http://localhost:4000/tools

## 🐛 Resolução Rápida

### Docker não inicia
```bash
docker --version  # Verificar se Docker está instalado
docker ps         # Verificar se Docker está rodando
```

### Erro de conexão SQL Server
```bash
# Verificar variáveis no .env
cat .env | grep DB_

# Testar conexão
telnet localhost 1433
```

### MCP Server não responde
```bash
# Verificar logs
docker-compose logs mcp-sqlserver

# Restart
docker-compose restart mcp-sqlserver
```

### Erro de dependências Python
```bash
# Recriar ambiente
rm -rf venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

## 📁 Estrutura Importante

```
NewSQL-Server-MCP/
├── 📄 .env                  ← Configure suas credenciais
├── 📄 docker-compose.yml    ← Deploy completo
├── 📄 example_client.py     ← Teste suas operações
├── 📁 .vscode/              ← Configurações do Cursor
│   ├── settings.json        ← Configurações Python
│   ├── tasks.json           ← Tasks automatizadas
│   └── launch.json          ← Configurações debug
└── 📁 src/                  ← Código fonte
    ├── main.py              ← Aplicação principal
    ├── mcp_server.py        ← Servidor MCP
    └── ...
```

## 💡 Dicas Pro

1. **Use Tasks**: Ctrl+Shift+P → "Tasks" para comandos rápidos
2. **Debug Mode**: F5 para debugar com breakpoints
3. **Terminal Split**: Ctrl+Shift+5 para múltiplos terminais
4. **Logs em Tempo Real**: Use task "Docker: Logs" 
5. **Health Monitoring**: Use task "Test: Health Check"

## 🎯 Próximos Passos

1. ✅ Configure `.env` com suas credenciais
2. ✅ Execute `docker-compose up -d`
3. ✅ Acesse http://localhost:4000/docs
4. ✅ Execute `python example_client.py`
5. ✅ Configure MCP no Cursor
6. 🚀 **Comece a usar suas ferramentas SQL!**

---

**💬 Precisa de ajuda?** Consulte o [README.md](README.md) completo ou abra uma issue!
