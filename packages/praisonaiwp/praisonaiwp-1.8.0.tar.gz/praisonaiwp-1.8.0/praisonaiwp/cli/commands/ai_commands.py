"""AI-powered content generation commands"""
import click

from praisonaiwp.ai import AI_AVAILABLE
from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager

# Import all AI command modules
from praisonaiwp.cli.commands.ai_summarizer import summarize
from praisonaiwp.cli.commands.ai_optimizer import optimize
from praisonaiwp.cli.commands.ai_translator import translate
from praisonaiwp.cli.commands.ai_scheduler import schedule
from praisonaiwp.cli.commands.ai_moderator import moderate
from praisonaiwp.cli.commands.ai_curator import curate
from praisonaiwp.cli.commands.ai_researcher import research
from praisonaiwp.cli.commands.ai_image import image
from praisonaiwp.cli.commands.ai_chatbot import chatbot
from praisonaiwp.cli.commands.ai_analyzer import analyze
from praisonaiwp.cli.commands.ai_seo import seo
from praisonaiwp.cli.commands.ai_workflow import workflow
from praisonaiwp.cli.commands.ai_bulk import bulk


@click.group()
def ai():
    """AI-powered content generation commands"""
    pass


@ai.command()
@click.argument('topic')
@click.option('--title', help='Post title (defaults to topic)')
@click.option('--status', default='draft', help='Post status (draft/publish/private)')
@click.option('--type', 'post_type', default='post', help='Post type (post, page)')
@click.option('--category', help='Comma-separated category names or slugs')
@click.option('--category-id', help='Comma-separated category IDs')
@click.option('--author', help='Post author (user ID or login)')
@click.option('--excerpt', help='Post excerpt')
@click.option('--date', help='Post date (YYYY-MM-DD HH:MM:SS)')
@click.option('--tags', help='Comma-separated tag names or IDs')
@click.option('--meta', help='Post meta in JSON format: {"key":"value"}')
@click.option('--comment-status', help='Comment status (open, closed)')
@click.option('--auto-publish', is_flag=True, help='Automatically publish to WordPress')
@click.option('--verbose', is_flag=True, help='Verbose output')
@click.option('--server', help='Server name from config')
def generate(topic, title, status, post_type, category, category_id, author, excerpt,
             date, tags, meta, comment_status, auto_publish, verbose, server):
    """Generate content using AI

    Examples:
        praisonaiwp ai generate "AI Trends 2025"
        praisonaiwp ai generate "AI Trends" --title "The Future of AI" --auto-publish
        praisonaiwp ai generate "AI" --status publish --auto-publish --verbose
        praisonaiwp ai generate "AI" --category "Technology,AI" --auto-publish
        praisonaiwp ai generate "AI" --author praison --tags "ai,tech" --auto-publish
    """
    # Check if AI is available
    if not AI_AVAILABLE:
        click.echo(click.style(
            "Error: AI features not available. "
            "Install with: pip install 'praisonaiwp[ai]'",
            fg='red'
        ))
        raise click.Abort() from None

    # Load config
    config = Config()
    if not config.exists():
        click.echo(click.style(
            "Error: Configuration not found. Run 'praisonaiwp init' first.",
            fg='red'
        ))
        raise click.Abort() from None

    # Import here to avoid import errors when AI not installed
    from praisonaiwp.ai.integration import PraisonAIWPIntegration
    from praisonaiwp.core.wp_client import WPClient

    try:
        # Get server config
        server_config = config.get_server(server)

        # Create SSH manager and WP client
        ssh_manager = SSHManager(
            hostname=server_config.get('hostname') or server_config.get('ssh_host'),
            username=server_config.get('username') or server_config.get('ssh_user'),
            key_file=server_config.get('key_file') or server_config.get('ssh_key'),
            port=server_config.get('port', 22)
        )

        wp_client = WPClient(
            ssh=ssh_manager,
            wp_path=server_config.get('wp_path', '/var/www/html'),
            php_bin=server_config.get('php_bin', 'php'),
            wp_cli=server_config.get('wp_cli', '/usr/local/bin/wp'),
            verify_installation=False  # Skip verification for AI commands
        )

        # Create integration
        integration = PraisonAIWPIntegration(
            wp_client,
            status=status,
            verbose=1 if verbose else 0
        )

        # Show progress
        click.echo(f"Generating content about: {topic}")
        if verbose:
            click.echo("Model: gpt-4o-mini")
            click.echo(f"Status: {status}")
            click.echo(f"Type: {post_type}")
            if category or category_id:
                click.echo(f"Categories: {category or category_id}")
            if author:
                click.echo(f"Author: {author}")
            if tags:
                click.echo(f"Tags: {tags}")

        # Generate content
        result = integration.generate(
            topic=topic,
            title=title,
            auto_publish=auto_publish,
            post_type=post_type,
            category=category,
            category_id=category_id,
            author=author,
            excerpt=excerpt,
            date=date,
            tags=tags,
            meta=meta,
            comment_status=comment_status
        )

        # Show result
        click.echo("\n" + "="*50)
        click.echo(click.style("Generated Content:", fg='green', bold=True))
        click.echo("="*50)
        click.echo(result['content'])

        if result.get('post_id'):
            click.echo("\n" + "="*50)
            click.echo(click.style(
                f"✓ Published to WordPress! Post ID: {result['post_id']}",
                fg='green',
                bold=True
            ))
        else:
            click.echo("\n" + click.style(
                "Content generated (not published). Use --auto-publish to publish.",
                fg='yellow'
            ))

    except Exception as e:
        click.echo(click.style(f"Error: {str(e)}", fg='red'))
        if verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort() from e


# Add all AI subcommand groups to the main AI command
ai.add_command(summarize)
ai.add_command(optimize)
ai.add_command(translate)
ai.add_command(schedule)
ai.add_command(moderate)
ai.add_command(curate)
ai.add_command(research)
ai.add_command(image)
ai.add_command(chatbot)
ai.add_command(analyze)
ai.add_command(seo)
ai.add_command(workflow)
ai.add_command(bulk)
