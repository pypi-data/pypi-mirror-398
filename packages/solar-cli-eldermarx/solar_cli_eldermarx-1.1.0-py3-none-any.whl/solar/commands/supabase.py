"""
Comandos CLI para interagir com Supabase diretamente via terminal
Não requer IDE - funciona puro no CLI!
"""
import click
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from solar.utils.supabase_client import get_supabase_client

console = Console()


@click.group()
def supabase():
    """Gerenciar conexão direta com Supabase via CLI"""
    pass


@supabase.command()
@click.option('--url', '-u', help='URL do projeto Supabase (ex: https://xxx.supabase.co)')
@click.option('--key', '-k', help='Service key do Supabase')  
@click.option('--name', '-n', help='Nome do projeto (opcional)')
def setup(url, key, name):
    """Configurar conexão direta com Supabase"""
    console.print("\n[bold cyan]🔧 Configurando conexão com Supabase...[/bold cyan]\n")
    
    try:
        client = get_supabase_client()
        
        # Se não passou parâmetros, perguntar interativamente
        if not url:
            console.print("[yellow]📍 Passo 1:[/yellow] Encontre suas credenciais em:")
            console.print("   → https://app.supabase.com/project/[SEU-PROJETO]/settings/api\n")
            
            url = Prompt.ask("[cyan]URL do projeto Supabase[/cyan]")
        
        if not key:
            console.print("\n[yellow]🔑 Passo 2:[/yellow] Escolha qual key usar:")
            console.print("   • [green]anon/public key[/green]: Operações básicas (SELECT, INSERT)")
            console.print("   • [red]service_role key[/red]: Acesso total (recomendado)\n")
            
            key = Prompt.ask("[cyan]Service Key do Supabase[/cyan]", password=True)
        
        if not name:
            name = Prompt.ask("[cyan]Nome do projeto (opcional)[/cyan]", default="")
        
        # Configurar
        console.print("\n[dim]Testando conexão...[/dim]")
        client.configure(url, key, name if name else None)
        
        # Testar conexão
        if client.test_connection():
            console.print("[green]✅ Conexão estabelecida com sucesso![/green]\n")
        else:
            console.print("[yellow]⚠️  Configuração salva, mas não foi possível testar a conexão.[/yellow]")
            console.print("[dim]Isso pode ser normal dependendo das permissões da key.[/dim]\n")
        
        # Mostrar próximos passos
        panel_content = """[bold]Comandos disponíveis:[/bold]

📊 [cyan]solx supabase tables[/cyan]
   Lista todas as tabelas do projeto

🔍 [cyan]solx supabase describe TABELA[/cyan]
   Mostra o esquema de uma tabela

📖 [cyan]solx supabase select TABELA[/cyan]
   Consulta dados de uma tabela

➕ [cyan]solx supabase insert TABELA[/cyan]
   Insere dados em uma tabela

🔧 [cyan]solx supabase query "SELECT * FROM..."[/cyan]
   Executa SQL customizado

[bold green]✨ Tudo configurado e pronto para uso![/bold green]
"""
        
        console.print(Panel(panel_content, title="[bold green]Configuração Concluída[/bold green]", expand=False))
        
    except Exception as e:
        console.print(f"[red]❌ Erro: {str(e)}[/red]")


@supabase.command()
def status():
    """Verifica status da conexão"""
    console.print("\n[bold cyan]🔍 Verificando status...[/bold cyan]\n")
    
    try:
        client = get_supabase_client()
        
        # Criar tabela de status  
        table = Table(title="Status da Conexão Supabase")
        table.add_column("Item", style="cyan", no_wrap=True)
        table.add_column("Status", style="magenta")
        
        # Verificar configuração
        is_configured = client.is_configured()
        config_status = "[green]✅ Configurado[/green]" if is_configured else "[red]❌ Não configurado[/red]"
        table.add_row("Arquivo de configuração", config_status)
        
        if is_configured:
            table.add_row("URL", client.url or "N/A")
            table.add_row("Projeto", client.config.get('project_name', 'N/A'))
            
            # Testar conexão
            try:
                if client.test_connection():
                    table.add_row("Conexão", "[green]✅ Ativa[/green]")
                else:
                    table.add_row("Conexão", "[yellow]⚠️  Não testada[/yellow]")
            except:
                table.add_row("Conexão", "[red]❌ Falha[/red]")
        
        console.print(table)
        
        if not is_configured:
            console.print("\n[yellow]💡 Execute:[/yellow] [cyan]solx supabase setup[/cyan]\n")
        
    except Exception as e:
        console.print(f"[red]❌ Erro: {str(e)}[/red]")


