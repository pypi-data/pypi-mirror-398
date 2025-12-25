"""
MCP Prompts for WordPress Operations

Prompts are reusable templates that help LLMs perform common WordPress tasks.
They provide structured instructions for content creation and management.
"""

from typing import Dict, Optional


def create_blog_post_prompt(
    topic: str,
    style: str = "professional",
    length: str = "medium",
) -> str:
    """
    Generate a prompt for creating a blog post.

    Args:
        topic: The topic or subject of the blog post
        style: Writing style - 'professional', 'casual', 'technical', 'friendly'
        length: Post length - 'short' (300 words), 'medium' (600 words), 'long' (1200 words)

    Returns:
        Formatted prompt string for the LLM
    """
    length_words = {
        "short": "approximately 300 words",
        "medium": "approximately 600 words",
        "long": "approximately 1200 words",
    }

    style_descriptions = {
        "professional": "professional and authoritative tone, suitable for business audiences",
        "casual": "casual and conversational tone, engaging and easy to read",
        "technical": "technical and detailed, with accurate terminology and explanations",
        "friendly": "warm and friendly tone, approachable and encouraging",
    }

    word_count = length_words.get(length, length_words["medium"])
    style_desc = style_descriptions.get(style, style_descriptions["professional"])

    return f"""Create a WordPress blog post about: {topic}

**Requirements:**
- Length: {word_count}
- Style: {style_desc}
- Include an engaging introduction that hooks the reader
- Use clear headings and subheadings (H2, H3)
- Include a compelling conclusion with a call to action
- Format content with proper HTML tags for WordPress

**Structure:**
1. Introduction (hook the reader)
2. Main content (2-4 sections with headings)
3. Conclusion (summarize and call to action)

**After generating the content, use the create_post tool to publish it.**

Topic: {topic}
"""


def update_content_prompt(
    post_id: int,
    instructions: str,
) -> str:
    """
    Generate a prompt for updating existing content.

    Args:
        post_id: The ID of the post to update
        instructions: Specific instructions for the update

    Returns:
        Formatted prompt string for the LLM
    """
    return f"""Update WordPress post ID {post_id} with the following instructions:

**Instructions:**
{instructions}

**Steps:**
1. First, use the get_post tool to retrieve the current content of post {post_id}
2. Analyze the existing content
3. Apply the requested changes while maintaining the overall structure
4. Use the update_post tool to save the changes

**Guidelines:**
- Preserve the original voice and style unless instructed otherwise
- Maintain SEO-friendly formatting
- Keep existing headings structure if appropriate
- Ensure all links and media references remain intact

Post ID: {post_id}
"""


def bulk_update_prompt(
    operation: str,
    filters: Optional[Dict] = None,
) -> str:
    """
    Generate a prompt for bulk operations.

    Args:
        operation: The operation to perform - 'update_status', 'add_category', 'find_replace'
        filters: Filters to select posts (status, category, date_range, etc.)

    Returns:
        Formatted prompt string for the LLM
    """
    filters = filters or {}
    filter_str = "\n".join([f"- {k}: {v}" for k, v in filters.items()]) or "- No filters (all posts)"

    operation_instructions = {
        "update_status": """
**Operation: Update Post Status**
Change the status of matching posts (e.g., draft to publish, publish to private)
Use the update_post tool for each matching post.""",

        "add_category": """
**Operation: Add Category**
Add a category to matching posts without removing existing categories.
Use the set_post_categories tool for each matching post.""",

        "find_replace": """
**Operation: Find and Replace**
Find and replace text across matching posts.
Use the update_post tool with find_text and replace_text parameters.""",
    }

    instruction = operation_instructions.get(operation, f"**Operation: {operation}**")

    return f"""Perform a bulk operation on WordPress posts.

{instruction}

**Filters to apply:**
{filter_str}

**Steps:**
1. Use list_posts to find all posts matching the filters
2. Review the list of matching posts
3. For each post, apply the operation
4. Report the results

**Safety:**
- Always preview changes before applying
- Process posts in batches if there are many
- Report any errors encountered

Operation: {operation}
"""


def seo_optimize_prompt(post_id: int) -> str:
    """
    Generate a prompt for SEO optimization.

    Args:
        post_id: The ID of the post to optimize

    Returns:
        Formatted prompt string for the LLM
    """
    return f"""Optimize WordPress post ID {post_id} for SEO (Search Engine Optimization).

**Steps:**
1. Use get_post to retrieve the current content of post {post_id}
2. Analyze the content for SEO improvements

**SEO Checklist:**
- [ ] Title tag optimization (include primary keyword, 50-60 characters)
- [ ] Meta description (compelling, 150-160 characters)
- [ ] Heading structure (H1, H2, H3 hierarchy)
- [ ] Keyword placement (title, first paragraph, headings)
- [ ] Internal linking opportunities
- [ ] Image alt text optimization
- [ ] Content length (aim for 1000+ words for comprehensive topics)
- [ ] Readability (short paragraphs, bullet points)
- [ ] Call to action

**Recommendations:**
After analysis, provide specific recommendations for:
1. Title improvements
2. Content structure changes
3. Keyword optimization
4. Meta description suggestion
5. Internal linking suggestions

**Implementation:**
Use update_post to apply approved changes.

Post ID: {post_id}
"""
