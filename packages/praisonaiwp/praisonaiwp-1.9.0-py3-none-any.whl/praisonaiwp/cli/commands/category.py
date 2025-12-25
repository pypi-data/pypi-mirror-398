"""Category command - Manage WordPress post categories"""

import click
from rich.console import Console
from rich.table import Table

from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


def _parse_category_input(category_str, category_id_str, wp):
    """
    Parse category input and return list of category IDs

    Args:
        category_str: Comma-separated category names/slugs
        category_id_str: Comma-separated category IDs
        wp: WPClient instance

    Returns:
        List of category IDs
    """
    category_ids = []

    if category_id_str:
        # Parse category IDs
        try:
            category_ids = [int(cid.strip()) for cid in category_id_str.split(",")]
        except ValueError as err:
            raise click.ClickException(
                "Invalid category ID format. Must be comma-separated integers."
            ) from err

    elif category_str:
        # Parse category names/slugs
        category_names = [name.strip() for name in category_str.split(",")]

        for name in category_names:
            cat = wp.get_category_by_name(name)
            if not cat:
                raise click.ClickException(f"Category '{name}' not found")
            category_ids.append(int(cat["term_id"]))

    else:
        raise click.ClickException("Either --category or --category-id must be provided")

    return category_ids


@click.group()
def category_command():
    """Manage WordPress post categories"""
    pass


@category_command.command(name="set")
@click.argument("post_id", type=int)
@click.option("--category", help="Comma-separated category names/slugs")
@click.option("--category-id", help="Comma-separated category IDs")
@click.option("--server", default=None, help="Server name from config")
def set_categories(post_id, category, category_id, server):
    """
    Set post categories (replace all existing)

    Examples:

        # Set by category name
        praisonaiwp category set 48975 --category "RAG"

        # Set multiple categories
        praisonaiwp category set 48975 --category "RAG,AI,Python"

        # Set by category ID
        praisonaiwp category set 48975 --category-id "353"
    """
    try:
        config = Config()
        server_config = config.get_server(server)

        console.print(f"\n[yellow]Setting categories for post {post_id}...[/yellow]")

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

            # Parse category input
            category_ids = _parse_category_input(category, category_id, wp)

            # Get category names for display
            category_names = []
            for cid in category_ids:
                cat = wp.get_category_by_id(cid)
                if cat:
                    category_names.append(cat["name"])

            # Set categories
            wp.set_post_categories(post_id, category_ids)

            console.print(
                f"[green]✓ Set categories for post {post_id}: {', '.join(category_names)}[/green]\n"
            )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Category set failed: {e}")
        raise click.Abort() from None


@category_command.command(name="add")
@click.argument("post_id", type=int)
@click.option("--category", help="Comma-separated category names/slugs")
@click.option("--category-id", help="Comma-separated category IDs")
@click.option("--server", default=None, help="Server name from config")
def add_categories(post_id, category, category_id, server):
    """
    Add categories to post (append)

    Examples:

        # Add by category name
        praisonaiwp category add 48975 --category "Python"

        # Add multiple categories
        praisonaiwp category add 48975 --category "Python,Tutorial"

        # Add by category ID
        praisonaiwp category add 48975 --category-id "42"
    """
    try:
        config = Config()
        server_config = config.get_server(server)

        console.print(f"\n[yellow]Adding categories to post {post_id}...[/yellow]")

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

            # Parse category input
            category_ids = _parse_category_input(category, category_id, wp)

            # Add each category
            added_names = []
            for cid in category_ids:
                wp.add_post_category(post_id, cid)
                cat = wp.get_category_by_id(cid)
                if cat:
                    added_names.append(cat["name"])

            console.print(
                f"[green]✓ Added categories to post {post_id}: {', '.join(added_names)}[/green]\n"
            )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Category add failed: {e}")
        raise click.Abort() from None


@category_command.command(name="remove")
@click.argument("post_id", type=int)
@click.option("--category", help="Comma-separated category names/slugs")
@click.option("--category-id", help="Comma-separated category IDs")
@click.option("--server", default=None, help="Server name from config")
def remove_categories(post_id, category, category_id, server):
    """
    Remove categories from post

    Examples:

        # Remove by category name
        praisonaiwp category remove 48975 --category "Uncategorized"

        # Remove multiple categories
        praisonaiwp category remove 48975 --category "Draft,Uncategorized"

        # Remove by category ID
        praisonaiwp category remove 48975 --category-id "1"
    """
    try:
        config = Config()
        server_config = config.get_server(server)

        console.print(f"\n[yellow]Removing categories from post {post_id}...[/yellow]")

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

            # Parse category input
            category_ids = _parse_category_input(category, category_id, wp)

            # Remove each category
            removed_names = []
            for cid in category_ids:
                cat = wp.get_category_by_id(cid)
                if cat:
                    removed_names.append(cat["name"])
                wp.remove_post_category(post_id, cid)

            console.print(
                f"[green]✓ Removed categories from post {post_id}: {', '.join(removed_names)}[/green]\n"
            )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Category remove failed: {e}")
        raise click.Abort() from None