@supabase.command()
def tables():
    """Lista todas as tabelas disponíveis"""
    console.print("\n[bold cyan]📊 Listando tabelas...[/bold cyan]\n")
    
    try:
        client = get_supabase_client()
        
        if not client.is_configured():
            console.print("[red]❌ Não configurado. Execute: solx supabase setup[/red]")
            return
        
        tables_list = client.list_tables()
        
        if not tables_list:
            console.print("[yellow]⚠️  Nenhuma tabela encontrada ou sem permissão.[/yellow]")
            console.print("[dim]Dica: Use service_role key para listagem completa.[/dim]")
            return
        
        # Mostrar em tabela
        table = Table(title=f"Tabelas - {client.config.get('project_name', 'Projeto')}")
        table.add_column("#", style="dim", width=4)
        table.add_column("Nome", style="cyan")
        table.add_column("Schema", style="green")
        
        for idx, tbl in enumerate(tables_list, 1):
            table.add_row(
                str(idx),
                tbl.get('table_name', 'N/A'),
                tbl.get('table_schema', 'public')
            )
        
        console.print(table)
        console.print(f"\n[dim]Total: {len(tables_list)} tabelas[/dim]\n")
        
    except Exception as e:
        console.print(f"[red]❌ Erro: {str(e)}[/red]")


@supabase.command()
@click.argument('table_name')
def describe(table_name):
    """Mostra o esquema de uma tabela"""
    console.print(f"\n[bold cyan]📋 Esquema da tabela: {table_name}[/bold cyan]\n")
    
    try:
        client = get_supabase_client()
        
        if not client.is_configured():
            console.print("[red]❌ Não configurado. Execute: solx supabase setup[/red]")
            return
        
        schema = client.get_table_schema(table_name)
        
        if not schema.get('columns'):
            console.print(f"[yellow]⚠️  Tabela '{table_name}' não encontrada ou sem permissão.[/yellow]")
            return
        
        # Mostrar esquema
        table = Table(title=f"Esquema: {table_name}")
        table.add_column("Coluna", style="cyan")
        table.add_column("Tipo", style="green")
        table.add_column("Nulo?", style="yellow")
        table.add_column("Padrão", style="blue")
        
        for col in schema['columns']:
            table.add_row(
                col.get('column_name', ''),
                col.get('data_type', ''),
                col.get('is_nullable', ''),
                col.get('column_default', '') or '-'
            )
        
        console.print(table)
        console.print()
        
    except Exception as e:
        console.print(f"[red]❌ Erro: {str(e)}[/red]")


@supabase.command()
@click.argument('table_name')
@click.option('--limit', '-l', default=10, help='Limite de registros')
@click.option('--filter', '-f', multiple=True, help='Filtro: campo=valor')
def select(table_name, limit, filter):
    """Consulta dados de uma tabela"""
    console.print(f"\n[bold cyan]� Consultando: {table_name}[/bold cyan]\n")
    
    try:
        client = get_supabase_client()
        
        if not client.is_configured():
            console.print("[red]❌ Não configurado. Execute: solx supabase setup[/red]")
            return
        
        # Processar filtros
        filters = {}
        if filter:
            for f in filter:
                if '=' in f:
                    key, value = f.split('=', 1)
                    filters[key.strip()] = value.strip()
        
        # Consultar
        data = client.select_from_table(table_name, limit=limit, filters=filters if filters else None)
        
        if not data:
            console.print(f"[yellow]⚠️  Nenhum registro encontrado.[/yellow]")
            return
        
        # Mostrar resultados em JSON formatado
        console.print(f"[green]✅ {len(data)} registro(s) encontrado(s):[/green]\n")
        
        for idx, record in enumerate(data, 1):
            syntax = Syntax(json.dumps(record, indent=2, ensure_ascii=False), "json", theme="monokai")
            console.print(f"[bold cyan]Registro #{idx}:[/bold cyan]")
            console.print(syntax)
            console.print()
        
    except Exception as e:
        console.print(f"[red]❌ Erro: {str(e)}[/red]")


