@echo off
REM Script para executar o MCP SQL Server no Windows

echo.
echo ================================
echo   Iniciando MCP SQL Server
echo ================================
echo.

REM Verifica se .env existe
if not exist .env (
    echo ❌ Arquivo .env não encontrado!
    echo    Execute setup.bat primeiro
    pause
    exit /b 1
)

REM Ativa ambiente virtual se existir
if exist venv\Scripts\activate.bat (
    echo 🔄 Ativando ambiente virtual...
    call venv\Scripts\activate.bat
)

REM Executa o servidor
echo 🚀 Iniciando servidor...
echo    Acesse: http://localhost:4000/docs
echo    Pressione Ctrl+C para parar
echo.

python -m src.main

pause
