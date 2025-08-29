"""
Aplicação principal do MCP SQL Server
FastAPI app que expõe endpoints para interação com o servidor MCP
"""

import os
import asyncio
import uvicorn
import structlog
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import pytz

# Carrega variáveis de ambiente
load_dotenv()

# Configura timezone
if os.getenv("TZ"):
    os.environ["TZ"] = os.getenv("TZ", "America/Sao_Paulo")

# Imports do projeto
from .mcp_server import get_mcp_server, shutdown_mcp_server

logger = structlog.get_logger(__name__)


# Modelos Pydantic para requests
class ToolCallRequest(BaseModel):
    tool_name: str = Field(..., description="Nome da ferramenta a ser executada")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Argumentos para a ferramenta")
    client_id: Optional[str] = Field(default="default", description="ID do cliente")


class HealthResponse(BaseModel):
    status: str
    database_connection: bool
    server_running: bool
    timestamp: str
    mode: Optional[str] = None
    error: Optional[str] = None


class ServerInfoResponse(BaseModel):
    name: str
    version: str
    mode: str
    tools_count: int
    configuration: Dict[str, Any]
    status: str


class ToolsResponse(BaseModel):
    tools: Dict[str, Any]
    mode: str
    server_info: Dict[str, Any]


# Context manager para ciclo de vida da aplicação
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação"""
    try:
        logger.info("Iniciando aplicação MCP SQL Server")
        
        # Inicializa servidor MCP
        await get_mcp_server()
        
        logger.info("Aplicação iniciada com sucesso")
        yield
        
    except Exception as e:
        logger.error("Erro ao iniciar aplicação", error=str(e))
        raise
    
    finally:
        logger.info("Encerrando aplicação")
        try:
            await shutdown_mcp_server()
            logger.info("Aplicação encerrada com sucesso")
        except Exception as e:
            logger.error("Erro ao encerrar aplicação", error=str(e))


# Cria aplicação FastAPI
app = FastAPI(
    title="MCP SQL Server",
    description="Model Context Protocol server para SQL Server",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure adequadamente em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware para logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para logging de requisições"""
    start_time = asyncio.get_event_loop().time()
    
    # Log da requisição
    logger.info("Requisição recebida",
               method=request.method,
               url=str(request.url),
               client_ip=request.client.host if request.client else None)
    
    # Processa requisição
    response = await call_next(request)
    
    # Log da resposta
    process_time = asyncio.get_event_loop().time() - start_time
    logger.info("Requisição processada",
               method=request.method,
               url=str(request.url),
               status_code=response.status_code,
               process_time=process_time)
    
    return response


