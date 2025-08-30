"""
Módulo de conexão com SQL Server
Gerencia pool de conexões, configurações de segurança e tratamento de erros
"""

import os
import asyncio
import pyodbc
import structlog
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import threading
from queue import Queue, Empty
from dataclasses import dataclass

logger = structlog.get_logger(__name__)


@dataclass
class ConnectionConfig:
    """Configuração de conexão com o banco de dados"""
    host: str
    port: int
    database: str
    username: str
    password: str
    timeout: int = 30
    pool_size: int = 10
    max_overflow: int = 20
    
    @classmethod
    def from_env(cls) -> "ConnectionConfig":
        """Cria configuração a partir de variáveis de ambiente"""
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "1433")),
            database=os.getenv("DB_NAME", "master"),
            username=os.getenv("DB_USER", "sa"),
            password=os.getenv("DB_PASSWORD", ""),
            timeout=int(os.getenv("QUERY_TIMEOUT", "30")),
            pool_size=int(os.getenv("CONNECTION_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("CONNECTION_POOL_MAX_OVERFLOW", "20"))
        )


class ConnectionPool:
    """Pool de conexões thread-safe para SQL Server"""
    
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self._pool: Queue = Queue(maxsize=config.pool_size + config.max_overflow)
        self._lock = threading.Lock()
        self._created_connections = 0
        self._max_connections = config.pool_size + config.max_overflow
        self._initialize_pool()
        
    def _initialize_pool(self):
        """Inicializa o pool com conexões"""
        for _ in range(self.config.pool_size):
            try:
                conn = self._create_connection()
                self._pool.put(conn)
                self._created_connections += 1
            except Exception as e:
                logger.error("Erro ao inicializar pool de conexões", error=str(e))
                
    def _create_connection(self) -> pyodbc.Connection:
        """Cria uma nova conexão com SQL Server"""
        connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={self.config.host},{self.config.port};"
            f"DATABASE={self.config.database};"
            f"UID={self.config.username};"
            f"PWD={self.config.password};"
            f"TrustServerCertificate=yes;"
            f"Connection Timeout={self.config.timeout};"
        )
        
        try:
            connection = pyodbc.connect(connection_string)
            connection.timeout = self.config.timeout
            logger.debug("Nova conexão criada", 
                        host=self.config.host,
                        database=self.config.database)
            return connection
        except Exception as e:
            logger.error("Erro ao criar conexão", 
                        error=str(e),
                        host=self.config.host,
                        database=self.config.database)
            raise
    
    def get_connection(self, timeout: float = 5.0) -> pyodbc.Connection:
        """Obtém uma conexão do pool"""
        try:
            # Tenta obter uma conexão do pool
            connection = self._pool.get(timeout=timeout)
            
            # Verifica se a conexão ainda está válida
            try:
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                return connection
            except:
                # Conexão inválida, cria uma nova
                logger.warning("Conexão inválida detectada, criando nova")
                connection.close()
                return self._create_new_connection()
                
        except Empty:
            # Pool vazio, tenta criar nova conexão se possível
            return self._create_new_connection()
    
    def _create_new_connection(self) -> pyodbc.Connection:
        """Cria nova conexão se limite não foi atingido"""
        with self._lock:
            if self._created_connections < self._max_connections:
                connection = self._create_connection()
                self._created_connections += 1
                return connection
            else:
                raise Exception("Limite máximo de conexões atingido")
    
    def return_connection(self, connection: pyodbc.Connection):
        """Retorna uma conexão para o pool"""
        try:
            if connection and not connection.closed:
                self._pool.put_nowait(connection)
            else:
                # Conexão fechada, decrementa contador
                with self._lock:
                    self._created_connections -= 1
        except:
            # Pool cheio, fecha a conexão
            try:
                connection.close()
                with self._lock:
                    self._created_connections -= 1
            except:
                pass
    
    def close_all(self):
        """Fecha todas as conexões do pool"""
        while not self._pool.empty():
            try:
                connection = self._pool.get_nowait()
                connection.close()
            except:
                pass
        self._created_connections = 0


