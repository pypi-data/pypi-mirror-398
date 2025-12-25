"""
Comprehensive tests for block_converter module.

Tests cover edge cases and scenarios that users/LLMs might forget:
- Already converted content
- Mixed HTML and blocks
- Empty/None content
- Malformed HTML
- Nested structures
- Special characters
- Custom HTML with CSS/JS
- Complex real-world scenarios
"""

from praisonaiwp.utils.block_converter import (
    BlockConverter,
    convert_to_blocks,
    has_blocks,
)


class TestHasBlocks:
    """Test has_blocks detection"""

    def test_has_blocks_true(self):
        """Test detection of existing blocks"""
        content = '<!-- wp:paragraph --><p>Test</p><!-- /wp:paragraph -->'
        assert has_blocks(content) is True

    def test_has_blocks_false(self):
        """Test detection of plain HTML"""
        content = '<p>Test</p>'
        assert has_blocks(content) is False

    def test_has_blocks_empty(self):
        """Test empty content"""
        assert has_blocks('') is False

    def test_has_blocks_partial(self):
        """Test partial block comment"""
        content = '<!-- wp: incomplete'
        assert has_blocks(content) is True  # Still detects wp: marker


class TestBasicConversions:
    """Test basic HTML to block conversions"""

    def test_simple_heading_h2(self):
        """Test H2 conversion"""
        html = '<h2>My Heading</h2>'
        result = convert_to_blocks(html)
        assert '<!-- wp:heading -->' in result
        assert '<h2 class="wp-block-heading">My Heading</h2>' in result
        assert '<!-- /wp:heading -->' in result

    def test_simple_heading_h3(self):
        """Test H3 conversion with level attribute"""
        html = '<h3>My Heading</h3>'
        result = convert_to_blocks(html)
        assert '<!-- wp:heading {"level":3} -->' in result
        assert '<h3 class="wp-block-heading">My Heading</h3>' in result

    def test_all_heading_levels(self):
        """Test all heading levels H1-H6"""
        for level in range(1, 7):
            html = f'<h{level}>Heading {level}</h{level}>'
            result = convert_to_blocks(html)
            assert '<!-- wp:heading' in result
            assert f'<h{level} class="wp-block-heading">Heading {level}</h{level}>' in result

    def test_simple_paragraph(self):
        """Test simple paragraph conversion"""
        html = '<p>Simple paragraph</p>'
        result = convert_to_blocks(html)
        assert '<!-- wp:paragraph -->' in result
        assert '<p>Simple paragraph</p>' in result
        assert '<!-- /wp:paragraph -->' in result

    def test_paragraph_with_inline_formatting(self):
        """Test paragraph with bold, italic, links"""
        html = '<p>Text with <strong>bold</strong>, <em>italic</em>, and <a href="#">link</a></p>'
        result = convert_to_blocks(html)
        assert '<!-- wp:paragraph -->' in result
        assert '<strong>bold</strong>' in result
        assert '<em>italic</em>' in result
        assert '<a href="#">link</a>' in result

    def test_code_block_with_language(self):
        """Test code block with language class"""
        html = '<pre><code class="language-python">print("hello")</code></pre>'
        result = convert_to_blocks(html)
        assert '<!-- wp:code -->' in result
        assert '<pre class="wp-block-code"><code class="language-python">print("hello")</code></pre>' in result

    def test_code_block_without_language(self):
        """Test code block without language"""
        html = '<pre><code>some code</code></pre>'
        result = convert_to_blocks(html)
        assert '<!-- wp:code -->' in result
        assert '<pre class="wp-block-code"><code>some code</code></pre>' in result

    def test_simple_unordered_list(self):
        """Test simple UL conversion"""
        html = '<ul><li>Item 1</li><li>Item 2</li></ul>'
        result = convert_to_blocks(html)
        assert '<!-- wp:list -->' in result
        assert '<ul class="wp-block-list">' in result
        assert '<li>Item 1</li>' in result

    def test_simple_ordered_list(self):
        """Test simple OL conversion"""
        html = '<ol><li>First</li><li>Second</li></ol>'
        result = convert_to_blocks(html)
        assert '<!-- wp:list {"ordered":true} -->' in result
        assert '<ol class="wp-block-list">' in result


