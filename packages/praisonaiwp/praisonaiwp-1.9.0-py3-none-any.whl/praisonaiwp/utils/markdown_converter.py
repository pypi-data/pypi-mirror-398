"""
Convert Markdown content to HTML or WordPress Gutenberg blocks.

This module provides conversion from Markdown to HTML and then to Gutenberg blocks.
"""

try:
    from markdown_it import MarkdownIt
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

from praisonaiwp.utils.block_converter import convert_to_blocks


def is_markdown(content: str) -> bool:
    """
    Detect if content is likely Markdown format.

    Args:
        content: Content to check

    Returns:
        True if content appears to be Markdown
    """
    # Check for common Markdown patterns
    markdown_patterns = [
        '# ',      # Headings
        '## ',
        '### ',
        '```',     # Code blocks
        '**',      # Bold
        '__',      # Bold alternative
        '*',       # Italic or list
        '_',       # Italic alternative
        '[',       # Links
        '](',      # Link URL
        '- ',      # Lists
        '* ',      # Lists alternative
        '1. ',     # Numbered lists
    ]

    # If content has Gutenberg blocks, it's not Markdown
    if '<!-- wp:' in content:
        return False

    # Count Markdown patterns
    pattern_count = sum(1 for pattern in markdown_patterns if pattern in content)

    # If we find multiple Markdown patterns, it's likely Markdown
    return pattern_count >= 3


def markdown_to_html(markdown_content: str, downgrade_h1: bool = True) -> str:
    """
    Convert Markdown to HTML.

    Args:
        markdown_content: Markdown content
        downgrade_h1: If True, convert H1 to H2 (since post title is H1)

    Returns:
        HTML content
    """
    if not MARKDOWN_AVAILABLE:
        # Fallback: return as-is if markdown-it not available
        return markdown_content

    md = MarkdownIt()
    html = md.render(markdown_content)

    # Downgrade H1 to H2 since WordPress post title is already H1
    if downgrade_h1:
        import re
        # Replace <h1> with <h2>
        html = re.sub(r'<h1(\s[^>]*)?>|<h1>', '<h2>', html)
        html = re.sub(r'</h1>', '</h2>', html)

    return html


def markdown_to_blocks(markdown_content: str) -> str:
    """
    Convert Markdown to WordPress Gutenberg blocks.

    Args:
        markdown_content: Markdown content

    Returns:
        Gutenberg block content
    """
    # First convert Markdown to HTML
    html_content = markdown_to_html(markdown_content)

    # Then convert HTML to Gutenberg blocks
    blocks = convert_to_blocks(html_content)

    return blocks


def auto_convert_content(content: str, to_blocks: bool = True) -> str:
    """
    Automatically detect and convert content format.

    Args:
        content: Content to convert
        to_blocks: If True, convert to Gutenberg blocks. If False, convert to HTML.

    Returns:
        Converted content
    """
    # Check if already has Gutenberg blocks
    if '<!-- wp:' in content:
        return content

    # Check if it's Markdown
    if is_markdown(content):
        if to_blocks:
            return markdown_to_blocks(content)
        else:
            return markdown_to_html(content)

    # If it's HTML, optionally convert to blocks
    if to_blocks and '<' in content and '>' in content:
        return convert_to_blocks(content)

    # Return as-is
    return content
