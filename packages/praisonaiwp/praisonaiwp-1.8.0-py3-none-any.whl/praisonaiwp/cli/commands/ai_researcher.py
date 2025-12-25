"""AI Research Assistant - Research topics and generate comprehensive content with citations"""

import click
from typing import Dict, Any, List, Optional

from praisonaiwp.ai import AI_AVAILABLE
from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.ai_formatter import AIFormatter


@click.group()
def research():
    """AI-powered research and content generation with citations"""
    pass


@research.command()
@click.argument('topic')
@click.option('--depth', default='comprehensive', help='Research depth (quick, standard, comprehensive)')
@click.option('--sources', type=int, default=10, help='Number of sources to research')
@click.option('--citations', is_flag=True, default=True, help='Include citations')
@click.option('--format', default='apa', help='Citation format (apa, mla, chicago)')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def topic(topic, depth, sources, citations, format, server, json_output, verbose):
    """Research a topic and generate comprehensive content"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"research topic \"{topic}\"",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"research topic \"{topic}\"",
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
        
        # Research topic
        if verbose:
            click.echo(f"Researching topic: {topic}")
            click.echo(f"Depth: {depth} | Sources: {sources} | Citations: {citations}")
        
        research_result = integration.research_topic(
            topic=topic,
            depth=depth,
            num_sources=sources,
            include_citations=citations,
            citation_format=format
        )
        
        # Format output
        success_msg = AIFormatter.success_response(
            research_result,
            f"Research complete for topic: {topic}",
            command=f"research topic \"{topic}\""
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n🔬 Research Results: {topic}")
            click.echo("=" * 60)
            
            # Overview
            overview = research_result.get('overview', {})
            click.echo(f"\n📋 Research Overview:")
            click.echo(f"  Sources found: {overview.get('sources_found', 0)}")
            click.echo(f"  Sources used: {overview.get('sources_used', 0)}")
            click.echo(f"  Word count: {overview.get('word_count', 0)}")
            click.echo(f"  Confidence: {overview.get('confidence', 0):.2f}")
            
            # Generated content
            content = research_result.get('content', '')
            if content:
                click.echo(f"\n📄 Generated Content:")
                click.echo("-" * 40)
                # Show first 1000 characters
                preview = content[:1000] + "..." if len(content) > 1000 else content
                click.echo(preview)
            
            # Sources
            sources_list = research_result.get('sources', [])
            if sources_list:
                click.echo(f"\n📚 Sources ({len(sources_list)}):")
                for i, source in enumerate(sources_list[:5], 1):
                    click.echo(f"  {i}. {source.get('title', 'Untitled')}")
                    click.echo(f"     {source.get('url', 'N/A')}")
                    click.echo(f"     {source.get('citation', '')}")
                if len(sources_list) > 5:
                    click.echo(f"     ... and {len(sources_list) - 5} more sources")
            
            # Key findings
            findings = research_result.get('key_findings', [])
            if findings:
                click.echo(f"\n🔍 Key Findings:")
                for i, finding in enumerate(findings[:5], 1):
                    click.echo(f"  {i}. {finding}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"research topic \"{topic}\"",
            error_code="RESEARCH_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@research.command()
@click.argument('post_id', type=int)
@click.option('--fact-check', is_flag=True, help='Perform fact checking')
@click.option('--verify-sources', is_flag=True, help='Verify source credibility')
@click.option('--add-citations', is_flag=True, help='Add missing citations')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def fact_check(post_id, fact_check, verify_sources, add_citations, server, json_output, verbose):
    """Fact check and verify content in a post"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"research fact-check {post_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"research fact-check {post_id}",
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
                command=f"research fact-check {post_id}",
                error_code="NOT_FOUND"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Perform fact checking
        if verbose:
            click.echo(f"Fact checking post {post_id}: {post['title']}")
        
        fact_check_result = integration.fact_check_content(
            post['content'],
            fact_check=fact_check,
            verify_sources=verify_sources,
            add_citations=add_citations
        )
        
        # Format output
        success_msg = AIFormatter.success_response(
            fact_check_result,
            f"Fact check complete for post {post_id}",
            command=f"research fact-check {post_id}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n🔍 Fact Check Results for Post {post_id}")
            click.echo("=" * 50)
            click.echo(f"Post: {post['title']}")
            
            # Overall assessment
            assessment = fact_check_result.get('overall_assessment', {})
            click.echo(f"\n📊 Overall Assessment:")
            click.echo(f"  Factual accuracy: {assessment.get('factual_accuracy', 'N/A')}/10")
            click.echo(f"  Source reliability: {assessment.get('source_reliability', 'N/A')}/10")
            click.echo(f"  Overall score: {assessment.get('overall_score', 'N/A')}/10")
            
            # Issues found
            issues = fact_check_result.get('issues', [])
            if issues:
                click.echo(f"\n⚠️  Issues Found ({len(issues)}):")
                for i, issue in enumerate(issues, 1):
                    severity = issue.get('severity', 'medium')
                    click.echo(f"  {i}. [{severity.upper()}] {issue.get('description', 'Unknown issue')}")
                    if issue.get('suggestion'):
                        click.echo(f"     Suggestion: {issue['suggestion']}")
            else:
                click.echo(f"\n✅ No factual issues found!")
            
            # Verified claims
            verified_claims = fact_check_result.get('verified_claims', [])
            if verified_claims:
                click.echo(f"\n✅ Verified Claims ({len(verified_claims)}):")
                for i, claim in enumerate(verified_claims[:5], 1):
                    click.echo(f"  {i}. {claim.get('claim', 'Unknown claim')}")
                    click.echo(f"     Source: {claim.get('source', 'N/A')}")
            
            # Suggested citations
            suggested_citations = fact_check_result.get('suggested_citations', [])
            if suggested_citations:
                click.echo(f"\n📚 Suggested Citations ({len(suggested_citations)}):")
                for i, citation in enumerate(suggested_citations[:3], 1):
                    click.echo(f"  {i}. {citation.get('text', 'Unknown citation')}")
                    click.echo(f"     Source: {citation.get('source', 'N/A')}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"research fact-check {post_id}",
            error_code="FACT_CHECK_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@research.command()
@click.argument('post_id', type=int)
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def verify_sources(post_id, server, json_output, verbose):
    """Verify sources cited in a post"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"research verify-sources {post_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"research verify-sources {post_id}",
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
                command=f"research verify-sources {post_id}",
                error_code="NOT_FOUND"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Verify sources
        if verbose:
            click.echo(f"Verifying sources for post {post_id}: {post['title']}")
        
        verification_result = integration.verify_sources(post['content'])
        
        # Format output
        success_msg = AIFormatter.success_response(
            verification_result,
            f"Source verification complete for post {post_id}",
            command=f"research verify-sources {post_id}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n🔍 Source Verification Results for Post {post_id}")
            click.echo("=" * 50)
            click.echo(f"Post: {post['title']}")
            
            # Summary
            summary = verification_result.get('summary', {})
            click.echo(f"\n📊 Summary:")
            click.echo(f"  Total sources found: {summary.get('total_sources', 0)}")
            click.echo(f"  Verified sources: {summary.get('verified_sources', 0)}")
            click.echo(f"  Unverified sources: {summary.get('unverified_sources', 0)}")
            click.echo(f"  Broken links: {summary.get('broken_links', 0)}")
            
            # Verified sources
            verified = verification_result.get('verified_sources', [])
            if verified:
                click.echo(f"\n✅ Verified Sources ({len(verified)}):")
                for i, source in enumerate(verified[:5], 1):
                    click.echo(f"  {i}. {source.get('title', 'Untitled')}")
                    click.echo(f"     {source.get('url', 'N/A')}")
                    click.echo(f"     Reliability: {source.get('reliability', 'N/A')}/10")
            
            # Unverified sources
            unverified = verification_result.get('unverified_sources', [])
            if unverified:
                click.echo(f"\n❓ Unverified Sources ({len(unverified)}):")
                for i, source in enumerate(unverified[:5], 1):
                    click.echo(f"  {i}. {source.get('title', 'Untitled')}")
                    click.echo(f"     {source.get('url', 'N/A')}")
                    click.echo(f"     Issue: {source.get('issue', 'Unknown')}")
            
            # Recommendations
            recommendations = verification_result.get('recommendations', [])
            if recommendations:
                click.echo(f"\n💡 Recommendations:")
                for i, rec in enumerate(recommendations, 1):
                    click.echo(f"  {i}. {rec}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"research verify-sources {post_id}",
            error_code="SOURCE_VERIFICATION_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@research.command()
@click.argument('topic')
@click.option('--count', type=int, default=5, help='Number of research questions to generate')
@click.option('--difficulty', default='medium', help='Difficulty level (easy, medium, hard)')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def questions(topic, count, difficulty, server, json_output, verbose):
    """Generate research questions for a topic"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"research questions \"{topic}\"",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"research questions \"{topic}\"",
            error_code="CONFIG_NOT_FOUND"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    try:
        # Get server config (minimal client needed for AI)
        server_config = config.get_server(server)
        
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
        
        # Generate research questions
        if verbose:
            click.echo(f"Generating {count} research questions for: {topic}")
        
        questions_result = integration.generate_research_questions(
            topic=topic,
            count=count,
            difficulty=difficulty
        )
        
        # Format output
        success_msg = AIFormatter.success_response(
            questions_result,
            f"Generated {len(questions_result.get('questions', []))} research questions",
            command=f"research questions \"{topic}\""
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n🤔 Research Questions: {topic}")
            click.echo("=" * 50)
            click.echo(f"Difficulty: {difficulty}")
            click.echo(f"Number of questions: {len(questions_result.get('questions', []))}")
            
            questions = questions_result.get('questions', [])
            for i, question in enumerate(questions, 1):
                click.echo(f"\n{i}. {question.get('question', 'Untitled')}")
                if question.get('description'):
                    click.echo(f"   {question['description']}")
                click.echo(f"   Category: {question.get('category', 'General')}")
                click.echo(f"   Difficulty: {question.get('difficulty', difficulty)}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"research questions \"{topic}\"",
            error_code="QUESTIONS_GENERATION_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@research.command()
@click.argument('topic')
@click.option('--count', type=int, default=10, help='Number of sources to find')
@click.option('--type', 'source_type', help='Source type (academic, news, books, web)')
@click.option('--recency', default='any', help='Recency filter (recent, last_year, last_5_years, any)')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def sources(topic, count, source_type, recency, server, json_output, verbose):
    """Find research sources for a topic"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"research sources \"{topic}\"",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"research sources \"{topic}\"",
            error_code="CONFIG_NOT_FOUND"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    try:
        # Get server config (minimal client needed for AI)
        server_config = config.get_server(server)
        
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
        
        # Find sources
        if verbose:
            type_str = f" of type {source_type}" if source_type else ""
            recency_str = f" from {recency}" if recency != 'any' else ""
            click.echo(f"Finding {count} sources{type_str}{recency_str} for: {topic}")
        
        sources_result = integration.find_research_sources(
            topic=topic,
            count=count,
            source_type=source_type,
            recency=recency
        )
        
        # Format output
        success_msg = AIFormatter.success_response(
            sources_result,
            f"Found {len(sources_result.get('sources', []))} research sources",
            command=f"research sources \"{topic}\""
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n📚 Research Sources: {topic}")
            click.echo("=" * 50)
            if source_type:
                click.echo(f"Source type: {source_type}")
            if recency != 'any':
                click.echo(f"Recency: {recency}")
            
            sources = sources_result.get('sources', [])
            if not sources:
                click.echo("No sources found matching the criteria.")
                return
            
            for i, source in enumerate(sources, 1):
                click.echo(f"\n{i}. {source.get('title', 'Untitled')}")
                click.echo(f"   Author(s): {source.get('authors', 'N/A')}")
                click.echo(f"   Publication: {source.get('publication', 'N/A')}")
                click.echo(f"   Year: {source.get('year', 'N/A')}")
                click.echo(f"   Type: {source.get('type', 'Unknown')}")
                click.echo(f"   URL: {source.get('url', 'N/A')}")
                if source.get('description'):
                    desc = source['description'][:150] + '...' if len(source['description']) > 150 else source['description']
                    click.echo(f"   Description: {desc}")
                if source.get('relevance_score'):
                    click.echo(f"   Relevance: {source['relevance_score']:.2f}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"research sources \"{topic}\"",
            error_code="SOURCES_SEARCH_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
