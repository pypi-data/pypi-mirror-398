---
layout: default
title: AI Commands
---

# AI Commands Reference

## ai

AI content generation and management.

```bash
praisonaiwp ai [COMMAND] [OPTIONS]
```

### Subcommands

- `generate` - Generate content
- `analyze` - Analyze content
- `optimize` - Optimize content
- `translate` - Translate content
- `summarize` - Summarize content
- `seo` - SEO optimization
- `image` - Generate images
- `bulk` - Bulk operations
- `workflow` - Workflow automation
- `scheduler` - Schedule AI tasks
- `researcher` - Research topics
- `curator` - Curate content
- `moderator` - Moderate content
- `chatbot` - Chatbot interactions

---

## ai-analyzer

Analyze content with AI.

```bash
praisonaiwp ai-analyzer [OPTIONS]
```

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--content TEXT` | string | Content to analyze |
| `--post-id INTEGER` | int | Post ID to analyze |
| `--type TEXT` | string | Analysis type: sentiment, readability, seo, all |
| `--model TEXT` | string | AI model to use |
| `--temperature FLOAT` | float | Temperature (0.0-1.0) |
| `--max-tokens INTEGER` | int | Max tokens |
| `--output-file TEXT` | string | Save results to file |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp ai-analyzer --content "Your content here" --type sentiment
praisonaiwp ai-analyzer --post-id 123 --type seo
praisonaiwp ai-analyzer --content "Text" --type all --output-file analysis.json
```

---

## ai-bulk

Bulk AI operations on multiple posts.

```bash
praisonaiwp ai-bulk [COMMAND] [OPTIONS]
```

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--operation TEXT` | string | Operation: generate, translate, optimize, summarize |
| `--post-ids TEXT` | string | Post IDs (comma-separated) |
| `--category TEXT` | string | Filter by category |
| `--tag TEXT` | string | Filter by tag |
| `--status TEXT` | string | Filter by status |
| `--batch-size INTEGER` | int | Batch size (default: 10) |
| `--delay INTEGER` | int | Delay between batches (seconds) |
| `--model TEXT` | string | AI model |
| `--temperature FLOAT` | float | Temperature |
| `--dry-run` | flag | Preview without executing |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
# Optimize all posts in category
praisonaiwp ai-bulk --operation optimize --category "Tech" --batch-size 5

# Translate posts
praisonaiwp ai-bulk --operation translate --post-ids "1,2,3" --target-lang es

# Generate summaries
praisonaiwp ai-bulk --operation summarize --status publish --batch-size 10

# Dry run
praisonaiwp ai-bulk --operation optimize --category "News" --dry-run
```

---

## ai-chatbot

AI chatbot interactions.

```bash
praisonaiwp ai-chatbot [OPTIONS]
```

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--message TEXT` | string | User message |
| `--conversation-id TEXT` | string | Conversation ID |
| `--system-prompt TEXT` | string | System prompt |
| `--model TEXT` | string | AI model |
| `--temperature FLOAT` | float | Temperature |
| `--max-tokens INTEGER` | int | Max tokens |
| `--stream` | flag | Stream response |
| `--context TEXT` | string | Additional context |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp ai-chatbot --message "How do I optimize my posts?"
praisonaiwp ai-chatbot --message "Translate this" --context "Spanish"
praisonaiwp ai-chatbot --message "Help" --conversation-id abc123
```

---

## ai-curator

Curate and organize content with AI.

```bash
praisonaiwp ai-curator [OPTIONS]
```

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--action TEXT` | string | Action: categorize, tag, organize, recommend |
| `--post-id INTEGER` | int | Post ID |
| `--content TEXT` | string | Content to curate |
| `--categories TEXT` | string | Available categories |
| `--tags TEXT` | string | Available tags |
| `--auto-apply` | flag | Auto-apply suggestions |
| `--model TEXT` | string | AI model |
| `--temperature FLOAT` | float | Temperature |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
# Auto-categorize post
praisonaiwp ai-curator --action categorize --post-id 123 --auto-apply

# Suggest tags
praisonaiwp ai-curator --action tag --content "AI and machine learning"

# Get recommendations
praisonaiwp ai-curator --action recommend --post-id 123
```

---

## ai-image

Generate images with AI.

```bash
praisonaiwp ai-image [OPTIONS]
```

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--prompt TEXT` | string | Image prompt |
| `--post-id INTEGER` | int | Attach to post |
| `--model TEXT` | string | Image model: dall-e-3, stable-diffusion |
| `--size TEXT` | string | Image size: 1024x1024, 1792x1024, 1024x1792 |
| `--quality TEXT` | string | Quality: standard, hd |
| `--style TEXT` | string | Style: vivid, natural |
| `--n INTEGER` | int | Number of images |
| `--output-dir TEXT` | string | Output directory |
| `--set-featured` | flag | Set as featured image |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
# Generate image
praisonaiwp ai-image --prompt "A sunset over mountains" --size 1024x1024

# Generate and attach to post
praisonaiwp ai-image --prompt "Tech illustration" --post-id 123 --set-featured

# Multiple images
praisonaiwp ai-image --prompt "Abstract art" --n 4 --output-dir ./images
```

