"""
Convert HTML content to WordPress Gutenberg blocks.

This module provides safe conversion of HTML to Gutenberg block format.
It uses a conservative approach - only converting well-known, safe patterns
and wrapping everything else in wp:html blocks to prevent content loss.
"""

import re


class BlockConverter:
    """Convert HTML to WordPress Gutenberg blocks safely."""

    # Safe block mappings - only convert these well-known patterns
    SAFE_CONVERSIONS = {
        # Headings - most reliable
        'h1': {'block': 'heading', 'attrs': '{"level":1}'},
        'h2': {'block': 'heading', 'attrs': ''},
        'h3': {'block': 'heading', 'attrs': '{"level":3}'},
        'h4': {'block': 'heading', 'attrs': '{"level":4}'},
        'h5': {'block': 'heading', 'attrs': '{"level":5}'},
        'h6': {'block': 'heading', 'attrs': '{"level":6}'},
    }

    def __init__(self, html_content: str):
        """
        Initialize the converter.

        Args:
            html_content: HTML content to convert
        """
        self.html_content = html_content
        self.has_blocks = self._check_has_blocks()

    def _check_has_blocks(self) -> bool:
        """Check if content already has Gutenberg blocks."""
        return '<!-- wp:' in self.html_content

    def convert(self, safe_mode: bool = True) -> str:
        """
        Convert HTML to Gutenberg blocks.

        Args:
            safe_mode: If True, only convert safe patterns and wrap rest in wp:html.
                      If False, attempt more aggressive conversion (not recommended).

        Returns:
            Block-formatted content
        """
        # If already has blocks, return as-is
        if self.has_blocks:
            return self.html_content

        if safe_mode:
            return self._safe_convert()
        else:
            return self._aggressive_convert()

    def _safe_convert(self) -> str:
        """
        Safe conversion - only convert well-known patterns.

        This is the recommended approach. It converts:
        - Headings (h1-h6)
        - Simple paragraphs (no nested HTML)
        - Simple lists (ul/ol with li)
        - Code blocks (pre > code)

        Everything else is wrapped in <!-- wp:html --> to preserve it exactly.
        """
        content = self.html_content

        # Step 1: Convert headings (most reliable)
        for tag, config in self.SAFE_CONVERSIONS.items():
            pattern = f'<{tag}([^>]*)>(.*?)</{tag}>'
            attrs_str = f' {config["attrs"]}' if config["attrs"] else ''
            replacement = f'<!-- wp:{config["block"]}{attrs_str} -->\n<{tag} class="wp-block-{config["block"]}"\\1>\\2</{tag}>\n<!-- /wp:{config["block"]} -->'
            content = re.sub(pattern, replacement, content, flags=re.DOTALL | re.IGNORECASE)

        # Step 2: Convert simple paragraphs (no nested block-level elements)
        # Only convert <p> tags that don't contain other block elements
        def convert_paragraph(match):
            attrs = match.group(1)
            inner = match.group(2)

            # Check if paragraph contains block-level elements
            block_elements = ['<div', '<section', '<article', '<header', '<footer', '<nav', '<aside', '<main']
            if any(elem in inner for elem in block_elements):
                # Don't convert - might be complex HTML
                return match.group(0)

            return f'<!-- wp:paragraph -->\n<p{attrs}>{inner}</p>\n<!-- /wp:paragraph -->'

        content = re.sub(
            r'<p([^>]*)>(.*?)</p>',
            convert_paragraph,
            content,
            flags=re.DOTALL | re.IGNORECASE
        )

        # Step 3: Convert code blocks (pre > code)
        def convert_code_block(match):
            code_attrs = match.group(1)
            code_content = match.group(2)

            # Extract language if present
            lang_match = re.search(r'class=["\'](?:language-)?(\w+)["\']', code_attrs)
            lang = lang_match.group(1) if lang_match else ''

            if lang:
                return f'<!-- wp:code -->\n<pre class="wp-block-code"><code class="language-{lang}">{code_content}</code></pre>\n<!-- /wp:code -->'
            else:
                return f'<!-- wp:code -->\n<pre class="wp-block-code"><code>{code_content}</code></pre>\n<!-- /wp:code -->'

        content = re.sub(
            r'<pre[^>]*><code([^>]*)>(.*?)</code></pre>',
            convert_code_block,
            content,
            flags=re.DOTALL | re.IGNORECASE
        )

        # Step 4: Convert simple unordered lists
        def convert_list(match):
            list_tag = match.group(1)  # ul or ol
            attrs = match.group(2)
            inner = match.group(3)

            # Check if list is simple (no nested lists or complex HTML)
            if '<ul' in inner or '<ol' in inner or '<div' in inner:
                # Complex list - don't convert
                return match.group(0)

            block_type = 'list' if list_tag == 'ul' else 'list'
            attrs_str = ' {"ordered":true}' if list_tag == 'ol' else ''

            return f'<!-- wp:{block_type}{attrs_str} -->\n<{list_tag} class="wp-block-list"{attrs}>{inner}</{list_tag}>\n<!-- /wp:{block_type} -->'

        content = re.sub(
            r'<(ul|ol)([^>]*)>(.*?)</\1>',
            convert_list,
            content,
            flags=re.DOTALL | re.IGNORECASE
        )

        # Step 5: Wrap any remaining unconverted HTML blocks in wp:html
        # This preserves custom HTML, CSS, JavaScript, etc.
        content = self._wrap_remaining_html(content)

        return content

    def _wrap_remaining_html(self, content: str) -> str:
        """
        Wrap any remaining unconverted HTML in wp:html blocks.

        This ensures nothing breaks - custom HTML, CSS, JS all preserved.
        """
        # Find blocks of HTML that aren't already in Gutenberg blocks
        lines = content.split('\n')
        result = []
        in_block = False
        html_buffer = []

        for line in lines:
            stripped = line.strip()

            # Check if we're in a Gutenberg block
            if stripped.startswith('<!-- wp:'):
                # Flush any HTML buffer
                if html_buffer:
                    html_content = '\n'.join(html_buffer)
                    if html_content.strip():
                        result.append(f'<!-- wp:html -->\n{html_content}\n<!-- /wp:html -->')
                    html_buffer = []

                in_block = True
                result.append(line)
            elif stripped.startswith('<!-- /wp:'):
                in_block = False
                result.append(line)
            elif in_block:
                # Inside a block, keep as-is
                result.append(line)
            else:
                # Outside blocks - check if it's HTML
                if stripped and not stripped.startswith('<!--'):
                    html_buffer.append(line)
                elif not stripped:
                    # Empty line
                    if html_buffer:
                        result.append(line)
                    else:
                        html_buffer.append(line)

        # Flush remaining HTML buffer
        if html_buffer:
            html_content = '\n'.join(html_buffer)
            if html_content.strip():
                result.append(f'<!-- wp:html -->\n{html_content}\n<!-- /wp:html -->')

        return '\n'.join(result)

    def _aggressive_convert(self) -> str:
        """
        Aggressive conversion - attempts to convert more patterns.

        WARNING: This may break complex HTML. Use with caution.
        Not recommended for production use.
        """
        # Start with safe conversion
        content = self._safe_convert()

        # TODO: Add more aggressive patterns here if needed
        # For now, safe mode is recommended

        return content


def convert_to_blocks(html_content: str, safe_mode: bool = True) -> str:
    """
    Convert HTML content to WordPress Gutenberg blocks.

    Args:
        html_content: HTML content to convert
        safe_mode: If True, only convert safe patterns (recommended)

    Returns:
        Block-formatted content

    Example:
        >>> html = '<h2>Title</h2><p>Content</p>'
        >>> blocks = convert_to_blocks(html)
        >>> print(blocks)
        <!-- wp:heading -->
        <h2 class="wp-block-heading">Title</h2>
        <!-- /wp:heading -->
        <!-- wp:paragraph -->
        <p>Content</p>
        <!-- /wp:paragraph -->
    """
    converter = BlockConverter(html_content)
    return converter.convert(safe_mode=safe_mode)


def has_blocks(content: str) -> bool:
    """
    Check if content already has Gutenberg blocks.

    Args:
        content: Content to check

    Returns:
        True if content has blocks, False otherwise
    """
    return '<!-- wp:' in content
