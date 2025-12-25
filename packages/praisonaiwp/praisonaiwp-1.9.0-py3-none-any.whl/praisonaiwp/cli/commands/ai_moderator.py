"""AI Comment Moderator - Intelligent comment moderation and response generation"""

import click
from typing import Dict, Any, List, Optional

from praisonaiwp.ai import AI_AVAILABLE
from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.ai_formatter import AIFormatter


@click.group()
def moderate():
    """AI-powered comment moderation and response generation"""
    pass


@moderate.command()
@click.option('--auto-approve', is_flag=True, help='Auto-approve non-spam comments')
@click.option('--spam-threshold', type=float, default=0.7, help='Spam detection threshold (0-1)')
@click.option('--sentiment-filter', help='Filter by sentiment (positive, negative, neutral)')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def comments(auto_approve, spam_threshold, sentiment_filter, server, json_output, verbose):
    """Moderate comments using AI"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command="moderate comments",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command="moderate comments",
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
        
        # Get pending comments
        if verbose:
            click.echo("Fetching pending comments...")
        
        pending_comments = wp_client.get_comments(status='hold', limit=50)
        
        if not pending_comments:
            success_msg = AIFormatter.success_response(
                {'message': 'No pending comments to moderate'},
                "No pending comments found",
                command="moderate comments"
            )
            click.echo(AIFormatter.format_output(success_msg, json_output))
            return
        
        # Moderate each comment
        results = {
            'total_comments': len(pending_comments),
            'moderated_comments': [],
            'summary': {
                'approved': 0,
                'spam': 0,
                'trash': 0,
                'held': 0
            }
        }
        
        for comment in pending_comments:
            if verbose:
                click.echo(f"Moderating comment {comment['id']}...")
            
            try:
                # Analyze comment
                analysis = integration.analyze_comment(comment['content'])
                
                moderation_result = {
                    'comment_id': comment['id'],
                    'author': comment['author'],
                    'content_preview': comment['content'][:100] + '...' if len(comment['content']) > 100 else comment['content'],
                    'analysis': analysis
                }
                
                # Apply moderation rules
                spam_score = analysis.get('spam_score', 0)
                sentiment = analysis.get('sentiment', 'neutral')
                toxicity_score = analysis.get('toxicity_score', 0)
                
                action = 'hold'  # Default action
                reason = ''
                
                # Check for spam
                if spam_score >= spam_threshold:
                    action = 'spam'
                    reason = f'Spam score: {spam_score:.2f}'
                # Check for toxicity
                elif toxicity_score >= 0.8:
                    action = 'trash'
                    reason = f'Toxicity score: {toxicity_score:.2f}'
                # Check sentiment filter
                elif sentiment_filter and sentiment != sentiment_filter:
                    action = 'hold'
                    reason = f'Sentiment filter: {sentiment} != {sentiment_filter}'
                # Auto-approve if enabled and comment is clean
                elif auto_approve and spam_score < 0.3 and toxicity_score < 0.3:
                    action = 'approve'
                    reason = 'Auto-approved (clean content)'
                
                # Apply action
                if action != 'hold':
                    wp_client.moderate_comment(comment['id'], action)
                    moderation_result['action'] = action
                    moderation_result['reason'] = reason
                    results['summary'][action] += 1
                else:
                    moderation_result['action'] = 'hold'
                    moderation_result['reason'] = 'Held for manual review'
                    results['summary']['held'] += 1
                
                results['moderated_comments'].append(moderation_result)
                
                if verbose:
                    status_icon = {'approve': '✅', 'spam': '🚫', 'trash': '🗑️', 'hold': '⏸️'}.get(action, '❓')
                    click.echo(f"  {status_icon} Comment {comment['id']}: {action} - {reason}")
                
            except Exception as e:
                if verbose:
                    click.echo(f"  ❌ Failed to moderate comment {comment['id']}: {str(e)}")
                
                moderation_result = {
                    'comment_id': comment['id'],
                    'error': str(e)
                }
                results['moderated_comments'].append(moderation_result)
        
        # Format output
        success_msg = AIFormatter.success_response(
            results,
            f"Moderated {len(results['moderated_comments'])} comments",
            command="moderate comments"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n✅ Comment Moderation Complete")
            click.echo("=" * 50)
            click.echo(f"Total comments processed: {results['total_comments']}")
            click.echo(f"Approved: {results['summary']['approved']}")
            click.echo(f"Marked as spam: {results['summary']['spam']}")
            click.echo(f"Trashed: {results['summary']['trash']}")
            click.echo(f"Held for review: {results['summary']['held']}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command="moderate comments",
            error_code="MODERATION_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@moderate.command()
@click.argument('comment_id', type=int)
@click.option('--tone', default='friendly', help='Response tone (friendly, professional, casual)')
@click.option('--length', default='medium', help='Response length (short, medium, long)')
@click.option('--include-question', is_flag=True, help='Include a question to encourage engagement')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def respond(comment_id, tone, length, include_question, server, json_output, verbose):
    """Generate AI response to a comment"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"moderate respond {comment_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"moderate respond {comment_id}",
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
        
        # Get comment
        comment = wp_client.get_comment(comment_id)
        if not comment:
            error_msg = AIFormatter.error_response(
                f"Comment with ID {comment_id} not found",
                command=f"moderate respond {comment_id}",
                error_code="NOT_FOUND"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Generate response
        if verbose:
            click.echo(f"Generating response to comment {comment_id}...")
        
        response = integration.generate_comment_response(
            comment['content'],
            tone=tone,
            length=length,
            include_question=include_question
        )
        
        # Format output
        success_msg = AIFormatter.success_response(
            {
                'comment_id': comment_id,
                'original_comment': comment['content'][:200] + '...' if len(comment['content']) > 200 else comment['content'],
                'generated_response': response['text'],
                'tone': tone,
                'length': length,
                'confidence': response.get('confidence', 0.95)
            },
            f"Generated response for comment {comment_id}",
            command=f"moderate respond {comment_id}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n💬 Generated Response for Comment {comment_id}")
            click.echo("=" * 50)
            click.echo(f"Original Comment: {comment['content']}")
            click.echo(f"\nGenerated Response ({tone}, {length}):")
            click.echo(response['text'])
            click.echo(f"\nConfidence: {response.get('confidence', 0.95):.2f}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"moderate respond {comment_id}",
            error_code="RESPONSE_GENERATION_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@moderate.command()
@click.argument('post_id', type=int)
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def analyze_comments(post_id, server, json_output, verbose):
    """Analyze comments for a specific post"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"moderate analyze-comments {post_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"moderate analyze-comments {post_id}",
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
        
        # Get post comments
        comments = wp_client.get_comments(post_id=post_id, limit=100)
        
        if not comments:
            success_msg = AIFormatter.success_response(
                {'message': 'No comments found for this post'},
                f"No comments found for post {post_id}",
                command=f"moderate analyze-comments {post_id}"
            )
            click.echo(AIFormatter.format_output(success_msg, json_output))
            return
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Analyze comments
        if verbose:
            click.echo(f"Analyzing {len(comments)} comments for post {post_id}...")
        
        analysis = integration.analyze_post_comments(comments)
        
        # Format output
        success_msg = AIFormatter.success_response(
            analysis,
            f"Analyzed {len(comments)} comments for post {post_id}",
            command=f"moderate analyze-comments {post_id}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n📊 Comment Analysis for Post {post_id}")
            click.echo("=" * 50)
            
            # Sentiment analysis
            sentiment = analysis.get('sentiment_analysis', {})
            click.echo(f"\n😊 Sentiment Analysis:")
            click.echo(f"  Positive: {sentiment.get('positive', 0)} ({sentiment.get('positive_pct', 0):.1f}%)")
            click.echo(f"  Neutral: {sentiment.get('neutral', 0)} ({sentiment.get('neutral_pct', 0):.1f}%)")
            click.echo(f"  Negative: {sentiment.get('negative', 0)} ({sentiment.get('negative_pct', 0):.1f}%)")
            
            # Quality metrics
            quality = analysis.get('quality_metrics', {})
            click.echo(f"\n📈 Quality Metrics:")
            click.echo(f"  Average sentiment score: {quality.get('avg_sentiment_score', 0):.2f}")
            click.echo(f"  Spam likelihood: {quality.get('spam_likelihood', 0):.2f}")
            click.echo(f"  Engagement quality: {quality.get('engagement_quality', 0):.2f}")
            
            # Top comments
            top_comments = analysis.get('top_comments', [])
            if top_comments:
                click.echo(f"\n⭐ Top Comments by Engagement:")
                for i, comment in enumerate(top_comments[:3], 1):
                    click.echo(f"  {i}. Comment {comment['id']}: {comment['engagement_score']:.1f}")
                    preview = comment['content'][:80] + '...' if len(comment['content']) > 80 else comment['content']
                    click.echo(f"     {preview}")
            
            # Issues found
            issues = analysis.get('issues', [])
            if issues:
                click.echo(f"\n⚠️  Issues Found:")
                for issue in issues:
                    click.echo(f"  • {issue}")
            else:
                click.echo(f"\n✅ No major issues detected!")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"moderate analyze-comments {post_id}",
            error_code="COMMENT_ANALYSIS_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@moderate.command()
@click.option('--sentiment', help='Filter by sentiment (positive, negative, neutral)')
@click.option('--min-score', type=float, help='Minimum engagement score')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def find_best(sentiment, min_score, server, json_output, verbose):
    """Find best comments for engagement"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command="moderate find-best",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command="moderate find-best",
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
        
        # Find best comments
        if verbose:
            filter_str = f" with sentiment '{sentiment}'" if sentiment else ""
            score_str = f" with min score {min_score}" if min_score else ""
            click.echo(f"Finding best comments{filter_str}{score_str}...")
        
        best_comments = integration.find_best_comments(
            sentiment=sentiment,
            min_score=min_score,
            limit=20
        )
        
        # Format output
        success_msg = AIFormatter.success_response(
            best_comments,
            f"Found {len(best_comments.get('comments', []))} best comments",
            command="moderate find-best"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n⭐ Best Comments for Engagement")
            click.echo("=" * 50)
            
            comments = best_comments.get('comments', [])
            if not comments:
                click.echo("No comments found matching the criteria.")
                return
            
            for i, comment in enumerate(comments[:10], 1):
                click.echo(f"\n{i}. Comment {comment['id']} (Score: {comment['engagement_score']:.1f})")
                click.echo(f"   Post: {comment['post_title']}")
                click.echo(f"   Author: {comment['author']}")
                click.echo(f"   Sentiment: {comment['sentiment']}")
                preview = comment['content'][:100] + '...' if len(comment['content']) > 100 else comment['content']
                click.echo(f"   Content: {preview}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command="moderate find-best",
            error_code="FIND_BEST_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