@category_command.command(name="list")
@click.argument("post_id", type=int, required=False)
@click.option("--search", help="Search query")
@click.option("--server", default=None, help="Server name from config")
def list_categories(post_id, search, server):
    """
    List categories (all or for specific post)

    Examples:

        # List all categories
        praisonaiwp category list

        # List categories for specific post
        praisonaiwp category list 48975

        # Search categories
        praisonaiwp category list --search "RAG"
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

            if post_id:
                # List categories for specific post
                console.print(f"\n[yellow]Fetching categories for post {post_id}...[/yellow]\n")
                categories = wp.get_post_categories(post_id)
                title = f"Categories for Post {post_id}"
            else:
                # List all categories
                if search:
                    console.print(f"\n[yellow]Searching categories for '{search}'...[/yellow]\n")
                else:
                    console.print("\n[yellow]Fetching all categories...[/yellow]\n")
                categories = wp.list_categories(search=search)
                title = "All Categories" if not search else f"Categories matching '{search}'"

            if not categories:
                console.print("[yellow]No categories found[/yellow]\n")
                return

            # Display results in table
            table = Table(title=f"{title} ({len(categories)})")

            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="white")
            table.add_column("Slug", style="dim")
            table.add_column("Parent", style="yellow")

            if not post_id:
                table.add_column("Count", style="green")

            for cat in categories:
                row = [str(cat["term_id"]), cat["name"], cat["slug"], str(cat.get("parent", "0"))]

                if not post_id:
                    row.append(str(cat.get("count", "0")))

                table.add_row(*row)

            console.print(table)
            console.print()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Category list failed: {e}")
        raise click.Abort() from None


@category_command.command(name="search")
@click.argument("query")
@click.option("--server", default=None, help="Server name from config")
def search_categories(query, server):
    """
    Search for categories by name

    Examples:

        # Search for categories
        praisonaiwp category search "RAG"

        # Search for AI categories
        praisonaiwp category search "AI"
    """
    try:
        config = Config()
        server_config = config.get_server(server)

        console.print(f"\n[yellow]Searching for categories matching '{query}'...[/yellow]\n")

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

            categories = wp.list_categories(search=query)

            if not categories:
                console.print(f"[yellow]No categories found matching '{query}'[/yellow]\n")
                return

            # Display results in table
            table = Table(title=f"Categories matching '{query}' ({len(categories)})")

            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="white")
            table.add_column("Slug", style="dim")
            table.add_column("Parent", style="yellow")
            table.add_column("Count", style="green")

            for cat in categories:
                table.add_row(
                    str(cat["term_id"]),
                    cat["name"],
                    cat["slug"],
                    str(cat.get("parent", "0")),
                    str(cat.get("count", "0")),
                )

            console.print(table)
            console.print()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Category search failed: {e}")
        raise click.Abort() from None


@category_command.command(name="create")
@click.argument("name")
@click.option("--slug", help="Category slug")
@click.option("--description", help="Category description")
@click.option("--parent", type=int, help="Parent category ID")
@click.option("--server", default=None, help="Server name from config")
def create_category(name, slug, description, parent, server):
    """
    Create a new category

    Examples:

        # Create basic category
        praisonaiwp category create "Technology"

        # Create category with slug and description
        praisonaiwp category create "AI" --slug "artificial-intelligence" --description "AI related posts"

        # Create child category
        praisonaiwp category create "Machine Learning" --parent 123
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

            category_id = wp.create_category(
                name=name, slug=slug, description=description, parent=parent
            )

            console.print(f"[green]✓ Created category '{name}' with ID {category_id}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Create category failed: {e}")
        raise click.Abort() from None


@category_command.command(name="update")
@click.argument("category_id", type=int)
@click.option("--name", help="New category name")
@click.option("--slug", help="New category slug")
@click.option("--description", help="New category description")
@click.option("--parent", type=int, help="New parent category ID")
@click.option("--server", default=None, help="Server name from config")
def update_category(category_id, name, slug, description, parent, server):
    """
    Update an existing category

    Examples:

        # Update category name
        praisonaiwp category update 123 --name "New Name"

        # Update multiple fields
        praisonaiwp category update 123 --name "AI" --slug "artificial-intelligence" --description "Updated description"
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

            success = wp.update_category(
                category_id=category_id,
                name=name,
                slug=slug,
                description=description,
                parent=parent,
            )

            if success:
                console.print(f"[green]✓ Updated category {category_id}[/green]")
            else:
                console.print(f"[red]Failed to update category {category_id}[/red]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Update category failed: {e}")
        raise click.Abort() from None


@category_command.command(name="delete")
@click.argument("category_id", type=int)
@click.option("--server", default=None, help="Server name from config")
@click.confirmation_option(prompt="Are you sure you want to delete this category?")
def delete_category(category_id, server):
    """
    Delete a category

    Examples:

        # Delete category
        praisonaiwp category delete 123
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

            success = wp.delete_category(category_id)

            if success:
                console.print(f"[green]✓ Deleted category {category_id}[/green]")
            else:
                console.print(f"[red]Failed to delete category {category_id}[/red]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Delete category failed: {e}")
        raise click.Abort() from None
