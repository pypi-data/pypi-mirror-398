"""AI Content Translator - Translate WordPress content to multiple languages"""

import click
from typing import Dict, Any, List, Optional

from praisonaiwp.ai import AI_AVAILABLE
from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.ai_formatter import AIFormatter


@click.group()
def translate():
    """AI-powered content translation for WordPress"""
    pass


@translate.command()
@click.argument('post_id', type=int)
@click.option('--to', 'target_langs', required=True, help='Target languages (comma-separated: es,fr,de,zh)')
@click.option('--create-new', is_flag=True, help='Create new posts for translations')
@click.option('--preserve-formatting', is_flag=True, default=True, help='Preserve HTML/Gutenberg formatting')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def post(post_id, target_langs, create_new, preserve_formatting, server, json_output, verbose):
    """Translate a WordPress post to multiple languages"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"translate post {post_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"translate post {post_id}",
            error_code="CONFIG_NOT_FOUND"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    try:
        # Parse target languages
        languages = [lang.strip().lower() for lang in target_langs.split(',')]
        
        # Language mapping
        lang_map = {
            'es': 'Spanish',
            'fr': 'French', 
            'de': 'German',
            'zh': 'Chinese',
            'ja': 'Japanese',
            'ko': 'Korean',
            'pt': 'Portuguese',
            'it': 'Italian',
            'ru': 'Russian',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'th': 'Thai',
            'vi': 'Vietnamese',
            'nl': 'Dutch',
            'sv': 'Swedish',
            'da': 'Danish',
            'no': 'Norwegian',
            'fi': 'Finnish',
            'pl': 'Polish',
            'tr': 'Turkish'
        }
        
        # Validate languages
        invalid_langs = [lang for lang in languages if lang not in lang_map]
        if invalid_langs:
            error_msg = AIFormatter.error_response(
                f"Invalid languages: {', '.join(invalid_langs)}. Supported: {', '.join(lang_map.keys())}",
                command=f"translate post {post_id}",
                error_code="INVALID_LANGUAGE"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return
        
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
                command=f"translate post {post_id}",
                error_code="NOT_FOUND"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        original_title = post['title']
        original_content = post['content']
        
        results = {
            'original_post_id': post_id,
            'original_title': original_title,
            'translations': [],
            'created_posts': []
        }
        
        # Translate to each language
        for lang in languages:
            if verbose:
                click.echo(f"Translating to {lang_map[lang]}...")
            
            try:
                # Translate content
                translation = integration.translate_content(
                    original_title,
                    original_content,
                    target_language=lang,
                    preserve_formatting=preserve_formatting
                )
                
                translation_result = {
                    'language': lang,
                    'language_name': lang_map[lang],
                    'translated_title': translation['title'],
                    'translated_content': translation['content'],
                    'confidence': translation.get('confidence', 0.95)
                }
                
                # Create new post if requested
                if create_new:
                    if verbose:
                        click.echo(f"Creating new post in {lang_map[lang]}...")
                    
                    new_post_data = {
                        'title': translation['title'],
                        'content': translation['content'],
                        'status': 'draft',
                        'type': post.get('type', 'post'),
                        'author': post.get('author'),
                        'category': post.get('category'),
                        'tags': post.get('tags', []) + [f'translated-{lang}']
                    }
                    
                    new_post = wp_client.create_post(**new_post_data)
                    translation_result['new_post_id'] = new_post.get('id')
                    results['created_posts'].append(new_post.get('id'))
                
                results['translations'].append(translation_result)
                
                if verbose:
                    status = "✓ Created" if create_new else "✓ Translated"
                    click.echo(f"  {status} {lang_map[lang]} (confidence: {translation.get('confidence', 0.95):.2f})")
                
            except Exception as e:
                if verbose:
                    click.echo(f"  ✗ Failed to translate to {lang_map[lang]}: {str(e)}")
                
                translation_result = {
                    'language': lang,
                    'language_name': lang_map[lang],
                    'error': str(e)
                }
                results['translations'].append(translation_result)
        
        # Format output
        success_msg = AIFormatter.success_response(
            results,
            f"Translated post {post_id} to {len(languages)} languages",
            command=f"translate post {post_id}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n✅ Translation complete for post {post_id}")
            click.echo("=" * 60)
            click.echo(f"Target languages: {', '.join([lang_map[lang] for lang in languages])}")
            
            successful_translations = [t for t in results['translations'] if 'error' not in t]
            click.echo(f"Successful translations: {len(successful_translations)}")
            
            if create_new:
                click.echo(f"New posts created: {len(results['created_posts'])}")
                if results['created_posts']:
                    click.echo(f"New post IDs: {', '.join(map(str, results['created_posts']))}")
            
            click.echo(f"\n📝 Translation Results:")
            for translation in results['translations']:
                if 'error' in translation:
                    click.echo(f"  ❌ {translation['language_name']}: {translation['error']}")
                else:
                    status = "Created" if create_new else "Translated"
                    confidence = translation.get('confidence', 0.95)
                    click.echo(f"  ✅ {translation['language_name']}: {status} (confidence: {confidence:.2f})")
                    if create_new and 'new_post_id' in translation:
                        click.echo(f"     New Post ID: {translation['new_post_id']}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"translate post {post_id}",
            error_code="TRANSLATION_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@translate.command()
@click.option('--posts', help='Post IDs or range (e.g., "1,2,3" or "1-10")')
@click.option('--category', help='Translate all posts in category')
@click.option('--status', default='publish', help='Post status filter')
@click.option('--limit', type=int, default=10, help='Maximum number of posts to translate')
@click.option('--to', 'target_langs', required=True, help='Target languages (comma-separated)')
@click.option('--create-new', is_flag=True, help='Create new posts for translations')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def batch(posts, category, status, limit, target_langs, create_new, server, json_output, verbose):
    """Translate multiple posts in batch"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command="translate batch",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command="translate batch",
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
        
        # Get posts to translate
        posts_to_translate = []
        
        if posts:
            # Parse post IDs or range
            if '-' in posts:
                # Range like "1-10"
                start, end = map(int, posts.split('-'))
                posts_to_translate = list(range(start, end + 1))
            else:
                # Comma-separated list
                posts_to_translate = [int(p.strip()) for p in posts.split(',')]
        
        elif category:
            # Get posts by category
            if verbose:
                click.echo(f"Finding posts in category: {category}")
            
            category_posts = wp_client.get_posts(category=category, status=status, limit=limit)
            posts_to_translate = [post['id'] for post in category_posts]
        
        else:
            # Get recent posts
            if verbose:
                click.echo(f"Finding recent posts (limit: {limit})")
            
            recent_posts = wp_client.get_posts(status=status, limit=limit)
            posts_to_translate = [post['id'] for post in recent_posts]
        
        if not posts_to_translate:
            error_msg = AIFormatter.error_response(
                "No posts found to translate",
                command="translate batch",
                error_code="NO_POSTS_FOUND"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return
        
        # Parse target languages
        languages = [lang.strip().lower() for lang in target_langs.split(',')]
        
        results = {
            'total_posts': len(posts_to_translate),
            'target_languages': languages,
            'translations': [],
            'summary': {
                'successful': 0,
                'failed': 0,
                'created_posts': 0
            }
        }
        
        # Translate each post
        for i, post_id in enumerate(posts_to_translate, 1):
            if verbose:
                click.echo(f"\n[{i}/{len(posts_to_translate)}] Translating post {post_id}...")
            
            try:
                # Get post content
                post = wp_client.get_post(post_id)
                if not post:
                    if verbose:
                        click.echo(f"  Post {post_id} not found, skipping...")
                    continue
                
                # Import AI integration
                from praisonaiwp.ai.integration import PraisonAIWPIntegration
                integration = PraisonAIWPIntegration(wp_client, verbose=0)
                
                # Translate to each language
                post_translations = []
                for lang in languages:
                    try:
                        translation = integration.translate_content(
                            post['title'],
                            post['content'],
                            target_language=lang,
                            preserve_formatting=True
                        )
                        
                        # Create new post if requested
                        new_post_id = None
                        if create_new:
                            new_post_data = {
                                'title': translation['title'],
                                'content': translation['content'],
                                'status': 'draft',
                                'type': post.get('type', 'post'),
                                'author': post.get('author'),
                                'category': post.get('category'),
                                'tags': post.get('tags', []) + [f'translated-{lang}']
                            }
                            
                            new_post = wp_client.create_post(**new_post_data)
                            new_post_id = new_post.get('id')
                            results['summary']['created_posts'] += 1
                        
                        post_translations.append({
                            'language': lang,
                            'new_post_id': new_post_id,
                            'confidence': translation.get('confidence', 0.95)
                        })
                        
                    except Exception as e:
                        if verbose:
                            click.echo(f"    Failed to translate to {lang}: {str(e)}")
                        post_translations.append({
                            'language': lang,
                            'error': str(e)
                        })
                
                results['translations'].append({
                    'post_id': post_id,
                    'title': post['title'],
                    'translations': post_translations
                })
                
                successful_langs = [t for t in post_translations if 'error' not in t]
                if successful_langs:
                    results['summary']['successful'] += 1
                else:
                    results['summary']['failed'] += 1
                
                if verbose:
                    click.echo(f"  ✓ Translated {len(successful_langs)}/{len(languages)} languages")
                
            except Exception as e:
                if verbose:
                    click.echo(f"  ✗ Failed to translate post {post_id}: {str(e)}")
                
                results['translations'].append({
                    'post_id': post_id,
                    'error': str(e)
                })
                results['summary']['failed'] += 1
        
        # Format output
        success_msg = AIFormatter.success_response(
            results,
            f"Batch translation complete: {results['summary']['successful']}/{results['total_posts']} posts successful",
            command="translate batch"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n✅ Batch Translation Complete")
            click.echo("=" * 50)
            click.echo(f"Total posts processed: {results['total_posts']}")
            click.echo(f"Successful translations: {results['summary']['successful']}")
            click.echo(f"Failed translations: {results['summary']['failed']}")
            if create_new:
                click.echo(f"New posts created: {results['summary']['created_posts']}")
            
            click.echo(f"\n📊 Results Summary:")
            for result in results['translations']:
                if 'error' in result:
                    click.echo(f"  ❌ Post {result['post_id']}: {result['error']}")
                else:
                    successful_langs = [t for t in result['translations'] if 'error' not in t]
                    click.echo(f"  ✅ Post {result['post_id']}: {len(successful_langs)}/{len(languages)} languages")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command="translate batch",
            error_code="BATCH_TRANSLATION_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@translate.command()
@click.argument('text')
@click.option('--to', 'target_lang', required=True, help='Target language (es,fr,de,zh,etc.)')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def text(text, target_lang, server, json_output, verbose):
    """Translate a text string to target language"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"translate text \"{text[:50]}...\"",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"translate text \"{text[:50]}...\"",
            error_code="CONFIG_NOT_FOUND"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    try:
        # Language mapping
        lang_map = {
            'es': 'Spanish', 'fr': 'French', 'de': 'German', 'zh': 'Chinese',
            'ja': 'Japanese', 'ko': 'Korean', 'pt': 'Portuguese', 'it': 'Italian',
            'ru': 'Russian', 'ar': 'Arabic', 'hi': 'Hindi', 'th': 'Thai',
            'vi': 'Vietnamese', 'nl': 'Dutch', 'sv': 'Swedish', 'da': 'Danish'
        }
        
        if target_lang not in lang_map:
            error_msg = AIFormatter.error_response(
                f"Invalid language: {target_lang}. Supported: {', '.join(lang_map.keys())}",
                command=f"translate text \"{text[:50]}...\"",
                error_code="INVALID_LANGUAGE"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return
        
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
        
        # Translate text
        if verbose:
            click.echo(f"Translating text to {lang_map[target_lang]}...")
        
        result = integration.translate_text(text, target_lang)
        
        # Format output
        success_msg = AIFormatter.success_response(
            {
                'original_text': text,
                'translated_text': result['text'],
                'target_language': target_lang,
                'language_name': lang_map[target_lang],
                'confidence': result.get('confidence', 0.95)
            },
            f"Text translated to {lang_map[target_lang]}",
            command=f"translate text \"{text[:50]}...\""
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n✅ Translation Complete")
            click.echo("=" * 30)
            click.echo(f"Original: {text}")
            click.echo(f"Translated ({lang_map[target_lang]}): {result['text']}")
            click.echo(f"Confidence: {result.get('confidence', 0.95):.2f}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"translate text \"{text[:50]}...\"",
            error_code="TEXT_TRANSLATION_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
