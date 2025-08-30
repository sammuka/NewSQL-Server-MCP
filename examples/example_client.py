#!/usr/bin/env python3
"""
Cliente de exemplo para testar o MCP SQL Server
Demonstra como usar as diferentes ferramentas disponíveis
"""

import asyncio
import httpx
import json
from typing import Dict, Any


class MCPSQLClient:
    """Cliente para interagir com o MCP SQL Server"""
    
    def __init__(self, base_url: str = "http://localhost:4000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do servidor"""
        response = await self.client.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    async def get_server_info(self) -> Dict[str, Any]:
        """Obtém informações do servidor"""
        response = await self.client.get(f"{self.base_url}/info")
        response.raise_for_status()
        return response.json()
    
    async def list_available_tools(self) -> Dict[str, Any]:
        """Lista ferramentas disponíveis"""
        response = await self.client.get(f"{self.base_url}/tools")
        response.raise_for_status()
        return response.json()
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None, 
                       client_id: str = "example_client") -> Dict[str, Any]:
        """Chama uma ferramenta específica"""
        payload = {
            "tool_name": tool_name,
            "arguments": arguments or {},
            "client_id": client_id
        }
        
        response = await self.client.post(
            f"{self.base_url}/tools/call",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def list_tables(self, schema: str = None) -> Dict[str, Any]:
        """Lista tabelas do banco"""
        args = {"schema": schema} if schema else {}
        return await self.call_tool("list_tables", args)
    
    async def describe_table(self, table_name: str, schema: str = None) -> Dict[str, Any]:
        """Descreve estrutura de uma tabela"""
        args = {"table_name": table_name}
        if schema:
            args["schema"] = schema
        return await self.call_tool("describe_table", args)
    
    async def execute_select(self, query: str, limit: int = None) -> Dict[str, Any]:
        """Executa uma query SELECT"""
        args = {"query": query}
        if limit:
            args["limit"] = limit
        return await self.call_tool("execute_select", args)


async def run_examples():
    """Executa exemplos de uso do cliente"""
    
    async with MCPSQLClient() as client:
        print("🚀 Iniciando testes do MCP SQL Server\n")
        
        # 1. Health Check
        print("1️⃣ Verificando saúde do servidor...")
        try:
            health = await client.health_check()
            print(f"   Status: {health['status']}")
            print(f"   Banco conectado: {health['database_connection']}")
            print(f"   Modo: {health.get('mode', 'N/A')}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            return
        
        print()
        
        # 2. Informações do servidor
        print("2️⃣ Obtendo informações do servidor...")
        try:
            info = await client.get_server_info()
            print(f"   Nome: {info['name']}")
            print(f"   Versão: {info['version']}")
            print(f"   Modo: {info['mode']}")
            print(f"   Ferramentas: {info['tools_count']}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
        
        print()
        
        # 3. Listar ferramentas disponíveis
        print("3️⃣ Listando ferramentas disponíveis...")
        try:
            tools = await client.list_available_tools()
            print(f"   Modo: {tools['mode']}")
            print(f"   Ferramentas disponíveis:")
            for tool_name in tools['tools'].keys():
                print(f"     - {tool_name}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
        
        print()
        
        # 4. Listar tabelas
        print("4️⃣ Listando tabelas do banco...")
        try:
            tables_result = await client.list_tables()
            if tables_result['success']:
                tables = tables_result['tables']
                print(f"   Total de tabelas: {len(tables)}")
                for table in tables[:5]:  # Mostra apenas as primeiras 5
                    print(f"     - {table['schema']}.{table['name']} ({table['type']})")
                if len(tables) > 5:
                    print(f"     ... e mais {len(tables) - 5} tabelas")
            else:
                print(f"   ❌ Erro: {tables_result['error']}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
        
        print()
        
        # 5. Descrever uma tabela (se existir)
        print("5️⃣ Descrevendo uma tabela...")
        try:
            # Tenta usar uma tabela comum do sistema
            table_result = await client.describe_table("sysobjects", "sys")
            if table_result['success']:
                columns = table_result['columns']
                print(f"   Tabela: {table_result['table_name']}")
                print(f"   Colunas: {len(columns)}")
                for col in columns[:3]:  # Mostra apenas as primeiras 3
                    pk = " (PK)" if col['is_primary_key'] else ""
                    nullable = "NULL" if col['is_nullable'] else "NOT NULL"
                    print(f"     - {col['name']}: {col['data_type']} {nullable}{pk}")
                if len(columns) > 3:
                    print(f"     ... e mais {len(columns) - 3} colunas")
            else:
                print(f"   ❌ Erro: {table_result['error']}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
        
        print()
        
        # 6. Executar query simples
        print("6️⃣ Executando query SELECT simples...")
        try:
            query_result = await client.execute_select(
                "SELECT TOP 3 name, type_desc FROM sys.objects WHERE type = 'U'",
                limit=10
            )
            if query_result['success']:
                data = query_result['data']
                print(f"   Registros retornados: {len(data)}")
                for row in data:
                    print(f"     - {row.get('name', 'N/A')}: {row.get('type_desc', 'N/A')}")
            else:
                print(f"   ❌ Erro: {query_result['error']}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
        
        print("\n✅ Testes concluídos!")


def print_usage():
    """Mostra informações de uso"""
    print("""
🔧 Cliente de Exemplo - MCP SQL Server

Este script demonstra como usar o cliente Python para interagir
com o servidor MCP SQL Server.

Uso:
    python example_client.py

Pré-requisitos:
    - MCP SQL Server rodando em http://localhost:4000
    - Banco de dados SQL Server configurado
    - Dependências: pip install httpx

Exemplos de ferramentas testadas:
    ✅ Health check
    ✅ Informações do servidor  
    ✅ Lista de ferramentas
    ✅ Lista de tabelas
    ✅ Descrição de tabela
    ✅ Execução de SELECT

Para mais exemplos, consulte o README.md
    """)


async def main():
    """Função principal"""
    print_usage()
    
    try:
        await run_examples()
    except KeyboardInterrupt:
        print("\n⚠️ Operação cancelada pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")


if __name__ == "__main__":
    asyncio.run(main())