class TestEdgeCases:
    """Test edge cases users/LLMs might forget"""

    def test_empty_content(self):
        """Test empty string"""
        result = convert_to_blocks('')
        assert result == ''

    def test_whitespace_only(self):
        """Test whitespace-only content"""
        result = convert_to_blocks('   \n  \t  ')
        # Should wrap in html block or return as-is
        assert isinstance(result, str)

    def test_already_converted_content(self):
        """Test content that already has blocks - should not double-convert"""
        html = '<!-- wp:paragraph --><p>Already converted</p><!-- /wp:paragraph -->'
        result = convert_to_blocks(html)
        assert result == html  # Should return unchanged

    def test_mixed_blocks_and_html(self):
        """Test content with some blocks and some HTML"""
        html = '<!-- wp:paragraph --><p>Block</p><!-- /wp:paragraph -->\n<p>Plain HTML</p>'
        result = convert_to_blocks(html)
        # Should preserve existing blocks
        assert '<!-- wp:paragraph --><p>Block</p><!-- /wp:paragraph -->' in result

    def test_malformed_html_unclosed_tags(self):
        """Test malformed HTML with unclosed tags"""
        html = '<p>Unclosed paragraph'
        result = convert_to_blocks(html)
        # Should not crash, wrap in html block
        assert isinstance(result, str)
        assert 'Unclosed paragraph' in result

    def test_malformed_html_mismatched_tags(self):
        """Test mismatched tags"""
        html = '<p>Start</div>'
        result = convert_to_blocks(html)
        # Should not crash
        assert isinstance(result, str)

    def test_special_characters_in_content(self):
        """Test special characters that might break regex"""
        html = '<p>Special chars: $100, 50% off, <>&"\'</p>'
        result = convert_to_blocks(html)
        assert '<!-- wp:paragraph -->' in result
        assert '$100' in result
        assert '50%' in result

    def test_unicode_characters(self):
        """Test Unicode characters"""
        html = '<h2>日本語 Título Тест 🎉</h2>'
        result = convert_to_blocks(html)
        assert '<!-- wp:heading -->' in result
        assert '日本語' in result
        assert 'Título' in result
        assert 'Тест' in result
        assert '🎉' in result

    def test_html_entities(self):
        """Test HTML entities"""
        html = '<p>&lt;script&gt;alert(&quot;test&quot;)&lt;/script&gt;</p>'
        result = convert_to_blocks(html)
        assert '<!-- wp:paragraph -->' in result
        assert '&lt;script&gt;' in result

    def test_multiline_content(self):
        """Test content spanning multiple lines"""
        html = '''<p>Line 1
Line 2
Line 3</p>'''
        result = convert_to_blocks(html)
        assert '<!-- wp:paragraph -->' in result
        assert 'Line 1' in result
        assert 'Line 3' in result


class TestComplexStructures:
    """Test complex HTML structures"""

    def test_nested_divs_not_converted(self):
        """Test nested divs are wrapped in html block, not converted"""
        html = '<div class="container"><div class="inner"><p>Nested</p></div></div>'
        result = convert_to_blocks(html)
        # Complex structure should be wrapped in html block
        assert '<!-- wp:html -->' in result or '<div class="container">' in result

    def test_paragraph_with_nested_div(self):
        """Test paragraph containing div - should not convert"""
        html = '<p><div class="special">Content</div></p>'
        result = convert_to_blocks(html)
        # Should not convert due to block element inside
        assert '<div class="special">Content</div>' in result

    def test_nested_lists_not_converted(self):
        """Test nested lists are not converted (complex structure)"""
        html = '<ul><li>Item 1<ul><li>Nested</li></ul></li></ul>'
        result = convert_to_blocks(html)
        # Should not convert nested list
        assert '<ul><li>Item 1<ul><li>Nested</li></ul></li></ul>' in result

    def test_table_wrapped_in_html_block(self):
        """Test table is wrapped in html block"""
        html = '<table><tr><td>Cell</td></tr></table>'
        result = convert_to_blocks(html)
        # Tables should be wrapped in html block
        assert '<table>' in result
        assert '<td>Cell</td>' in result

    def test_form_elements_preserved(self):
        """Test form elements are preserved"""
        html = '<form><input type="text" name="test"><button>Submit</button></form>'
        result = convert_to_blocks(html)
        assert '<form>' in result
        assert '<input' in result
        assert '<button>Submit</button>' in result


