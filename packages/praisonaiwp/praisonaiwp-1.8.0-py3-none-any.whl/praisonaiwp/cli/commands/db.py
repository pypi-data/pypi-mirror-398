"""WordPress database commands"""

import click
from rich.console import Console
from rich.table import Table

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


@click.group()
def db_command():
    """WordPress database operations"""
    pass


@db_command.command("query")
@click.argument("sql_query")
@click.option("--server", default=None, help="Server name from config")
def db_query(sql_query, server):
    """
    Execute a database query

    Examples:

        # Simple query
        praisonaiwp db query "SELECT COUNT(*) FROM wp_posts"

        # Query with conditions
        praisonaiwp db query "SELECT * FROM wp_posts WHERE post_status = 'publish' LIMIT 5"

        # Query on specific server
        praisonaiwp db query "SHOW TABLES" --server production
    """
    try:
        config = Config()
        server_config = config.get_server(server)

        with SSHManager(
            server_config["hostname"],
            server_config["username"],
            server_config.get("key_filename"),
            server_config.get("port", 22),
        ) as ssh:

            wp = WPClient(
                ssh,
                server_config["wp_path"],
                server_config.get("php_bin", "php"),
                server_config.get("wp_cli", "/usr/local/bin/wp"),
            )

            results = wp.db_query(sql_query)

            if results:
                if isinstance(results, list) and len(results) > 0:
                    # Display results in table format
                    if isinstance(results[0], dict):
                        table = Table(title=f"Query Results ({len(results)} rows)")

                        # Add columns from first row
                        for column in results[0].keys():
                            table.add_column(column, style="cyan")

                        # Add rows
                        for row in results:
                            table.add_row(*[str(value) for value in row.values()])

                        console.print(table)
                    else:
                        # Simple list of values
                        console.print(f"[cyan]Results ({len(results)}):[/cyan]")
                        for i, result in enumerate(results, 1):
                            console.print(f"  {i}. {result}")
                else:
                    # Single result
                    console.print(f"[cyan]Result:[/cyan] {results}")
            else:
                console.print("[yellow]No results returned[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Database query failed: {e}")
        raise click.Abort() from None
