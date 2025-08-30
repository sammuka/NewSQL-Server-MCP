@echo off
REM Script para executar MCP SQL Server com Docker no Windows

echo.
echo ========================================
echo   MCP SQL Server - Docker Deployment
echo ========================================
echo.

REM Verifica se Docker está instalado
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker não encontrado!
    echo    Instale Docker Desktop de https://docker.com
    pause
    exit /b 1
)

echo ✅ Docker encontrado
docker --version

REM Verifica se docker-compose está disponível
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ docker-compose não encontrado!
    pause
    exit /b 1
)

echo ✅ docker-compose encontrado

REM Verifica se .env existe
if not exist .env (
    echo.
    echo 📝 Criando arquivo .env...
    copy config\.env.example .env >nul
    echo ✅ Arquivo .env criado
    echo.
    echo ⚠️  IMPORTANTE: Configure as variáveis em .env!
    echo    Especialmente DB_PASSWORD para o SQL Server
    echo.
    pause
)

echo.
echo 🐳 Escolha o modo de deployment:
echo.
echo 1. Completo (MCP Server + SQL Server) - Recomendado para desenvolvimento
echo 2. Apenas MCP Server - Para usar com SQL Server externo
echo.

set /p choice="Digite sua escolha (1 ou 2): "

if "%choice%"=="1" (
    echo.
    echo 🚀 Iniciando deployment completo...
    docker-compose -f docker/docker-compose.yml up -d
) else if "%choice%"=="2" (
    echo.
    echo 🚀 Iniciando apenas MCP Server...
    docker-compose -f docker/docker-compose.mcp-only.yml up -d
) else (
    echo ❌ Escolha inválida!
    pause
    exit /b 1
)

if %errorlevel% neq 0 (
    echo ❌ Erro ao iniciar containers!
    pause
    exit /b 1
)

echo.
echo ✅ Containers iniciados com sucesso!
echo.
echo 📊 Status dos containers:
docker-compose -f docker/docker-compose.yml ps

echo.
echo 🌐 Serviços disponíveis:
echo    - API: http://localhost:4000
echo    - Docs: http://localhost:4000/docs
echo    - Health: http://localhost:4000/health

if "%choice%"=="1" (
    echo    - SQL Server: localhost:1433
)

echo.
echo 📋 Comandos úteis:
echo    docker-compose -f docker/docker-compose.yml logs -f mcp-sqlserver    # Ver logs
echo    docker-compose -f docker/docker-compose.yml down                     # Parar containers
echo    docker-compose -f docker/docker-compose.yml restart mcp-sqlserver    # Reiniciar MCP
echo.

echo 🧪 Testar servidor? (y/n)
set /p test="Digite sua escolha: "

if /i "%test%"=="y" (
    echo.
    echo 🔍 Testando servidor...
    timeout /t 5 /nobreak >nul
    curl http://localhost:4000/health
    echo.
)

echo.
echo 🎉 Deployment concluído!
pause