---

## ai-moderator

Moderate content with AI.

```bash
praisonaiwp ai-moderator [OPTIONS]
```

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--content TEXT` | string | Content to moderate |
| `--post-id INTEGER` | int | Post ID |
| `--comment-id INTEGER` | int | Comment ID |
| `--check TEXT` | string | Check: spam, toxicity, profanity, all |
| `--threshold FLOAT` | float | Threshold (0.0-1.0) |
| `--auto-action` | flag | Auto-take action |
| `--action TEXT` | string | Action: flag, delete, approve |
| `--model TEXT` | string | AI model |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
# Check comment
praisonaiwp ai-moderator --comment-id 456 --check all

# Moderate post
praisonaiwp ai-moderator --post-id 123 --check toxicity --threshold 0.7

# Auto-moderate
praisonaiwp ai-moderator --comment-id 789 --check spam --auto-action --action delete
```

---

## ai-optimizer

Optimize content with AI.

```bash
praisonaiwp ai-optimizer [OPTIONS]
```

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--post-id INTEGER` | int | Post ID |
| `--content TEXT` | string | Content to optimize |
| `--type TEXT` | string | Optimization: readability, seo, engagement, all |
| `--target-audience TEXT` | string | Target audience |
| `--tone TEXT` | string | Tone: professional, casual, friendly |
| `--apply` | flag | Apply changes |
| `--model TEXT` | string | AI model |
| `--temperature FLOAT` | float | Temperature |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
# Optimize for SEO
praisonaiwp ai-optimizer --post-id 123 --type seo --apply

# Improve readability
praisonaiwp ai-optimizer --content "Complex text" --type readability

# Full optimization
praisonaiwp ai-optimizer --post-id 123 --type all --tone professional --apply
```

---

## ai-researcher

Research topics with AI.

```bash
praisonaiwp ai-researcher [OPTIONS]
```

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--topic TEXT` | string | Research topic |
| `--query TEXT` | string | Search query |
| `--depth TEXT` | string | Depth: basic, detailed, comprehensive |
| `--sources INTEGER` | int | Number of sources |
| `--format TEXT` | string | Output format: summary, outline, full |
| `--create-post` | flag | Create post from research |
| `--category TEXT` | string | Post category |
| `--status TEXT` | string | Post status |
| `--model TEXT` | string | AI model |
| `--output-file TEXT` | string | Save to file |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
# Research topic
praisonaiwp ai-researcher --topic "AI trends 2024" --depth detailed

# Research and create post
praisonaiwp ai-researcher --topic "WordPress security" --create-post --category "Tech"

# Comprehensive research
praisonaiwp ai-researcher --query "machine learning" --depth comprehensive --sources 10
```

---

## ai-scheduler

Schedule AI tasks.

```bash
praisonaiwp ai-scheduler [COMMAND] [OPTIONS]
```

### Subcommands

- `create` - Create scheduled task
- `list` - List scheduled tasks
- `delete` - Delete scheduled task
- `run` - Run task now
- `pause` - Pause task
- `resume` - Resume task

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--task-id TEXT` | string | Task ID |
| `--name TEXT` | string | Task name |
| `--command TEXT` | string | AI command to run |
| `--schedule TEXT` | string | Cron schedule |
| `--params TEXT` | string | Command parameters (JSON) |
| `--enabled` | flag | Enable task |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
# Schedule daily optimization
praisonaiwp ai-scheduler create --name "Daily Optimize" --command "ai-optimizer" --schedule "0 2 * * *"

# List tasks
praisonaiwp ai-scheduler list

# Run task now
praisonaiwp ai-scheduler run --task-id abc123

# Delete task
praisonaiwp ai-scheduler delete --task-id abc123
```

---

## ai-seo

SEO optimization with AI.

```bash
praisonaiwp ai-seo [OPTIONS]
```

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--post-id INTEGER` | int | Post ID |
| `--content TEXT` | string | Content to optimize |
| `--keyword TEXT` | string | Target keyword |
| `--generate-meta` | flag | Generate meta description |
| `--generate-title` | flag | Generate SEO title |
| `--suggest-keywords` | flag | Suggest keywords |
| `--analyze` | flag | Analyze SEO score |
| `--apply` | flag | Apply suggestions |
| `--model TEXT` | string | AI model |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
# Analyze SEO
praisonaiwp ai-seo --post-id 123 --analyze

# Generate meta
praisonaiwp ai-seo --post-id 123 --generate-meta --apply

# Keyword research
praisonaiwp ai-seo --content "AI article" --suggest-keywords

# Full SEO optimization
praisonaiwp ai-seo --post-id 123 --keyword "wordpress ai" --generate-meta --generate-title --apply
```

