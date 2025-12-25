"""AI-powered bulk operations for content management commands"""
import click

from praisonaiwp.ai import AI_AVAILABLE
from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.ai_formatter import AIFormatter

@click.group()
def bulk():
    pass


@bulk.command()
@click.option('--posts', help='Post IDs or range (e.g., "1,2,3" or "1-10")')
@click.option('--category', help='Process all posts in category')
@click.option('--status', default='publish', help='Post status filter')
@click.option('--limit', type=int, default=10, help='Maximum number of posts to process')
@click.option('--operation', required=True, help='Operation to perform (optimize, translate, summarize)')
@click.option('--params', help='Operation parameters (JSON format)')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def process(posts, category, status, limit, operation, params, server, json_output, verbose):
    """Perform bulk AI operations on multiple posts"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command="bulk process",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command="bulk process",
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
        
        # Get posts to process
        posts_to_process = []
        
        if posts:
            # Parse post IDs or range
            if '-' in posts:
                # Range like "1-10"
                start, end = map(int, posts.split('-'))
                posts_to_process = list(range(start, end + 1))
            else:
                # Comma-separated list
                posts_to_process = [int(p.strip()) for p in posts.split(',')]
        
        elif category:
            # Get posts by category
            if verbose:
                click.echo(f"Finding posts in category: {category}")
            
            category_posts = wp_client.get_posts(category=category, status=status, limit=limit)
            posts_to_process = [post['id'] for post in category_posts]
        
        else:
            # Get recent posts
            if verbose:
                click.echo(f"Finding recent posts (limit: {limit})")
            
            recent_posts = wp_client.get_posts(status=status, limit=limit)
            posts_to_process = [post['id'] for post in recent_posts]
        
        if not posts_to_process:
            error_msg = AIFormatter.error_response(
                "No posts found to process",
                command="bulk process",
                error_code="NO_POSTS_FOUND"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Parse parameters
        operation_params = {}
        if params:
            import json
            try:
                operation_params = json.loads(params)
            except json.JSONDecodeError:
                error_msg = AIFormatter.error_response(
                    "Invalid JSON format for parameters",
                    command="bulk process",
                    error_code="INVALID_PARAMS"
                )
                click.echo(AIFormatter.format_output(error_msg, json_output))
                return
        
        # Process posts
        if verbose:
            click.echo(f"Performing bulk {operation} on {len(posts_to_process)} posts...")
        
        results = {
            'operation': operation,
            'total_posts': len(posts_to_process),
            'processed_posts': [],
            'summary': {
                'successful': 0,
                'failed': 0,
                'skipped': 0
            }
        }
        
        for i, post_id in enumerate(posts_to_process, 1):
            if verbose:
                click.echo(f"[{i}/{len(posts_to_process)}] Processing post {post_id}...")
            
            try:
                # Get post content
                post = wp_client.get_post(post_id)
                if not post:
                    if verbose:
                        click.echo(f"  Post {post_id} not found, skipping...")
                    results['summary']['skipped'] += 1
                    continue
                
                # Perform operation
                if operation == 'optimize':
                    result = integration.optimize_content_bulk(post_id, **operation_params)
                elif operation == 'translate':
                    result = integration.translate_content_bulk(post_id, **operation_params)
                elif operation == 'summarize':
                    result = integration.summarize_content_bulk(post_id, **operation_params)
                else:
                    result = {'error': f'Unknown operation: {operation}'}
                
                if 'error' in result:
                    results['summary']['failed'] += 1
                    if verbose:
                        click.echo(f"  ❌ Failed: {result['error']}")
                else:
                    results['summary']['successful'] += 1
                    if verbose:
                        click.echo(f"  ✅ Success")
                
                results['processed_posts'].append({
                    'post_id': post_id,
                    'title': post['title'],
                    'result': result
                })
                
            except Exception as e:
                if verbose:
                    click.echo(f"  ❌ Failed: {str(e)}")
                results['summary']['failed'] += 1
                results['processed_posts'].append({
                    'post_id': post_id,
                    'error': str(e)
                })
        
        # Format output
        success_msg = AIFormatter.success_response(
            results,
            f"Bulk {operation} complete: {results['summary']['successful']}/{results['total_posts']} posts successful",
            command="bulk process"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n✅ Bulk {operation} Complete")
            click.echo("=" * 50)
            click.echo(f"Total posts processed: {results['total_posts']}")
            click.echo(f"Successful: {results['summary']['successful']}")
            click.echo(f"Failed: {results['summary']['failed']}")
            click.echo(f"Skipped: {results['summary']['skipped']}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command="bulk process",
            error_code="BULK_PROCESS_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@bulk.command()
@click.option('--category', help='Analyze posts in specific category')
@click.option('--status', default='publish', help='Post status filter')
@click.option('--limit', type=int, default=50, help='Maximum number of posts to analyze')
@click.option('--analysis-type', default='seo', help='Type of analysis (seo, performance, quality)')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def analyze(category, status, limit, analysis_type, server, json_output, verbose):
    """Analyze multiple posts for insights and recommendations"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command="bulk analyze",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command="bulk analyze",
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
        
        # Get posts to analyze
        if verbose:
            category_str = f" in category '{category}'" if category else ""
            click.echo(f"Finding posts{category_str} for {analysis_type} analysis...")
        
        posts = wp_client.get_posts(category=category, status=status, limit=limit)
        
        if not posts:
            success_msg = AIFormatter.success_response(
                {'message': 'No posts found to analyze'},
                "No posts found for analysis",
                command="bulk analyze"
            )
            click.echo(AIFormatter.format_output(success_msg, json_output))
            return
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Analyze posts
        if verbose:
            click.echo(f"Analyzing {len(posts)} posts for {analysis_type} insights...")
        
        analysis_result = integration.bulk_analyze_posts(
            posts,
            analysis_type=analysis_type
        )
        
        # Format output
        success_msg = AIFormatter.success_response(
            analysis_result,
            f"Bulk {analysis_type} analysis complete for {len(posts)} posts",
            command="bulk analyze"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n📊 Bulk {analysis_type.title()} Analysis Complete")
            click.echo("=" * 50)
            click.echo(f"Total posts analyzed: {len(posts)}")
            
            # Overall statistics
            stats = analysis_result.get('overall_statistics', {})
            if stats:
                click.echo(f"\n📈 Overall Statistics:")
                for key, value in stats.items():
                    if isinstance(value, (int, float)):
                        click.echo(f"  {key.replace('_', ' ').title()}: {value:,}")
                    else:
                        click.echo(f"  {key.replace('_', ' ').title()}: {value}")
            
            # Top performers
            top_performers = analysis_result.get('top_performers', [])
            if top_performers:
                click.echo(f"\n🏆 Top Performers:")
                for i, post in enumerate(top_performers[:5], 1):
                    score = post.get('score', 0)
                    click.echo(f"  {i}. {post.get('title', 'Unknown')} (Score: {score:.1f})")
            
            # Issues found
            issues = analysis_result.get('common_issues', [])
            if issues:
                click.echo(f"\n⚠️  Common Issues:")
                for i, issue in enumerate(issues[:5], 1):
                    click.echo(f"  {i}. {issue.get('issue', 'Unknown')} ({issue.get('count', 0)} posts)")
            
            # Recommendations
            recommendations = analysis_result.get('recommendations', [])
            if recommendations:
                click.echo(f"\n💡 Recommendations:")
                for i, rec in enumerate(recommendations, 1):
                    click.echo(f"  {i}. {rec}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command="bulk analyze",
            error_code="BULK_ANALYSIS_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@bulk.command()
@click.option('--category', help='Generate content for specific category')
@click.option('--count', type=int, default=5, help='Number of posts to generate')
@click.option('--template', help='Content template to use')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def generate(category, count, template, server, json_output, verbose):
    """Generate multiple posts using AI"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command="bulk generate",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command="bulk generate",
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
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Generate posts
        if verbose:
            category_str = f" in category '{category}'" if category else ""
            template_str = f" using template '{template}'" if template else ""
            click.echo(f"Generating {count} posts{category_str}{template_str}...")
        
        generation_result = integration.bulk_generate_posts(
            count=count,
            category=category,
            template=template
        )
        
        # Format output
        success_msg = AIFormatter.success_response(
            generation_result,
            f"Generated {len(generation_result.get('posts', []))} posts",
            command="bulk generate"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n✅ Bulk Post Generation Complete")
            click.echo("=" * 50)
            
            posts = generation_result.get('posts', [])
            click.echo(f"Posts generated: {len(posts)}")
            
            for i, post in enumerate(posts, 1):
                click.echo(f"\n{i}. {post.get('title', 'Untitled')}")
                click.echo(f"   ID: {post.get('id', 'N/A')}")
                click.echo(f"   Category: {post.get('category', 'N/A')}")
                click.echo(f"   Status: {post.get('status', 'N/A')}")
                if post.get('url'):
                    click.echo(f"   URL: {post['url']}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command="bulk generate",
            error_code="BULK_GENERATION_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@bulk.command()
@click.option('--days', type=int, default=30, help='Number of days to analyze')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def cleanup(days, server, json_output, verbose):
    """Clean up and optimize content using AI"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command="bulk cleanup",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command="bulk cleanup",
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
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Perform cleanup
        if verbose:
            click.echo(f"Performing AI cleanup for the last {days} days...")
        
        cleanup_result = integration.bulk_content_cleanup(days)
        
        # Format output
        success_msg = AIFormatter.success_response(
            cleanup_result,
            f"Content cleanup complete for {days} days",
            command="bulk cleanup"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n🧹 Bulk Content Cleanup Complete")
            click.echo("=" * 50)
            
            # Cleanup summary
            summary = cleanup_result.get('summary', {})
            if summary:
                click.echo(f"\n📊 Cleanup Summary:")
                click.echo(f"  Posts analyzed: {summary.get('posts_analyzed', 0)}")
                click.echo(f"  Posts optimized: {summary.get('posts_optimized', 0)}")
                click.echo(f"  Duplicate content removed: {summary.get('duplicates_removed', 0)}")
                click.echo(f"  Broken links fixed: {summary.get('broken_links_fixed', 0)}")
                click.echo(f"  Images optimized: {summary.get('images_optimized', 0)}")
            
            # Issues found
            issues = cleanup_result.get('issues_found', [])
            if issues:
                click.echo(f"\n⚠️  Issues Found and Fixed:")
                for i, issue in enumerate(issues[:5], 1):
                    click.echo(f"  {i}. {issue.get('type', 'Unknown')}: {issue.get('count', 0)} items")
            
            # Recommendations
            recommendations = cleanup_result.get('recommendations', [])
            if recommendations:
                click.echo(f"\n💡 Maintenance Recommendations:")
                for i, rec in enumerate(recommendations, 1):
                    click.echo(f"  {i}. {rec}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command="bulk cleanup",
            error_code="BULK_CLEANUP_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@bulk.command()
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def status(server, json_output, verbose):
    """Get status of bulk operations"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command="bulk status",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command="bulk status",
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
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Get bulk operations status
        if verbose:
            click.echo("Getting bulk operations status...")
        
        status_result = integration.get_bulk_operations_status()
        
        # Format output
        success_msg = AIFormatter.success_response(
            status_result,
            "Bulk operations status retrieved",
            command="bulk status"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n📊 Bulk Operations Status")
            click.echo("=" * 40)
            
            # Active operations
            active = status_result.get('active_operations', [])
            if active:
                click.echo(f"\n🔄 Active Operations:")
                for op in active:
                    progress = op.get('progress', 0)
                    click.echo(f"  • {op.get('type', 'Unknown')}: {progress}% complete")
                    click.echo(f"    Started: {op.get('started_at', 'N/A')}")
            
            # Recent operations
            recent = status_result.get('recent_operations', [])
            if recent:
                click.echo(f"\n📋 Recent Operations:")
                for op in recent[:5]:
                    status_icon = "✅" if op.get('status') == 'completed' else "❌"
                    click.echo(f"  {status_icon} {op.get('type', 'Unknown')} - {op.get('status', 'Unknown')}")
                    click.echo(f"    Posts: {op.get('posts_processed', 0)}/{op.get('total_posts', 0)}")
            
            # Statistics
            stats = status_result.get('statistics', {})
            if stats:
                click.echo(f"\n📈 Statistics:")
                click.echo(f"  Total operations: {stats.get('total_operations', 0)}")
                click.echo(f"  Successful: {stats.get('successful', 0)}")
                click.echo(f"  Failed: {stats.get('failed', 0)}")
                click.echo(f"  Posts processed: {stats.get('posts_processed', 0):,}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command="bulk status",
            error_code="BULK_STATUS_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
