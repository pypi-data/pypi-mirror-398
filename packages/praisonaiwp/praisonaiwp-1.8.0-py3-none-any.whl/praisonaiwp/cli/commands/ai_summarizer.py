"""AI Content Summarizer - Generate summaries, excerpts, and social media posts"""

import click
from typing import Dict, Any, List, Optional

from praisonaiwp.ai import AI_AVAILABLE
from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.ai_formatter import AIFormatter


@click.group()
def summarize():
    """AI-powered content summarization and social media generation"""
    pass


@summarize.command()
@click.argument('post_id', type=int)
@click.option('--excerpt', is_flag=True, help='Generate post excerpt')
@click.option('--social', help='Generate social media posts (comma-separated: twitter,linkedin,facebook)')
@click.option('--tldr', help='Generate TL;DR summary with target word count')
@click.option('--length', type=int, default=150, help='Target length for summaries')
@click.option('--hashtags', is_flag=True, help='Include hashtags in social media posts')
@click.option('--tone', default='professional', help='Content tone (professional, casual, technical)')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def post(post_id, excerpt, social, tldr, length, hashtags, tone, server, json_output, verbose):
    """Generate summaries and social media content for a post"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"summarize post {post_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"summarize post {post_id}",
            error_code="CONFIG_NOT_FOUND"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
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
            verify_installation=False
        )
        
        # Get post content
        post = wp_client.get_post(post_id)
        if not post:
            error_msg = AIFormatter.error_response(
                f"Post with ID {post_id} not found",
                command=f"summarize post {post_id}",
                error_code="NOT_FOUND"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        results = {}
        
        # Generate excerpt
        if excerpt:
            if verbose:
                click.echo("Generating excerpt...")
            excerpt_result = integration.generate_excerpt(
                post['content'], 
                target_length=length,
                tone=tone
            )
            results['excerpt'] = excerpt_result
        
        # Generate social media posts
        if social:
            platforms = [p.strip().lower() for p in social.split(',')]
            if verbose:
                click.echo(f"Generating social media posts for: {', '.join(platforms)}")
            
            social_posts = integration.generate_social_posts(
                post['title'],
                post['content'],
                platforms=platforms,
                include_hashtags=hashtags,
                tone=tone
            )
            results['social_media'] = social_posts
        
        # Generate TL;DR
        if tldr:
            if verbose:
                click.echo(f"Generating TL;DR summary (target: {tldr} words)...")
            tldr_result = integration.generate_summary(
                post['content'],
                target_length=int(tldr),
                style="tldr"
            )
            results['tldr'] = tldr_result
        
        # Generate default summary if no specific options
        if not excerpt and not social and not tldr:
            if verbose:
                click.echo("Generating default summary...")
            summary = integration.generate_summary(
                post['content'],
                target_length=length,
                style="summary"
            )
            results['summary'] = summary
        
        # Format output
        success_msg = AIFormatter.success_response(
            results,
            f"Generated summaries for post {post_id}",
            command=f"summarize post {post_id}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n✅ Summaries generated for post {post_id}:")
            click.echo("=" * 50)
            
            for key, value in results.items():
                click.echo(f"\n📝 {key.upper()}:")
                click.echo("-" * 20)
                if isinstance(value, dict):
                    for platform, content in value.items():
                        click.echo(f"\n{platform.title()}:")
                        click.echo(content)
                else:
                    click.echo(value)
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"summarize post {post_id}",
            error_code="GENERATION_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@summarize.command()
@click.argument('post_id', type=int)
@click.option('--count', type=int, default=10, help='Number of keywords to extract')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def keywords(post_id, count, server, json_output, verbose):
    """Extract keywords from a post"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"summarize keywords {post_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"summarize keywords {post_id}",
            error_code="CONFIG_NOT_FOUND"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
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
            verify_installation=False
        )
        
        # Get post content
        post = wp_client.get_post(post_id)
        if not post:
            error_msg = AIFormatter.error_response(
                f"Post with ID {post_id} not found",
                command=f"summarize keywords {post_id}",
                error_code="NOT_FOUND"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Extract keywords
        if verbose:
            click.echo(f"Extracting {count} keywords...")
        
        keywords = integration.extract_keywords(post['content'], count=count)
        
        # Format output
        success_msg = AIFormatter.success_response(
            {'keywords': keywords},
            f"Extracted {len(keywords)} keywords from post {post_id}",
            command=f"summarize keywords {post_id}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n✅ Keywords extracted from post {post_id}:")
            click.echo("=" * 50)
            for i, keyword in enumerate(keywords, 1):
                click.echo(f"{i}. {keyword}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"summarize keywords {post_id}",
            error_code="GENERATION_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@summarize.command()
@click.argument('post_id', type=int)
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def meta(post_id, server, json_output, verbose):
    """Generate meta description and SEO meta tags"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"summarize meta {post_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"summarize meta {post_id}",
            error_code="CONFIG_NOT_FOUND"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
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
            verify_installation=False
        )
        
        # Get post content
        post = wp_client.get_post(post_id)
        if not post:
            error_msg = AIFormatter.error_response(
                f"Post with ID {post_id} not found",
                command=f"summarize meta {post_id}",
                error_code="NOT_FOUND"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Generate meta tags
        if verbose:
            click.echo("Generating meta description and SEO tags...")
        
        meta_data = integration.generate_meta_tags(post['title'], post['content'])
        
        # Format output
        success_msg = AIFormatter.success_response(
            meta_data,
            f"Generated meta tags for post {post_id}",
            command=f"summarize meta {post_id}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n✅ Meta tags generated for post {post_id}:")
            click.echo("=" * 50)
            click.echo(f"\n📝 Meta Description:")
            click.echo(meta_data['meta_description'])
            click.echo(f"\n🔍 SEO Title:")
            click.echo(meta_data['seo_title'])
            click.echo(f"\n🏷️  Keywords:")
            click.echo(meta_data['meta_keywords'])
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"summarize meta {post_id}",
            error_code="GENERATION_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