---

## ai-summarizer

Summarize content with AI.

```bash
praisonaiwp ai-summarizer [OPTIONS]
```

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--post-id INTEGER` | int | Post ID |
| `--content TEXT` | string | Content to summarize |
| `--length TEXT` | string | Length: short, medium, long |
| `--style TEXT` | string | Style: bullet, paragraph, key-points |
| `--update-excerpt` | flag | Update post excerpt |
| `--model TEXT` | string | AI model |
| `--temperature FLOAT` | float | Temperature |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
# Summarize post
praisonaiwp ai-summarizer --post-id 123 --length short

# Generate excerpt
praisonaiwp ai-summarizer --post-id 123 --style paragraph --update-excerpt

# Custom summary
praisonaiwp ai-summarizer --content "Long article text" --length medium --style bullet
```

---

## ai-translator

Translate content with AI.

```bash
praisonaiwp ai-translator [OPTIONS]
```

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--post-id INTEGER` | int | Post ID |
| `--content TEXT` | string | Content to translate |
| `--source-lang TEXT` | string | Source language (auto-detect if omitted) |
| `--target-lang TEXT` | string | Target language (required) |
| `--create-post` | flag | Create new post with translation |
| `--update-post` | flag | Update existing post |
| `--preserve-html` | flag | Preserve HTML tags |
| `--model TEXT` | string | AI model |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
# Translate post
praisonaiwp ai-translator --post-id 123 --target-lang es

# Create translated post
praisonaiwp ai-translator --post-id 123 --target-lang fr --create-post

# Translate text
praisonaiwp ai-translator --content "Hello world" --target-lang de

# Multiple languages
praisonaiwp ai-translator --post-id 123 --target-lang "es,fr,de" --create-post
```

---

## ai-workflow

Automate AI workflows.

```bash
praisonaiwp ai-workflow [COMMAND] [OPTIONS]
```

### Subcommands

- `create` - Create workflow
- `list` - List workflows
- `run` - Run workflow
- `delete` - Delete workflow
- `export` - Export workflow
- `import` - Import workflow

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--workflow-id TEXT` | string | Workflow ID |
| `--name TEXT` | string | Workflow name |
| `--steps TEXT` | string | Workflow steps (JSON) |
| `--trigger TEXT` | string | Trigger: manual, schedule, event |
| `--schedule TEXT` | string | Cron schedule |
| `--file TEXT` | string | Workflow file |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
# Create workflow
praisonaiwp ai-workflow create --name "Content Pipeline" --steps '[{"action":"generate"},{"action":"optimize"}]'

# List workflows
praisonaiwp ai-workflow list

# Run workflow
praisonaiwp ai-workflow run --workflow-id wf123

# Export workflow
praisonaiwp ai-workflow export --workflow-id wf123 --file workflow.json

# Import workflow
praisonaiwp ai-workflow import --file workflow.json
```

---

## AI Configuration

### Environment Variables

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-4"

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
export ANTHROPIC_MODEL="claude-3-opus"

# Google
export GOOGLE_API_KEY="..."
export GOOGLE_MODEL="gemini-pro"
```

### Config File

```yaml
# ~/.praisonaiwp/config.yml
ai:
  provider: openai
  model: gpt-4
  temperature: 0.7
  max_tokens: 2000
  
  providers:
    openai:
      api_key: ${OPENAI_API_KEY}
      models:
        - gpt-4
        - gpt-3.5-turbo
    
    anthropic:
      api_key: ${ANTHROPIC_API_KEY}
      models:
        - claude-3-opus
        - claude-3-sonnet
```

### AI Models

| Provider | Model | Use Case |
|----------|-------|----------|
| OpenAI | gpt-4 | Complex tasks, best quality |
| OpenAI | gpt-3.5-turbo | Fast, cost-effective |
| Anthropic | claude-3-opus | Long context, analysis |
| Anthropic | claude-3-sonnet | Balanced performance |
| Google | gemini-pro | Multimodal tasks |

### Best Practices

```bash
# Use appropriate temperature
--temperature 0.3  # Factual, consistent
--temperature 0.7  # Balanced (default)
--temperature 0.9  # Creative, varied

# Batch operations
praisonaiwp ai-bulk --batch-size 10 --delay 2

# Test before applying
praisonaiwp ai-optimizer --post-id 123 --type seo  # Preview
praisonaiwp ai-optimizer --post-id 123 --type seo --apply  # Apply

# Use workflows for complex tasks
praisonaiwp ai-workflow create --name "Publish Pipeline" \
  --steps '[
    {"action":"generate","params":{"topic":"AI"}},
    {"action":"optimize","params":{"type":"seo"}},
    {"action":"translate","params":{"lang":"es"}},
    {"action":"publish"}
  ]'
```
