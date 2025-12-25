---
layout: default
title: Configuration
---

# Configuration Reference

## Config File Location

```bash
~/.praisonaiwp/config.yml
```

## Basic Configuration

```yaml
# Default server
default_server: production

# Servers
servers:
  production:
    hostname: example.com
    username: ubuntu
    port: 22
    key_file: ~/.ssh/id_rsa
    wp_path: /var/www/html
    
  staging:
    hostname: staging.example.com
    username: ubuntu
    port: 22
    key_file: ~/.ssh/id_rsa
    wp_path: /var/www/staging
    
  local:
    hostname: localhost
    username: user
    wp_path: /Users/user/Sites/wordpress

# WordPress defaults
wordpress:
  author: admin
  category: Uncategorized
  status: publish
  comment_status: open

# Output format
output:
  format: table  # table, json, yaml
  color: true
  verbose: false
```

## Server Configuration

### SSH Connection

```yaml
servers:
  myserver:
    # Required
    hostname: example.com
    username: ubuntu
    wp_path: /var/www/html
    
    # Optional
    port: 22
    key_file: ~/.ssh/id_rsa
    password: null  # Use key_file instead
    timeout: 30
    
    # WP-CLI path (if not in PATH)
    wp_cli_path: /usr/local/bin/wp
```

### Multiple Servers

```yaml
servers:
  prod:
    hostname: prod.example.com
    username: ubuntu
    wp_path: /var/www/html
    
  staging:
    hostname: staging.example.com
    username: ubuntu
    wp_path: /var/www/staging
    
  dev:
    hostname: dev.example.com
    username: developer
    wp_path: /home/developer/wordpress
```

### Server Groups

```yaml
server_groups:
  all_sites:
    - prod
    - staging
    - dev
  
  production_only:
    - prod
```

## WordPress Configuration

### Post Defaults

```yaml
wordpress:
  posts:
    author: admin
    status: publish
    type: post
    category: Blog
    comment_status: open
    ping_status: open
    
  pages:
    author: admin
    status: draft
    type: page
    comment_status: closed
```

### Content Settings

```yaml
content:
  # Block conversion
  auto_convert_blocks: true
  preserve_html: true
  
  # Gutenberg blocks
  default_blocks:
    - paragraph
    - heading
    - list
    - code
    - image
  
  # Media
  media_upload_path: wp-content/uploads
  max_image_size: 2048
  image_quality: 85
```

## AI Configuration

### API Keys

```yaml
ai:
  provider: openai  # openai, anthropic, google
  
  openai:
    api_key: ${OPENAI_API_KEY}
    organization: ${OPENAI_ORG_ID}
    model: gpt-4
    base_url: https://api.openai.com/v1
    
  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    model: claude-3-opus-20240229
    
  google:
    api_key: ${GOOGLE_API_KEY}
    model: gemini-pro
```

### Model Settings

```yaml
ai:
  models:
    default:
      temperature: 0.7
      max_tokens: 2000
      top_p: 1.0
      frequency_penalty: 0.0
      presence_penalty: 0.0
    
    creative:
      temperature: 0.9
      max_tokens: 3000
    
    factual:
      temperature: 0.3
      max_tokens: 1500
```

### AI Features

```yaml
ai:
  features:
    # Content generation
    generation:
      enabled: true
      default_length: medium
      tone: professional
      
    # Translation
    translation:
      enabled: true
      preserve_formatting: true
      auto_detect_language: true
      
    # SEO
    seo:
      enabled: true
      generate_meta: true
      suggest_keywords: true
      
    # Image generation
    image:
      enabled: true
      model: dall-e-3
      size: 1024x1024
      quality: standard
```

## Output Configuration

### Format Options

```yaml
output:
  # Default format
  format: table  # table, json, yaml, csv
  
  # Table settings
  table:
    max_width: 120
    truncate: true
    borders: true
    
  # JSON settings
  json:
    pretty: true
    indent: 2
    
  # Colors
  colors:
    enabled: true
    success: green
    error: red
    warning: yellow
    info: blue
```

### Logging

```yaml
logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR
  file: ~/.praisonaiwp/logs/praisonaiwp.log
  max_size: 10485760  # 10MB
  backup_count: 5
  
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
  # Log to console
  console: true
  console_level: WARNING
```

## Cache Configuration

```yaml
cache:
  enabled: true
  ttl: 3600  # seconds
  
  # Cache directory
  directory: ~/.praisonaiwp/cache
  
  # What to cache
  cache_posts: true
  cache_media: true
  cache_users: false
  
  # Cache size limits
  max_size: 104857600  # 100MB
  max_entries: 1000
```

## Performance Configuration

```yaml
performance:
  # Parallel operations
  parallel:
    enabled: true
    max_workers: 4
    
  # Batch operations
  batch:
    size: 10
    delay: 1  # seconds between batches
    
  # Timeouts
  timeouts:
    connect: 10
    read: 30
    write: 30
    
  # Retries
  retries:
    max_attempts: 3
    backoff_factor: 2
```

## Security Configuration

