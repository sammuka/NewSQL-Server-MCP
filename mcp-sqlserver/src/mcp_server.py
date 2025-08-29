"""
Servidor Model Context Protocol (MCP) para SQL Server
Implementa o protocolo MCP com ferramentas específicas para SQL Server
"""

import os
import asyncio
import structlog
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json
from dataclasses import asdict

# Configuração de logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if os.getenv("LOG_FORMAT") == "json" else structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Imports das ferramentas
from .tools.read_tools import ReadOnlyTools
from .tools.write_tools import FullAccessTools
from .database.connection import get_connection, close_connections


class MCPSQLServerConfig:
    """Configuração do servidor MCP"""
    
    def __init__(self):
        self.mode = os.getenv("MCP_MODE", "READ_ONLY")
        self.host = os.getenv("MCP_HOST", "0.0.0.0")
        self.port = int(os.getenv("MCP_PORT", "4000"))
        self.rate_limit = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
        self.query_timeout = int(os.getenv("QUERY_TIMEOUT", "30"))
        self.max_result_rows = int(os.getenv("MAX_RESULT_ROWS", "1000"))
        
        # Validação do modo
        if self.mode not in ["READ_ONLY", "FULL_ACCESS"]:
            raise ValueError(f"MCP_MODE deve ser 'READ_ONLY' ou 'FULL_ACCESS', recebido: {self.mode}")


class RateLimiter:
    """Limitador de taxa simples baseado em tokens"""
    
    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
        
    def is_allowed(self, client_id: str) -> bool:
        """Verifica se a requisição é permitida"""
        now = datetime.now().timestamp()
        
        # Remove requisições antigas
        if client_id in self.requests:
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if now - req_time < self.window_seconds
            ]
        
        # Verifica limite
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        if len(self.requests[client_id]) >= self.max_requests:
            return False
        
        # Adiciona nova requisição
        self.requests[client_id].append(now)
        return True