class DatabaseConnection:
    """Gerenciador de conexão com SQL Server"""
    
    def __init__(self, config: Optional[ConnectionConfig] = None):
        self.config = config or ConnectionConfig.from_env()
        self._pool: Optional[ConnectionPool] = None
        self._health_status = False
        
    async def initialize(self):
        """Inicializa o pool de conexões"""
        try:
            self._pool = ConnectionPool(self.config)
            self._health_status = await self.health_check()
            logger.info("Pool de conexões inicializado", 
                       pool_size=self.config.pool_size,
                       max_overflow=self.config.max_overflow)
        except Exception as e:
            logger.error("Erro ao inicializar conexões", error=str(e))
            raise
    
    @asynccontextmanager
    async def get_connection(self):
        """Context manager para obter conexão de forma segura"""
        if not self._pool:
            raise Exception("Pool de conexões não inicializado")
            
        connection = None
        try:
            # Executa em thread pool para não bloquear event loop
            loop = asyncio.get_event_loop()
            connection = await loop.run_in_executor(
                None, self._pool.get_connection
            )
            yield connection
        except Exception as e:
            logger.error("Erro ao obter conexão", error=str(e))
            raise
        finally:
            if connection and self._pool:
                await loop.run_in_executor(
                    None, self._pool.return_connection, connection
                )
    
    async def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Executa uma query e retorna os resultados"""
        async with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                
                # Log da query (sanitizada)
                logger.info("Executando query", 
                           query=query[:100] + "..." if len(query) > 100 else query,
                           has_params=params is not None)
                
                start_time = datetime.now(timezone.utc)
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Mede o tempo de execução
                execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
                
                # Obtém os resultados
                if cursor.description:
                    columns = [column[0] for column in cursor.description]
                    rows = cursor.fetchall()
                    
                    result = []
                    for row in rows:
                        result.append(dict(zip(columns, row)))
                    
                    logger.info("Query executada com sucesso",
                               execution_time=execution_time,
                               rows_returned=len(result))
                    
                    return result
                else:
                    # Query sem retorno (INSERT, UPDATE, DELETE)
                    rowcount = cursor.rowcount
                    logger.info("Query executada com sucesso",
                               execution_time=execution_time,
                               rows_affected=rowcount)
                    return [{"rows_affected": rowcount}]
                    
            except Exception as e:
                logger.error("Erro ao executar query", 
                           error=str(e),
                           query=query[:100] + "..." if len(query) > 100 else query)
                raise
            finally:
                cursor.close()
    
    async def execute_scalar(self, query: str, params: Optional[tuple] = None) -> Any:
        """Executa uma query que retorna um único valor"""
        result = await self.execute_query(query, params)
        if result and len(result) > 0:
            first_row = result[0]
            if first_row:
                return list(first_row.values())[0]
        return None
    
    async def health_check(self) -> bool:
        """Verifica a saúde da conexão com o banco"""
        try:
            result = await self.execute_scalar("SELECT 1")
            self._health_status = result == 1
            return self._health_status
        except Exception as e:
            logger.error("Health check falhou", error=str(e))
            self._health_status = False
            return False
    
    @property
    def is_healthy(self) -> bool:
        """Retorna o status de saúde da conexão"""
        return self._health_status
    
    async def close(self):
        """Fecha todas as conexões"""
        if self._pool:
            self._pool.close_all()
            self._pool = None
            logger.info("Pool de conexões fechado")


# Instância global do gerenciador de conexão
_connection_manager: Optional[DatabaseConnection] = None


async def get_connection() -> DatabaseConnection:
    """Obtém a instância global do gerenciador de conexão"""
    global _connection_manager
    
    if _connection_manager is None:
        _connection_manager = DatabaseConnection()
        await _connection_manager.initialize()
    
    return _connection_manager


async def close_connections():
    """Fecha todas as conexões globais"""
    global _connection_manager
    
    if _connection_manager:
        await _connection_manager.close()
        _connection_manager = None