class TestCustomHTMLPreservation:
    """Test that custom HTML/CSS/JS is preserved"""

    def test_inline_styles_preserved(self):
        """Test inline styles are preserved"""
        html = '<div style="color: red; font-size: 20px;">Styled content</div>'
        result = convert_to_blocks(html)
        assert 'style="color: red; font-size: 20px;"' in result
        assert 'Styled content' in result

    def test_css_classes_preserved(self):
        """Test CSS classes are preserved"""
        html = '<div class="custom-class another-class">Content</div>'
        result = convert_to_blocks(html)
        assert 'class="custom-class another-class"' in result

    def test_data_attributes_preserved(self):
        """Test data attributes are preserved"""
        html = '<div data-id="123" data-type="custom">Content</div>'
        result = convert_to_blocks(html)
        assert 'data-id="123"' in result
        assert 'data-type="custom"' in result

    def test_script_tags_preserved(self):
        """Test script tags are preserved"""
        html = '<script>console.log("test");</script>'
        result = convert_to_blocks(html)
        assert '<script>' in result
        assert 'console.log' in result

    def test_style_tags_preserved(self):
        """Test style tags are preserved"""
        html = '<style>.custom { color: blue; }</style>'
        result = convert_to_blocks(html)
        assert '<style>' in result
        assert '.custom { color: blue; }' in result

    def test_iframe_preserved(self):
        """Test iframe is preserved"""
        html = '<iframe src="https://example.com" width="600" height="400"></iframe>'
        result = convert_to_blocks(html)
        assert '<iframe' in result
        assert 'src="https://example.com"' in result


class TestRealWorldScenarios:
    """Test real-world content scenarios"""

    def test_blog_post_structure(self):
        """Test typical blog post with mixed content"""
        html = '''
<h2>Introduction</h2>
<p>This is a blog post with <strong>bold text</strong>.</p>
<h3>Code Example</h3>
<pre><code class="language-python">
def hello():
    print("world")
</code></pre>
<p>More content here.</p>
'''
        result = convert_to_blocks(html)
        assert '<!-- wp:heading -->' in result
        assert '<!-- wp:heading {"level":3} -->' in result
        assert '<!-- wp:paragraph -->' in result
        assert '<!-- wp:code -->' in result
        assert 'language-python' in result

    def test_documentation_page(self):
        """Test documentation with lists and code"""
        html = '''
<h2>Installation</h2>
<p>Follow these steps:</p>
<ol>
<li>Download the package</li>
<li>Install dependencies</li>
</ol>
<pre><code class="language-bash">pip install package</code></pre>
'''
        result = convert_to_blocks(html)
        assert '<!-- wp:heading -->' in result
        assert '<!-- wp:paragraph -->' in result
        assert '<!-- wp:list {"ordered":true} -->' in result
        assert '<!-- wp:code -->' in result

    def test_landing_page_with_custom_html(self):
        """Test landing page with custom sections"""
        html = '''
<section class="hero">
    <div class="container">
        <h1>Welcome</h1>
        <p>Custom landing page</p>
    </div>
</section>
'''
        result = convert_to_blocks(html)
        # Custom sections should be preserved
        assert '<section class="hero">' in result
        assert '<div class="container">' in result

    def test_wordpress_shortcodes_preserved(self):
        """Test WordPress shortcodes are preserved"""
        html = '<p>Some text [gallery ids="1,2,3"] more text</p>'
        result = convert_to_blocks(html)
        assert '[gallery ids="1,2,3"]' in result

    def test_mixed_content_from_wysiwyg(self):
        """Test content from WYSIWYG editor"""
        html = '''
<p>Paragraph 1</p>
<p><br></p>
<p>Paragraph 2 with <a href="#">link</a></p>
<ul>
<li>List item</li>
</ul>
'''
        result = convert_to_blocks(html)
        assert '<!-- wp:paragraph -->' in result
        assert '<!-- wp:list -->' in result
        assert '<a href="#">link</a>' in result


class TestSafetyAndRobustness:
    """Test safety and robustness"""

    def test_very_long_content(self):
        """Test very long content doesn't crash"""
        html = '<p>' + 'A' * 10000 + '</p>'
        result = convert_to_blocks(html)
        assert '<!-- wp:paragraph -->' in result
        assert 'A' * 100 in result  # Check partial content

    def test_deeply_nested_html(self):
        """Test deeply nested HTML"""
        html = '<div>' * 50 + 'Content' + '</div>' * 50
        result = convert_to_blocks(html)
        # Should not crash
        assert 'Content' in result

    def test_multiple_consecutive_headings(self):
        """Test multiple headings in a row"""
        html = '<h2>Title 1</h2><h2>Title 2</h2><h3>Subtitle</h3>'
        result = convert_to_blocks(html)
        assert result.count('<!-- wp:heading -->') == 2
        assert result.count('<!-- wp:heading {"level":3} -->') == 1

    def test_empty_tags(self):
        """Test empty tags"""
        html = '<p></p><h2></h2><ul></ul>'
        result = convert_to_blocks(html)
        # Should handle empty tags gracefully
        assert isinstance(result, str)

    def test_comments_in_html(self):
        """Test HTML comments (not Gutenberg blocks)"""
        html = '<p>Text <!-- HTML comment --> more text</p>'
        result = convert_to_blocks(html)
        assert '<!-- HTML comment -->' in result
        assert '<!-- wp:paragraph -->' in result

    def test_cdata_sections(self):
        """Test CDATA sections"""
        html = '<p><![CDATA[Some data]]></p>'
        result = convert_to_blocks(html)
        assert 'CDATA' in result


