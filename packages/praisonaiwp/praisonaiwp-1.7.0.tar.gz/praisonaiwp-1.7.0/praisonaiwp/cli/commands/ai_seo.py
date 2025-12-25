"""AI-powered SEO analysis and optimization commands"""

import click

from praisonaiwp.ai import AI_AVAILABLE
from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.ai_formatter import AIFormatter


@click.group()
def seo():
    """AI-powered SEO analysis and optimization"""
    pass


@seo.command()
@click.argument('post_id', type=int)
@click.option('--depth', default='comprehensive', help='Audit depth (quick, standard, comprehensive)')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def audit(post_id, depth, server, json_output, verbose):
    """Perform comprehensive SEO audit of a post"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"seo audit {post_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"seo audit {post_id}",
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
                command=f"seo audit {post_id}",
                error_code="NOT_FOUND"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Perform SEO audit
        if verbose:
            click.echo(f"Performing {depth} SEO audit for post {post_id}: {post['title']}")
        
        audit_result = integration.seo_audit(
            post_id,
            depth=depth
        )
        
        # Format output
        success_msg = AIFormatter.success_response(
            audit_result,
            f"SEO audit complete for post {post_id}",
            command=f"seo audit {post_id}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n🔍 SEO Audit Results for Post {post_id}")
            click.echo("=" * 50)
            click.echo(f"Post: {post['title']}")
            click.echo(f"Audit depth: {depth}")
            
            # Overall score
            overall_score = audit_result.get('overall_score', {})
            if overall_score:
                click.echo(f"\n📊 Overall SEO Score: {overall_score.get('score', 0)}/100")
                click.echo(f"Grade: {overall_score.get('grade', 'N/A')}")
            
            # Technical SEO
            technical = audit_result.get('technical_seo', {})
            if technical:
                click.echo(f"\n⚙️  Technical SEO:")
                for item, result in technical.items():
                    status = "✅" if result.get('status') == 'pass' else "❌"
                    click.echo(f"  {status} {item}: {result.get('message', 'N/A')}")
            
            # Content SEO
            content_seo = audit_result.get('content_seo', {})
            if content_seo:
                click.echo(f"\n📝 Content SEO:")
                for item, result in content_seo.items():
                    status = "✅" if result.get('status') == 'pass' else "❌"
                    click.echo(f"  {status} {item}: {result.get('message', 'N/A')}")
            
            # Keywords
            keywords = audit_result.get('keyword_analysis', {})
            if keywords:
                click.echo(f"\n🔑 Keyword Analysis:")
                primary = keywords.get('primary_keywords', [])
                if primary:
                    click.echo(f"  Primary: {', '.join(primary)}")
                secondary = keywords.get('secondary_keywords', [])
                if secondary:
                    click.echo(f"  Secondary: {', '.join(secondary[:5])}")
                density = keywords.get('keyword_density', {})
                if density:
                    click.echo(f"  Density: {density.get('overall', 0):.1f}%")
            
            # Issues
            issues = audit_result.get('issues', [])
            if issues:
                click.echo(f"\n⚠️  Issues Found ({len(issues)}):")
                for i, issue in enumerate(issues[:10], 1):
                    severity = issue.get('severity', 'medium')
                    click.echo(f"  {i}. [{severity.upper()}] {issue.get('description', 'Unknown')}")
            
            # Recommendations
            recommendations = audit_result.get('recommendations', [])
            if recommendations:
                click.echo(f"\n💡 Recommendations ({len(recommendations)}):")
                for i, rec in enumerate(recommendations[:10], 1):
                    priority = rec.get('priority', 'medium')
                    click.echo(f"  {i}. [{priority.upper()}] {rec.get('action', 'Unknown')}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"seo audit {post_id}",
            error_code="SEO_AUDIT_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@seo.command()
@click.argument('post_id', type=int)
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def keywords(post_id, server, json_output, verbose):
    """Analyze and suggest keywords for a post"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"seo keywords {post_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"seo keywords {post_id}",
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
                command=f"seo keywords {post_id}",
                error_code="NOT_FOUND"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Analyze keywords
        if verbose:
            click.echo(f"Analyzing keywords for post {post_id}: {post['title']}")
        
        keyword_result = integration.analyze_keywords(post_id)
        
        # Format output
        success_msg = AIFormatter.success_response(
            keyword_result,
            f"Keyword analysis complete for post {post_id}",
            command=f"seo keywords {post_id}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n🔑 Keyword Analysis for Post {post_id}")
            click.echo("=" * 50)
            click.echo(f"Post: {post['title']}")
            
            # Current keywords
            current = keyword_result.get('current_keywords', {})
            if current:
                click.echo(f"\n📊 Current Keywords:")
                primary = current.get('primary', [])
                if primary:
                    click.echo(f"  Primary: {', '.join(primary)}")
                secondary = current.get('secondary', [])
                if secondary:
                    click.echo(f"  Secondary: {', '.join(secondary[:5])}")
                density = current.get('density', {})
                if density:
                    click.echo(f"  Overall density: {density.get('overall', 0):.1f}%")
            
            # Suggested keywords
            suggested = keyword_result.get('suggested_keywords', [])
            if suggested:
                click.echo(f"\n💡 Suggested Keywords:")
                for i, keyword in enumerate(suggested[:10], 1):
                    difficulty = keyword.get('difficulty', 'medium')
                    volume = keyword.get('search_volume', 'N/A')
                    click.echo(f"  {i}. {keyword.get('keyword', 'Unknown')}")
                    click.echo(f"     Difficulty: {difficulty} | Volume: {volume}")
                    click.echo(f"     Relevance: {keyword.get('relevance', 0):.2f}")
            
            # Keyword gaps
            gaps = keyword_result.get('keyword_gaps', [])
            if gaps:
                click.echo(f"\n🎯 Keyword Opportunities:")
                for i, gap in enumerate(gaps[:5], 1):
                    click.echo(f"  {i}. {gap.get('keyword', 'Unknown')}")
                    click.echo(f"     Reason: {gap.get('reason', 'Unknown')}")
                    click.echo(f"     Potential: {gap.get('potential', 'Unknown')}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"seo keywords {post_id}",
            error_code="KEYWORD_ANALYSIS_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@seo.command()
@click.argument('post_id', type=int)
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def meta(post_id, server, json_output, verbose):
    """Analyze and optimize meta tags"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"seo meta {post_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"seo meta {post_id}",
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
                command=f"seo meta {post_id}",
                error_code="NOT_FOUND"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Analyze meta tags
        if verbose:
            click.echo(f"Analyzing meta tags for post {post_id}: {post['title']}")
        
        meta_result = integration.analyze_meta_tags(post_id)
        
        # Format output
        success_msg = AIFormatter.success_response(
            meta_result,
            f"Meta tag analysis complete for post {post_id}",
            command=f"seo meta {post_id}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n🏷️  Meta Tag Analysis for Post {post_id}")
            click.echo("=" * 50)
            click.echo(f"Post: {post['title']}")
            
            # Current meta tags
            current = meta_result.get('current_meta', {})
            if current:
                click.echo(f"\n📊 Current Meta Tags:")
                if current.get('title'):
                    click.echo(f"  Title: {current['title']}")
                    click.echo(f"    Length: {len(current['title'])} characters")
                if current.get('description'):
                    click.echo(f"  Description: {current['description']}")
                    click.echo(f"    Length: {len(current['description'])} characters")
                if current.get('keywords'):
                    click.echo(f"  Keywords: {current['keywords']}")
            
            # Optimized meta tags
            optimized = meta_result.get('optimized_meta', {})
            if optimized:
                click.echo(f"\n⚡ Optimized Meta Tags:")
                if optimized.get('title'):
                    click.echo(f"  Title: {optimized['title']}")
                    click.echo(f"    Length: {len(optimized['title'])} characters")
                if optimized.get('description'):
                    click.echo(f"  Description: {optimized['description']}")
                    click.echo(f"    Length: {len(optimized['description'])} characters")
                if optimized.get('keywords'):
                    click.echo(f"  Keywords: {optimized['keywords']}")
            
            # Issues
            issues = meta_result.get('issues', [])
            if issues:
                click.echo(f"\n⚠️  Meta Tag Issues:")
                for i, issue in enumerate(issues, 1):
                    severity = issue.get('severity', 'medium')
                    click.echo(f"  {i}. [{severity.upper()}] {issue.get('description', 'Unknown')}")
                    if issue.get('suggestion'):
                        click.echo(f"     Suggestion: {issue['suggestion']}")
            
            # Recommendations
            recommendations = meta_result.get('recommendations', [])
            if recommendations:
                click.echo(f"\n💡 Meta Tag Recommendations:")
                for i, rec in enumerate(recommendations, 1):
                    click.echo(f"  {i}. {rec}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"seo meta {post_id}",
            error_code="META_ANALYSIS_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@seo.command()
@click.argument('post_id', type=int)
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def structure(post_id, server, json_output, verbose):
    """Analyze content structure for SEO"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"seo structure {post_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"seo structure {post_id}",
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
                command=f"seo structure {post_id}",
                error_code="NOT_FOUND"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Analyze structure
        if verbose:
            click.echo(f"Analyzing content structure for post {post_id}: {post['title']}")
        
        structure_result = integration.analyze_content_structure(post_id)
        
        # Format output
        success_msg = AIFormatter.success_response(
            structure_result,
            f"Content structure analysis complete for post {post_id}",
            command=f"seo structure {post_id}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n📐 Content Structure Analysis for Post {post_id}")
            click.echo("=" * 50)
            click.echo(f"Post: {post['title']}")
            
            # Heading structure
            headings = structure_result.get('headings', {})
            if headings:
                click.echo(f"\n📝 Heading Structure:")
                for level in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    if level in headings:
                        heading_list = headings[level]
                        click.echo(f"  {level.upper()} ({len(heading_list)}):")
                        for heading in heading_list[:3]:
                            preview = heading[:40] + "..." if len(heading) > 40 else heading
                            click.echo(f"    • {preview}")
                        if len(heading_list) > 3:
                            click.echo(f"    ... and {len(heading_list) - 3} more")
            
            # Content metrics
            metrics = structure_result.get('content_metrics', {})
            if metrics:
                click.echo(f"\n📊 Content Metrics:")
                click.echo(f"  Word count: {metrics.get('word_count', 0):,}")
                click.echo(f"  Paragraph count: {metrics.get('paragraph_count', 0)}")
                click.echo(f"  Average paragraph length: {metrics.get('avg_paragraph_length', 0):.1f} words")
                click.echo(f"  Readability score: {metrics.get('readability_score', 0):.1f}")
            
            # Structure issues
            issues = structure_result.get('structure_issues', [])
            if issues:
                click.echo(f"\n⚠️  Structure Issues:")
                for i, issue in enumerate(issues, 1):
                    severity = issue.get('severity', 'medium')
                    click.echo(f"  {i}. [{severity.upper()}] {issue.get('description', 'Unknown')}")
                    if issue.get('suggestion'):
                        click.echo(f"     Suggestion: {issue['suggestion']}")
            
            # Recommendations
            recommendations = structure_result.get('recommendations', [])
            if recommendations:
                click.echo(f"\n💡 Structure Recommendations:")
                for i, rec in enumerate(recommendations, 1):
                    click.echo(f"  {i}. {rec}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"seo structure {post_id}",
            error_code="STRUCTURE_ANALYSIS_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@seo.command()
@click.argument('post_id', type=int)
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def competitors(post_id, server, json_output, verbose):
    """Analyze competitor content for SEO insights"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"seo competitors {post_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"seo competitors {post_id}",
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
                command=f"seo competitors {post_id}",
                error_code="NOT_FOUND"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Analyze competitors
        if verbose:
            click.echo(f"Analyzing competitors for post {post_id}: {post['title']}")
        
        competitor_result = integration.analyze_competitors(post_id)
        
        # Format output
        success_msg = AIFormatter.success_response(
            competitor_result,
            f"Competitor analysis complete for post {post_id}",
            command=f"seo competitors {post_id}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n🏁 Competitor Analysis for Post {post_id}")
            click.echo("=" * 50)
            click.echo(f"Post: {post['title']}")
            
            # Top competitors
            competitors = competitor_result.get('competitors', [])
            if competitors:
                click.echo(f"\n🏆 Top Competitors:")
                for i, competitor in enumerate(competitors[:5], 1):
                    click.echo(f"  {i}. {competitor.get('title', 'Unknown')}")
                    click.echo(f"     URL: {competitor.get('url', 'N/A')}")
                    click.echo(f"     SEO Score: {competitor.get('seo_score', 0)}/100")
                    click.echo(f"     Traffic: {competitor.get('estimated_traffic', 'N/A')}")
            
            # Keyword gaps
            keyword_gaps = competitor_result.get('keyword_gaps', [])
            if keyword_gaps:
                click.echo(f"\n🎯 Keyword Opportunities:")
                for i, gap in enumerate(keyword_gaps[:5], 1):
                    click.echo(f"  {i}. {gap.get('keyword', 'Unknown')}")
                    click.echo(f"     Difficulty: {gap.get('difficulty', 'Unknown')}")
                    click.echo(f"     Opportunity: {gap.get('opportunity', 'Unknown')}")
            
            # Content gaps
            content_gaps = competitor_result.get('content_gaps', [])
            if content_gaps:
                click.echo(f"\n📝 Content Gaps:")
                for i, gap in enumerate(content_gaps[:3], 1):
                    click.echo(f"  {i}. {gap.get('topic', 'Unknown')}")
                    click.echo(f"     Reason: {gap.get('reason', 'Unknown')}")
                    click.echo(f"     Priority: {gap.get('priority', 'Unknown')}")
            
            # Recommendations
            recommendations = competitor_result.get('recommendations', [])
            if recommendations:
                click.echo(f"\n💡 Competitive Recommendations:")
                for i, rec in enumerate(recommendations, 1):
                    click.echo(f"  {i}. {rec}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"seo competitors {post_id}",
            error_code="COMPETITOR_ANALYSIS_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
