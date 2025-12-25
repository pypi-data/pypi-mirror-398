"""AI-powered content performance analysis and insights commands"""
import click

from praisonaiwp.ai import AI_AVAILABLE
from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.ai_formatter import AIFormatter


@click.group()
def analyze():
    """AI-powered content performance analysis and insights"""
    pass


@analyze.command()
@click.argument('post_id', type=int)
@click.option('--metrics', help='Metrics to analyze (views,engagement,conversions,all)')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def performance(post_id, metrics, server, json_output, verbose):
    """Analyze performance of a specific post"""

    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"analyze performance {post_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return

    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"analyze performance {post_id}",
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
                command=f"analyze performance {post_id}",
                error_code="NOT_FOUND"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return

        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)

        # Analyze performance
        if verbose:
            click.echo(f"Analyzing performance for post {post_id}: {post['title']}")

        performance_result = integration.analyze_post_performance(
            post_id,
            metrics=metrics or 'all'
        )

        # Format output
        success_msg = AIFormatter.success_response(
            performance_result,
            f"Performance analysis complete for post {post_id}",
            command=f"analyze performance {post_id}"
        )

        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n📊 Performance Analysis for Post {post_id}")
            click.echo("=" * 50)
            click.echo(f"Post: {post['title']}")

            # Performance metrics
            metrics_data = performance_result.get('metrics', {})
            if metrics_data:
                click.echo("\n📈 Performance Metrics:")
                for metric, value in metrics_data.items():
                    if isinstance(value, (int, float)):
                        click.echo(f"  {metric.title()}: {value:,}")
                    else:
                        click.echo(f"  {metric.title()}: {value}")

            # Performance score
            score = performance_result.get('performance_score', {})
            if score:
                click.echo("\n⭐ Performance Score:")
                click.echo(f"  Overall: {score.get('overall', 0)}/100")
                click.echo(f"  Views: {score.get('views', 0)}/100")
                click.echo(f"  Engagement: {score.get('engagement', 0)}/100")
                click.echo(f"  SEO: {score.get('seo', 0)}/100")

            # Recommendations
            recommendations = performance_result.get('recommendations', [])
            if recommendations:
                click.echo("\n💡 Performance Recommendations:")
                for i, rec in enumerate(recommendations, 1):
                    click.echo(f"  {i}. {rec}")

    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"analyze performance {post_id}",
            error_code="PERFORMANCE_ANALYSIS_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@analyze.command()
