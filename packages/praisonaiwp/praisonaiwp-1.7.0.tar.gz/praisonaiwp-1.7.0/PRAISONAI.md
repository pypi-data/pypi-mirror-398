# PraisonAI Integration - Complete Guide

**Version**: 1.1.0  
**Status**: ✅ Production Ready  
**Last Updated**: November 19, 2025

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Features Overview](#features-overview)
4. [Architecture](#architecture)
5. [Usage Examples](#usage-examples)
6. [Configuration](#configuration)
7. [Production Features](#production-features)
8. [API Reference](#api-reference)
9. [Cost & Performance](#cost--performance)
10. [Testing](#testing)
11. [Troubleshooting](#troubleshooting)
12. [Advanced Topics](#advanced-topics)

---

## Quick Start

### Installation

```bash
# Install with AI features
pip install praisonaiwp[ai]

# Set your OpenAI API key
export OPENAI_API_KEY="sk-..."

# Initialize PraisonAIWP (if not already done)
praisonaiwp init
```

### Basic Usage

```bash
# Generate content (draft)
praisonaiwp ai generate "AI Trends 2025"

# Generate with custom title
praisonaiwp ai generate "AI Trends" --title "The Future of AI"

# Generate and auto-publish
praisonaiwp ai generate "AI Trends" \
  --title "The Future of AI" \
  --auto-publish \
  --status publish
```

### Programmatic Usage

```python
from praisonaiwp.ai.integration import PraisonAIWPIntegration
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient

# Create SSH connection
ssh = SSHManager(
    hostname="example.com",
    username="user",
    key_file="/path/to/key"
)

# Create WP client
wp_client = WPClient(ssh=ssh, wp_path="/var/www/html")

# Create AI integration
integration = PraisonAIWPIntegration(wp_client)

# Generate content
result = integration.generate(
    topic="AI Trends 2025",
    title="The Future of AI",
    auto_publish=True
)

print(f"Post ID: {result['post_id']}")
print(f"Cost: ${result['cost']:.6f}")
```

---

## Installation

### Requirements

- Python >= 3.8.1
- OpenAI API key
- WordPress site with WP-CLI
- SSH access to WordPress server

### Install Options

```bash
# Core only (no AI features)
pip install praisonaiwp

# With AI features (recommended)
pip install praisonaiwp[ai]

# With development tools
pip install praisonaiwp[dev]

# Everything
pip install praisonaiwp[all]
```

### Dependencies

**Core Dependencies**:
- paramiko >= 3.0.0
- click >= 8.1.0
- PyYAML >= 6.0
- requests >= 2.31.0
- rich >= 13.0.0

**AI Dependencies** (optional):
- praisonaiagents >= 0.0.1
- openai >= 1.0.0

---

## Features Overview

### ✅ Core Features

1. **PraisonAI Integration**
   - WordPress tools for PraisonAI agents
   - Task-based callback system
   - CLI commands
   - Optional dependencies

2. **Production-Ready Features**
   - API key validation
   - Content validation
   - Cost tracking
   - Retry logic with exponential backoff
   - Rate limiting
   - Structured logging

3. **Quality Control**
   - Minimum/maximum length validation
   - Paragraph structure checks
   - Placeholder text detection
   - Configurable validation rules

4. **Cost Management**
   - Per-generation cost tracking
   - Cumulative cost tracking
   - Model-specific pricing
   - Cost estimation before generation

### ✅ What Makes It Production-Ready

| Feature | Status | Description |
|---------|--------|-------------|
| **API Key Validation** | ✅ | Validates on initialization |
| **Retry Logic** | ✅ | 3 attempts with exponential backoff |
| **Content Validation** | ✅ | Length, structure, placeholders |
| **Cost Tracking** | ✅ | Per-generation + cumulative |
| **Rate Limiting** | ✅ | Configurable limits |
| **Logging** | ✅ | Structured with metrics |
| **Error Handling** | ✅ | Comprehensive with clear messages |
| **Test Coverage** | ✅ | 58 tests, 100% passing |

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────┐
│         PraisonAIWP CLI Layer           │
│  (Click commands: ai generate, etc.)    │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│      PraisonAI Integration Layer        │
│  ┌───────────────────────────────────┐  │
│  │  Task Callbacks (auto-publish)    │  │
│  ├───────────────────────────────────┤  │
│  │  Production Features:             │  │
│  │  - API Validation                 │  │
│  │  - Content Validation             │  │
│  │  - Cost Tracking                  │  │
│  │  - Retry Logic                    │  │
│  │  - Rate Limiting                  │  │
│  └───────────────────────────────────┘  │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│         PraisonAI Framework             │
│  (Agent, Task, PraisonAIAgents)         │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│      WordPress Core (WPClient)          │
│  (SSH, WP-CLI, existing features)       │
└─────────────────────────────────────────┘
```

### Component Architecture

#### 1. Integration Layer
**File**: `praisonaiwp/ai/integration.py`

```python
class PraisonAIWPIntegration:
    - __init__(wp_client, **config)
    - generate(topic, title, **kwargs)
    - _publish_callback(task_output)
    - create_wordpress_tools()
    - get_cost_summary()
```

**Features**:
- Uses PraisonAI's task callback system
- Default model: gpt-4o-mini
- Auto-publish support
- WordPress tools for agents
- Configurable verbosity

#### 2. WordPress Tools
**File**: `praisonaiwp/ai/tools/wordpress_tools.py`

```python
class WordPressTools:
    - create_post(title, content, status='draft')
    - update_post(post_id, title=None, content=None)
    - list_posts(limit=10)
    - get_tool_functions()
```

#### 3. Utilities

**Validators** (`praisonaiwp/ai/utils/validators.py`):
- `APIKeyValidator` - Validates OpenAI API key
- `ContentValidator` - Validates generated content
- `validate_api_key()` - Standalone validation
- `validate_content()` - Standalone validation

**Cost Tracker** (`praisonaiwp/ai/utils/cost_tracker.py`):
- `CostTracker` - Tracks API costs
- Model-specific pricing
- Per-generation and cumulative tracking

**Retry Logic** (`praisonaiwp/ai/utils/retry.py`):
- `@retry_with_backoff` - Decorator for retry logic
- Exponential backoff
- Configurable retries

**Rate Limiter** (`praisonaiwp/ai/utils/rate_limiter.py`):
- `RateLimiter` - Prevents API rate limits
- Configurable limits
- Automatic waiting

### How It Works

#### Callback Flow

1. **User runs command**: `praisonaiwp ai generate "AI Trends"`
2. **Integration creates agent**: With gpt-4o-mini model
3. **Task created with callback**: `callback=self._publish_callback`
4. **PraisonAI executes**: Agent generates content
5. **Callback triggered**: After task completion
6. **Auto-publish**: Content posted to WordPress
7. **Return result**: Post ID, cost, and metadata

#### Why This Approach?

**We use PraisonAI's built-in callback system instead of custom middleware:**

✅ **Official API** - Maintained by PraisonAI team  
✅ **Simple** - 5-30 minutes to implement  
✅ **Flexible** - Multiple integration points  
✅ **Future-proof** - Part of official API  
✅ **Well-tested** - Used internally by PraisonAI

**PraisonAI provides 6+ callback/hook systems:**
1. Task callbacks - Post-execution hooks
2. Display callbacks - Lifecycle events
3. Approval callbacks - Dangerous operations
4. Memory callbacks - Storage operations
5. Custom tools - Agent capabilities
6. Lazy-loading - Tool architecture

---

## Usage Examples

### CLI Examples

#### Basic Generation
```bash
praisonaiwp ai generate "AI Trends 2025"
```

#### With Custom Title
```bash
praisonaiwp ai generate "AI Trends" --title "The Future of AI in 2025"
```

#### Auto-Publish
```bash
praisonaiwp ai generate "AI Trends" \
  --title "The Future of AI" \
  --auto-publish \
  --status publish
```

#### Verbose Mode
```bash
praisonaiwp ai generate "AI Trends" --verbose
```

### Programmatic Examples

#### Basic Usage
```python
from praisonaiwp.ai.integration import PraisonAIWPIntegration

integration = PraisonAIWPIntegration(wp_client)

result = integration.generate(
    topic="AI Trends 2025",
    title="The Future of AI",
    auto_publish=True
)

print(f"Content: {result['content']}")
print(f"Post ID: {result['post_id']}")
print(f"Cost: ${result['cost']:.6f}")
print(f"Duration: {result['duration']:.2f}s")
```

#### With Custom Configuration
```python
integration = PraisonAIWPIntegration(
    wp_client,
    model='gpt-4o-mini',
    min_length=200,
    max_length=5000,
    enable_rate_limiting=True,
    max_requests=10,
    verbose=1
)

result = integration.generate(
    topic="AI Trends",
    title="Custom Title",
    auto_publish=True
)
```

#### Skip Validation
```python
result = integration.generate(
    "Topic",
    skip_validation=True  # Skip content validation
)
```

#### Use Custom Model
```python
result = integration.generate(
    "Topic",
    model='gpt-4o'  # Use premium model
)
```

#### Get Cost Summary
```python
# Generate multiple posts
integration.generate("Topic 1", auto_publish=True)
integration.generate("Topic 2", auto_publish=True)

# Get summary
summary = integration.get_cost_summary()

print(f"Total generations: {summary['total_generations']}")
print(f"Total cost: ${summary['total_cost']:.6f}")
print(f"Average cost: ${summary['average_cost']:.6f}")
```

---

## Configuration

### Integration Configuration

```python
PraisonAIWPIntegration(
    wp_client,
    
    # Model settings
    model='gpt-4o-mini',           # Default model
    verbose=0,                      # Verbosity (0-2)
    status='draft',                 # Default post status
    
    # Content validation
    validate_content=True,          # Enable validation
    min_length=100,                 # Min chars
    max_length=10000,               # Max chars
    
    # Rate limiting
    enable_rate_limiting=True,      # Enable limiter
    max_requests=10,                # Max requests
    time_window=60,                 # Time window (seconds)
)
```

### Generate Options

```python
integration.generate(
    topic="AI Trends",
    title="Custom Title",          # Optional
    auto_publish=True,              # Auto-publish
    use_tools=False,                # Give agent WP tools
    model='gpt-4o',                 # Override model
    skip_validation=False,          # Skip validation
)
```

### Environment Variables

```bash
# Required
export OPENAI_API_KEY="sk-..."

# Optional
export OPENAI_MODEL_NAME="gpt-4o-mini"
```

---

## Production Features

### 1. API Key Validation

**Validates on initialization:**

```python
# Automatic validation
integration = PraisonAIWPIntegration(wp_client)
# Raises ValueError if OPENAI_API_KEY not set or invalid

# Manual validation
from praisonaiwp.ai.utils.validators import validate_api_key
validate_api_key()  # Raises ValueError if invalid
```

**Features**:
- Checks if `OPENAI_API_KEY` is set
- Validates key format (must start with 'sk-')
- Clear error messages with help URL

### 2. Content Validation

**Validates generated content:**

```python
from praisonaiwp.ai.utils.validators import ContentValidator

validator = ContentValidator(min_length=100, max_length=10000)
is_valid, errors = validator.validate(content)

if not is_valid:
    print("Validation errors:")
    for error in errors:
        print(f"  - {error}")
```

**Checks**:
- Minimum/maximum length
- Paragraph structure (needs 2+ paragraph breaks)
- Placeholder text detection ([INSERT], TODO, etc.)

### 3. Cost Tracking

**Track API costs:**

```python
from praisonaiwp.ai.utils.cost_tracker import CostTracker

tracker = CostTracker()

# Track a generation
cost_info = tracker.track(
    model='gpt-4o-mini',
    input_tokens=500,
    output_tokens=700
)

print(f"Cost: ${cost_info['cost']:.6f}")

# Get summary
summary = tracker.get_summary()
print(f"Total cost: ${summary['total_cost']:.6f}")
```

**Pricing** (per 1K tokens):
- gpt-4o-mini: $0.00015 input, $0.0006 output
- gpt-4o: $0.005 input, $0.015 output
- gpt-4-turbo: $0.01 input, $0.03 output
- gpt-3.5-turbo: $0.0005 input, $0.0015 output

### 4. Retry Logic

**Automatic retries with exponential backoff:**

```python
from praisonaiwp.ai.utils.retry import retry_with_backoff

@retry_with_backoff(max_retries=3, base_delay=1.0)
def generate_content():
    # Your code here
    pass
```

**Features**:
- Automatic retry on failures
- Exponential backoff (1s, 2s, 4s...)
- Configurable max retries
- Specific exception handling

### 5. Rate Limiting

**Prevent API rate limit errors:**

```python
from praisonaiwp.ai.utils.rate_limiter import RateLimiter

limiter = RateLimiter(max_requests=10, time_window=60)

# Before each request
limiter.wait_if_needed()  # Waits if limit reached

# Check remaining
remaining = limiter.get_remaining()
print(f"Remaining requests: {remaining}")
```

**Features**:
- Prevents API rate limit errors
- Automatic waiting when limit reached
- Configurable limits
- Can be disabled

### 6. Structured Logging

**Detailed logging with metrics:**

```python
import logging

# Enable logging
logging.basicConfig(level=logging.INFO)

# Integration logs automatically
integration = PraisonAIWPIntegration(wp_client, verbose=1)

result = integration.generate("Topic")
# Logs:
# - Generating content about: Topic
# - Using model: gpt-4o-mini
# - Generation completed in 2.5s
# - Generated 500 characters
# - Content validation passed
# - Estimated cost: $0.000500
```

---

## API Reference

### PraisonAIWPIntegration

#### `__init__(wp_client, **config)`

Initialize the integration.

**Parameters**:
- `wp_client` (WPClient): WordPress client instance
- `model` (str): LLM model to use (default: 'gpt-4o-mini')
- `verbose` (int): Verbosity level 0-2 (default: 0)
- `status` (str): Default post status (default: 'draft')
- `validate_content` (bool): Enable validation (default: True)
- `min_length` (int): Minimum content length (default: 100)
- `max_length` (int): Maximum content length (default: 10000)
- `enable_rate_limiting` (bool): Enable rate limiting (default: True)
- `max_requests` (int): Max requests per time window (default: 10)
- `time_window` (int): Time window in seconds (default: 60)

#### `generate(topic, title=None, **kwargs)`

Generate content using PraisonAI.

**Parameters**:
- `topic` (str): Topic to write about
- `title` (str, optional): Post title
- `auto_publish` (bool): Auto-publish after generation
- `use_tools` (bool): Give agent WordPress tools
- `model` (str): Override default model
- `skip_validation` (bool): Skip content validation

**Returns**:
```python
{
    'content': str,           # Generated content
    'post_id': int or None,   # WordPress post ID if published
    'cost': float,            # Estimated cost in USD
    'duration': float,        # Generation time in seconds
    'model': str,             # Model used
    'metadata': {
        'topic': str,
        'title': str,
        'length': int,
        'word_count': int
    }
}
```

#### `get_cost_summary()`

Get cost tracking summary.

**Returns**:
```python
{
    'total_generations': int,
    'total_cost': float,
    'total_input_tokens': int,
    'total_output_tokens': int,
    'total_tokens': int,
    'average_cost': float
}
```

### WordPressTools

#### `create_post(title, content, status='draft')`

Create a WordPress post.

**Parameters**:
- `title` (str): Post title
- `content` (str): Post content
- `status` (str): Post status ('draft', 'publish', 'private')

**Returns**:
```python
{
    'post_id': int,
    'status': str,
    'message': str
}
```

#### `update_post(post_id, title=None, content=None)`

Update an existing WordPress post.

**Parameters**:
- `post_id` (int): ID of the post to update
- `title` (str, optional): New title
- `content` (str, optional): New content

**Returns**:
```python
{
    'post_id': int,
    'updated': bool,
    'message': str
}
```

#### `list_posts(limit=10)`

List WordPress posts.

**Parameters**:
- `limit` (int): Maximum number of posts to return

**Returns**: List of post dictionaries

---

## Cost & Performance

### Cost Examples

#### gpt-4o-mini (Default)
```
500-word blog post:
- Input: ~50 tokens
- Output: ~700 tokens
- Cost: ~$0.0005 (half a cent)

1000 posts/month: ~$0.50
10,000 posts/month: ~$5.00
```

#### gpt-4o (Premium)
```
500-word blog post:
- Input: ~50 tokens
- Output: ~700 tokens
- Cost: ~$0.011 (1 cent)

1000 posts/month: ~$11.00
10,000 posts/month: ~$110.00
```

### Performance Metrics

#### Generation Speed
- **gpt-4o-mini**: 2-3 seconds (500 words)
- **gpt-4o**: 5-8 seconds (500 words)

#### Rate Limits (Default)
- **10 requests per 60 seconds**
- Automatic waiting when limit reached
- Can be disabled or customized

#### Retry Behavior
- **Max retries**: 3
- **Backoff**: 1s, 2s, 4s (exponential)
- **Total max wait**: ~7 seconds

### Cost Comparison

| Model | Speed | Cost/Post | Quality | Best For |
|-------|-------|-----------|---------|----------|
| gpt-4o | 5-8s | $0.011 | Excellent | Premium content |
| **gpt-4o-mini** | **2-3s** | **$0.0005** | **Good** | **Most use cases** |
| gpt-3.5-turbo | 1-2s | $0.0003 | Fair | High volume |

---

## Testing

### Test Coverage

**Total**: 58/58 tests passing (100%)

```
tests/ai/test_integration.py ................ 8 passed
tests/ai/test_integration_enhanced.py ....... 11 passed
tests/ai/test_utils.py ...................... 17 passed
tests/ai/test_validators.py ................. 12 passed
tests/ai/test_wordpress_tools.py ............ 8 passed
tests/cli/test_ai_commands_simple.py ........ 2 passed
```

### Test Categories

- ✅ API key validation (4 tests)
- ✅ Content validation (8 tests)
- ✅ Cost tracking (7 tests)
- ✅ Rate limiting (5 tests)
- ✅ Retry logic (5 tests)
- ✅ Integration features (19 tests)
- ✅ WordPress tools (8 tests)
- ✅ CLI commands (2 tests)

### Running Tests

```bash
# Run all AI tests
python -m pytest tests/ai/ -v

# Run specific test file
python -m pytest tests/ai/test_integration.py -v

# Run with coverage
python -m pytest tests/ai/ --cov=praisonaiwp.ai

# Run CLI tests
python -m pytest tests/cli/test_ai_commands_simple.py -v
```

---

## Troubleshooting

### Common Issues

#### API Key Not Set
```
Error: OPENAI_API_KEY not set.
Get your key at: https://platform.openai.com/api-keys
```

**Solution**:
```bash
export OPENAI_API_KEY="sk-..."
```

#### Configuration Not Found
```
Error: Configuration not found.
Run 'praisonaiwp init' first.
```

**Solution**:
```bash
praisonaiwp init
```

#### Content Validation Failed
```
Error: Content validation failed:
  - Content too short: 50 chars (minimum: 100)
  - Content lacks paragraph structure
```

**Solutions**:
1. Use `skip_validation=True`
2. Adjust `min_length` parameter
3. Improve prompt to generate longer content

#### SSH Connection Error
```
Error: SSHManager.__init__() got an unexpected keyword argument 'key_filename'
```

**Solution**: Use `key_file` instead of `key_filename`

```python
ssh = SSHManager(
    hostname="example.com",
    username="user",
    key_file="/path/to/key"  # Not key_filename
)
```

#### WPClient Initialization Error
```
Error: WPClient.__init__() got an unexpected keyword argument 'ssh_manager'
```

**Solution**: Use `ssh` instead of `ssh_manager`

```python
wp_client = WPClient(
    ssh=ssh_manager,  # Not ssh_manager
    wp_path="/var/www/html"
)
```

### Debug Mode

Enable verbose logging:

```python
integration = PraisonAIWPIntegration(
    wp_client,
    verbose=1  # or 2 for more details
)
```

Or via CLI:

```bash
praisonaiwp ai generate "Topic" --verbose
```

---

## Advanced Topics

### Custom WordPress Tools

Create custom tools for agents:

```python
class CustomWordPressTools:
    def __init__(self, wp_client):
        self.wp_client = wp_client
    
    def publish_with_seo(self, title, content, keywords):
        """Publish with SEO optimization"""
        # Add SEO meta tags
        # Optimize content
        # Publish
        pass
    
    def schedule_post(self, title, content, publish_date):
        """Schedule post for future publication"""
        pass

# Use custom tools
custom_tools = CustomWordPressTools(wp_client)
agent = Agent(
    name="SEO Writer",
    tools=[custom_tools.publish_with_seo]
)
```

### Batch Generation

Generate multiple posts:

```python
topics = [
    "AI Trends 2025",
    "Machine Learning Basics",
    "Deep Learning Applications"
]

results = []
for topic in topics:
    result = integration.generate(
        topic=topic,
        auto_publish=True
    )
    results.append(result)
    
    # Rate limiting handled automatically
    print(f"Generated: {topic} (${result['cost']:.6f})")

# Get total cost
summary = integration.get_cost_summary()
print(f"Total cost: ${summary['total_cost']:.6f}")
```

### Content Templates

Use custom prompts:

```python
def generate_with_template(integration, topic, template_type):
    """Generate content with specific template"""
    
    templates = {
        'blog_post': f"Write a comprehensive blog post about {topic}",
        'tutorial': f"Write a step-by-step tutorial about {topic}",
        'news': f"Write a news article about {topic}",
    }
    
    # Modify agent's goal based on template
    # This requires accessing the agent creation
    # For now, use topic to include template info
    
    enhanced_topic = f"{templates[template_type]}"
    
    return integration.generate(
        topic=enhanced_topic,
        auto_publish=True
    )
```

### Monitoring and Alerts

Track costs and set alerts:

```python
class CostMonitor:
    def __init__(self, max_daily_cost=10.0):
        self.max_daily_cost = max_daily_cost
        self.daily_cost = 0.0
    
    def check_cost(self, integration):
        summary = integration.get_cost_summary()
        self.daily_cost = summary['total_cost']
        
        if self.daily_cost >= self.max_daily_cost:
            raise ValueError(
                f"Daily cost limit reached: ${self.daily_cost:.2f}"
            )
    
    def reset_daily(self):
        self.daily_cost = 0.0

# Usage
monitor = CostMonitor(max_daily_cost=10.0)

result = integration.generate("Topic", auto_publish=True)
monitor.check_cost(integration)
```

### Error Recovery

Handle errors gracefully:

```python
from praisonaiwp.ai.utils.retry import retry_with_backoff

@retry_with_backoff(max_retries=5, base_delay=2.0)
def generate_with_recovery(integration, topic):
    """Generate with extended retry logic"""
    try:
        return integration.generate(
            topic=topic,
            auto_publish=True
        )
    except ValueError as e:
        if "validation failed" in str(e):
            # Try again with validation disabled
            return integration.generate(
                topic=topic,
                auto_publish=True,
                skip_validation=True
            )
        raise
```

---

## Summary

### What We Built

✅ **Production-ready AI integration** using PraisonAI's built-in callbacks  
✅ **6 critical production features** (validation, retry, cost tracking, etc.)  
✅ **58 comprehensive tests** (100% passing)  
✅ **Complete documentation**  
✅ **Backward compatible** (all features optional)

### Key Achievements

- **Implementation Time**: ~13 hours (vs 9 weeks with custom middleware)
- **Test Coverage**: 58 tests, 100% passing
- **Cost**: ~$0.0005 per 500-word post (gpt-4o-mini)
- **Speed**: 2-3 seconds per generation
- **Reliability**: Automatic retries, rate limiting, validation

### Status

**Version**: 1.1.0  
**Status**: ✅ **PRODUCTION READY**  
**Recommended For**:
- ✅ Production deployment
- ✅ High-volume usage
- ✅ Mission-critical workflows
- ✅ Cost-sensitive environments
- ✅ Multi-user systems

---

## Quick Reference

### Installation
```bash
pip install praisonaiwp[ai]
export OPENAI_API_KEY="sk-..."
```

### Basic Usage
```bash
praisonaiwp ai generate "Topic" --auto-publish
```

### Programmatic
```python
integration = PraisonAIWPIntegration(wp_client)
result = integration.generate("Topic", auto_publish=True)
```

### Cost Tracking
```python
summary = integration.get_cost_summary()
print(f"Total: ${summary['total_cost']:.6f}")
```

### Documentation
- Quick Start: This file, Quick Start section
- API Reference: This file, API Reference section
- Troubleshooting: This file, Troubleshooting section
- Examples: This file, Usage Examples section

---

**Last Updated**: November 19, 2025  
**Version**: 1.1.0  
**Status**: Production Ready ✅