class MCPSQLServer:
    """Servidor MCP principal para SQL Server"""
    
    def __init__(self, config: Optional[MCPSQLServerConfig] = None):
        self.config = config or MCPSQLServerConfig()
        self.rate_limiter = RateLimiter(self.config.rate_limit)
        self.is_running = False
        
        # Inicializa ferramentas baseado no modo
        if self.config.mode == "READ_ONLY":
            self.tools = ReadOnlyTools()
            logger.info("Servidor iniciado em modo READ_ONLY")
        else:
            self.tools = FullAccessTools()
            logger.info("Servidor iniciado em modo FULL_ACCESS")
        
        # Registro de ferramentas disponíveis
        self._register_tools()
    
    def _register_tools(self):
        """Registra todas as ferramentas disponíveis"""
        self.available_tools = {}
        
        # Ferramentas READ_ONLY (sempre disponíveis)
        readonly_tools = {
            "list_tables": {
                "description": "Lista todas as tabelas do banco de dados",
                "parameters": {
                    "schema": {"type": "string", "required": False, "description": "Nome do schema (opcional)"}
                }
            },
            "describe_table": {
                "description": "Obtém a estrutura detalhada de uma tabela",
                "parameters": {
                    "table_name": {"type": "string", "required": True, "description": "Nome da tabela"},
                    "schema": {"type": "string", "required": False, "description": "Nome do schema (opcional)"}
                }
            },
            "list_columns": {
                "description": "Lista colunas de uma tabela",
                "parameters": {
                    "table_name": {"type": "string", "required": True, "description": "Nome da tabela"},
                    "schema": {"type": "string", "required": False, "description": "Nome do schema (opcional)"}
                }
            },
            "list_indexes": {
                "description": "Lista índices de uma tabela",
                "parameters": {
                    "table_name": {"type": "string", "required": True, "description": "Nome da tabela"},
                    "schema": {"type": "string", "required": False, "description": "Nome do schema (opcional)"}
                }
            },
            "list_views": {
                "description": "Lista todas as views do banco",
                "parameters": {}
            },
            "list_procedures": {
                "description": "Lista stored procedures do banco",
                "parameters": {}
            },
            "list_functions": {
                "description": "Lista funções do banco",
                "parameters": {}
            },
            "execute_select": {
                "description": "Executa uma query SELECT com validação de segurança",
                "parameters": {
                    "query": {"type": "string", "required": True, "description": "Query SELECT a ser executada"},
                    "limit": {"type": "integer", "required": False, "description": "Limite de registros"}
                }
            },
            "get_table_data": {
                "description": "Obtém dados de uma tabela com paginação",
                "parameters": {
                    "table_name": {"type": "string", "required": True, "description": "Nome da tabela"},
                    "schema": {"type": "string", "required": False, "description": "Nome do schema (opcional)"},
                    "limit": {"type": "integer", "required": False, "description": "Número máximo de registros"},
                    "offset": {"type": "integer", "required": False, "description": "Número de registros para pular"}
                }
            },
            "get_database_schema": {
                "description": "Obtém esquema completo do banco de dados",
                "parameters": {}
            },
            "check_constraints": {
                "description": "Lista constraints de uma tabela",
                "parameters": {
                    "table_name": {"type": "string", "required": True, "description": "Nome da tabela"},
                    "schema": {"type": "string", "required": False, "description": "Nome do schema (opcional)"}
                }
            }
        }
        
        self.available_tools.update(readonly_tools)
        
        # Ferramentas FULL_ACCESS (apenas se modo permitir)
        if self.config.mode == "FULL_ACCESS":
            write_tools = {
                "execute_query": {
                    "description": "Executa qualquer query SQL (disponível apenas em FULL_ACCESS)",
                    "parameters": {
                        "query": {"type": "string", "required": True, "description": "Query SQL a ser executada"},
                        "params": {"type": "array", "required": False, "description": "Parâmetros para a query"}
                    }
                },
                "create_table": {
                    "description": "Cria uma nova tabela",
                    "parameters": {
                        "table_name": {"type": "string", "required": True, "description": "Nome da tabela"},
                        "columns": {"type": "array", "required": True, "description": "Definições das colunas"},
                        "schema": {"type": "string", "required": False, "description": "Nome do schema"}
                    }
                },
                "alter_table": {
                    "description": "Altera estrutura de uma tabela",
                    "parameters": {
                        "table_name": {"type": "string", "required": True, "description": "Nome da tabela"},
                        "operation": {"type": "string", "required": True, "description": "Operação (ADD_COLUMN, DROP_COLUMN, ALTER_COLUMN)"},
                        "column_definition": {"type": "object", "required": False, "description": "Definição da coluna"},
                        "schema": {"type": "string", "required": False, "description": "Nome do schema"}
                    }
                },
                "drop_table": {
                    "description": "Remove uma tabela",
                    "parameters": {
                        "table_name": {"type": "string", "required": True, "description": "Nome da tabela"},
                        "schema": {"type": "string", "required": False, "description": "Nome do schema"}
                    }
                },
                "insert_data": {
                    "description": "Insere dados em uma tabela",
                    "parameters": {
                        "table_name": {"type": "string", "required": True, "description": "Nome da tabela"},
                        "data": {"type": "array", "required": True, "description": "Dados a inserir"},
                        "schema": {"type": "string", "required": False, "description": "Nome do schema"}
                    }
                },
                "update_data": {
                    "description": "Atualiza dados em uma tabela",
                    "parameters": {
                        "table_name": {"type": "string", "required": True, "description": "Nome da tabela"},
                        "set_values": {"type": "object", "required": True, "description": "Valores a atualizar"},
                        "where_clause": {"type": "string", "required": True, "description": "Cláusula WHERE"},
                        "where_params": {"type": "array", "required": False, "description": "Parâmetros do WHERE"},
                        "schema": {"type": "string", "required": False, "description": "Nome do schema"}
                    }
                },
                "delete_data": {
                    "description": "Deleta dados de uma tabela",
                    "parameters": {
                        "table_name": {"type": "string", "required": True, "description": "Nome da tabela"},
                        "where_clause": {"type": "string", "required": True, "description": "Cláusula WHERE"},
                        "where_params": {"type": "array", "required": False, "description": "Parâmetros do WHERE"},
                        "schema": {"type": "string", "required": False, "description": "Nome do schema"}
                    }
                },
                "create_index": {
                    "description": "Cria um índice",
                    "parameters": {
                        "index_name": {"type": "string", "required": True, "description": "Nome do índice"},
                        "table_name": {"type": "string", "required": True, "description": "Nome da tabela"},
                        "columns": {"type": "array", "required": True, "description": "Colunas do índice"},
                        "unique": {"type": "boolean", "required": False, "description": "Índice único"},
                        "schema": {"type": "string", "required": False, "description": "Nome do schema"}
                    }
                },
                "drop_index": {
                    "description": "Remove um índice",
                    "parameters": {
                        "index_name": {"type": "string", "required": True, "description": "Nome do índice"},
                        "table_name": {"type": "string", "required": True, "description": "Nome da tabela"},
                        "schema": {"type": "string", "required": False, "description": "Nome do schema"}
                    }
                },
                "execute_procedure": {
                    "description": "Executa uma stored procedure",
                    "parameters": {
                        "procedure_name": {"type": "string", "required": True, "description": "Nome da procedure"},
                        "params": {"type": "array", "required": False, "description": "Parâmetros da procedure"},
                        "schema": {"type": "string", "required": False, "description": "Nome do schema"}
                    }
                },
                "backup_table": {
                    "description": "Faz backup de uma tabela",
                    "parameters": {
                        "table_name": {"type": "string", "required": True, "description": "Nome da tabela"},
                        "backup_name": {"type": "string", "required": False, "description": "Nome do backup"},
                        "schema": {"type": "string", "required": False, "description": "Nome do schema"}
                    }
                }
            }
            
            self.available_tools.update(write_tools)
        
        logger.info("Ferramentas registradas", 
                   mode=self.config.mode, 
                   tool_count=len(self.available_tools))
    
    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any], 
                              client_id: str = "default") -> Dict[str, Any]:
        """
        Manipula chamadas de ferramentas
        
        Args:
            tool_name: Nome da ferramenta
            arguments: Argumentos da ferramenta
            client_id: ID do cliente para rate limiting
            
        Returns:
            Dict com resultado da operação
        """
        start_time = datetime.now()
        
        try:
            # Verifica rate limiting
            if not self.rate_limiter.is_allowed(client_id):
                logger.warning("Rate limit excedido", client_id=client_id, tool=tool_name)
                return {
                    "success": False,
                    "error": "Rate limit excedido. Aguarde antes de fazer nova requisição.",
                    "error_code": "RATE_LIMIT_EXCEEDED"
                }
            
            # Verifica se a ferramenta existe
            if tool_name not in self.available_tools:
                logger.error("Ferramenta não encontrada", tool=tool_name)
                return {
                    "success": False,
                    "error": f"Ferramenta '{tool_name}' não encontrada",
                    "error_code": "TOOL_NOT_FOUND"
                }
            
            # Log da chamada
            logger.info("Chamada de ferramenta", 
                       tool=tool_name, 
                       client_id=client_id,
                       args_keys=list(arguments.keys()))
            
            # Chama a ferramenta correspondente
            if hasattr(self.tools, tool_name):
                method = getattr(self.tools, tool_name)
                result = await method(**arguments)
            else:
                return {
                    "success": False,
                    "error": f"Método '{tool_name}' não implementado",
                    "error_code": "METHOD_NOT_IMPLEMENTED"
                }
            
            # Calcula tempo de execução
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Adiciona metadados ao resultado
            if isinstance(result, dict):
                result["execution_time"] = execution_time
                result["tool_name"] = tool_name
                result["timestamp"] = datetime.now().isoformat()
            
            logger.info("Ferramenta executada com sucesso",
                       tool=tool_name,
                       execution_time=execution_time,
                       success=result.get("success", True))
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error("Erro ao executar ferramenta",
                        tool=tool_name,
                        error=str(e),
                        execution_time=execution_time)
            
            return {
                "success": False,
                "error": str(e),
                "error_code": "EXECUTION_ERROR",
                "execution_time": execution_time,
                "tool_name": tool_name,
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_available_tools(self) -> Dict[str, Any]:
        """Retorna lista de ferramentas disponíveis"""
        return {
            "tools": self.available_tools,
            "mode": self.config.mode,
            "server_info": {
                "version": "1.0.0",
                "mode": self.config.mode,
                "max_result_rows": self.config.max_result_rows,
                "query_timeout": self.config.query_timeout,
                "rate_limit": self.config.rate_limit
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica a saúde do servidor e conexão com banco"""
        try:
            # Verifica conexão com banco
            db = await get_connection()
            db_healthy = await db.health_check()
            
            health_status = {
                "status": "healthy" if db_healthy else "unhealthy",
                "database_connection": db_healthy,
                "server_running": self.is_running,
                "mode": self.config.mode,
                "timestamp": datetime.now().isoformat(),
                "uptime": "N/A"  # Implementar se necessário
            }
            
            logger.info("Health check realizado", 
                       status=health_status["status"],
                       db_healthy=db_healthy)
            
            return health_status
            
        except Exception as e:
            logger.error("Erro no health check", error=str(e))
            return {
                "status": "unhealthy",
                "database_connection": False,
                "server_running": self.is_running,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_server_info(self) -> Dict[str, Any]:
        """Retorna informações do servidor"""
        return {
            "name": "MCP SQL Server",
            "version": "1.0.0",
            "mode": self.config.mode,
            "tools_count": len(self.available_tools),
            "configuration": {
                "host": self.config.host,
                "port": self.config.port,
                "max_result_rows": self.config.max_result_rows,
                "query_timeout": self.config.query_timeout,
                "rate_limit": self.config.rate_limit
            },
            "status": "running" if self.is_running else "stopped"
        }
    
    async def start(self):
        """Inicia o servidor MCP"""
        try:
            logger.info("Iniciando servidor MCP", 
                       mode=self.config.mode,
                       host=self.config.host,
                       port=self.config.port)
            
            # Inicializa conexão com banco
            await get_connection()
            
            self.is_running = True
            logger.info("Servidor MCP iniciado com sucesso")
            
        except Exception as e:
            logger.error("Erro ao iniciar servidor MCP", error=str(e))
            raise
    
    async def stop(self):
        """Para o servidor MCP"""
        try:
            logger.info("Parando servidor MCP")
            
            self.is_running = False
            
            # Fecha conexões com banco
            await close_connections()
            
            logger.info("Servidor MCP parado com sucesso")
            
        except Exception as e:
            logger.error("Erro ao parar servidor MCP", error=str(e))
            raise


# Instância global do servidor
_mcp_server: Optional[MCPSQLServer] = None


async def get_mcp_server() -> MCPSQLServer:
    """Obtém a instância global do servidor MCP"""
    global _mcp_server
    
    if _mcp_server is None:
        config = MCPSQLServerConfig()
        _mcp_server = MCPSQLServer(config)
        await _mcp_server.start()
    
    return _mcp_server


async def shutdown_mcp_server():
    """Para o servidor MCP global"""
    global _mcp_server
    
    if _mcp_server:
        await _mcp_server.stop()
        _mcp_server = None
