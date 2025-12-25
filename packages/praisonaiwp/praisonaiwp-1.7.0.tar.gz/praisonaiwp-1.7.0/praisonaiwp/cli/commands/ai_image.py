"""AI Image Generator & Optimizer - Generate and optimize images for WordPress posts"""

import click
from typing import Dict, Any, List, Optional
import os

from praisonaiwp.ai import AI_AVAILABLE
from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.ai_formatter import AIFormatter


@click.group()
def image():
    """AI-powered image generation and optimization"""
    pass


@image.command()
@click.argument('prompt')
@click.option('--style', default='photorealistic', help='Image style (photorealistic, digital_art, illustration, 3d_render)')
@click.option('--size', default='1024x1024', help='Image size (256x256, 512x512, 1024x1024, 1792x1024)')
@click.option('--quality', default='standard', help='Image quality (standard, hd)')
@click.option('--count', type=int, default=1, help='Number of images to generate')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def generate(prompt, style, size, quality, count, server, json_output, verbose):
    """Generate AI images using DALL-E"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"image generate \"{prompt[:50]}...\"",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"image generate \"{prompt[:50]}...\"",
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
        
        # Generate images
        if verbose:
            click.echo(f"Generating {count} images with prompt: {prompt}")
            click.echo(f"Style: {style} | Size: {size} | Quality: {quality}")
        
        images_result = integration.generate_images(
            prompt=prompt,
            style=style,
            size=size,
            quality=quality,
            count=count
        )
        
        # Format output
        success_msg = AIFormatter.success_response(
            images_result,
            f"Generated {len(images_result.get('images', []))} images",
            command=f"image generate \"{prompt[:50]}...\""
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n🎨 Generated Images")
            click.echo("=" * 50)
            click.echo(f"Prompt: {prompt}")
            click.echo(f"Style: {style} | Size: {size} | Quality: {quality}")
            
            images = images_result.get('images', [])
            for i, image in enumerate(images, 1):
                click.echo(f"\n{i}. Image {image.get('id', 'Unknown')}")
                click.echo(f"   URL: {image.get('url', 'N/A')}")
                click.echo(f"   Size: {image.get('size', 'N/A')}")
                click.echo(f"   Revised prompt: {image.get('revised_prompt', 'N/A')}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"image generate \"{prompt[:50]}...\"",
            error_code="IMAGE_GENERATION_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@image.command()
@click.argument('media_id', type=int)
@click.option('--compress', is_flag=True, help='Compress image')
@click.option('--webp', is_flag=True, help='Convert to WebP format')
@click.option('--resize', help='Resize dimensions (e.g., 800x600)')
@click.option('--quality', type=int, default=85, help='Compression quality (1-100)')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def optimize(media_id, compress, webp, resize, quality, server, json_output, verbose):
    """Optimize images for web performance"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"image optimize {media_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"image optimize {media_id}",
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
        
        # Get media item
        media_item = wp_client.get_media_item(media_id)
        if not media_item:
            error_msg = AIFormatter.error_response(
                f"Media item with ID {media_id} not found",
                command=f"image optimize {media_id}",
                error_code="NOT_FOUND"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Optimize image
        if verbose:
            click.echo(f"Optimizing media item {media_id}: {media_item.get('title', 'Untitled')}")
        
        optimization_options = {
            'compress': compress,
            'webp': webp,
            'quality': quality
        }
        if resize:
            optimization_options['resize'] = resize
        
        optimization_result = integration.optimize_image(
            media_id,
            **optimization_options
        )
        
        # Format output
        success_msg = AIFormatter.success_response(
            optimization_result,
            f"Optimized media item {media_id}",
            command=f"image optimize {media_id}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n⚡ Image Optimization Complete")
            click.echo("=" * 50)
            click.echo(f"Media ID: {media_id}")
            click.echo(f"Original file: {media_item.get('filename', 'N/A')}")
            
            # Show optimization results
            if 'original_size' in optimization_result and 'optimized_size' in optimization_result:
                original_size = optimization_result['original_size']
                optimized_size = optimization_result['optimized_size']
                savings = original_size - optimized_size
                savings_percent = (savings / original_size) * 100 if original_size > 0 else 0
                
                click.echo(f"\n📊 Size Reduction:")
                click.echo(f"  Original: {original_size:,} bytes")
                click.echo(f"  Optimized: {optimized_size:,} bytes")
                click.echo(f"  Savings: {savings:,} bytes ({savings_percent:.1f}%)")
            
            # Show new formats
            new_formats = optimization_result.get('new_formats', [])
            if new_formats:
                click.echo(f"\n📄 New Formats:")
                for fmt in new_formats:
                    click.echo(f"  • {fmt.get('format', 'Unknown')}: {fmt.get('url', 'N/A')}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"image optimize {media_id}",
            error_code="IMAGE_OPTIMIZATION_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@image.command()
@click.argument('media_id', type=int)
@click.option('--length', default='medium', help='Alt text length (short, medium, long)')
@click.option('--style', default='descriptive', help='Alt text style (descriptive, functional, seo)')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def alt_text(media_id, length, style, server, json_output, verbose):
    """Generate alt text for images using AI vision"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"image alt-text {media_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"image alt-text {media_id}",
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
        
        # Get media item
        media_item = wp_client.get_media_item(media_id)
        if not media_item:
            error_msg = AIFormatter.error_response(
                f"Media item with ID {media_id} not found",
                command=f"image alt-text {media_id}",
                error_code="NOT_FOUND"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Generate alt text
        if verbose:
            click.echo(f"Generating alt text for media item {media_id}")
        
        alt_text_result = integration.generate_alt_text(
            media_id,
            length=length,
            style=style
        )
        
        # Format output
        success_msg = AIFormatter.success_response(
            alt_text_result,
            f"Generated alt text for media item {media_id}",
            command=f"image alt-text {media_id}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n🏷️  Alt Text Generated")
            click.echo("=" * 50)
            click.echo(f"Media ID: {media_id}")
            click.echo(f"File: {media_item.get('filename', 'N/A')}")
            
            alt_text = alt_text_result.get('alt_text', '')
            confidence = alt_text_result.get('confidence', 0)
            
            click.echo(f"\nGenerated Alt Text ({length}, {style}):")
            click.echo(f"  {alt_text}")
            click.echo(f"\nConfidence: {confidence:.2f}")
            
            # Show detected objects
            objects = alt_text_result.get('detected_objects', [])
            if objects:
                click.echo(f"\n🔍 Detected Objects:")
                for obj in objects[:5]:
                    click.echo(f"  • {obj}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"image alt-text {media_id}",
            error_code="ALT_TEXT_GENERATION_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@image.command()
@click.argument('post_id', type=int)
@click.option('--style', default='photorealistic', help='Image style')
@click.option('--count', type=int, default=3, help='Number of suggestions')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def suggest_featured(post_id, style, count, server, json_output, verbose):
    """Suggest featured images for a post"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"image suggest-featured {post_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"image suggest-featured {post_id}",
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
                command=f"image suggest-featured {post_id}",
                error_code="NOT_FOUND"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Generate featured image suggestions
        if verbose:
            click.echo(f"Generating {count} featured image suggestions for post {post_id}")
        
        suggestions = integration.suggest_featured_images(
            post['title'],
            post['content'],
            style=style,
            count=count
        )
        
        # Format output
        success_msg = AIFormatter.success_response(
            suggestions,
            f"Generated {len(suggestions.get('suggestions', []))} featured image suggestions",
            command=f"image suggest-featured {post_id}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n🖼️ Featured Image Suggestions for Post {post_id}")
            click.echo("=" * 50)
            click.echo(f"Post: {post['title']}")
            
            suggestion_list = suggestions.get('suggestions', [])
            for i, suggestion in enumerate(suggestion_list, 1):
                click.echo(f"\n{i}. {suggestion.get('prompt', 'Untitled')}")
                click.echo(f"   Reason: {suggestion.get('reason', 'N/A')}")
                click.echo(f"   Relevance: {suggestion.get('relevance_score', 0):.2f}")
                if suggestion.get('generated_image'):
                    img = suggestion['generated_image']
                    click.echo(f"   Generated URL: {img.get('url', 'N/A')}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"image suggest-featured {post_id}",
            error_code="FEATURED_SUGGESTION_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@image.command()
@click.argument('post_id', type=int)
@click.option('--optimize', is_flag=True, help='Optimize all images in post')
@click.option('--add-alt-text', is_flag=True, help='Add alt text to all images')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def bulk_optimize(post_id, optimize, add_alt_text, server, json_output, verbose):
    """Bulk optimize all images in a post"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"image bulk-optimize {post_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"image bulk-optimize {post_id}",
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
                command=f"image bulk-optimize {post_id}",
                error_code="NOT_FOUND"
            )
            click.echo(AIFormatter.format_output(error_msg, json_output))
            return
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Extract images from post
        if verbose:
            click.echo(f"Extracting images from post {post_id}...")
        
        images = integration.extract_images_from_content(post['content'])
        
        if not images:
            success_msg = AIFormatter.success_response(
                {'message': 'No images found in post'},
                f"No images found in post {post_id}",
                command=f"image bulk-optimize {post_id}"
            )
            click.echo(AIFormatter.format_output(success_msg, json_output))
            return
        
        # Process images
        results = {
            'total_images': len(images),
            'processed_images': [],
            'summary': {
                'optimized': 0,
                'alt_text_added': 0,
                'errors': 0
            }
        }
        
        for image in images:
            if verbose:
                click.echo(f"Processing image: {image.get('src', 'Unknown')}")
            
            try:
                image_result = {
                    'src': image.get('src'),
                    'media_id': image.get('media_id'),
                    'actions': []
                }
                
                # Optimize image
                if optimize and image.get('media_id'):
                    optimization = integration.optimize_image(
                        image['media_id'],
                        compress=True,
                        webp=True,
                        quality=85
                    )
                    image_result['actions'].append('optimized')
                    image_result['optimization'] = optimization
                    results['summary']['optimized'] += 1
                
                # Add alt text
                if add_alt_text and image.get('media_id'):
                    alt_text = integration.generate_alt_text(
                        image['media_id'],
                        length='medium',
                        style='descriptive'
                    )
                    image_result['actions'].append('alt_text_added')
                    image_result['alt_text'] = alt_text
                    results['summary']['alt_text_added'] += 1
                
                results['processed_images'].append(image_result)
                
                if verbose:
                    actions_str = ', '.join(image_result['actions'])
                    click.echo(f"  ✓ {actions_str}")
                
            except Exception as e:
                if verbose:
                    click.echo(f"  ✗ Failed: {str(e)}")
                results['summary']['errors'] += 1
        
        # Format output
        success_msg = AIFormatter.success_response(
            results,
            f"Bulk optimized {results['summary']['optimized']} images and added alt text to {results['summary']['alt_text_added']} images",
            command=f"image bulk-optimize {post_id}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n⚡ Bulk Image Optimization Complete")
            click.echo("=" * 50)
            click.echo(f"Post: {post['title']}")
            click.echo(f"Total images: {results['total_images']}")
            click.echo(f"Optimized: {results['summary']['optimized']}")
            click.echo(f"Alt text added: {results['summary']['alt_text_added']}")
            click.echo(f"Errors: {results['summary']['errors']}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"image bulk-optimize {post_id}",
            error_code="BULK_OPTIMIZATION_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
