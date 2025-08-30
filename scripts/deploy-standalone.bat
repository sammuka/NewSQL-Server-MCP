@echo off
echo 🚀 ===========================================
echo    DEPLOY STANDALONE - MCP SQL SERVER
echo ===========================================

cd /d "%~dp0.."

echo.
echo 🛑 Parando containers anteriores...
docker-compose -f docker/docker-compose.mcp-only.yml down 2>nul

echo.
echo ⚙️ Configurando variáveis de ambiente...
set DB_HOST=host.docker.internal
set DB_PORT=1433
set DB_NAME=master
set DB_USER=sa
set DB_PASSWORD=TestPassword123!
set MCP_MODE=READ_ONLY
set MCP_PORT=4000
set LOG_FORMAT=console
set TZ=America/Sao_Paulo

echo.
echo 🚀 Iniciando MCP Server em modo standalone...
docker run -d ^
  --name mcp-sqlserver ^
  --network bridge ^
  -p 4000:4000 ^
  -e DB_HOST=%DB_HOST% ^
  -e DB_PORT=%DB_PORT% ^
  -e DB_NAME=%DB_NAME% ^
  -e DB_USER=%DB_USER% ^
  -e DB_PASSWORD=%DB_PASSWORD% ^
  -e MCP_MODE=%MCP_MODE% ^
  -e MCP_PORT=%MCP_PORT% ^
  -e MCP_HOST=0.0.0.0 ^
  -e LOG_FORMAT=%LOG_FORMAT% ^
  -e TZ=%TZ% ^
  -e QUERY_TIMEOUT=30 ^
  -e RATE_LIMIT_PER_MINUTE=60 ^
  --restart unless-stopped ^
  mcp-sqlserver:final

echo.
echo ⏱️ Aguardando 10 segundos para inicialização...
timeout /t 10 >nul

echo.
echo 🔍 Status do container...
docker ps | findstr mcp-sqlserver

echo.
echo 📋 Logs do container...
docker logs mcp-sqlserver --tail=15

echo.
echo 🧪 Teste do endpoint...
curl -s http://localhost:4000/health

echo.
echo ✅ ===========================================
echo    DEPLOY STANDALONE CONCLUÍDO!
echo ===========================================
echo.
echo 📌 Container: mcp-sqlserver
echo 📌 Porta: http://localhost:4000
echo 📌 Health: http://localhost:4000/health
echo.
pause
