"""
Ferramentas FULL_ACCESS para o servidor MCP SQL Server
Inclui todas as ferramentas READ_ONLY plus operações de escrita
"""

import os
import re
import structlog
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime
from ..database.connection import get_connection
from ..database.operations import DatabaseOperations
from .read_tools import ReadOnlyTools

logger = structlog.get_logger(__name__)


class FullAccessTools(ReadOnlyTools):
    """Ferramentas disponíveis em modo FULL_ACCESS (inclui READ_ONLY + escrita)"""
    
    def __init__(self):
        super().__init__()
        self.max_affected_rows = int(os.getenv("MAX_AFFECTED_ROWS", "10000"))
    
    def _sanitize_sql_identifier(self, identifier: str) -> str:
        """Sanitiza identificadores SQL para prevenir injection"""
        # Remove caracteres perigosos
        sanitized = re.sub(r'[^\w\-_]', '', identifier)
        
        # Verifica se não é vazio após sanitização
        if not sanitized:
            raise ValueError("Identificador inválido após sanitização")
        
        return sanitized
    
    def _validate_table_name(self, table_name: str) -> str:
        """Valida e sanitiza nome de tabela"""
        if not table_name or len(table_name.strip()) == 0:
            raise ValueError("Nome da tabela não pode estar vazio")
        
        # Remove espaços e sanitiza
        clean_name = self._sanitize_sql_identifier(table_name.strip())
        
        # Verifica comprimento
        if len(clean_name) > 128:
            raise ValueError("Nome da tabela muito longo (máximo 128 caracteres)")
        
        return clean_name
    
    async def execute_query(self, query: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
        """
        Executa qualquer query SQL (disponível apenas em modo FULL_ACCESS)
        
        Args:
            query: Query SQL a ser executada
            params: Parâmetros para a query (opcional)
            
        Returns:
            Dict com resultados da query
        """
        try:
            logger.info("Executando query", query_length=len(query))
            
            # Converte lista para tupla se necessário
            if params:
                params = tuple(params)
            
            db = await get_connection()
            results = await db.execute_query(query, params)
            
            result = {
                "success": True,
                "data": results,
                "row_count": len(results) if isinstance(results, list) else None,
                "rows_affected": results[0].get("rows_affected") if results and "rows_affected" in results[0] else None
            }
            
            logger.info("Query executada com sucesso", 
                       rows=len(results) if isinstance(results, list) else "N/A")
            return result
            
        except Exception as e:
            logger.error("Erro ao executar query", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "data": []
            }
    
    async def create_table(self, table_name: str, columns: List[Dict[str, Any]], 
                          schema: Optional[str] = None) -> Dict[str, Any]:
        """
        Cria uma nova tabela
        
        Args:
            table_name: Nome da tabela
            columns: Lista de definições de colunas
            schema: Nome do schema (opcional, padrão: dbo)
            
        Returns:
            Dict com resultado da operação
        """
        try:
            logger.info("Criando tabela", table=table_name, schema=schema, columns=len(columns))
            
            # Valida e sanitiza nome da tabela
            clean_table_name = self._validate_table_name(table_name)
            schema = schema or "dbo"
            clean_schema = self._sanitize_sql_identifier(schema)
            
            # Constrói definições de colunas
            column_definitions = []
            for col in columns:
                col_name = self._sanitize_sql_identifier(col["name"])
                col_type = col["type"]
                
                # Monta definição da coluna
                definition = f"[{col_name}] {col_type}"
                
                # Adiciona NOT NULL se especificado
                if not col.get("nullable", True):
                    definition += " NOT NULL"
                
                # Adiciona DEFAULT se especificado
                if "default" in col:
                    definition += f" DEFAULT {col['default']}"
                
                # Adiciona PRIMARY KEY se especificado
                if col.get("primary_key", False):
                    definition += " PRIMARY KEY"
                
                column_definitions.append(definition)
            
            # Constrói query CREATE TABLE
            columns_sql = ",\n    ".join(column_definitions)
            query = f"""
            CREATE TABLE [{clean_schema}].[{clean_table_name}] (
                {columns_sql}
            )
            """
            
            result = await self.execute_query(query)
            
            if result["success"]:
                logger.info("Tabela criada com sucesso", table=clean_table_name)
                result["table_name"] = clean_table_name
                result["schema"] = clean_schema
            
            return result
            
        except Exception as e:
            logger.error("Erro ao criar tabela", table=table_name, error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def alter_table(self, table_name: str, operation: str, 
                         column_definition: Optional[Dict[str, Any]] = None,
                         schema: Optional[str] = None) -> Dict[str, Any]:
        """
        Altera estrutura de uma tabela
        
        Args:
            table_name: Nome da tabela
            operation: Tipo de operação (ADD_COLUMN, DROP_COLUMN, ALTER_COLUMN)
            column_definition: Definição da coluna para ADD/ALTER
            schema: Nome do schema (opcional, padrão: dbo)
            
        Returns:
            Dict com resultado da operação
        """
        try:
            logger.info("Alterando tabela", table=table_name, operation=operation)
            
            # Valida e sanitiza nomes
            clean_table_name = self._validate_table_name(table_name)
            schema = schema or "dbo"
            clean_schema = self._sanitize_sql_identifier(schema)
            
            query = ""
            
            if operation == "ADD_COLUMN":
                if not column_definition:
                    raise ValueError("Definição da coluna é obrigatória para ADD_COLUMN")
                
                col_name = self._sanitize_sql_identifier(column_definition["name"])
                col_type = column_definition["type"]
                
                query = f"ALTER TABLE [{clean_schema}].[{clean_table_name}] ADD [{col_name}] {col_type}"
                
                if not column_definition.get("nullable", True):
                    query += " NOT NULL"
                
                if "default" in column_definition:
                    query += f" DEFAULT {column_definition['default']}"
            
            elif operation == "DROP_COLUMN":
                if not column_definition or "name" not in column_definition:
                    raise ValueError("Nome da coluna é obrigatório para DROP_COLUMN")
                
                col_name = self._sanitize_sql_identifier(column_definition["name"])
                query = f"ALTER TABLE [{clean_schema}].[{clean_table_name}] DROP COLUMN [{col_name}]"
            
            elif operation == "ALTER_COLUMN":
                if not column_definition:
                    raise ValueError("Definição da coluna é obrigatória para ALTER_COLUMN")
                
                col_name = self._sanitize_sql_identifier(column_definition["name"])
                col_type = column_definition["type"]
                
                query = f"ALTER TABLE [{clean_schema}].[{clean_table_name}] ALTER COLUMN [{col_name}] {col_type}"
                
                if not column_definition.get("nullable", True):
                    query += " NOT NULL"
            
            else:
                raise ValueError(f"Operação '{operation}' não suportada")
            
            result = await self.execute_query(query)
            
            if result["success"]:
                logger.info("Tabela alterada com sucesso", table=clean_table_name, operation=operation)
                result["table_name"] = clean_table_name
                result["operation"] = operation
            
            return result
            
        except Exception as e:
            logger.error("Erro ao alterar tabela", table=table_name, error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def drop_table(self, table_name: str, schema: Optional[str] = None) -> Dict[str, Any]:
        """
        Remove uma tabela
        
        Args:
            table_name: Nome da tabela
            schema: Nome do schema (opcional, padrão: dbo)
            
        Returns:
            Dict com resultado da operação
        """
        try:
            logger.info("Removendo tabela", table=table_name, schema=schema)
            
            # Valida e sanitiza nomes
            clean_table_name = self._validate_table_name(table_name)
            schema = schema or "dbo"
            clean_schema = self._sanitize_sql_identifier(schema)
            
            query = f"DROP TABLE [{clean_schema}].[{clean_table_name}]"
            
            result = await self.execute_query(query)
            
            if result["success"]:
                logger.info("Tabela removida com sucesso", table=clean_table_name)
                result["table_name"] = clean_table_name
                result["schema"] = clean_schema
            
            return result
            
        except Exception as e:
            logger.error("Erro ao remover tabela", table=table_name, error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def insert_data(self, table_name: str, data: List[Dict[str, Any]], 
                         schema: Optional[str] = None) -> Dict[str, Any]:
        """
        Insere dados em uma tabela
        
        Args:
            table_name: Nome da tabela
            data: Lista de dicionários com os dados a inserir
            schema: Nome do schema (opcional, padrão: dbo)
            
        Returns:
            Dict com resultado da operação
        """
        try:
            logger.info("Inserindo dados", table=table_name, rows=len(data))
            
            if not data:
                return {
                    "success": False,
                    "error": "Nenhum dado fornecido para inserção"
                }
            
            # Valida e sanitiza nomes
            clean_table_name = self._validate_table_name(table_name)
            schema = schema or "dbo"
            clean_schema = self._sanitize_sql_identifier(schema)
            
            # Obtém colunas do primeiro registro
            columns = list(data[0].keys())
            clean_columns = [self._sanitize_sql_identifier(col) for col in columns]
            
            # Constrói query INSERT
            columns_sql = ", ".join([f"[{col}]" for col in clean_columns])
            placeholders = ", ".join(["?" for _ in columns])
            
            query = f"INSERT INTO [{clean_schema}].[{clean_table_name}] ({columns_sql}) VALUES ({placeholders})"
            
            # Executa inserções em lote
            rows_inserted = 0
            errors = []
            
            for i, row in enumerate(data):
                try:
                    # Prepara valores na ordem das colunas
                    values = [row.get(col) for col in columns]
                    
                    result = await self.execute_query(query, values)
                    
                    if result["success"]:
                        rows_inserted += 1
                    else:
                        errors.append(f"Linha {i}: {result['error']}")
                
                except Exception as e:
                    errors.append(f"Linha {i}: {str(e)}")
            
            result = {
                "success": rows_inserted > 0,
                "rows_inserted": rows_inserted,
                "total_rows": len(data),
                "errors": errors
            }
            
            logger.info("Inserção concluída", 
                       table=clean_table_name, 
                       inserted=rows_inserted, 
                       total=len(data))
            
            return result
            
        except Exception as e:
            logger.error("Erro ao inserir dados", table=table_name, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "rows_inserted": 0
            }
    
    async def update_data(self, table_name: str, set_values: Dict[str, Any], 
                         where_clause: str, where_params: Optional[List[Any]] = None,
                         schema: Optional[str] = None) -> Dict[str, Any]:
        """
        Atualiza dados em uma tabela
        
        Args:
            table_name: Nome da tabela
            set_values: Dicionário com valores a atualizar
            where_clause: Cláusula WHERE
            where_params: Parâmetros para a cláusula WHERE
            schema: Nome do schema (opcional, padrão: dbo)
            
        Returns:
            Dict com resultado da operação
        """
        try:
            logger.info("Atualizando dados", table=table_name)
            
            # Valida e sanitiza nomes
            clean_table_name = self._validate_table_name(table_name)
            schema = schema or "dbo"
            clean_schema = self._sanitize_sql_identifier(schema)
            
            # Constrói cláusula SET
            set_clauses = []
            set_params = []
            
            for col, value in set_values.items():
                clean_col = self._sanitize_sql_identifier(col)
                set_clauses.append(f"[{clean_col}] = ?")
                set_params.append(value)
            
            set_sql = ", ".join(set_clauses)
            
            # Constrói query UPDATE
            query = f"UPDATE [{clean_schema}].[{clean_table_name}] SET {set_sql}"
            
            # Adiciona WHERE se fornecido
            params = set_params.copy()
            if where_clause:
                query += f" WHERE {where_clause}"
                if where_params:
                    params.extend(where_params)
            
            result = await self.execute_query(query, params)
            
            if result["success"]:
                logger.info("Dados atualizados com sucesso", 
                           table=clean_table_name,
                           rows_affected=result.get("rows_affected", 0))
            
            return result
            
        except Exception as e:
            logger.error("Erro ao atualizar dados", table=table_name, error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_data(self, table_name: str, where_clause: str, 
                         where_params: Optional[List[Any]] = None,
                         schema: Optional[str] = None) -> Dict[str, Any]:
        """
        Deleta dados de uma tabela
        
        Args:
            table_name: Nome da tabela
            where_clause: Cláusula WHERE
            where_params: Parâmetros para a cláusula WHERE
            schema: Nome do schema (opcional, padrão: dbo)
            
        Returns:
            Dict com resultado da operação
        """
        try:
            logger.info("Deletando dados", table=table_name)
            
            # Valida e sanitiza nomes
            clean_table_name = self._validate_table_name(table_name)
            schema = schema or "dbo"
            clean_schema = self._sanitize_sql_identifier(schema)
            
            # Constrói query DELETE
            query = f"DELETE FROM [{clean_schema}].[{clean_table_name}]"
            
            params = None
            if where_clause:
                query += f" WHERE {where_clause}"
                if where_params:
                    params = tuple(where_params)
            else:
                # Proteção contra DELETE sem WHERE
                return {
                    "success": False,
                    "error": "DELETE sem cláusula WHERE não é permitido por segurança"
                }
            
            result = await self.execute_query(query, params)
            
            if result["success"]:
                logger.info("Dados deletados com sucesso", 
                           table=clean_table_name,
                           rows_affected=result.get("rows_affected", 0))
            
            return result
            
        except Exception as e:
            logger.error("Erro ao deletar dados", table=table_name, error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_index(self, index_name: str, table_name: str, columns: List[str],
                          unique: bool = False, schema: Optional[str] = None) -> Dict[str, Any]:
        """
        Cria um índice
        
        Args:
            index_name: Nome do índice
            table_name: Nome da tabela
            columns: Lista de colunas do índice
            unique: Se o índice deve ser único
            schema: Nome do schema (opcional, padrão: dbo)
            
        Returns:
            Dict com resultado da operação
        """
        try:
            logger.info("Criando índice", index=index_name, table=table_name)
            
            # Valida e sanitiza nomes
            clean_index_name = self._sanitize_sql_identifier(index_name)
            clean_table_name = self._validate_table_name(table_name)
            schema = schema or "dbo"
            clean_schema = self._sanitize_sql_identifier(schema)
            
            # Sanitiza nomes das colunas
            clean_columns = [self._sanitize_sql_identifier(col) for col in columns]
            columns_sql = ", ".join([f"[{col}]" for col in clean_columns])
            
            # Constrói query CREATE INDEX
            unique_sql = "UNIQUE " if unique else ""
            query = f"""
            CREATE {unique_sql}INDEX [{clean_index_name}] 
            ON [{clean_schema}].[{clean_table_name}] ({columns_sql})
            """
            
            result = await self.execute_query(query)
            
            if result["success"]:
                logger.info("Índice criado com sucesso", index=clean_index_name)
                result["index_name"] = clean_index_name
                result["table_name"] = clean_table_name
            
            return result
            
        except Exception as e:
            logger.error("Erro ao criar índice", index=index_name, error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def drop_index(self, index_name: str, table_name: str, 
                        schema: Optional[str] = None) -> Dict[str, Any]:
        """
        Remove um índice
        
        Args:
            index_name: Nome do índice
            table_name: Nome da tabela
            schema: Nome do schema (opcional, padrão: dbo)
            
        Returns:
            Dict com resultado da operação
        """
        try:
            logger.info("Removendo índice", index=index_name, table=table_name)
            
            # Valida e sanitiza nomes
            clean_index_name = self._sanitize_sql_identifier(index_name)
            clean_table_name = self._validate_table_name(table_name)
            schema = schema or "dbo"
            clean_schema = self._sanitize_sql_identifier(schema)
            
            query = f"DROP INDEX [{clean_index_name}] ON [{clean_schema}].[{clean_table_name}]"
            
            result = await self.execute_query(query)
            
            if result["success"]:
                logger.info("Índice removido com sucesso", index=clean_index_name)
                result["index_name"] = clean_index_name
                result["table_name"] = clean_table_name
            
            return result
            
        except Exception as e:
            logger.error("Erro ao remover índice", index=index_name, error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def execute_procedure(self, procedure_name: str, params: Optional[List[Any]] = None,
                               schema: Optional[str] = None) -> Dict[str, Any]:
        """
        Executa uma stored procedure
        
        Args:
            procedure_name: Nome da procedure
            params: Parâmetros para a procedure
            schema: Nome do schema (opcional, padrão: dbo)
            
        Returns:
            Dict com resultado da execução
        """
        try:
            logger.info("Executando procedure", procedure=procedure_name)
            
            # Valida e sanitiza nomes
            clean_procedure_name = self._sanitize_sql_identifier(procedure_name)
            schema = schema or "dbo"
            clean_schema = self._sanitize_sql_identifier(schema)
            
            # Constrói query EXEC
            if params:
                placeholders = ", ".join(["?" for _ in params])
                query = f"EXEC [{clean_schema}].[{clean_procedure_name}] {placeholders}"
                result = await self.execute_query(query, params)
            else:
                query = f"EXEC [{clean_schema}].[{clean_procedure_name}]"
                result = await self.execute_query(query)
            
            if result["success"]:
                logger.info("Procedure executada com sucesso", procedure=clean_procedure_name)
                result["procedure_name"] = clean_procedure_name
                result["schema"] = clean_schema
            
            return result
            
        except Exception as e:
            logger.error("Erro ao executar procedure", procedure=procedure_name, error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def backup_table(self, table_name: str, backup_name: Optional[str] = None,
                          schema: Optional[str] = None) -> Dict[str, Any]:
        """
        Faz backup de uma tabela criando uma cópia
        
        Args:
            table_name: Nome da tabela original
            backup_name: Nome da tabela de backup (opcional, será gerado automaticamente)
            schema: Nome do schema (opcional, padrão: dbo)
            
        Returns:
            Dict com resultado da operação
        """
        try:
            logger.info("Fazendo backup da tabela", table=table_name)
            
            # Valida e sanitiza nomes
            clean_table_name = self._validate_table_name(table_name)
            schema = schema or "dbo"
            clean_schema = self._sanitize_sql_identifier(schema)
            
            # Gera nome do backup se não fornecido
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{clean_table_name}_backup_{timestamp}"
            else:
                backup_name = self._validate_table_name(backup_name)
            
            # Cria tabela de backup
            query = f"""
            SELECT * INTO [{clean_schema}].[{backup_name}] 
            FROM [{clean_schema}].[{clean_table_name}]
            """
            
            result = await self.execute_query(query)
            
            if result["success"]:
                logger.info("Backup criado com sucesso", 
                           original=clean_table_name, backup=backup_name)
                result["original_table"] = clean_table_name
                result["backup_table"] = backup_name
                result["schema"] = clean_schema
            
            return result
            
        except Exception as e:
            logger.error("Erro ao fazer backup da tabela", table=table_name, error=str(e))
            return {
                "success": False,
                "error": str(e)
            }


# Definições de schema para validação das ferramentas de escrita
class ExecuteQueryRequest(BaseModel):
    query: str = Field(..., description="Query SQL a ser executada")
    params: Optional[List[Any]] = Field(None, description="Parâmetros para a query")


class CreateTableRequest(BaseModel):
    table_name: str = Field(..., description="Nome da tabela")
    columns: List[Dict[str, Any]] = Field(..., description="Definições das colunas")
    schema: Optional[str] = Field(None, description="Nome do schema")


class AlterTableRequest(BaseModel):
    table_name: str = Field(..., description="Nome da tabela")
    operation: str = Field(..., description="Operação (ADD_COLUMN, DROP_COLUMN, ALTER_COLUMN)")
    column_definition: Optional[Dict[str, Any]] = Field(None, description="Definição da coluna")
    schema: Optional[str] = Field(None, description="Nome do schema")


class DropTableRequest(BaseModel):
    table_name: str = Field(..., description="Nome da tabela")
    schema: Optional[str] = Field(None, description="Nome do schema")


class InsertDataRequest(BaseModel):
    table_name: str = Field(..., description="Nome da tabela")
    data: List[Dict[str, Any]] = Field(..., description="Dados a inserir")
    schema: Optional[str] = Field(None, description="Nome do schema")


class UpdateDataRequest(BaseModel):
    table_name: str = Field(..., description="Nome da tabela")
    set_values: Dict[str, Any] = Field(..., description="Valores a atualizar")
    where_clause: str = Field(..., description="Cláusula WHERE")
    where_params: Optional[List[Any]] = Field(None, description="Parâmetros do WHERE")
    schema: Optional[str] = Field(None, description="Nome do schema")


class DeleteDataRequest(BaseModel):
    table_name: str = Field(..., description="Nome da tabela")
    where_clause: str = Field(..., description="Cláusula WHERE")
    where_params: Optional[List[Any]] = Field(None, description="Parâmetros do WHERE")
    schema: Optional[str] = Field(None, description="Nome do schema")


class CreateIndexRequest(BaseModel):
    index_name: str = Field(..., description="Nome do índice")
    table_name: str = Field(..., description="Nome da tabela")
    columns: List[str] = Field(..., description="Colunas do índice")
    unique: bool = Field(False, description="Índice único")
    schema: Optional[str] = Field(None, description="Nome do schema")


class DropIndexRequest(BaseModel):
    index_name: str = Field(..., description="Nome do índice")
    table_name: str = Field(..., description="Nome da tabela")
    schema: Optional[str] = Field(None, description="Nome do schema")


class ExecuteProcedureRequest(BaseModel):
    procedure_name: str = Field(..., description="Nome da procedure")
    params: Optional[List[Any]] = Field(None, description="Parâmetros da procedure")
    schema: Optional[str] = Field(None, description="Nome do schema")


class BackupTableRequest(BaseModel):
    table_name: str = Field(..., description="Nome da tabela")
    backup_name: Optional[str] = Field(None, description="Nome do backup")
    schema: Optional[str] = Field(None, description="Nome do schema")