@click.argument('post_id', type=int)
@click.option('--metrics', help='Metrics to predict (views,engagement,conversions)')
@click.option('--timeframe', default='30days', help='Prediction timeframe (7days,30days,90days)')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def predict(post_id, metrics, timeframe, server, json_output, verbose):
    """Predict future performance of a post"""

    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"analyze predict {post_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return

    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"analyze predict {post_id}",
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
                command=f"analyze predict {post_id}",
                error_code="NOT_FOUND"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return

        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)

        # Predict performance
        if verbose:
            click.echo(f"Predicting performance for post {post_id} over {timeframe}")

        prediction_result = integration.predict_post_performance(
            post_id,
            metrics=metrics or 'views,engagement',
            timeframe=timeframe
        )

        # Format output
        success_msg = AIFormatter.success_response(
            prediction_result,
            f"Performance prediction complete for post {post_id}",
            command=f"analyze predict {post_id}"
        )

        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n🔮 Performance Prediction for Post {post_id}")
            click.echo("=" * 50)
            click.echo(f"Post: {post['title']}")
            click.echo(f"Timeframe: {timeframe}")

            # Predictions
            predictions = prediction_result.get('predictions', {})
            if predictions:
                click.echo("
📊 Predicted Metrics:")
                for metric, prediction in predictions.items():
                    if isinstance(prediction, dict):
                        current = prediction.get('current', 0)
                        predicted = prediction.get('predicted', 0)
                        change = prediction.get('change_percent', 0)
                        change_str = f"+{change:.1f}%" if change > 0 else f"{change:.1f}%"
                        click.echo(f"  {metric.title()}: {current:,} → {predicted:,} ({change_str})")
                        click.echo(f"    Confidence: {prediction.get('confidence', 0):.1f}")
                    else:
                        click.echo(f"  {metric.title()}: {prediction}")

            # Factors
            factors = prediction_result.get('influencing_factors', [])
            if factors:
                click.echo("
🎯 Key Influencing Factors:")
                for i, factor in enumerate(factors[:5], 1):
                    click.echo(f"  {i}. {factor.get('factor', 'Unknown')} ({factor.get('impact', 'Unknown')})")

            # Recommendations
            recommendations = prediction_result.get('optimization_recommendations', [])
            if recommendations:
                click.echo("
💡 Optimization Recommendations:")
                for i, rec in enumerate(recommendations, 1):
                    click.echo(f"  {i}. {rec}")

    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"analyze predict {post_id}",
            error_code="PREDICTION_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@analyze.command()
@click.option('--category', help='Analyze trends in specific category')
@click.option('--timeframe', default='month', help='Analysis timeframe (week, month, quarter)')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def trends(category, timeframe, server, json_output, verbose):
    """Analyze content trends and patterns"""

    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command="analyze trends",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return

    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command="analyze trends",
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

        # Analyze trends
        if verbose:
            category_str = f" in category '{category}'" if category else ""
            click.echo(f"Analyzing content trends{category_str} for {timeframe}")

        trends_result = integration.analyze_content_trends(
            category=category,
            timeframe=timeframe
        )

        # Format output
        success_msg = AIFormatter.success_response(
            trends_result,
            f"Content trends analysis complete for {timeframe}",
            command="analyze trends"
        )

        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n📈 Content Trends Analysis ({timeframe})")
            click.echo("=" * 50)
            if category:
                click.echo(f"Category: {category}")

            # Trending topics
            trending_topics = trends_result.get('trending_topics', [])
            if trending_topics:
                click.echo("
🔥 Trending Topics:")
                for i, topic in enumerate(trending_topics[:5], 1):
                    click.echo(f"  {i}. {topic.get('topic', 'Unknown')} (+{topic.get('growth_rate', 0):.1f}%)")
                    click.echo(f"     Posts: {topic.get('post_count', 0)} | Engagement: {topic.get('avg_engagement', 0):.1f}")

            # Declining topics
            declining_topics = trends_result.get('declining_topics', [])
            if declining_topics:
                click.echo("
📉 Declining Topics:")
                for i, topic in enumerate(declining_topics[:3], 1):
                    click.echo(f"  {i}. {topic.get('topic', 'Unknown')} ({topic.get('growth_rate', 0):.1f}%)")

            # Performance patterns
            patterns = trends_result.get('performance_patterns', [])
            if patterns:
                click.echo("
🎯 Performance Patterns:")
                for i, pattern in enumerate(patterns, 1):
                    click.echo(f"  {i}. {pattern.get('pattern', 'Unknown')}")
                    click.echo(f"     Impact: {pattern.get('impact', 'Unknown')}")

            # Recommendations
            recommendations = trends_result.get('recommendations', [])
            if recommendations:
                click.echo("
💡 Trend-Based Recommendations:")
                for i, rec in enumerate(recommendations, 1):
                    click.echo(f"  {i}. {rec}")

    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command="analyze trends",
            error_code="TRENDS_ANALYSIS_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@analyze.command()
@click.argument('post_id', type=int)
@click.option('--goal', default='engagement', help='Optimization goal (engagement,views,conversions)')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def optimize(post_id, goal, server, json_output, verbose):
    """Get optimization suggestions for a post"""

    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"analyze optimize {post_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return

    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"analyze optimize {post_id}",
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
                command=f"analyze optimize {post_id}",
                error_code="NOT_FOUND"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return

        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)

        # Get optimization suggestions
        if verbose:
            click.echo(f"Analyzing optimization opportunities for post {post_id} (goal: {goal})")

        optimization_result = integration.get_optimization_suggestions(
            post_id,
            goal=goal
        )

        # Format output
        success_msg = AIFormatter.success_response(
            optimization_result,
            f"Optimization analysis complete for post {post_id}",
            command=f"analyze optimize {post_id}"
        )

        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n⚡ Optimization Analysis for Post {post_id}")
            click.echo("=" * 50)
            click.echo(f"Post: {post['title']}")
            click.echo(f"Goal: {goal}")

            # Current performance
            current = optimization_result.get('current_performance', {})
            if current:
                click.echo("
📊 Current Performance:")
                for metric, value in current.items():
                    click.echo(f"  {metric.title()}: {value}")

            # Optimization opportunities
            opportunities = optimization_result.get('optimization_opportunities', [])
            if opportunities:
                click.echo("
🎯 Optimization Opportunities:")
                for i, opportunity in enumerate(opportunities, 1):
                    impact = opportunity.get('impact', 'medium')
                    effort = opportunity.get('effort', 'medium')
                    click.echo(f"  {i}. {opportunity.get('title', 'Unknown')}")
                    click.echo(f"     Impact: {impact} | Effort: {effort}")
                    click.echo(f"     Expected improvement: {opportunity.get('expected_improvement', 'Unknown')}")
                    if opportunity.get('description'):
                        click.echo(f"     Description: {opportunity['description']}")

            # Quick wins
            quick_wins = optimization_result.get('quick_wins', [])
            if quick_wins:
                click.echo("
⚡ Quick Wins:")
                for i, win in enumerate(quick_wins, 1):
                    click.echo(f"  {i}. {win.get('action', 'Unknown')}")
                    click.echo(f"     Time to implement: {win.get('time_to_implement', 'Unknown')}")
                    click.echo(f"     Expected impact: {win.get('expected_impact', 'Unknown')}")

            # Priority actions
            priority_actions = optimization_result.get('priority_actions', [])
            if priority_actions:
                click.echo("
🚀 Priority Actions:")
                for i, action in enumerate(priority_actions, 1):
                    priority = action.get('priority', 'medium')
                    click.echo(f"  {i}. [{priority.upper()}] {action.get('action', 'Unknown')}")
                    if action.get('steps'):
                        for step in action['steps']:
                            click.echo(f"     • {step}")

    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"analyze optimize {post_id}",
            error_code="OPTIMIZATION_ANALYSIS_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@analyze.command()
@click.option('--days', type=int, default=30, help='Number of days to analyze')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def compare(days, server, json_output, verbose):
    """Compare performance across posts"""

    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command="analyze compare",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return

    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command="analyze compare",
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

        # Compare posts
        if verbose:
            click.echo(f"Comparing post performance for the last {days} days")

        comparison_result = integration.compare_post_performance(days)

        # Format output
        success_msg = AIFormatter.success_response(
            comparison_result,
            f"Post performance comparison complete for {days} days",
            command="analyze compare"
        )

        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo("
📊 Post Performance Comparison ({days} days)")
            click.echo("=" * 50)

            # Top performers
            top_performers = comparison_result.get('top_performers', [])
            if top_performers:
                click.echo("
🏆 Top Performers:")
                for i, post in enumerate(top_performers[:5], 1):
                    score = post.get('performance_score', 0)
                    click.echo(f"  {i}. {post.get('title', 'Unknown')} (Score: {score:.1f})")
                    click.echo(f"     Views: {post.get('views', 0):,} | Engagement: {post.get('engagement', 0):.1f}")

            # Underperformers
            underperformers = comparison_result.get('underperformers', [])
            if underperformers:
                click.echo("
📉 Underperformers:")
                for i, post in enumerate(underperformers[:3], 1):
                    score = post.get('performance_score', 0)
                    click.echo(f"  {i}. {post.get('title', 'Unknown')} (Score: {score:.1f})")
                    click.echo(f"     Views: {post.get('views', 0):,} | Engagement: {post.get('engagement', 0):.1f}")

            # Insights
            insights = comparison_result.get('insights', [])
            if insights:
                click.echo("
💡 Key Insights:")
                for i, insight in enumerate(insights, 1):
                    click.echo(f"  {i}. {insight}")

            # Recommendations
            recommendations = comparison_result.get('recommendations', [])
            if recommendations:
                click.echo("
🎯 Recommendations:")
                for i, rec in enumerate(recommendations, 1):
                    click.echo(f"  {i}. {rec}")

    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command="analyze compare",
            error_code="COMPARISON_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
