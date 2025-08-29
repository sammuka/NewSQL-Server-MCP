"""
Database module - Módulo de gerenciamento de banco de dados
Contém funcionalidades de conexão e operações com SQL Server
"""

from .connection import DatabaseConnection, get_connection
from .operations import DatabaseOperations

__all__ = ["DatabaseConnection", "get_connection", "DatabaseOperations"]