@supabase.command()
@click.argument('table_name')
@click.option('--data', '-d', help='Dados JSON para inserir')
def insert(table_name, data):
    """Insere dados em uma tabela"""
    console.print(f"\n[bold cyan]➕ Inserindo em: {table_name}[/bold cyan]\n")
    
    try:
        client = get_supabase_client()
        
        if not client.is_configured():
            console.print("[red]❌ Não configurado. Execute: solx supabase setup[/red]")
            return
        
        # Parse JSON
        if not data:
            console.print("[yellow]Exemplo:[/yellow] solx supabase insert users --data '{\"name\": \"João\", \"email\": \"joao@example.com\"}'")
            console.print("\n[dim]Digite os dados no formato JSON:[/dim]")
            data = Prompt.ask("[cyan]Dados[/cyan]")
        
        try:
            data_dict = json.loads(data)
        except json.JSONDecodeError as e:
            console.print(f"[red]❌ JSON inválido: {str(e)}[/red]")
            return
        
        # Inserir
        result = client.insert_into_table(table_name, data_dict)
        
        console.print("[green]✅ Registro inserido com sucesso![/green]\n")
        syntax = Syntax(json.dumps(result, indent=2, ensure_ascii=False), "json", theme="monokai")
        console.print(syntax)
        console.print()
        
    except Exception as e:
        console.print(f"[red]❌ Erro: {str(e)}[/red]")


@supabase.command()
@click.argument('sql_query')
def query(sql_query):
    """Executa uma query SQL customizada"""
    console.print(f"\n[bold cyan]� Executando query...[/bold cyan]\n")
    
    try:
        client = get_supabase_client()
        
        if not client.is_configured():
            console.print("[red]❌ Não configurado. Execute: solx supabase setup[/red]")
            return
        
        # Mostrar query
        syntax = Syntax(sql_query, "sql", theme="monokai")
        console.print("[bold]Query:[/bold]")
        console.print(syntax)
        console.print()
        
        # Confirmar execução
        if not Confirm.ask("[yellow]Executar esta query?[/yellow]"):
            console.print("[dim]Cancelado.[/dim]")
            return
        
        # Executar
        result = client.execute_query(sql_query)
        
        console.print(f"[green]✅ Query executada![/green]\n")
        
        if result:
            console.print(f"[cyan]Resultados ({len(result)} linha(s)):[/cyan]\n")
            syntax = Syntax(json.dumps(result, indent=2, ensure_ascii=False), "json", theme="monokai")
            console.print(syntax)
        else:
            console.print("[dim]Nenhum resultado retornado.[/dim]")
        
        console.print()
        
    except Exception as e:
        console.print(f"[red]❌ Erro: {str(e)}[/red]")


@supabase.command()
@click.argument('table_name')
@click.option('--column', '-c', multiple=True, required=True, help='Coluna: nome:tipo')
def create_table(table_name, column):
    """Cria uma nova tabela"""
    console.print(f"\n[bold cyan]🆕 Criando tabela: {table_name}[/bold cyan]\n")
    
    try:
        client = get_supabase_client()
        
        if not client.is_configured():
            console.print("[red]❌ Não configurado. Execute: solx supabase setup[/red]")
            return
        
        # Processar colunas
        columns = {}
        for col in column:
            if ':' in col:
                name, dtype = col.split(':', 1)
                columns[name.strip()] = dtype.strip()
        
        if not columns:
            console.print("[red]❌ Nenhuma coluna especificada.[/red]")
            console.print("[yellow]Exemplo:[/yellow] solx supabase create-table products -c 'id:uuid PRIMARY KEY' -c 'name:text NOT NULL'")
            return
        
        # Mostrar SQL que será executado
        columns_sql = ",\n  ".join([f"{name} {dtype}" for name, dtype in columns.items()])
        sql = f"CREATE TABLE {table_name} (\n  {columns_sql}\n);"
        
        syntax = Syntax(sql, "sql", theme="monokai")
        console.print("[bold]SQL que será executado:[/bold]")
        console.print(syntax)
        console.print()
        
        # Confirmar
        if not Confirm.ask("[yellow]Criar esta tabela?[/yellow]"):
            console.print("[dim]Cancelado.[/dim]")
            return
        
        # Criar
        client.create_table(table_name, columns)
        console.print(f"[green]✅ Tabela '{table_name}' criada com sucesso![/green]\n")
        
    except Exception as e:
        console.print(f"[red]❌ Erro: {str(e)}[/red]")


if __name__ == '__main__':
    supabase()