class TestBlockConverterClass:
    """Test BlockConverter class directly"""

    def test_converter_initialization(self):
        """Test converter initialization"""
        converter = BlockConverter('<p>Test</p>')
        assert converter.html_content == '<p>Test</p>'
        assert converter.has_blocks is False

    def test_converter_detects_existing_blocks(self):
        """Test converter detects existing blocks"""
        html = '<!-- wp:paragraph --><p>Test</p><!-- /wp:paragraph -->'
        converter = BlockConverter(html)
        assert converter.has_blocks is True

    def test_safe_mode_default(self):
        """Test safe mode is default"""
        converter = BlockConverter('<p>Test</p>')
        result = converter.convert()
        assert '<!-- wp:paragraph -->' in result

    def test_aggressive_mode_not_recommended(self):
        """Test aggressive mode (not recommended)"""
        converter = BlockConverter('<p>Test</p>')
        result = converter.convert(safe_mode=False)
        # Should still work, just might be more aggressive
        assert isinstance(result, str)


class TestUserMistakes:
    """Test common user/LLM mistakes"""

    def test_forgot_to_close_paragraph(self):
        """User forgets to close <p> tag"""
        html = '<p>Forgot to close'
        result = convert_to_blocks(html)
        # Should not crash
        assert 'Forgot to close' in result

    def test_mixed_case_tags(self):
        """User uses mixed case tags"""
        html = '<P>Mixed Case</P><H2>Heading</H2>'
        result = convert_to_blocks(html)
        # Should handle case-insensitive
        assert 'Mixed Case' in result
        assert 'Heading' in result

    def test_extra_whitespace(self):
        """User adds extra whitespace"""
        html = '  <p>  Text with spaces  </p>  '
        result = convert_to_blocks(html)
        assert '<!-- wp:paragraph -->' in result

    def test_tabs_and_newlines(self):
        """User has tabs and newlines"""
        html = '\t<p>\n\tText\n</p>\n'
        result = convert_to_blocks(html)
        assert '<!-- wp:paragraph -->' in result

    def test_forgot_language_class_on_code(self):
        """User forgets language class on code block"""
        html = '<pre><code>code without language</code></pre>'
        result = convert_to_blocks(html)
        assert '<!-- wp:code -->' in result
        assert 'code without language' in result

    def test_using_br_for_spacing(self):
        """User uses <br> tags for spacing"""
        html = '<p>Line 1<br><br>Line 2</p>'
        result = convert_to_blocks(html)
        assert '<!-- wp:paragraph -->' in result
        assert '<br>' in result

    def test_nbsp_entities(self):
        """User has &nbsp; entities"""
        html = '<p>Text&nbsp;&nbsp;with&nbsp;spaces</p>'
        result = convert_to_blocks(html)
        assert '&nbsp;' in result


class TestIntegration:
    """Integration tests"""

    def test_full_article_conversion(self):
        """Test converting a full article"""
        html = '''
<h2>Article Title</h2>
<p>Introduction paragraph with <strong>bold</strong> text.</p>
<h3>Section 1</h3>
<p>Content for section 1.</p>
<ul>
<li>Point 1</li>
<li>Point 2</li>
</ul>
<h3>Code Example</h3>
<pre><code class="language-python">
def example():
    return "Hello"
</code></pre>
<p>Conclusion paragraph.</p>
'''
        result = convert_to_blocks(html)

        # Verify all conversions happened
        assert result.count('<!-- wp:heading -->') >= 1
        assert result.count('<!-- wp:heading {"level":3} -->') >= 2
        assert result.count('<!-- wp:paragraph -->') >= 3
        assert '<!-- wp:list -->' in result
        assert '<!-- wp:code -->' in result

        # Verify content preserved
        assert 'Article Title' in result
        assert '<strong>bold</strong>' in result
        assert 'language-python' in result
        assert 'Conclusion paragraph' in result

    def test_idempotent_conversion(self):
        """Test converting already converted content is idempotent"""
        html = '<h2>Test</h2><p>Content</p>'
        result1 = convert_to_blocks(html)
        result2 = convert_to_blocks(result1)
        # Second conversion should not change anything
        assert result1 == result2
