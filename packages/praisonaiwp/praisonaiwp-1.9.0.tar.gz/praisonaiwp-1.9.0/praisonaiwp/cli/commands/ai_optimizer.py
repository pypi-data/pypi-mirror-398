"""AI Content Optimizer - Optimize content for SEO, readability, and engagement"""

import click
from typing import Dict, Any, List, Optional

from praisonaiwp.ai import AI_AVAILABLE
from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.ai_formatter import AIFormatter


@click.group()
def optimize():
    """AI-powered content optimization for SEO and readability"""
    pass


@optimize.command()
@click.argument('post_id', type=int)
@click.option('--seo', is_flag=True, help='Optimize for SEO')
@click.option('--readability', is_flag=True, help='Improve readability')
@click.option('--tone', help='Adjust tone (professional, casual, technical, friendly)')
@click.option('--expand', is_flag=True, help='Expand content')
@click.option('--compress', is_flag=True, help='Compress content')
@click.option('--target-words', type=int, help='Target word count for expansion/compression')
@click.option('--apply', is_flag=True, help='Apply optimizations to the post')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def post(post_id, seo, readability, tone, expand, compress, target_words, apply, server, json_output, verbose):
    """Optimize a WordPress post using AI"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"optimize post {post_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"optimize post {post_id}",
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
                command=f"optimize post {post_id}",
                error_code="NOT_FOUND"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        original_content = post['content']
        original_title = post['title']
        
        results = {
            'original_title': original_title,
            'original_content': original_content,
            'optimizations': []
        }
        
        # SEO optimization
        if seo:
            if verbose:
                click.echo("Performing SEO optimization...")
            
            seo_result = integration.optimize_seo(original_title, original_content)
            results['seo_optimization'] = seo_result
            results['optimizations'].append('SEO')
        
        # Readability improvement
        if readability:
            if verbose:
                click.echo("Improving readability...")
            
            readability_result = integration.improve_readability(original_content)
            results['readability_optimization'] = readability_result
            results['optimizations'].append('Readability')
        
        # Tone adjustment
        if tone:
            if verbose:
                click.echo(f"Adjusting tone to {tone}...")
            
            tone_result = integration.adjust_tone(original_content, tone)
            results['tone_optimization'] = tone_result
            results['optimizations'].append(f'Tone ({tone})')
        
        # Content expansion
        if expand:
            if verbose:
                click.echo("Expanding content...")
            
            expand_result = integration.expand_content(
                original_content, 
                target_words=target_words or 1500
            )
            results['content_expansion'] = expand_result
            results['optimizations'].append('Content Expansion')
        
        # Content compression
        if compress:
            if verbose:
                click.echo("Compressing content...")
            
            compress_result = integration.compress_content(
                original_content,
                target_words=target_words or 500
            )
            results['content_compression'] = compress_result
            results['optimizations'].append('Content Compression')
        
        # Apply optimizations if requested
        if apply:
            if verbose:
                click.echo("Applying optimizations to post...")
            
            # Create optimized content
            optimized_content = original_content
            optimized_title = original_title
            
            if seo and 'seo_optimization' in results:
                optimized_title = results['seo_optimization'].get('optimized_title', original_title)
                optimized_content = results['seo_optimization'].get('optimized_content', original_content)
            
            if readability and 'readability_optimization' in results:
                optimized_content = results['readability_optimization'].get('improved_content', optimized_content)
            
            if tone and 'tone_optimization' in results:
                optimized_content = results['tone_optimization'].get('adjusted_content', optimized_content)
            
            if expand and 'content_expansion' in results:
                optimized_content = results['content_expansion'].get('expanded_content', optimized_content)
            
            if compress and 'content_compression' in results:
                optimized_content = results['content_compression'].get('compressed_content', optimized_content)
            
            # Update the post
            update_result = wp_client.update_post(
                post_id,
                title=optimized_title,
                content=optimized_content
            )
            
            results['applied'] = True
            results['updated_post_id'] = post_id
            results['final_title'] = optimized_title
            results['final_content'] = optimized_content
        else:
            results['applied'] = False
        
        # Format output
        message = f"Optimized post {post_id} with: {', '.join(results['optimizations'])}"
        if apply:
            message += " (applied)"
        
        success_msg = AIFormatter.success_response(
            results,
            message,
            command=f"optimize post {post_id}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n✅ Content optimization complete for post {post_id}")
            click.echo("=" * 60)
            click.echo(f"Optimizations applied: {', '.join(results['optimizations'])}")
            
            if apply:
                click.echo(f"\n📝 Post has been updated!")
                click.echo(f"New title: {results.get('final_title', original_title)}")
                click.echo(f"Content length: {len(results.get('final_content', original_content))} characters")
            else:
                click.echo(f"\n📊 Preview (use --apply to update the post):")
                
                if 'seo_optimization' in results:
                    seo_opt = results['seo_optimization']
                    click.echo(f"\n🔍 SEO Optimized Title:")
                    click.echo(seo_opt.get('optimized_title', 'No change'))
                
                if 'readability_optimization' in results:
                    read_opt = results['readability_optimization']
                    click.echo(f"\n📖 Readability Score: {read_opt.get('readability_score', 'N/A')}")
                    click.echo(f"Improvements: {', '.join(read_opt.get('improvements', []))}")
                
                if 'tone_optimization' in results:
                    tone_opt = results['tone_optimization']
                    click.echo(f"\n🎭 Tone Adjustment:")
                    click.echo(f"Confidence: {tone_opt.get('confidence', 'N/A')}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"optimize post {post_id}",
            error_code="OPTIMIZATION_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@optimize.command()
@click.argument('post_id', type=int)
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def analyze(post_id, server, json_output, verbose):
    """Analyze content quality and provide recommendations"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"optimize analyze {post_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"optimize analyze {post_id}",
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
                command=f"optimize analyze {post_id}",
                error_code="NOT_FOUND"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Analyze content
        if verbose:
            click.echo("Analyzing content quality...")
        
        analysis = integration.analyze_content(post['title'], post['content'])
        
        # Format output
        success_msg = AIFormatter.success_response(
            analysis,
            f"Content analysis complete for post {post_id}",
            command=f"optimize analyze {post_id}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n📊 Content Analysis for Post {post_id}")
            click.echo("=" * 50)
            
            # Overall scores
            scores = analysis.get('scores', {})
            click.echo(f"\n📈 Overall Scores:")
            click.echo(f"  SEO Score: {scores.get('seo', 'N/A')}/100")
            click.echo(f"  Readability: {scores.get('readability', 'N/A')}/100")
            click.echo(f"  Engagement: {scores.get('engagement', 'N/A')}/100")
            click.echo(f"  Overall: {scores.get('overall', 'N/A')}/100")
            
            # Issues found
            issues = analysis.get('issues', [])
            if issues:
                click.echo(f"\n⚠️  Issues Found ({len(issues)}):")
                for i, issue in enumerate(issues, 1):
                    click.echo(f"  {i}. {issue}")
            else:
                click.echo(f"\n✅ No major issues found!")
            
            # Recommendations
            recommendations = analysis.get('recommendations', [])
            if recommendations:
                click.echo(f"\n💡 Recommendations ({len(recommendations)}):")
                for i, rec in enumerate(recommendations, 1):
                    click.echo(f"  {i}. {rec}")
            
            # Word count and stats
            stats = analysis.get('statistics', {})
            click.echo(f"\n📊 Statistics:")
            click.echo(f"  Word Count: {stats.get('word_count', 'N/A')}")
            click.echo(f"  Character Count: {stats.get('character_count', 'N/A')}")
            click.echo(f"  Paragraph Count: {stats.get('paragraph_count', 'N/A')}")
            click.echo(f"  Avg Sentence Length: {stats.get('avg_sentence_length', 'N/A')}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"optimize analyze {post_id}",
            error_code="ANALYSIS_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@optimize.command()
@click.argument('post_id', type=int)
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def grammar(post_id, server, json_output, verbose):
    """Check and fix grammar and style issues"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"optimize grammar {post_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"optimize grammar {post_id}",
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
                command=f"optimize grammar {post_id}",
                error_code="NOT_FOUND"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Check grammar
        if verbose:
            click.echo("Checking grammar and style...")
        
        grammar_result = integration.check_grammar(post['content'])
        
        # Format output
        success_msg = AIFormatter.success_response(
            grammar_result,
            f"Grammar check complete for post {post_id}",
            command=f"optimize grammar {post_id}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n📝 Grammar Check for Post {post_id}")
            click.echo("=" * 50)
            
            errors = grammar_result.get('errors', [])
            suggestions = grammar_result.get('suggestions', [])
            corrected_content = grammar_result.get('corrected_content')
            
            if errors:
                click.echo(f"\n❌ Grammar Issues Found ({len(errors)}):")
                for i, error in enumerate(errors, 1):
                    click.echo(f"  {i}. {error}")
            else:
                click.echo(f"\n✅ No grammar errors found!")
            
            if suggestions:
                click.echo(f"\n💡 Style Suggestions ({len(suggestions)}):")
                for i, suggestion in enumerate(suggestions, 1):
                    click.echo(f"  {i}. {suggestion}")
            
            if corrected_content:
                click.echo(f"\n📄 Corrected Content Preview:")
                click.echo("-" * 30)
                # Show first 500 characters of corrected content
                preview = corrected_content[:500] + "..." if len(corrected_content) > 500 else corrected_content
                click.echo(preview)
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"optimize grammar {post_id}",
            error_code="GRAMMAR_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
