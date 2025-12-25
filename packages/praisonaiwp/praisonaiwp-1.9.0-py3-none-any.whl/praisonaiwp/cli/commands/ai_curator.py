"""AI Content Curator - Curate and suggest related content automatically"""

import click
from typing import Dict, Any, List, Optional

from praisonaiwp.ai import AI_AVAILABLE
from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.ai_formatter import AIFormatter


@click.group()
def curate():
    """AI-powered content curation and recommendations"""
    pass


@curate.command()
@click.argument('post_id', type=int)
@click.option('--count', type=int, default=5, help='Number of related posts to find')
@click.option('--similarity-threshold', type=float, default=0.3, help='Minimum similarity threshold (0-1)')
@click.option('--exclude-same-category', is_flag=True, help='Exclude posts from same category')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def related(post_id, count, similarity_threshold, exclude_same_category, server, json_output, verbose):
    """Find related posts for a given post"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"curate related {post_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"curate related {post_id}",
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
        
        # Get the target post
        target_post = wp_client.get_post(post_id)
        if not target_post:
            error_msg = AIFormatter.error_response(
                f"Post with ID {post_id} not found",
                command=f"curate related {post_id}",
                error_code="NOT_FOUND"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Find related posts
        if verbose:
            click.echo(f"Finding {count} related posts for post {post_id}...")
        
        related_posts = integration.find_related_posts(
            target_post,
            count=count,
            similarity_threshold=similarity_threshold,
            exclude_same_category=exclude_same_category
        )
        
        # Format output
        success_msg = AIFormatter.success_response(
            related_posts,
            f"Found {len(related_posts.get('posts', []))} related posts",
            command=f"curate related {post_id}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n🔗 Related Posts for Post {post_id}")
            click.echo("=" * 50)
            click.echo(f"Target post: {target_post['title']}")
            
            posts = related_posts.get('posts', [])
            if not posts:
                click.echo("No related posts found.")
                return
            
            for i, post in enumerate(posts, 1):
                similarity = post.get('similarity_score', 0)
                click.echo(f"\n{i}. {post['title']} (Similarity: {similarity:.2f})")
                click.echo(f"   ID: {post['id']} | URL: {post.get('url', 'N/A')}")
                if post.get('excerpt'):
                    excerpt = post['excerpt'][:100] + '...' if len(post['excerpt']) > 100 else post['excerpt']
                    click.echo(f"   Excerpt: {excerpt}")
                if post.get('reason'):
                    click.echo(f"   Reason: {post['reason']}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"curate related {post_id}",
            error_code="RELATED_POSTS_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@curate.command()
@click.argument('post_id', type=int)
@click.option('--max-links', type=int, default=5, help='Maximum number of internal links to suggest')
@click.option('--min-relevance', type=float, default=0.4, help='Minimum relevance score (0-1)')
@click.option('--anchor-text', help='Preferred anchor text style (exact, partial, contextual)')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def links(post_id, max_links, min_relevance, anchor_text, server, json_output, verbose):
    """Suggest internal linking opportunities"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"curate links {post_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"curate links {post_id}",
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
        
        # Get the target post
        target_post = wp_client.get_post(post_id)
        if not target_post:
            error_msg = AIFormatter.error_response(
                f"Post with ID {post_id} not found",
                command=f"curate links {post_id}",
                error_code="NOT_FOUND"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Suggest internal links
        if verbose:
            click.echo(f"Suggesting up to {max_links} internal links for post {post_id}...")
        
        link_suggestions = integration.suggest_internal_links(
            target_post,
            max_links=max_links,
            min_relevance=min_relevance,
            anchor_text_style=anchor_text or 'contextual'
        )
        
        # Format output
        success_msg = AIFormatter.success_response(
            link_suggestions,
            f"Found {len(link_suggestions.get('suggestions', []))} internal link suggestions",
            command=f"curate links {post_id}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n🔗 Internal Link Suggestions for Post {post_id}")
            click.echo("=" * 50)
            click.echo(f"Target post: {target_post['title']}")
            
            suggestions = link_suggestions.get('suggestions', [])
            if not suggestions:
                click.echo("No internal link suggestions found.")
                return
            
            for i, suggestion in enumerate(suggestions, 1):
                click.echo(f"\n{i}. Link to: {suggestion['target_title']}")
                click.echo(f"   Target ID: {suggestion['target_id']} | Relevance: {suggestion.get('relevance_score', 0):.2f}")
                click.echo(f"   Anchor text: {suggestion.get('anchor_text', 'N/A')}")
                click.echo(f"   Context: {suggestion.get('context', 'N/A')}")
                if suggestion.get('html_snippet'):
                    click.echo(f"   HTML: {suggestion['html_snippet']}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"curate links {post_id}",
            error_code="LINK_SUGGESTIONS_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@curate.command()
@click.option('--category', help='Cluster posts by category')
@click.option('--tags', help='Cluster posts by tags (comma-separated)')
@click.option('--min-cluster-size', type=int, default=3, help='Minimum posts per cluster')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def cluster(category, tags, min_cluster_size, server, json_output, verbose):
    """Cluster content by topic similarity"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command="curate cluster",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command="curate cluster",
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
        
        # Parse tags if provided
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
        
        # Cluster content
        if verbose:
            filter_str = f" in category '{category}'" if category else ""
            tag_str = f" with tags {tags}" if tags else ""
            click.echo(f"Clustering content{filter_str}{tag_str}...")
        
        clusters = integration.cluster_content(
            category=category,
            tags=tag_list,
            min_cluster_size=min_cluster_size
        )
        
        # Format output
        success_msg = AIFormatter.success_response(
            clusters,
            f"Created {len(clusters.get('clusters', []))} content clusters",
            command="curate cluster"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n📊 Content Clustering Results")
            click.echo("=" * 50)
            if category:
                click.echo(f"Category: {category}")
            if tags:
                click.echo(f"Tags: {tags}")
            
            clusters_list = clusters.get('clusters', [])
            if not clusters_list:
                click.echo("No clusters found with the specified criteria.")
                return
            
            total_posts = sum(len(cluster.get('posts', [])) for cluster in clusters_list)
            click.echo(f"\nTotal clusters: {len(clusters_list)}")
            click.echo(f"Total posts clustered: {total_posts}")
            
            for i, cluster in enumerate(clusters_list, 1):
                posts = cluster.get('posts', [])
                click.echo(f"\n{i}. Cluster: {cluster.get('topic_name', 'Untitled')} ({len(posts)} posts)")
                click.echo(f"   Keywords: {', '.join(cluster.get('keywords', []))}")
                click.echo(f"   Coherence score: {cluster.get('coherence_score', 0):.2f}")
                
                # Show top posts in cluster
                top_posts = posts[:3]
                for j, post in enumerate(top_posts, 1):
                    click.echo(f"   {j}. {post['title']} (ID: {post['id']})")
                
                if len(posts) > 3:
                    click.echo(f"   ... and {len(posts) - 3} more posts")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command="curate cluster",
            error_code="CLUSTERING_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@curate.command()
@click.option('--analyze', is_flag=True, help='Analyze content gaps')
@click.option('--recommend', is_flag=True, help='Recommend missing content')
@click.option('--timeframe', default='month', help='Analysis timeframe (week, month, quarter)')
@click.option('--category', help='Focus on specific category')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def gaps(analyze, recommend, timeframe, category, server, json_output, verbose):
    """Identify content gaps and suggest missing topics"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command="curate gaps",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command="curate gaps",
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
        
        results = {}
        
        # Analyze content gaps
        if analyze:
            if verbose:
                category_str = f" in category '{category}'" if category else ""
                click.echo(f"Analyzing content gaps{category_str} for {timeframe}...")
            
            gap_analysis = integration.analyze_content_gaps(
                category=category,
                timeframe=timeframe
            )
            results['gap_analysis'] = gap_analysis
        
        # Generate recommendations
        if recommend:
            if verbose:
                click.echo("Generating content recommendations...")
            
            recommendations = integration.generate_content_recommendations(
                category=category,
                timeframe=timeframe
            )
            results['recommendations'] = recommendations
        
        # Format output
        success_msg = AIFormatter.success_response(
            results,
            f"Content gap analysis complete",
            command="curate gaps"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n🔍 Content Gap Analysis")
            click.echo("=" * 50)
            if category:
                click.echo(f"Category: {category}")
            click.echo(f"Timeframe: {timeframe}")
            
            # Show missing topics
            if 'gap_analysis' in results:
                gap_analysis = results['gap_analysis']
                missing_topics = gap_analysis.get('missing_topics', [])
                if missing_topics:
                    click.echo(f"\n📝 Missing Topics ({len(missing_topics)}):")
                    for i, topic in enumerate(missing_topics[:10], 1):
                        priority = topic.get('priority', 'medium')
                        click.echo(f"  {i}. {topic.get('title', 'Untitled')} [{priority}]")
                        if topic.get('reason'):
                            click.echo(f"     Reason: {topic['reason']}")
            
            # Show recommendations
            if 'recommendations' in results:
                recommendations = results['recommendations']
                content_rec = recommendations.get('content_suggestions', [])
                if content_rec:
                    click.echo(f"\n💡 Content Recommendations ({len(content_rec)}):")
                    for i, rec in enumerate(content_rec[:10], 1):
                        click.echo(f"  {i}. {rec.get('title', 'Untitled')}")
                        click.echo(f"     Type: {rec.get('content_type', 'post')}")
                        click.echo(f"     Priority: {rec.get('priority', 'medium')}")
                        if rec.get('description'):
                            click.echo(f"     Description: {rec['description']}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command="curate gaps",
            error_code="GAP_ANALYSIS_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@curate.command()
@click.option('--days', type=int, default=30, help='Number of days to analyze')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def trends(days, server, json_output, verbose):
    """Analyze content trends and patterns"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command="curate trends",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command="curate trends",
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
            click.echo(f"Analyzing content trends for the last {days} days...")
        
        trends_analysis = integration.analyze_content_trends(days)
        
        # Format output
        success_msg = AIFormatter.success_response(
            trends_analysis,
            f"Content trends analysis complete for {days} days",
            command="curate trends"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n📈 Content Trends Analysis ({days} days)")
            click.echo("=" * 50)
            
            # Rising topics
            rising_topics = trends_analysis.get('rising_topics', [])
            if rising_topics:
                click.echo(f"\n📈 Rising Topics:")
                for i, topic in enumerate(rising_topics[:5], 1):
                    click.echo(f"  {i}. {topic.get('topic', 'Untitled')} (+{topic.get('growth_rate', 0):.1f}%)")
                    click.echo(f"     Mentions: {topic.get('mentions', 0)} → {topic.get('recent_mentions', 0)}")
            
            # Declining topics
            declining_topics = trends_analysis.get('declining_topics', [])
            if declining_topics:
                click.echo(f"\n📉 Declining Topics:")
                for i, topic in enumerate(declining_topics[:3], 1):
                    click.echo(f"  {i}. {topic.get('topic', 'Untitled')} ({topic.get('growth_rate', 0):.1f}%)")
            
            # Emerging patterns
            patterns = trends_analysis.get('emerging_patterns', [])
            if patterns:
                click.echo(f"\n🔍 Emerging Patterns:")
                for i, pattern in enumerate(patterns[:3], 1):
                    click.echo(f"  {i}. {pattern.get('pattern', 'Untitled')}")
                    click.echo(f"     Confidence: {pattern.get('confidence', 0):.2f}")
                    if pattern.get('description'):
                        click.echo(f"     Description: {pattern['description']}")
            
            # Recommendations
            recommendations = trends_analysis.get('recommendations', [])
            if recommendations:
                click.echo(f"\n💡 Trend-Based Recommendations:")
                for i, rec in enumerate(recommendations, 1):
                    click.echo(f"  {i}. {rec}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command="curate trends",
            error_code="TRENDS_ANALYSIS_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
