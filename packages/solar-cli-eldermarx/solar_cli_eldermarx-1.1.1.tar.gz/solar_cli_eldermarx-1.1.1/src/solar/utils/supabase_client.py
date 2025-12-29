"""
Cliente Supabase para uso direto via CLI
Conecta diretamente com a API do Supabase sem depender de MCP ou IDE
"""
import os
import json
from typing import Dict, List, Any, Optional
from supabase import create_client, Client
from pathlib import Path


class SupabaseDirectClient:
    """Cliente para conectar diretamente com Supabase via API"""
    
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        """
        Inicializa o cliente Supabase
        
        Args:
            url: URL do projeto Supabase (opcional, busca do config)
            key: Service key do Supabase (opcional, busca do config)
        """
        self.config_path = self._get_config_path()
        self.config = self._load_config()
        
        # Usar parâmetros ou config
        self.url = url or self.config.get('url')
        self.key = key or self.config.get('service_key')
        
        self.client: Optional[Client] = None
        
        if self.url and self.key:
            try:
                self.client = create_client(self.url, self.key)
            except Exception as e:
                raise ConnectionError(f"Erro ao conectar com Supabase: {str(e)}")
    
    def _get_config_path(self) -> Path:
        """Retorna o caminho do arquivo de configuração"""
        # Procura no diretório atual primeiro
        local_config = Path.cwd() / '.solar' / 'supabase.json'
        if local_config.exists():
            return local_config
        
        # Depois no diretório home
        home_config = Path.home() / '.solar' / 'supabase.json'
        return home_config
    
    def _load_config(self) -> Dict[str, Any]:
        """Carrega configuração do arquivo"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_config(self, config: Dict[str, Any]):
        """Salva configuração no arquivo"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def configure(self, url: str, key: str, project_name: Optional[str] = None):
        """
        Configura conexão com Supabase
        
        Args:
            url: URL do projeto (ex: https://xxx.supabase.co)
            key: Service key ou anon key
            project_name: Nome do projeto (opcional)
        """
        config = {
            'url': url,
            'service_key': key,
        }
        
        if project_name:
            config['project_name'] = project_name
        
        self._save_config(config)
        self.url = url
        self.key = key
        self.config = config
        
        # Testar conexão
        try:
            self.client = create_client(url, key)
            return True
        except Exception as e:
            raise ConnectionError(f"Erro ao conectar: {str(e)}")
    
    def is_configured(self) -> bool:
        """Verifica se está configurado"""
        return self.config_path.exists() and bool(self.url and self.key)
    
    def test_connection(self) -> bool:
        """Testa a conexão com Supabase"""
        if not self.client:
            return False
        
        try:
            # Tenta listar tabelas para testar conexão
            result = self.client.table('_supabase_migrations').select("*").limit(1).execute()
            return True
        except:
            # Se não conseguir acessar _supabase_migrations, tenta outro endpoint
            try:
                # Endpoint alternativo para verificar conexão
                return self.client is not None
            except:
                return False
    
    def list_tables(self) -> List[Dict[str, Any]]:
        """
        Lista todas as tabelas do projeto
        
        Returns:
            List[Dict]: Lista de tabelas com informações
        """
        if not self.client:
            raise ConnectionError("Cliente não configurado. Execute 'solx supabase setup' primeiro.")
        
        # Query SQL para listar tabelas
        query = """
        SELECT 
            table_name,
            table_schema
        FROM information_schema.tables
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
        """
        
        try:
            result = self.client.rpc('exec_sql', {'query': query}).execute()
            return result.data if result.data else []
        except Exception as e:
            # Método alternativo: usar PostgREST API introspection
            # Isso funciona com a anon key também
            try:
                # Tenta pegar metadata das tabelas públicas
                from supabase import create_client
                # Usando REST API para descobrir tabelas
                # Não há endpoint direto, então vamos tentar common tables
                common_tables = ['users', 'profiles', 'posts', 'products', 'orders']
                tables = []
                for table in common_tables:
                    try:
                        self.client.table(table).select("*").limit(0).execute()
                        tables.append({'table_name': table, 'table_schema': 'public'})
                    except:
                        pass
                return tables
            except:
                raise Exception(f"Erro ao listar tabelas: {str(e)}\nDica: Use uma service_role key para acesso completo.")
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """
        Obtém o esquema de uma tabela
        
        Args:
            table_name: Nome da tabela
            
        Returns:
            Dict: Esquema da tabela
        """
        if not self.client:
            raise ConnectionError("Cliente não configurado.")
        
        query = f"""
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_name = '{table_name}'
        AND table_schema = 'public'
        ORDER BY ordinal_position;
        """
        
        try:
            result = self.client.rpc('exec_sql', {'query': query}).execute()
            
            return {
                'table_name': table_name,
                'columns': result.data if result.data else []
            }
        except Exception as e:
            raise Exception(f"Erro ao obter esquema: {str(e)}\nDica: Use uma service_role key.")
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Executa uma query SQL customizada
        
        Args:
            query: Query SQL
            
        Returns:
            List[Dict]: Resultados
            
        Warning:
            Use com cuidado! Esta função executa SQL direto.
        """
        if not self.client:
            raise ConnectionError("Cliente não configurado.")
        
        try:
            result = self.client.rpc('exec_sql', {'query': query}).execute()
            return result.data if result.data else []
        except Exception as e:
            raise Exception(f"Erro ao executar query: {str(e)}")
    
    def select_from_table(
        self, 
        table_name: str, 
        columns: str = "*",
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Seleciona dados de uma tabela
        
        Args:
            table_name: Nome da tabela
            columns: Colunas a retornar (padrão: "*")
            limit: Limite de registros
            filters: Filtros a aplicar (ex: {'status': 'active'})
            
        Returns:
            List[Dict]: Registros encontrados
        """
        if not self.client:
            raise ConnectionError("Cliente não configurado.")
        
        try:
            query = self.client.table(table_name).select(columns)
            
            # Aplicar filtros
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            result = query.limit(limit).execute()
            return result.data
        except Exception as e:
            raise Exception(f"Erro ao consultar tabela: {str(e)}")
    
    def insert_into_table(
        self, 
        table_name: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Insere dados em uma tabela
        
        Args:
            table_name: Nome da tabela
            data: Dados a inserir
            
        Returns:
            Dict: Registro inserido
        """
        if not self.client:
            raise ConnectionError("Cliente não configurado.")
        
        try:
            result = self.client.table(table_name).insert(data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            raise Exception(f"Erro ao inserir: {str(e)}")
    
    def update_table(
        self, 
        table_name: str, 
        data: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Atualiza registros em uma tabela
        
        Args:
            table_name: Nome da tabela
            data: Dados a atualizar
            filters: Filtros para identificar registros
            
        Returns:
            List[Dict]: Registros atualizados
        """
        if not self.client:
            raise ConnectionError("Cliente não configurado.")
        
        try:
            query = self.client.table(table_name).update(data)
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            result = query.execute()
            return result.data
        except Exception as e:
            raise Exception(f"Erro ao atualizar: {str(e)}")
    
    def delete_from_table(
        self, 
        table_name: str,
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Deleta registros de uma tabela
        
        Args:
            table_name: Nome da tabela
            filters: Filtros para identificar registros
            
        Returns:
            List[Dict]: Registros deletados
        """
        if not self.client:
            raise ConnectionError("Cliente não configurado.")
        
        try:
            query = self.client.table(table_name).delete()
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            result = query.execute()
            return result.data
        except Exception as e:
            raise Exception(f"Erro ao deletar: {str(e)}")
    
    def create_table(
        self, 
        table_name: str, 
        columns: Dict[str, str]
    ) -> bool:
        """
        Cria uma nova tabela
        
        Args:
            table_name: Nome da tabela
            columns: Dicionário {nome_coluna: tipo_sql}
            
        Returns:
            bool: True se sucesso
            
        Example:
            >>> client.create_table('products', {
            ...     'id': 'uuid PRIMARY KEY DEFAULT gen_random_uuid()',
            ...     'name': 'text NOT NULL',
            ...     'price': 'decimal(10,2)',
            ...     'created_at': 'timestamp DEFAULT now()'
            ... })
        """
        if not self.client:
            raise ConnectionError("Cliente não configurado.")
        
        columns_sql = ",\n  ".join([f"{name} {dtype}" for name, dtype in columns.items()])
        query = f"CREATE TABLE {table_name} (\n  {columns_sql}\n);"
        
        try:
            self.execute_query(query)
            return True
        except Exception as e:
            raise Exception(f"Erro ao criar tabela: {str(e)}")


# Singleton instance
_supabase_client: Optional[SupabaseDirectClient] = None


def get_supabase_client() -> SupabaseDirectClient:
    """Retorna instância singleton do cliente Supabase"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseDirectClient()
    return _supabase_client
