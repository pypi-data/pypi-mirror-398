"""AI Chatbot Integration - Add AI-powered chatbot to WordPress site"""

import click
from typing import Dict, Any, List, Optional

from praisonaiwp.ai import AI_AVAILABLE
from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.ai_formatter import AIFormatter


@click.group()
def chatbot():
    """AI-powered chatbot integration for WordPress"""
    pass


@chatbot.command()
@click.option('--content', default='all', help='Content to train on (all, posts, pages, categories)')
@click.option('--model', default='gpt-3.5-turbo', help='AI model to use (gpt-3.5-turbo, gpt-4)')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def train(content, model, server, json_output, verbose):
    """Train AI chatbot on site content"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command="chatbot train",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command="chatbot train",
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
        
        # Train chatbot
        if verbose:
            click.echo(f"Training chatbot on {content} content using {model}")
        
        training_result = integration.train_chatbot(
            content_type=content,
            model=model
        )
        
        # Format output
        success_msg = AIFormatter.success_response(
            training_result,
            f"Chatbot training complete using {training_result.get('documents_processed', 0)} documents",
            command="chatbot train"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n🤖 Chatbot Training Complete")
            click.echo("=" * 50)
            click.echo(f"Model: {model}")
            click.echo(f"Content type: {content}")
            
            training = training_result
            click.echo(f"\n📊 Training Statistics:")
            click.echo(f"  Documents processed: {training.get('documents_processed', 0)}")
            click.echo(f"  Tokens used: {training.get('tokens_used', 0):,}")
            click.echo(f"  Training time: {training.get('training_time', 0):.1f}s")
            click.echo(f"  Model ID: {training.get('model_id', 'N/A')}")
            
            # Sample questions
            sample_questions = training.get('sample_questions', [])
            if sample_questions:
                click.echo(f"\n💬 Sample Questions Chatbot Can Answer:")
                for i, question in enumerate(sample_questions[:5], 1):
                    click.echo(f"  {i}. {question}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command="chatbot train",
            error_code="TRAINING_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@chatbot.command()
@click.option('--widget-style', default='modern', help='Widget style (modern, classic, minimal)')
@click.option('--position', default='bottom-right', help='Widget position (bottom-right, bottom-left, top-right)')
@click.option('--color', default='#0073aa', help='Widget color (hex code)')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def deploy(widget_style, position, color, server, json_output, verbose):
    """Deploy chatbot widget to WordPress site"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command="chatbot deploy",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command="chatbot deploy",
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
        
        # Deploy chatbot
        if verbose:
            click.echo(f"Deploying chatbot widget ({widget_style}, {position})")
        
        deployment_result = integration.deploy_chatbot_widget(
            widget_style=widget_style,
            position=position,
            color=color
        )
        
        # Format output
        success_msg = AIFormatter.success_response(
            deployment_result,
            f"Chatbot widget deployed successfully",
            command="chatbot deploy"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n🚀 Chatbot Widget Deployed")
            click.echo("=" * 50)
            click.echo(f"Widget style: {widget_style}")
            click.echo(f"Position: {position}")
            click.echo(f"Color: {color}")
            
            deployment = deployment_result
            click.echo(f"\n📋 Deployment Details:")
            click.echo(f"  Widget ID: {deployment.get('widget_id', 'N/A')}")
            click.echo(f"  Embed code: {deployment.get('embed_code', 'N/A')}")
            click.echo(f"  Admin URL: {deployment.get('admin_url', 'N/A')}")
            
            # Instructions
            instructions = deployment.get('instructions', [])
            if instructions:
                click.echo(f"\n📝 Next Steps:")
                for i, instruction in enumerate(instructions, 1):
                    click.echo(f"  {i}. {instruction}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command="chatbot deploy",
            error_code="DEPLOYMENT_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@chatbot.command()
@click.option('--category', help='Generate FAQ for specific category')
@click.option('--count', type=int, default=10, help='Number of FAQ items to generate')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def faq(category, count, server, json_output, verbose):
    """Generate FAQ content using AI"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command="chatbot faq",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command="chatbot faq",
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
        
        # Generate FAQ
        if verbose:
            category_str = f" for category '{category}'" if category else ""
            click.echo(f"Generating {count} FAQ items{category_str}")
        
        faq_result = integration.generate_faq(
            category=category,
            count=count
        )
        
        # Format output
        success_msg = AIFormatter.success_response(
            faq_result,
            f"Generated {len(faq_result.get('faq_items', []))} FAQ items",
            command="chatbot faq"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n❓ Generated FAQ Content")
            click.echo("=" * 50)
            if category:
                click.echo(f"Category: {category}")
            
            faq_items = faq_result.get('faq_items', [])
            for i, item in enumerate(faq_items, 1):
                click.echo(f"\n{i}. Q: {item.get('question', 'Untitled')}")
                click.echo(f"   A: {item.get('answer', 'No answer')}")
                if item.get('category'):
                    click.echo(f"   Category: {item['category']}")
                if item.get('confidence'):
                    click.echo(f"   Confidence: {item['confidence']:.2f}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command="chatbot faq",
            error_code="FAQ_GENERATION_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@chatbot.command()
@click.option('--days', type=int, default=30, help='Number of days to analyze')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def analytics(days, server, json_output, verbose):
    """Get chatbot analytics and insights"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command="chatbot analytics",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command="chatbot analytics",
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
        
        # Get analytics
        if verbose:
            click.echo(f"Analyzing chatbot data for the last {days} days")
        
        analytics_result = integration.get_chatbot_analytics(days)
        
        # Format output
        success_msg = AIFormatter.success_response(
            analytics_result,
            f"Chatbot analytics complete for {days} days",
            command="chatbot analytics"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n📊 Chatbot Analytics ({days} days)")
            click.echo("=" * 50)
            
            # Usage statistics
            usage = analytics_result.get('usage_statistics', {})
            click.echo(f"\n💬 Usage Statistics:")
            click.echo(f"  Total conversations: {usage.get('total_conversations', 0)}")
            click.echo(f"  Total messages: {usage.get('total_messages', 0)}")
            click.echo(f"  Average messages per conversation: {usage.get('avg_messages_per_conversation', 0):.1f}")
            click.echo(f"  Unique users: {usage.get('unique_users', 0)}")
            
            # Popular questions
            popular_questions = analytics_result.get('popular_questions', [])
            if popular_questions:
                click.echo(f"\n🔥 Popular Questions:")
                for i, question in enumerate(popular_questions[:5], 1):
                    click.echo(f"  {i}. {question.get('question', 'Unknown')} ({question.get('count', 0)} times)")
            
            # Satisfaction metrics
            satisfaction = analytics_result.get('satisfaction_metrics', {})
            if satisfaction:
                click.echo(f"\n😊 Satisfaction Metrics:")
                click.echo(f"  Average rating: {satisfaction.get('avg_rating', 0):.1f}/5")
                click.echo(f"  Positive responses: {satisfaction.get('positive_responses', 0)}%")
                click.echo(f"  Resolution rate: {satisfaction.get('resolution_rate', 0)}%")
            
            # Insights
            insights = analytics_result.get('insights', [])
            if insights:
                click.echo(f"\n💡 Key Insights:")
                for i, insight in enumerate(insights, 1):
                    click.echo(f"  {i}. {insight}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command="chatbot analytics",
            error_code="ANALYTICS_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@chatbot.command()
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def status(server, json_output, verbose):
    """Check chatbot deployment status"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command="chatbot status",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command="chatbot status",
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
        
        # Check status
        if verbose:
            click.echo("Checking chatbot deployment status...")
        
        status_result = integration.get_chatbot_status()
        
        # Format output
        success_msg = AIFormatter.success_response(
            status_result,
            f"Chatbot status: {status_result.get('status', 'Unknown')}",
            command="chatbot status"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n🤖 Chatbot Status")
            click.echo("=" * 30)
            
            status = status_result.get('status', 'unknown')
            status_icon = {
                'active': '🟢',
                'inactive': '🔴',
                'training': '🟡',
                'error': '❌'
            }.get(status, '❓')
            
            click.echo(f"Status: {status_icon} {status.title()}")
            
            if status_result.get('model'):
                click.echo(f"Model: {status_result['model']}")
            
            if status_result.get('last_updated'):
                click.echo(f"Last updated: {status_result['last_updated']}")
            
            if status_result.get('version'):
                click.echo(f"Version: {status_result['version']}")
            
            # Configuration
            config_info = status_result.get('configuration', {})
            if config_info:
                click.echo(f"\n⚙️  Configuration:")
                click.echo(f"  Widget style: {config_info.get('widget_style', 'N/A')}")
                click.echo(f"  Position: {config_info.get('position', 'N/A')}")
                click.echo(f"  Color: {config_info.get('color', 'N/A')}")
            
            # Health checks
            health = status_result.get('health_checks', {})
            if health:
                click.echo(f"\n🏥 Health Checks:")
                for check, result in health.items():
                    icon = '✅' if result.get('status') == 'ok' else '❌'
                    click.echo(f"  {icon} {check.title()}: {result.get('message', 'Unknown')}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command="chatbot status",
            error_code="STATUS_CHECK_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
