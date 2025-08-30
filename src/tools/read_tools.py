"""
Ferramentas READ_ONLY para o servidor MCP SQL Server
Contém todas as ferramentas disponíveis em modo somente leitura
"""

import os
import structlog
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from ..database.connection import get_connection
from ..database.operations import DatabaseOperations, QueryValidator

logger = structlog.get_logger(__name__)


class ReadOnlyTools:
    """Ferramentas disponíveis em modo READ_ONLY"""
    
    def __init__(self):
        self.db_ops = DatabaseOperations()
        self.max_result_rows = int(os.getenv("MAX_RESULT_ROWS", "1000"))
    
    async def list_tables(self, schema: Optional[str] = None) -> Dict[str, Any]:
        """
        Lista todas as tabelas do banco de dados
        
        Args:
            schema: Nome do schema (opcional, padrão: todos os schemas)
            
        Returns:
            Dict com lista de tabelas e suas informações
        """
        try:
            logger.info("Listando tabelas", schema=schema)
            
            tables = await self.db_ops.list_tables(schema)
            
            result = {
                "success": True,
                "tables": [
                    {
                        "name": table.name,
                        "schema": table.schema,
                        "type": table.type,
                        "row_count": table.row_count,
                        "created_date": table.created_date
                    }
                    for table in tables
                ],
                "total_count": len(tables)
            }
            
            logger.info("Tabelas listadas com sucesso", count=len(tables))
            return result
            
        except Exception as e:
            logger.error("Erro ao listar tabelas", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "tables": []
            }
    
    async def describe_table(self, table_name: str, schema: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtém a estrutura de uma tabela específica
        
        Args:
            table_name: Nome da tabela
            schema: Nome do schema (opcional, padrão: dbo)
            
        Returns:
            Dict com informações detalhadas da tabela
        """
        try:
            logger.info("Descrevendo tabela", table=table_name, schema=schema)
            
            columns = await self.db_ops.describe_table(table_name, schema)
            
            result = {
                "success": True,
                "table_name": table_name,
                "schema": schema or "dbo",
                "columns": [
                    {
                        "name": col.name,
                        "data_type": col.data_type,
                        "max_length": col.max_length,
                        "precision": col.precision,
                        "scale": col.scale,
                        "is_nullable": col.is_nullable,
                        "is_primary_key": col.is_primary_key,
                        "is_foreign_key": col.is_foreign_key,
                        "default_value": col.default_value
                    }
                    for col in columns
                ],
                "column_count": len(columns)
            }
            
            logger.info("Tabela descrita com sucesso", table=table_name, columns=len(columns))
            return result
            
        except Exception as e:
            logger.error("Erro ao descrever tabela", table=table_name, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "table_name": table_name,
                "columns": []
            }
    
    async def list_columns(self, table_name: str, schema: Optional[str] = None) -> Dict[str, Any]:
        """
        Lista apenas as colunas de uma tabela
        
        Args:
            table_name: Nome da tabela
            schema: Nome do schema (opcional, padrão: dbo)
            
        Returns:
            Dict com lista simplificada de colunas
        """
        try:
            logger.info("Listando colunas", table=table_name, schema=schema)
            
            columns = await self.db_ops.describe_table(table_name, schema)
            
            result = {
                "success": True,
                "table_name": table_name,
                "schema": schema or "dbo",
                "columns": [col.name for col in columns],
                "column_details": [
                    {
                        "name": col.name,
                        "type": col.data_type,
                        "nullable": col.is_nullable
                    }
                    for col in columns
                ]
            }
            
            logger.info("Colunas listadas com sucesso", table=table_name, count=len(columns))
            return result
            
        except Exception as e:
            logger.error("Erro ao listar colunas", table=table_name, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "columns": []
            }
    
    async def list_indexes(self, table_name: str, schema: Optional[str] = None) -> Dict[str, Any]:
        """
        Lista índices de uma tabela
        
        Args:
            table_name: Nome da tabela
            schema: Nome do schema (opcional, padrão: dbo)
            
        Returns:
            Dict com lista de índices
        """
        try:
            logger.info("Listando índices", table=table_name, schema=schema)
            
            indexes = await self.db_ops.list_indexes(table_name, schema)
            
            result = {
                "success": True,
                "table_name": table_name,
                "schema": schema or "dbo",
                "indexes": [
                    {
                        "name": idx.name,
                        "columns": idx.columns,
                        "is_unique": idx.is_unique,
                        "is_primary": idx.is_primary,
                        "type": idx.type
                    }
                    for idx in indexes
                ],
                "index_count": len(indexes)
            }
            
            logger.info("Índices listados com sucesso", table=table_name, count=len(indexes))
            return result
            
        except Exception as e:
            logger.error("Erro ao listar índices", table=table_name, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "indexes": []
            }
    
    async def list_views(self) -> Dict[str, Any]:
        """
        Lista todas as views do banco de dados
        
        Returns:
            Dict com lista de views
        """
        try:
            logger.info("Listando views")
            
            views = await self.db_ops.list_views()
            
            result = {
                "success": True,
                "views": [
                    {
                        "name": view.name,
                        "schema": view.schema
                    }
                    for view in views
                ],
                "total_count": len(views)
            }
            
            logger.info("Views listadas com sucesso", count=len(views))
            return result
            
        except Exception as e:
            logger.error("Erro ao listar views", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "views": []
            }
    
    async def list_procedures(self) -> Dict[str, Any]:
        """
        Lista stored procedures do banco
        
        Returns:
            Dict com lista de procedures
        """
        try:
            logger.info("Listando procedures")
            
            procedures = await self.db_ops.list_procedures()
            
            result = {
                "success": True,
                "procedures": procedures,
                "total_count": len(procedures)
            }
            
            logger.info("Procedures listados com sucesso", count=len(procedures))
            return result
            
        except Exception as e:
            logger.error("Erro ao listar procedures", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "procedures": []
            }
    
    async def list_functions(self) -> Dict[str, Any]:
        """
        Lista funções do banco
        
        Returns:
            Dict com lista de funções
        """
        try:
            logger.info("Listando funções")
            
            functions = await self.db_ops.list_functions()
            
            result = {
                "success": True,
                "functions": functions,
                "total_count": len(functions)
            }
            
            logger.info("Funções listadas com sucesso", count=len(functions))
            return result
            
        except Exception as e:
            logger.error("Erro ao listar funções", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "functions": []
            }
    
    async def execute_select(self, query: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Executa uma query SELECT com validação e limite de registros
        
        Args:
            query: Query SELECT a ser executada
            limit: Limite de registros (opcional, usa MAX_RESULT_ROWS se não especificado)
            
        Returns:
            Dict com resultados da query
        """
        try:
            logger.info("Executando SELECT", query_length=len(query))
            
            # Valida se é uma query READ_ONLY
            is_valid, error_msg = QueryValidator.validate_read_only_query(query)
            if not is_valid:
                logger.warning("Query inválida para modo READ_ONLY", error=error_msg)
                return {
                    "success": False,
                    "error": f"Query inválida: {error_msg}",
                    "data": []
                }
            
            # Aplica limite se especificado
            limit = limit or self.max_result_rows
            if "TOP" not in query.upper() and "FETCH" not in query.upper():
                # Adiciona TOP se não existir
                query = query.strip()
                if query.upper().startswith("SELECT"):
                    query = f"SELECT TOP {limit} " + query[6:]
            
            db = await get_connection()
            results = await db.execute_query(query)
            
            # Aplica limite adicional se necessário
            if len(results) > limit:
                results = results[:limit]
                truncated = True
            else:
                truncated = False
            
            result = {
                "success": True,
                "data": results,
                "row_count": len(results),
                "truncated": truncated,
                "limit_applied": limit
            }
            
            logger.info("SELECT executado com sucesso", 
                       rows=len(results), truncated=truncated)
            return result
            
        except Exception as e:
            logger.error("Erro ao executar SELECT", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "data": []
            }
    
    async def get_table_data(self, table_name: str, schema: Optional[str] = None,
                           limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        Obtém dados de uma tabela com paginação
        
        Args:
            table_name: Nome da tabela
            schema: Nome do schema (opcional, padrão: dbo)
            limit: Número máximo de registros (padrão: 100)
            offset: Número de registros para pular (padrão: 0)
            
        Returns:
            Dict com dados da tabela
        """
        try:
            logger.info("Obtendo dados da tabela", 
                       table=table_name, schema=schema, limit=limit, offset=offset)
            
            # Limita o número máximo de registros
            limit = min(limit, self.max_result_rows)
            
            data = await self.db_ops.get_table_data(table_name, schema, limit, offset)
            
            result = {
                "success": True,
                "table_name": table_name,
                "schema": schema or "dbo",
                "data": data,
                "row_count": len(data),
                "limit": limit,
                "offset": offset,
                "has_more": len(data) == limit  # Indica se pode haver mais dados
            }
            
            logger.info("Dados da tabela obtidos com sucesso", 
                       table=table_name, rows=len(data))
            return result
            
        except Exception as e:
            logger.error("Erro ao obter dados da tabela", 
                        table=table_name, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "data": []
            }
    
    async def get_database_schema(self) -> Dict[str, Any]:
        """
        Obtém esquema completo do banco de dados
        
        Returns:
            Dict com esquema completo do banco
        """
        try:
            logger.info("Obtendo esquema do banco")
            
            schema = await self.db_ops.get_database_schema()
            
            result = {
                "success": True,
                "schema": schema,
                "summary": {
                    "table_count": len(schema.get("tables", [])),
                    "view_count": len(schema.get("views", [])),
                    "procedure_count": len(schema.get("procedures", [])),
                    "function_count": len(schema.get("functions", []))
                }
            }
            
            logger.info("Esquema do banco obtido com sucesso")
            return result
            
        except Exception as e:
            logger.error("Erro ao obter esquema do banco", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "schema": {}
            }
    
    async def check_constraints(self, table_name: str, schema: Optional[str] = None) -> Dict[str, Any]:
        """
        Lista constraints de uma tabela
        
        Args:
            table_name: Nome da tabela
            schema: Nome do schema (opcional, padrão: dbo)
            
        Returns:
            Dict com constraints da tabela
        """
        try:
            logger.info("Verificando constraints", table=table_name, schema=schema)
            
            constraints = await self.db_ops.check_constraints(table_name, schema)
            
            result = {
                "success": True,
                "table_name": table_name,
                "schema": schema or "dbo",
                "constraints": constraints,
                "constraint_count": len(constraints)
            }
            
            logger.info("Constraints verificados com sucesso", 
                       table=table_name, count=len(constraints))
            return result
            
        except Exception as e:
            logger.error("Erro ao verificar constraints", 
                        table=table_name, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "constraints": []
            }


# Definições de schema para validação das ferramentas MCP
class ListTablesRequest(BaseModel):
    schema: Optional[str] = Field(None, description="Nome do schema (opcional)")


class DescribeTableRequest(BaseModel):
    table_name: str = Field(..., description="Nome da tabela")
    schema: Optional[str] = Field(None, description="Nome do schema (opcional)")


class ListColumnsRequest(BaseModel):
    table_name: str = Field(..., description="Nome da tabela")
    schema: Optional[str] = Field(None, description="Nome do schema (opcional)")


class ListIndexesRequest(BaseModel):
    table_name: str = Field(..., description="Nome da tabela")
    schema: Optional[str] = Field(None, description="Nome do schema (opcional)")


class ExecuteSelectRequest(BaseModel):
    query: str = Field(..., description="Query SELECT a ser executada")
    limit: Optional[int] = Field(None, description="Limite de registros")


class GetTableDataRequest(BaseModel):
    table_name: str = Field(..., description="Nome da tabela")
    schema: Optional[str] = Field(None, description="Nome do schema (opcional)")
    limit: int = Field(100, description="Número máximo de registros")
    offset: int = Field(0, description="Número de registros para pular")


class CheckConstraintsRequest(BaseModel):
    table_name: str = Field(..., description="Nome da tabela")
    schema: Optional[str] = Field(None, description="Nome do schema (opcional)")