# Exception handler personalizado
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global para exceções"""
    logger.error("Erro não tratado",
                error=str(exc),
                method=request.method,
                url=str(request.url))
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Erro interno do servidor",
            "error_code": "INTERNAL_SERVER_ERROR"
        }
    )


# Endpoints
@app.get("/", summary="Raiz da API")
async def root():
    """Endpoint raiz da API"""
    return {
        "message": "MCP SQL Server está rodando",
        "version": "1.0.0",
        "documentation": "/docs"
    }


@app.get("/health", response_model=HealthResponse, summary="Health Check")
async def health_check():
    """
    Verifica a saúde do servidor e conexão com banco de dados
    """
    try:
        mcp_server = await get_mcp_server()
        health_data = await mcp_server.health_check()
        
        return HealthResponse(**health_data)
        
    except Exception as e:
        logger.error("Erro no health check", error=str(e))
        return HealthResponse(
            status="unhealthy",
            database_connection=False,
            server_running=False,
            timestamp="",
            error=str(e)
        )


@app.get("/info", response_model=ServerInfoResponse, summary="Informações do Servidor")
async def server_info():
    """
    Retorna informações detalhadas do servidor MCP
    """
    try:
        mcp_server = await get_mcp_server()
        info_data = await mcp_server.get_server_info()
        
        return ServerInfoResponse(**info_data)
        
    except Exception as e:
        logger.error("Erro ao obter informações do servidor", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tools", response_model=ToolsResponse, summary="Ferramentas Disponíveis")
async def list_tools():
    """
    Lista todas as ferramentas disponíveis no servidor MCP
    """
    try:
        mcp_server = await get_mcp_server()
        tools_data = await mcp_server.get_available_tools()
        
        return ToolsResponse(**tools_data)
        
    except Exception as e:
        logger.error("Erro ao listar ferramentas", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/call", summary="Executar Ferramenta")
async def call_tool(request: ToolCallRequest):
    """
    Executa uma ferramenta específica do servidor MCP
    
    Args:
        request: Dados da requisição contendo nome da ferramenta e argumentos
        
    Returns:
        Resultado da execução da ferramenta
    """
    try:
        mcp_server = await get_mcp_server()
        
        result = await mcp_server.handle_tool_call(
            tool_name=request.tool_name,
            arguments=request.arguments,
            client_id=request.client_id or "default"
        )
        
        # Se a operação falhou, retorna erro HTTP apropriado
        if not result.get("success", True):
            error_code = result.get("error_code", "UNKNOWN_ERROR")
            
            if error_code == "RATE_LIMIT_EXCEEDED":
                raise HTTPException(status_code=429, detail=result["error"])
            elif error_code == "TOOL_NOT_FOUND":
                raise HTTPException(status_code=404, detail=result["error"])
            elif error_code in ["METHOD_NOT_IMPLEMENTED", "EXECUTION_ERROR"]:
                raise HTTPException(status_code=500, detail=result["error"])
            else:
                raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao executar ferramenta", 
                    tool=request.tool_name, 
                    error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Endpoints específicos para facilitar integração
@app.get("/database/tables", summary="Listar Tabelas")
async def list_tables_endpoint(schema: Optional[str] = None):
    """Endpoint simplificado para listar tabelas"""
    request = ToolCallRequest(
        tool_name="list_tables",
        arguments={"schema": schema} if schema else {}
    )
    return await call_tool(request)


@app.get("/database/tables/{table_name}", summary="Descrever Tabela")
async def describe_table_endpoint(table_name: str, schema: Optional[str] = None):
    """Endpoint simplificado para descrever tabela"""
    request = ToolCallRequest(
        tool_name="describe_table",
        arguments={"table_name": table_name, "schema": schema}
    )
    return await call_tool(request)


@app.get("/database/tables/{table_name}/data", summary="Obter Dados da Tabela")
async def get_table_data_endpoint(
    table_name: str, 
    schema: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """Endpoint simplificado para obter dados da tabela"""
    request = ToolCallRequest(
        tool_name="get_table_data",
        arguments={
            "table_name": table_name,
            "schema": schema,
            "limit": limit,
            "offset": offset
        }
    )
    return await call_tool(request)


@app.get("/database/views", summary="Listar Views")
async def list_views_endpoint():
    """Endpoint simplificado para listar views"""
    request = ToolCallRequest(tool_name="list_views", arguments={})
    return await call_tool(request)


@app.get("/database/procedures", summary="Listar Procedures")
async def list_procedures_endpoint():
    """Endpoint simplificado para listar procedures"""
    request = ToolCallRequest(tool_name="list_procedures", arguments={})
    return await call_tool(request)


@app.get("/database/functions", summary="Listar Funções")
async def list_functions_endpoint():
    """Endpoint simplificado para listar funções"""
    request = ToolCallRequest(tool_name="list_functions", arguments={})
    return await call_tool(request)


@app.get("/database/schema", summary="Esquema do Banco")
async def get_database_schema_endpoint():
    """Endpoint simplificado para obter esquema do banco"""
    request = ToolCallRequest(tool_name="get_database_schema", arguments={})
    return await call_tool(request)


# Endpoint para executar SELECT (apenas em modo READ_ONLY)
@app.post("/database/select", summary="Executar SELECT")
async def execute_select_endpoint(query: str, limit: Optional[int] = None):
    """Endpoint para executar queries SELECT"""
    request = ToolCallRequest(
        tool_name="execute_select",
        arguments={"query": query, "limit": limit}
    )
    return await call_tool(request)


# Função principal para execução direta
def main():
    """Função principal para executar o servidor"""
    config = {
        "host": os.getenv("MCP_HOST", "0.0.0.0"),
        "port": int(os.getenv("MCP_PORT", "4000")),
        "log_level": os.getenv("LOG_LEVEL", "info").lower(),
        "reload": os.getenv("ENVIRONMENT", "production") == "development"
    }
    
    logger.info("Iniciando servidor FastAPI", **config)
    
    uvicorn.run(
        "src.main:app",
        **config
    )


if __name__ == "__main__":
    main()
