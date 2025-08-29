"""
Operações específicas de banco de dados SQL Server
Contém funcionalidades especializadas para diferentes tipos de operações
"""

import re
import structlog
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from .connection import DatabaseConnection, get_connection

logger = structlog.get_logger(__name__)


@dataclass
class TableInfo:
    """Informações sobre uma tabela"""
    name: str
    schema: str
    type: str
    row_count: Optional[int] = None
    created_date: Optional[str] = None


@dataclass
class ColumnInfo:
    """Informações sobre uma coluna"""
    name: str
    data_type: str
    max_length: Optional[int]
    precision: Optional[int]
    scale: Optional[int]
    is_nullable: bool
    is_primary_key: bool
    is_foreign_key: bool
    default_value: Optional[str]


@dataclass
class IndexInfo:
    """Informações sobre um índice"""
    name: str
    table_name: str
    columns: List[str]
    is_unique: bool
    is_primary: bool
    type: str


class QueryValidator:
    """Validador de queries SQL para modo READ_ONLY"""
    
    # Palavras-chave permitidas em modo READ_ONLY
    ALLOWED_KEYWORDS = {
        'SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL',
        'OUTER', 'ON', 'GROUP', 'BY', 'HAVING', 'ORDER', 'ASC', 'DESC',
        'UNION', 'INTERSECT', 'EXCEPT', 'WITH', 'AS', 'DISTINCT', 'TOP',
        'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'AND', 'OR', 'NOT', 'IN',
        'EXISTS', 'BETWEEN', 'LIKE', 'IS', 'NULL', 'COUNT', 'SUM', 'AVG',
        'MIN', 'MAX', 'LEN', 'SUBSTRING', 'UPPER', 'LOWER', 'LTRIM', 'RTRIM'
    }
    
    # Palavras-chave proibidas em modo READ_ONLY
    FORBIDDEN_KEYWORDS = {
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE',
        'EXEC', 'EXECUTE', 'SP_', 'XP_', 'BACKUP', 'RESTORE', 'BULK',
        'OPENROWSET', 'OPENDATASOURCE', 'OPENQUERY', 'OPENXML'
    }
    
    @classmethod
    def validate_read_only_query(cls, query: str) -> Tuple[bool, str]:
        """
        Valida se uma query é segura para modo READ_ONLY
        Retorna: (is_valid, error_message)
        """
        if not query or not query.strip():
            return False, "Query vazia"
        
        # Remove comentários
        query_clean = re.sub(r'--.*?\n', ' ', query)
        query_clean = re.sub(r'/\*.*?\*/', ' ', query_clean, flags=re.DOTALL)
        
        # Normaliza espaços
        query_clean = ' '.join(query_clean.split()).upper()
        
        # Verifica se começa com SELECT
        if not query_clean.strip().startswith('SELECT'):
            return False, "Apenas queries SELECT são permitidas em modo READ_ONLY"
        
        # Verifica palavras-chave proibidas
        for keyword in cls.FORBIDDEN_KEYWORDS:
            if keyword in query_clean:
                return False, f"Palavra-chave '{keyword}' não permitida em modo READ_ONLY"
        
        # Verifica padrões perigosos
        dangerous_patterns = [
            r';\s*SELECT',  # Multiple statements
            r'UNION\s+ALL\s+SELECT.*FROM\s+INFORMATION_SCHEMA',  # Info schema injection
            r'@@',  # System variables
            r'WAITFOR',  # Time delays
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, query_clean):
                return False, f"Padrão perigoso detectado: {pattern}"
        
        return True, ""
    
    @classmethod
    def sanitize_query(cls, query: str) -> str:
        """Sanitiza uma query removendo caracteres perigosos"""
        # Remove caracteres perigosos
        dangerous_chars = [';', '--', '/*', '*/', 'xp_', 'sp_']
        
        sanitized = query
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized.strip()


