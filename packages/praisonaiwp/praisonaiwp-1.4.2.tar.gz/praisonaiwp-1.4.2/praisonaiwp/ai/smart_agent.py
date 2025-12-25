"""Smart Content Agent with ServerRouter integration for intelligent posting"""

import logging
from typing import Dict, Any, Optional, List
from praisonaiwp.core.router import ServerRouter
from praisonaiwp.ai.integration import PraisonAIWPIntegration

logger = logging.getLogger(__name__)


class SmartContentAgent:
    """AI agent with intelligent server routing capabilities"""

    def __init__(self, wp_client, config: Dict[str, Any], **ai_config):
        """
        Initialize SmartContentAgent

        Args:
            wp_client: WordPress client instance
            config: Configuration dictionary with servers and settings
            **ai_config: Additional AI configuration options
        """
        self.wp_client = wp_client
        self.config = config
        self.ai_config = ai_config

        # Initialize ServerRouter
        self.router = ServerRouter(config)

        # Initialize AI integration (lazy loading)
        self._ai_integration = None

    @property
    def ai_integration(self):
        """Lazy load AI integration"""
        if self._ai_integration is None:
            self._ai_integration = PraisonAIWPIntegration(
                self.wp_client,
                **self.ai_config
            )
        return self._ai_integration

    def detect_server_from_context(
        self,
        title: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        server: Optional[str] = None
    ) -> str:
        """
        Detect appropriate server from context

        Args:
            title: Post title
            content: Post content
            tags: Post tags
            server: Explicit server name (takes precedence)

        Returns:
            Server name
        """
        # Explicit server takes precedence
        if server:
            return server

        # Check if auto_route is enabled
        auto_route = self.config.get('settings', {}).get('auto_route', False)

        if not auto_route:
            # Return default server if auto-route disabled
            return self.config.get('default_server', 'default')

        # Try to detect from title and content
        search_text = f"{title or ''} {content or ''}".strip()

        if search_text:
            server_name, _ = self.router.find_server_by_keywords(search_text)
            if server_name:
                logger.info(f"Auto-detected server from content: {server_name}")
                return server_name

        # Try to match by tags
        if tags:
            server_name = self._match_by_tags(tags)
            if server_name:
                logger.info(f"Matched server by tags: {server_name}")
                return server_name

        # Fallback to default
        default_server = self.config.get('default_server', 'default')
        logger.info(f"Using default server: {default_server}")
        return default_server

    def _match_by_tags(self, tags: List[str]) -> Optional[str]:
        """
        Match server by content tags

        Args:
            tags: List of content tags

        Returns:
            Server name or None
        """
        best_match = None
        best_score = 0

        for server_name, server_config in self.config.get('servers', {}).items():
            server_tags = server_config.get('tags', [])
            if not server_tags:
                continue

            # Calculate matching score
            matching_tags = set(tags) & set(server_tags)
            if matching_tags:
                score = len(matching_tags) / len(tags)
                if score > best_score:
                    best_score = score
                    best_match = server_name

        return best_match

    def suggest_server(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Suggest best server with confidence score

        Args:
            context: Context dictionary with title, content, tags, etc.

        Returns:
            Dictionary with server, confidence, and reason
        """
        title = context.get('title', '')
        content = context.get('content', '')
        tags = context.get('tags', [])

        # Try keyword matching first (high confidence)
        search_text = f"{title} {content}".strip()
        if search_text:
            server_name, _ = self.router.find_server_by_keywords(search_text)
            if server_name:
                return {
                    'server': server_name,
                    'confidence': 0.9,
                    'reason': 'Domain mentioned in content'
                }

        # Try tag matching (medium confidence)
        if tags:
            server_name = self._match_by_tags(tags)
            if server_name:
                server_tags = self.config['servers'][server_name].get('tags', [])
                matching_tags = set(tags) & set(server_tags)
                confidence = len(matching_tags) / len(tags)
                return {
                    'server': server_name,
                    'confidence': confidence,
                    'reason': f"Matching tags: {', '.join(matching_tags)}"
                }

        # Fallback to default (low confidence)
        default_server = self.config.get('default_server', 'default')
        return {
            'server': default_server,
            'confidence': 0.3,
            'reason': 'No specific match, using default'
        }

    def get_server_defaults(self, server_name: str) -> Dict[str, Any]:
        """
        Get server-specific defaults (author, category, etc.)

        Args:
            server_name: Server name

        Returns:
            Dictionary with default options
        """
        server_config = self.config.get('servers', {}).get(server_name, {})

        defaults = {}
        if 'author' in server_config:
            defaults['author'] = server_config['author']
        if 'category' in server_config:
            defaults['category'] = server_config['category']

        return defaults

    def create_post_with_routing(
        self,
        title: str,
        content: str,
        status: str = 'draft',
        server: Optional[str] = None,
        **options
    ) -> Dict[str, Any]:
        """
        Create post with automatic server routing

        Args:
            title: Post title
            content: Post content
            status: Post status
            server: Explicit server name (optional)
            **options: Additional post options

        Returns:
            Dictionary with post_id and server
        """
        # Detect server
        detected_server = self.detect_server_from_context(
            title=title,
            content=content,
            server=server
        )

        # Get server defaults
        server_defaults = self.get_server_defaults(detected_server)

        # Merge options with server defaults
        post_options = {**server_defaults, **options}

        # Create post
        result = self.wp_client.create_post(
            title=title,
            content=content,
            status=status,
            **post_options
        )

        return {
            'post_id': result.get('id'),
            'server': detected_server,
            'options': post_options
        }

    def generate_content(
        self,
        topic: str,
        server: Optional[str] = None,
        **generation_options
    ) -> Dict[str, Any]:
        """
        Generate content using AI with server context

        Args:
            topic: Content topic
            server: Target server (optional, for context)
            **generation_options: Additional generation options

        Returns:
            Dictionary with title and content
        """
        # Get server context if provided
        server_context = ""
        if server:
            server_config = self.config.get('servers', {}).get(server, {})
            description = server_config.get('description', '')
            tags = server_config.get('tags', [])
            website = server_config.get('website', '')

            if description or tags or website:
                server_context = f"\nTarget website: {website}\n"
                if description:
                    server_context += f"Website description: {description}\n"
                if tags:
                    server_context += f"Relevant topics: {', '.join(tags)}\n"

        # Generate content using AI integration
        prompt = f"Create a blog post about: {topic}{server_context}"

        # Use AI integration to generate
        result = self.ai_integration.generate_post(
            title=topic,
            **generation_options
        )

        return result
