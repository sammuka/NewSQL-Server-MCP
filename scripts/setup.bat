@echo off
REM Setup script para MCP SQL Server no Windows
REM Automatiza a configuração inicial do projeto

echo.
echo ============================================
echo    MCP SQL Server - Setup para Windows
echo ============================================
echo.

REM Verifica se Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python não encontrado!
    echo    Instale Python 3.11+ de https://python.org
    pause
    exit /b 1
)

echo ✅ Python encontrado
python --version

REM Verifica se pip está disponível
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip não encontrado!
    pause
    exit /b 1
)

echo ✅ pip encontrado

REM Cria ambiente virtual se não existir
if not exist venv (
    echo.
    echo 📦 Criando ambiente virtual...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ❌ Erro ao criar ambiente virtual
        pause
        exit /b 1
    )
    echo ✅ Ambiente virtual criado
)

REM Ativa ambiente virtual
echo.
echo 🔄 Ativando ambiente virtual...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ Erro ao ativar ambiente virtual
    pause
    exit /b 1
)

echo ✅ Ambiente virtual ativado

REM Atualiza pip
echo.
echo 🔄 Atualizando pip...
python -m pip install --upgrade pip

REM Instala dependências
echo.
echo 📦 Instalando dependências...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Erro ao instalar dependências
    pause
    exit /b 1
)

echo ✅ Dependências instaladas

REM Cria arquivo .env se não existir
if not exist .env (
    echo.
    echo 📝 Criando arquivo .env...
    copy config\.env.example .env >nul
    echo ✅ Arquivo .env criado
    echo.
    echo ⚠️  IMPORTANTE: Configure as variáveis em .env antes de executar!
) else (
    echo.
    echo ℹ️  Arquivo .env já existe
)

REM Cria diretório de logs
if not exist logs (
    mkdir logs
    echo ✅ Diretório de logs criado
)

echo.
echo ============================================
echo              🎉 Setup Concluído!
echo ============================================
echo.
echo 📋 Próximos passos:
echo.
echo 1. Configure o arquivo .env com suas credenciais SQL Server
echo 2. Execute o servidor:
echo    - Desenvolvimento: python -m src.main
echo    - Produção: python -m src.main
echo.
echo 3. Acesse a documentação: http://localhost:4000/docs
echo.
echo 🔧 Comandos úteis:
echo    run.bat          - Executa o servidor
echo    test-client.bat  - Testa o cliente
echo    docker-up.bat    - Inicia com Docker
echo.
echo ❓ Precisa de ajuda? Consulte README.md
echo.

pause