class DatabaseOperations:
    """Operações especializadas de banco de dados"""
    
    def __init__(self, db_connection: Optional[DatabaseConnection] = None):
        self.db = db_connection
        
    async def _get_db(self) -> DatabaseConnection:
        """Obtém a instância de conexão com o banco"""
        if self.db is None:
            self.db = await get_connection()
        return self.db
    
    async def list_tables(self, schema: Optional[str] = None) -> List[TableInfo]:
        """Lista todas as tabelas do banco de dados"""
        db = await self._get_db()
        
        query = """
        SELECT 
            t.TABLE_SCHEMA as schema_name,
            t.TABLE_NAME as table_name,
            t.TABLE_TYPE as table_type,
            p.rows as row_count,
            o.create_date
        FROM INFORMATION_SCHEMA.TABLES t
        LEFT JOIN sys.objects o ON o.name = t.TABLE_NAME AND o.type = 'U'
        LEFT JOIN sys.dm_db_partition_stats p ON o.object_id = p.object_id AND p.index_id <= 1
        WHERE t.TABLE_TYPE IN ('BASE TABLE', 'VIEW')
        """
        
        params = None
        if schema:
            query += " AND t.TABLE_SCHEMA = ?"
            params = (schema,)
        
        query += " ORDER BY t.TABLE_SCHEMA, t.TABLE_NAME"
        
        try:
            results = await db.execute_query(query, params)
            
            tables = []
            for row in results:
                tables.append(TableInfo(
                    name=row['table_name'],
                    schema=row['schema_name'],
                    type=row['table_type'],
                    row_count=row.get('row_count'),
                    created_date=str(row.get('create_date')) if row.get('create_date') else None
                ))
            
            return tables
            
        except Exception as e:
            logger.error("Erro ao listar tabelas", error=str(e))
            raise
    
    async def describe_table(self, table_name: str, schema: Optional[str] = None) -> List[ColumnInfo]:
        """Descreve a estrutura de uma tabela"""
        db = await self._get_db()
        
        schema = schema or 'dbo'
        
        query = """
        SELECT 
            c.COLUMN_NAME,
            c.DATA_TYPE,
            c.CHARACTER_MAXIMUM_LENGTH,
            c.NUMERIC_PRECISION,
            c.NUMERIC_SCALE,
            c.IS_NULLABLE,
            c.COLUMN_DEFAULT,
            CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 1 ELSE 0 END as is_primary_key,
            CASE WHEN fk.COLUMN_NAME IS NOT NULL THEN 1 ELSE 0 END as is_foreign_key
        FROM INFORMATION_SCHEMA.COLUMNS c
        LEFT JOIN (
            SELECT ku.TABLE_SCHEMA, ku.TABLE_NAME, ku.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku
                ON tc.CONSTRAINT_TYPE = 'PRIMARY KEY' 
                AND tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
        ) pk ON c.TABLE_SCHEMA = pk.TABLE_SCHEMA 
            AND c.TABLE_NAME = pk.TABLE_NAME 
            AND c.COLUMN_NAME = pk.COLUMN_NAME
        LEFT JOIN (
            SELECT ku.TABLE_SCHEMA, ku.TABLE_NAME, ku.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku
                ON tc.CONSTRAINT_TYPE = 'FOREIGN KEY' 
                AND tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
        ) fk ON c.TABLE_SCHEMA = fk.TABLE_SCHEMA 
            AND c.TABLE_NAME = fk.TABLE_NAME 
            AND c.COLUMN_NAME = fk.COLUMN_NAME
        WHERE c.TABLE_NAME = ? AND c.TABLE_SCHEMA = ?
        ORDER BY c.ORDINAL_POSITION
        """
        
        try:
            results = await db.execute_query(query, (table_name, schema))
            
            columns = []
            for row in results:
                columns.append(ColumnInfo(
                    name=row['COLUMN_NAME'],
                    data_type=row['DATA_TYPE'],
                    max_length=row.get('CHARACTER_MAXIMUM_LENGTH'),
                    precision=row.get('NUMERIC_PRECISION'),
                    scale=row.get('NUMERIC_SCALE'),
                    is_nullable=row['IS_NULLABLE'] == 'YES',
                    is_primary_key=bool(row['is_primary_key']),
                    is_foreign_key=bool(row['is_foreign_key']),
                    default_value=row.get('COLUMN_DEFAULT')
                ))
            
            return columns
            
        except Exception as e:
            logger.error("Erro ao descrever tabela", table=table_name, schema=schema, error=str(e))
            raise
    
    async def list_indexes(self, table_name: str, schema: Optional[str] = None) -> List[IndexInfo]:
        """Lista índices de uma tabela"""
        db = await self._get_db()
        
        schema = schema or 'dbo'
        
        query = """
        SELECT 
            i.name as index_name,
            t.name as table_name,
            i.is_unique,
            i.is_primary_key,
            i.type_desc as index_type,
            STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) as columns
        FROM sys.indexes i
        INNER JOIN sys.tables t ON i.object_id = t.object_id
        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
        INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        WHERE t.name = ? AND s.name = ? AND i.name IS NOT NULL
        GROUP BY i.name, t.name, i.is_unique, i.is_primary_key, i.type_desc
        ORDER BY i.name
        """
        
        try:
            results = await db.execute_query(query, (table_name, schema))
            
            indexes = []
            for row in results:
                indexes.append(IndexInfo(
                    name=row['index_name'],
                    table_name=row['table_name'],
                    columns=row['columns'].split(', ') if row['columns'] else [],
                    is_unique=bool(row['is_unique']),
                    is_primary=bool(row['is_primary_key']),
                    type=row['index_type']
                ))
            
            return indexes
            
        except Exception as e:
            logger.error("Erro ao listar índices", table=table_name, schema=schema, error=str(e))
            raise
    
    async def list_views(self) -> List[TableInfo]:
        """Lista todas as views do banco"""
        db = await self._get_db()
        
        query = """
        SELECT 
            TABLE_SCHEMA as schema_name,
            TABLE_NAME as table_name,
            'VIEW' as table_type
        FROM INFORMATION_SCHEMA.VIEWS
        ORDER BY TABLE_SCHEMA, TABLE_NAME
        """
        
        try:
            results = await db.execute_query(query)
            
            views = []
            for row in results:
                views.append(TableInfo(
                    name=row['table_name'],
                    schema=row['schema_name'],
                    type=row['table_type']
                ))
            
            return views
            
        except Exception as e:
            logger.error("Erro ao listar views", error=str(e))
            raise
    
    async def list_procedures(self) -> List[Dict[str, Any]]:
        """Lista stored procedures do banco"""
        db = await self._get_db()
        
        query = """
        SELECT 
            ROUTINE_SCHEMA as schema_name,
            ROUTINE_NAME as procedure_name,
            ROUTINE_TYPE as routine_type,
            CREATED,
            LAST_ALTERED
        FROM INFORMATION_SCHEMA.ROUTINES
        WHERE ROUTINE_TYPE = 'PROCEDURE'
        ORDER BY ROUTINE_SCHEMA, ROUTINE_NAME
        """
        
        try:
            results = await db.execute_query(query)
            return results
            
        except Exception as e:
            logger.error("Erro ao listar procedures", error=str(e))
            raise
    
    async def list_functions(self) -> List[Dict[str, Any]]:
        """Lista funções do banco"""
        db = await self._get_db()
        
        query = """
        SELECT 
            ROUTINE_SCHEMA as schema_name,
            ROUTINE_NAME as function_name,
            ROUTINE_TYPE as routine_type,
            DATA_TYPE as return_type,
            CREATED,
            LAST_ALTERED
        FROM INFORMATION_SCHEMA.ROUTINES
        WHERE ROUTINE_TYPE = 'FUNCTION'
        ORDER BY ROUTINE_SCHEMA, ROUTINE_NAME
        """
        
        try:
            results = await db.execute_query(query)
            return results
            
        except Exception as e:
            logger.error("Erro ao listar funções", error=str(e))
            raise
    
    async def get_table_data(self, table_name: str, schema: Optional[str] = None, 
                           limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Obtém dados de uma tabela com paginação"""
        db = await self._get_db()
        
        schema = schema or 'dbo'
        
        query = f"""
        SELECT * FROM [{schema}].[{table_name}]
        ORDER BY (SELECT NULL)
        OFFSET ? ROWS
        FETCH NEXT ? ROWS ONLY
        """
        
        try:
            results = await db.execute_query(query, (offset, limit))
            return results
            
        except Exception as e:
            logger.error("Erro ao obter dados da tabela", 
                        table=table_name, schema=schema, error=str(e))
            raise
    
    async def get_database_schema(self) -> Dict[str, Any]:
        """Obtém esquema completo do banco de dados"""
        try:
            tables = await self.list_tables()
            views = await self.list_views()
            procedures = await self.list_procedures()
            functions = await self.list_functions()
            
            # Obtém detalhes das tabelas
            table_details = {}
            for table in tables[:10]:  # Limita para evitar sobrecarga
                try:
                    columns = await self.describe_table(table.name, table.schema)
                    indexes = await self.list_indexes(table.name, table.schema)
                    
                    table_details[f"{table.schema}.{table.name}"] = {
                        "columns": [
                            {
                                "name": col.name,
                                "type": col.data_type,
                                "nullable": col.is_nullable,
                                "primary_key": col.is_primary_key,
                                "foreign_key": col.is_foreign_key
                            }
                            for col in columns
                        ],
                        "indexes": [
                            {
                                "name": idx.name,
                                "columns": idx.columns,
                                "unique": idx.is_unique,
                                "primary": idx.is_primary
                            }
                            for idx in indexes
                        ]
                    }
                except Exception as e:
                    logger.warning(f"Erro ao obter detalhes da tabela {table.name}", error=str(e))
            
            return {
                "tables": [
                    {
                        "name": t.name,
                        "schema": t.schema,
                        "type": t.type,
                        "row_count": t.row_count
                    }
                    for t in tables
                ],
                "views": [
                    {
                        "name": v.name,
                        "schema": v.schema
                    }
                    for v in views
                ],
                "procedures": procedures,
                "functions": functions,
                "table_details": table_details
            }
            
        except Exception as e:
            logger.error("Erro ao obter esquema do banco", error=str(e))
            raise
    
    async def check_constraints(self, table_name: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lista constraints de uma tabela"""
        db = await self._get_db()
        
        schema = schema or 'dbo'
        
        query = """
        SELECT 
            tc.CONSTRAINT_NAME,
            tc.CONSTRAINT_TYPE,
            kcu.COLUMN_NAME,
            CASE 
                WHEN tc.CONSTRAINT_TYPE = 'FOREIGN KEY' THEN
                    ccu.TABLE_SCHEMA + '.' + ccu.TABLE_NAME + '.' + ccu.COLUMN_NAME
                ELSE NULL
            END as REFERENCES
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
        LEFT JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
            ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
        LEFT JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE ccu
            ON tc.CONSTRAINT_NAME = ccu.CONSTRAINT_NAME
        WHERE tc.TABLE_NAME = ? AND tc.TABLE_SCHEMA = ?
        ORDER BY tc.CONSTRAINT_TYPE, tc.CONSTRAINT_NAME
        """
        
        try:
            results = await db.execute_query(query, (table_name, schema))
            return results
            
        except Exception as e:
            logger.error("Erro ao verificar constraints", 
                        table=table_name, schema=schema, error=str(e))
            raise
