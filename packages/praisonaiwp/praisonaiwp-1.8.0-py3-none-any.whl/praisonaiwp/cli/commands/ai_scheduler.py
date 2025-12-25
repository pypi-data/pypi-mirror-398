"""AI Content Scheduler - Intelligent content scheduling and analytics"""

import click
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from praisonaiwp.ai import AI_AVAILABLE
from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.ai_formatter import AIFormatter


@click.group()
def schedule():
    """AI-powered content scheduling and analytics"""
    pass


@schedule.command()
@click.option('--days', type=int, default=30, help='Number of days to analyze')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def analyze(days, server, json_output, verbose):
    """Analyze posting patterns and optimal scheduling times"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command="schedule analyze",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command="schedule analyze",
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
        
        # Analyze posting patterns
        if verbose:
            click.echo(f"Analyzing posting patterns for the last {days} days...")
        
        analysis = integration.analyze_posting_patterns(days)
        
        # Format output
        success_msg = AIFormatter.success_response(
            analysis,
            f"Posting pattern analysis complete for {days} days",
            command="schedule analyze"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n📊 Posting Pattern Analysis ({days} days)")
            click.echo("=" * 50)
            
            # Best posting times
            best_times = analysis.get('best_posting_times', [])
            if best_times:
                click.echo(f"\n⏰ Best Posting Times:")
                for i, time_slot in enumerate(best_times[:5], 1):
                    click.echo(f"  {i}. {time_slot['time']} (engagement: {time_slot['engagement_score']:.1f})")
            
            # Day of week analysis
            dow_analysis = analysis.get('day_of_week_analysis', {})
            if dow_analysis:
                click.echo(f"\n📅 Best Days of Week:")
                sorted_days = sorted(dow_analysis.items(), key=lambda x: x[1]['avg_engagement'], reverse=True)
                for day, data in sorted_days[:3]:
                    click.echo(f"  {day}: {data['posts']} posts, avg engagement: {data['avg_engagement']:.1f}")
            
            # Recommendations
            recommendations = analysis.get('recommendations', [])
            if recommendations:
                click.echo(f"\n💡 Scheduling Recommendations:")
                for i, rec in enumerate(recommendations, 1):
                    click.echo(f"  {i}. {rec}")
            
            # Statistics
            stats = analysis.get('statistics', {})
            click.echo(f"\n📈 Statistics:")
            click.echo(f"  Total posts analyzed: {stats.get('total_posts', 0)}")
            click.echo(f"  Average posts per day: {stats.get('avg_posts_per_day', 0):.1f}")
            click.echo(f"  Peak engagement hour: {stats.get('peak_hour', 'N/A')}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command="schedule analyze",
            error_code="ANALYSIS_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@schedule.command()
@click.option('--queue', is_flag=True, help='Optimize existing scheduled queue')
@click.option('--auto-schedule', is_flag=True, help='Auto-schedule draft posts')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def optimize(queue, auto_schedule, server, json_output, verbose):
    """Optimize content scheduling based on analytics"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command="schedule optimize",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command="schedule optimize",
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
        
        results = {
            'optimization_type': [],
            'optimized_items': []
        }
        
        # Optimize existing queue
        if queue:
            if verbose:
                click.echo("Optimizing existing scheduled posts...")
            
            queue_optimization = integration.optimize_scheduled_queue()
            results['optimization_type'].append('queue')
            results['queue_optimization'] = queue_optimization
            results['optimized_items'].extend(queue_optimization.get('optimized_posts', []))
        
        # Auto-schedule draft posts
        if auto_schedule:
            if verbose:
                click.echo("Auto-scheduling draft posts...")
            
            draft_scheduling = integration.auto_schedule_drafts()
            results['optimization_type'].append('auto_schedule')
            results['draft_scheduling'] = draft_scheduling
            results['optimized_items'].extend(draft_scheduling.get('scheduled_posts', []))
        
        # Format output
        success_msg = AIFormatter.success_response(
            results,
            f"Scheduling optimization complete: {', '.join(results['optimization_type'])}",
            command="schedule optimize"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n✅ Scheduling Optimization Complete")
            click.echo("=" * 50)
            click.echo(f"Optimization types: {', '.join(results['optimization_type'])}")
            
            if queue and 'queue_optimization' in results:
                queue_opt = results['queue_optimization']
                click.echo(f"\n📋 Queue Optimization:")
                click.echo(f"  Posts analyzed: {queue_opt.get('analyzed_posts', 0)}")
                click.echo(f"  Posts rescheduled: {queue_opt.get('rescheduled_posts', 0)}")
                click.echo(f"  Expected engagement boost: {queue_opt.get('engagement_boost', 0):.1f}%")
            
            if auto_schedule and 'draft_scheduling' in results:
                draft_opt = results['draft_scheduling']
                click.echo(f"\n📝 Draft Scheduling:")
                click.echo(f"  Drafts found: {draft_opt.get('drafts_found', 0)}")
                click.echo(f"  Posts scheduled: {draft_opt.get('scheduled_posts', 0)}")
                click.echo(f"  Average scheduling interval: {draft_opt.get('avg_interval_days', 0):.1f} days")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command="schedule optimize",
            error_code="OPTIMIZATION_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@schedule.command()
@click.argument('topic')
@click.option('--count', type=int, default=5, help='Number of content suggestions')
@click.option('--timeframe', default='week', help='Timeframe for suggestions (day, week, month)')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def suggest(topic, count, timeframe, server, json_output, verbose):
    """Suggest optimal content topics and timing"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"schedule suggest {topic}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"schedule suggest {topic}",
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
        
        # Generate content suggestions
        if verbose:
            click.echo(f"Generating {count} content suggestions for '{topic}'...")
        
        suggestions = integration.suggest_content_topics(
            topic=topic,
            count=count,
            timeframe=timeframe
        )
        
        # Format output
        success_msg = AIFormatter.success_response(
            suggestions,
            f"Generated {len(suggestions.get('suggestions', []))} content suggestions for '{topic}'",
            command=f"schedule suggest {topic}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n💡 Content Suggestions for '{topic}'")
            click.echo("=" * 50)
            click.echo(f"Timeframe: {timeframe}")
            click.echo(f"Number of suggestions: {len(suggestions.get('suggestions', []))}")
            
            for i, suggestion in enumerate(suggestions.get('suggestions', []), 1):
                click.echo(f"\n{i}. {suggestion.get('title', 'Untitled')}")
                click.echo(f"   Best time: {suggestion.get('optimal_time', 'N/A')}")
                click.echo(f"   Engagement potential: {suggestion.get('engagement_potential', 'N/A')}")
                click.echo(f"   Content type: {suggestion.get('content_type', 'N/A')}")
                if suggestion.get('description'):
                    click.echo(f"   Description: {suggestion['description']}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"schedule suggest {topic}",
            error_code="SUGGESTION_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@schedule.command()
@click.option('--category', help='Analyze content gaps in specific category')
@click.option('--timeframe', default='month', help='Analysis timeframe (week, month, quarter)')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def gaps(category, timeframe, server, json_output, verbose):
    """Analyze content gaps and suggest missing topics"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command="schedule gaps",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command="schedule gaps",
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
        
        # Analyze content gaps
        if verbose:
            category_str = f" in category '{category}'" if category else ""
            click.echo(f"Analyzing content gaps{category_str} for {timeframe}...")
        
        gap_analysis = integration.analyze_content_gaps(category=category, timeframe=timeframe)
        
        # Format output
        success_msg = AIFormatter.success_response(
            gap_analysis,
            f"Content gap analysis complete for {timeframe}",
            command="schedule gaps"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n🔍 Content Gap Analysis ({timeframe})")
            click.echo("=" * 50)
            if category:
                click.echo(f"Category: {category}")
            
            # Missing topics
            missing_topics = gap_analysis.get('missing_topics', [])
            if missing_topics:
                click.echo(f"\n📝 Missing Topics ({len(missing_topics)}):")
                for i, topic in enumerate(missing_topics[:10], 1):
                    priority = topic.get('priority', 'medium')
                    click.echo(f"  {i}. {topic.get('title', 'Untitled')} [{priority}]")
                    if topic.get('reason'):
                        click.echo(f"     Reason: {topic['reason']}")
            
            # Overcovered topics
            overcovered = gap_analysis.get('overcovered_topics', [])
            if overcovered:
                click.echo(f"\n📊 Overcovered Topics ({len(overcovered)}):")
                for i, topic in enumerate(overcovered[:5], 1):
                    click.echo(f"  {i}. {topic.get('title', 'Untitled')} ({topic.get('count', 0)} posts)")
            
            # Recommendations
            recommendations = gap_analysis.get('recommendations', [])
            if recommendations:
                click.echo(f"\n💡 Recommendations ({len(recommendations)}):")
                for i, rec in enumerate(recommendations, 1):
                    click.echo(f"  {i}. {rec}")
            
            # Statistics
            stats = gap_analysis.get('statistics', {})
            click.echo(f"\n📈 Statistics:")
            click.echo(f"  Total posts analyzed: {stats.get('total_posts', 0)}")
            click.echo(f"  Unique topics found: {stats.get('unique_topics', 0)}")
            click.echo(f"  Content diversity score: {stats.get('diversity_score', 0):.2f}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command="schedule gaps",
            error_code="GAP_ANALYSIS_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@schedule.command()
@click.option('--days', type=int, default=7, help='Number of days to create schedule for')
@click.option('--posts-per-day', type=int, default=1, help='Target posts per day')
@click.option('--category', help='Filter by category')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def create(days, posts_per_day, category, server, json_output, verbose):
    """Create an optimized content schedule"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command="schedule create",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command="schedule create",
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
        
        # Create optimized schedule
        if verbose:
            category_str = f" for category '{category}'" if category else ""
            click.echo(f"Creating {days}-day schedule{category_str} ({posts_per_day} posts/day)...")
        
        schedule = integration.create_optimized_schedule(
            days=days,
            posts_per_day=posts_per_day,
            category=category
        )
        
        # Format output
        success_msg = AIFormatter.success_response(
            schedule,
            f"Created {days}-day optimized schedule",
            command="schedule create"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n📅 Optimized Content Schedule ({days} days)")
            click.echo("=" * 50)
            click.echo(f"Posts per day: {posts_per_day}")
            if category:
                click.echo(f"Category: {category}")
            
            schedule_items = schedule.get('schedule', [])
            total_posts = len(schedule_items)
            click.echo(f"\n📋 Schedule Overview ({total_posts} posts total):")
            
            # Group by date
            from collections import defaultdict
            by_date = defaultdict(list)
            for item in schedule_items:
                by_date[item['date']].append(item)
            
            for date, items in sorted(by_date.items()):
                click.echo(f"\n📅 {date}:")
                for i, item in enumerate(items, 1):
                    time = item.get('time', '09:00')
                    topic = item.get('topic', 'Untitled')
                    engagement = item.get('predicted_engagement', 'N/A')
                    click.echo(f"  {i}. {time} - {topic} (engagement: {engagement})")
            
            # Summary
            summary = schedule.get('summary', {})
            click.echo(f"\n📊 Schedule Summary:")
            click.echo(f"  Total posts: {summary.get('total_posts', 0)}")
            click.echo(f"  Average engagement prediction: {summary.get('avg_engagement', 0):.1f}")
            click.echo(f"  Best posting day: {summary.get('best_day', 'N/A')}")
            click.echo(f"  Peak time slot: {summary.get('peak_time', 'N/A')}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command="schedule create",
            error_code="SCHEDULE_CREATION_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
