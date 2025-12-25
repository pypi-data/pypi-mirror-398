"""PraisonAI WordPress Integration"""
import logging
import time
from typing import Any, Dict, Optional

from praisonaiwp.ai import Agent, PraisonAIAgents, Task, check_ai_available
from praisonaiwp.ai.tools.wordpress_tools import WordPressTools
from praisonaiwp.ai.utils.validators import (
    validate_api_key,
    ContentValidator
)
from praisonaiwp.ai.utils.cost_tracker import CostTracker
from praisonaiwp.ai.utils.retry import retry_with_backoff
from praisonaiwp.ai.utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class PraisonAIWPIntegration:
    """Integration class for PraisonAI and WordPress"""

    def __init__(self, wp_client, **config):
        """Initialize the integration

        Args:
            wp_client: WordPress client instance
            **config: Configuration options
                - model: LLM model to use (default: gpt-4o-mini)
                - verbose: Verbosity level (default: 0)
                - status: Default post status (default: draft)
                - validate_content: Validate generated content (default: True)
                - min_length: Minimum content length (default: 100)
                - max_length: Maximum content length (default: 10000)
                - enable_rate_limiting: Enable rate limiting (default: True)
                - max_requests: Max requests per time window (default: 10)
                - time_window: Time window in seconds (default: 60)
        """
        # Check if AI is available
        check_ai_available()

        # Validate API key
        validate_api_key()

        self.wp_client = wp_client
        self.config = config

        # Set defaults
        if 'model' not in self.config:
            self.config['model'] = 'gpt-4o-mini'
        if 'verbose' not in self.config:
            self.config['verbose'] = 0
        if 'status' not in self.config:
            self.config['status'] = 'draft'
        if 'validate_content' not in self.config:
            self.config['validate_content'] = True
        if 'min_length' not in self.config:
            self.config['min_length'] = 100
        if 'max_length' not in self.config:
            self.config['max_length'] = 10000
        if 'enable_rate_limiting' not in self.config:
            self.config['enable_rate_limiting'] = True

        # Create WordPress tools
        self.wp_tools = WordPressTools(wp_client)

        # Initialize utilities
        self.cost_tracker = CostTracker()
        self.content_validator = ContentValidator(
            min_length=self.config['min_length'],
            max_length=self.config['max_length']
        )

        # Initialize rate limiter if enabled
        self.rate_limiter = None
        if self.config['enable_rate_limiting']:
            self.rate_limiter = RateLimiter(
                max_requests=self.config.get('max_requests', 10),
                time_window=self.config.get('time_window', 60)
            )

        # State for callbacks
        self.current_title = None
        self.current_post_options = {}
        self.last_post_id = None
        self.last_generation_cost = None

    def _publish_callback(self, task_output):
        """Callback to publish content to WordPress

        Args:
            task_output: Task output from PraisonAI

        Returns:
            dict: Post ID and content
        """
        import json
        from praisonaiwp.utils.markdown_converter import auto_convert_content

        # Ensure SSH connection is established
        if not self.wp_client.ssh.client:
            self.wp_client.ssh.connect()

        # Auto-convert Markdown to Gutenberg blocks if needed
        content = auto_convert_content(task_output.raw, to_blocks=True)

        # Prepare post data
        post_data = {
            'post_title': self.current_title,
            'post_content': content,
            'post_status': self.config.get('status', 'draft')
        }

        # Add optional fields
        if self.current_post_options.get('post_type'):
            post_data['post_type'] = self.current_post_options['post_type']
        if self.current_post_options.get('author'):
            post_data['post_author'] = self.current_post_options['author']
        if self.current_post_options.get('excerpt'):
            post_data['post_excerpt'] = self.current_post_options['excerpt']
        if self.current_post_options.get('date'):
            post_data['post_date'] = self.current_post_options['date']
        if self.current_post_options.get('comment_status'):
            post_data['comment_status'] = self.current_post_options['comment_status']

        # Create post
        post_id = self.wp_client.create_post(**post_data)

        # Set categories if provided
        category = self.current_post_options.get('category')
        category_id = self.current_post_options.get('category_id')
        if category or category_id:
            try:
                if category_id:
                    self.wp_client.set_post_categories(post_id, category_id)
                else:
                    self.wp_client.set_post_categories(post_id, category)
                logger.info(f"Set categories: {category or category_id}")
            except Exception as e:
                logger.warning(f"Failed to set categories: {e}")

        # Set tags if provided
        if self.current_post_options.get('tags'):
            try:
                tags = self.current_post_options['tags']
                # Use wp-cli to set tags
                self.wp_client.wp('post', 'term', 'set', str(post_id), 'post_tag', tags.replace(',', ' '))
                logger.info(f"Set tags: {tags}")
            except Exception as e:
                logger.warning(f"Failed to set tags: {e}")

        # Set meta if provided
        if self.current_post_options.get('meta'):
            try:
                meta_data = json.loads(self.current_post_options['meta'])
                for key, value in meta_data.items():
                    self.wp_client.set_post_meta(post_id, key, value)
                logger.info(f"Set meta fields: {list(meta_data.keys())}")
            except Exception as e:
                logger.warning(f"Failed to set meta: {e}")

        self.last_post_id = post_id

        return {
            'post_id': post_id,
            'content': content
        }

    def create_wordpress_tools(self):
        """Create WordPress tool functions for agents

        Returns:
            list: List of callable tool functions
        """
        return self.wp_tools.get_tool_functions()

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def _generate_with_retry(self, agents):
        """Execute generation with retry logic"""
        return agents.start()

    def generate(
        self,
        topic: str,
        title: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate content using PraisonAI

        Args:
            topic: Topic to write about
            title: Post title (optional, defaults to topic)
            **kwargs: Additional options
                - auto_publish: Auto-publish after generation (default: False)
                - post_type: Post type (post, page) (default: 'post')
                - category: Comma-separated category names (default: None)
                - category_id: Comma-separated category IDs (default: None)
                - author: Post author (user ID or login) (default: None)
                - excerpt: Post excerpt (default: None)
                - date: Post date (YYYY-MM-DD HH:MM:SS) (default: None)
                - tags: Comma-separated tag names (default: None)
                - meta: Post meta in JSON format (default: None)
                - comment_status: Comment status (open, closed) (default: None)
                - use_tools: Give agent WordPress tools (default: False)
                - model: Override default model
                - skip_validation: Skip content validation (default: False)

        Returns:
            dict: Generated content, post ID, cost, and metadata
        """
        # Rate limiting
        if self.rate_limiter:
            self.rate_limiter.wait_if_needed()

        self.current_title = title or topic
        self.current_post_options = {
            'post_type': kwargs.get('post_type'),
            'category': kwargs.get('category'),
            'category_id': kwargs.get('category_id'),
            'author': kwargs.get('author'),
            'excerpt': kwargs.get('excerpt'),
            'date': kwargs.get('date'),
            'tags': kwargs.get('tags'),
            'meta': kwargs.get('meta'),
            'comment_status': kwargs.get('comment_status')
        }
        self.last_post_id = None
        start_time = time.time()

        # Get model
        model = kwargs.get('model', self.config.get('model', 'gpt-4o-mini'))

        logger.info(f"Generating content about: {topic}")
        logger.info(f"Using model: {model}")

        # Create agent
        agent = Agent(
            name="WordPress Writer",
            role="Content Creator",
            goal=f"Create engaging content about {topic}",
            backstory="Expert content writer with SEO knowledge",
            llm=model,
            tools=self.create_wordpress_tools() if kwargs.get('use_tools') else None
        )

        # Create task with optional callback
        task = Task(
            description=f"Write a comprehensive blog post about {topic}",
            expected_output="SEO-optimized blog post content",
            agent=agent,
            callback=self._publish_callback if kwargs.get('auto_publish') else None
        )

        # Execute with retry
        agents_obj = PraisonAIAgents(
            agents=[agent],
            tasks=[task],
            verbose=self.config.get('verbose', 0)
        )

        result = self._generate_with_retry(agents_obj)
        duration = time.time() - start_time

        logger.info(f"Generation completed in {duration:.2f}s")
        logger.info(f"Generated {len(result)} characters")

        # Content validation
        if self.config['validate_content'] and not kwargs.get('skip_validation'):
            is_valid, errors = self.content_validator.validate(result)
            if not is_valid:
                error_msg = "Content validation failed:\n" + "\n".join(
                    f"  - {err}" for err in errors
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
            logger.info("Content validation passed")

        # Estimate cost (rough estimate based on content length)
        # Actual token count would require tokenizer
        estimated_input_tokens = len(topic.split()) * 2
        estimated_output_tokens = len(result.split())
        cost_info = self.cost_tracker.track(
            model=model,
            input_tokens=estimated_input_tokens,
            output_tokens=estimated_output_tokens,
            metadata={'topic': topic, 'duration': duration}
        )
        self.last_generation_cost = cost_info['cost']

        logger.info(f"Estimated cost: ${cost_info['cost']:.6f}")

        return {
            'content': result,
            'post_id': self.last_post_id,
            'cost': cost_info['cost'],
            'duration': duration,
            'model': model,
            'metadata': {
                'topic': topic,
                'title': self.current_title,
                'length': len(result),
                'word_count': len(result.split())
            }
        }

    def get_cost_summary(self) -> Dict:
        """Get cost tracking summary

        Returns:
            dict: Cost summary
        """
        return self.cost_tracker.get_summary()
