# Dockerfile Ultra-Simplificado para MCP SQL Server
FROM python:3.11-slim

# Configurações básicas
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    TZ=America/Sao_Paulo

# Instala dependências do sistema e drivers ODBC
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates gnupg2 unixodbc-dev unixodbc tzdata \
    && curl -sSL https://packages.microsoft.com/keys/microsoft.asc | \
       gpg --dearmor --output /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > \
       /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql17 \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Instala dependências Python DIRETAMENTE no Python global
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt \
    && pip list \
    && python -c "import uvicorn, fastapi, pyodbc; print('✅ TODAS as dependências instaladas!')"

# Cria usuário não-root
RUN groupadd -g 1000 mcpuser \
    && useradd -u 1000 -g mcpuser -s /bin/bash -m mcpuser \
    && mkdir -p /app /app/logs \
    && chown -R mcpuser:mcpuser /app

# Define diretório e copia arquivos
WORKDIR /app
COPY --chown=mcpuser:mcpuser src/ ./src/
COPY --chown=mcpuser:mcpuser config/.env.example ./config/.env.example

# Muda para usuário não-root
USER mcpuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=2 \
    CMD curl -f http://localhost:4000/health || exit 1

# Expõe porta
EXPOSE 4000

# Comando simples
CMD ["python", "-m", "src.main"]