```yaml
security:
  # SSH
  ssh:
    strict_host_key_checking: true
    known_hosts_file: ~/.ssh/known_hosts
    
  # API keys
  api_keys:
    encrypt: true
    keyring: true  # Use system keyring
    
  # Credentials
  credentials:
    store: keyring  # keyring, file, env
    file: ~/.praisonaiwp/credentials.enc
```

## Environment Variables

### Required

```bash
# AI Provider API Keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."
```

### Optional

```bash
# Configuration
export PRAISONAIWP_CONFIG="~/.praisonaiwp/config.yml"
export PRAISONAIWP_LOG_LEVEL="INFO"

# Server defaults
export PRAISONAIWP_SERVER="production"
export PRAISONAIWP_WP_PATH="/var/www/html"

# Output
export PRAISONAIWP_FORMAT="json"
export PRAISONAIWP_COLOR="true"

# Cache
export PRAISONAIWP_CACHE_DIR="~/.praisonaiwp/cache"
export PRAISONAIWP_CACHE_TTL="3600"
```

## Command-Line Options

### Global Options

```bash
# Config file
praisonaiwp --config /path/to/config.yml

# Server selection
praisonaiwp --server production

# Output format
praisonaiwp --json
praisonaiwp --yaml
praisonaiwp --format table

# Verbosity
praisonaiwp --verbose
praisonaiwp --quiet

# No color
praisonaiwp --no-color
```

### Priority Order

1. Command-line options (highest)
2. Environment variables
3. Config file
4. Defaults (lowest)

## Configuration Examples

### Minimal Setup

```yaml
default_server: prod

servers:
  prod:
    hostname: example.com
    username: ubuntu
    wp_path: /var/www/html
```

### Full Setup

```yaml
default_server: production

servers:
  production:
    hostname: prod.example.com
    username: ubuntu
    port: 22
    key_file: ~/.ssh/prod_key
    wp_path: /var/www/html
    wp_cli_path: /usr/local/bin/wp
    timeout: 30

wordpress:
  posts:
    author: admin
    status: publish
    category: Blog
    comment_status: open
  pages:
    status: draft
    comment_status: closed

ai:
  provider: openai
  openai:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4
  models:
    default:
      temperature: 0.7
      max_tokens: 2000

output:
  format: table
  colors:
    enabled: true
  
logging:
  level: INFO
  file: ~/.praisonaiwp/logs/app.log

cache:
  enabled: true
  ttl: 3600
  directory: ~/.praisonaiwp/cache

performance:
  parallel:
    enabled: true
    max_workers: 4
  batch:
    size: 10
    delay: 1
```

### Multi-Environment

```yaml
default_server: ${ENVIRONMENT:-staging}

servers:
  production:
    hostname: prod.example.com
    username: ubuntu
    wp_path: /var/www/html
    
  staging:
    hostname: staging.example.com
    username: ubuntu
    wp_path: /var/www/staging
    
  development:
    hostname: localhost
    username: developer
    wp_path: /Users/dev/Sites/wp

wordpress:
  posts:
    author: ${WP_AUTHOR:-admin}
    status: ${WP_STATUS:-publish}

ai:
  provider: ${AI_PROVIDER:-openai}
  openai:
    api_key: ${OPENAI_API_KEY}
    model: ${OPENAI_MODEL:-gpt-4}

output:
  format: ${OUTPUT_FORMAT:-table}
```

## Configuration Validation

### Check Configuration

```bash
praisonaiwp config validate
```

### Show Current Configuration

```bash
praisonaiwp config show
praisonaiwp config show --server production
praisonaiwp config show --format json
```

### Test Server Connection

```bash
praisonaiwp server test
praisonaiwp server test --server production
```

## Configuration Management

### Initialize Configuration

```bash
praisonaiwp init
praisonaiwp init --interactive
```

### Add Server

```bash
praisonaiwp config server add \
  --name production \
  --hostname example.com \
  --username ubuntu \
  --wp-path /var/www/html
```

### Set Default Server

```bash
praisonaiwp config set default_server production
```

### Get Configuration Value

```bash
praisonaiwp config get servers.production.hostname
praisonaiwp config get wordpress.posts.author
```

### Set Configuration Value

```bash
praisonaiwp config set wordpress.posts.status publish
praisonaiwp config set ai.provider openai
```

## Troubleshooting

### Debug Mode

```bash
export PRAISONAIWP_LOG_LEVEL=DEBUG
praisonaiwp --verbose [command]
```

### Connection Issues

```yaml
servers:
  myserver:
    # Increase timeout
    timeout: 60
    
    # Use password instead of key
    password: your_password
    
    # Custom port
    port: 2222
```

### Permission Issues

```bash
# Check SSH key permissions
chmod 600 ~/.ssh/id_rsa

# Check config file permissions
chmod 600 ~/.praisonaiwp/config.yml
```

### Cache Issues

```bash
# Clear cache
rm -rf ~/.praisonaiwp/cache/*

# Disable cache
praisonaiwp --no-cache [command]
```
