# PraisonAI WPcli

AI-powered WordPress CLI tool for content management with precision editing capabilities.

## Features

### 🎉 NEW in v1.7.0: Complete WP-CLI Command Coverage!
**15 additional WP-CLI commands for 100% WordPress management coverage!**

#### New WP-CLI Commands Added:
- **ability** - Manage user capabilities and permissions
- **admin** - WordPress admin management (URL, paths, settings)
- **block** - WordPress block management and registration
- **cap** - Role capability management
- **cli** - WP-CLI management and utilities
- **dist-archive** - Create distribution archives
- **embed** - WordPress embed management and providers
- **eval-file** - Execute PHP files in WordPress context
- **i18n** - Internationalization (POT/PO/MO file management)
- **language** - Language pack management
- **package** - WP-CLI package management
- **profile** - WordPress performance profiling
- **shell** - Interactive WordPress shell

**Total Commands: 65+** - Complete coverage of all standard WP-CLI functionality!

---

### 🎉 NEW in v1.6.0: Complete AI Feature Suite!
**15 powerful AI-powered features for WordPress content management!**

#### AI Content Generation & Optimization
- **AI Content Summarizer** - Generate summaries, excerpts, and social media posts
- **AI Content Optimizer** - Optimize content for SEO, readability, and engagement  
- **AI Content Translator** - Translate content to multiple languages with AI
- **AI Content Scheduler** - Intelligent content scheduling and analytics
- **AI Comment Moderator** - AI-powered comment moderation and response generation
- **AI Content Curator** - Curate and suggest related content automatically

#### AI Research & Analysis
- **AI Research Assistant** - Research topics and generate comprehensive content with citations
- **AI Image Generator** - Generate and optimize images for WordPress posts
- **AI Chatbot Integration** - Add AI-powered chatbot to WordPress site
- **AI Performance Analyzer** - Analyze content performance and provide insights
- **AI SEO Auditor** - Comprehensive SEO analysis and optimization

#### AI Automation & Workflow
- **AI Workflow Builder** - Create and manage automated content workflows
- **AI Bulk Operations** - Perform bulk AI operations on multiple posts

#### Usage Examples:
```bash
# Generate AI content
praisonaiwp ai generate "AI Trends 2025" --auto-publish

# Summarize content
praisonaiwp ai summarize post 123 --excerpt --social twitter,linkedin

# Optimize for SEO
praisonaiwp ai optimize post 123 --seo --readability --apply

# Translate content
praisonaiwp ai translate post 123 --to es,fr,de --create-new

# Schedule content
praisonaiwp ai schedule analyze --days 30

# Moderate comments
praisonaiwp ai moderate comments --auto-approve

# Curate related content
praisonaiwp ai curate related 123 --count 5

# Research topics
praisonaiwp ai research topic "Machine Learning" --depth comprehensive

# Generate images
praisonaiwp ai image generate "AI technology" --style photorealistic

# Deploy chatbot
praisonaiwp ai chatbot deploy --widget-style modern

# Analyze performance
praisonaiwp ai analyze performance 123

# SEO audit
praisonaiwp ai seo audit 123 --depth comprehensive

# Create workflow
praisonaiwp ai workflow create "Content Pipeline" --trigger schedule

# Bulk operations
praisonaiwp ai bulk process --category "Technology" --operation optimize
```

#### AI Features Overview:
- ✅ **15 AI Commands** - Complete suite of AI-powered tools
- ✅ **Multi-language Support** - Translate to 20+ languages
- ✅ **SEO Optimization** - Intelligent SEO analysis and recommendations
- ✅ **Content Automation** - Automated workflows and bulk operations
- ✅ **Performance Analytics** - AI-driven insights and predictions
- ✅ **Image Generation** - AI-powered image creation and optimization
- ✅ **Chatbot Integration** - Deploy AI chatbots on WordPress sites
- ✅ **Research Assistant** - AI-powered research with citations
- ✅ **Comment Moderation** - Intelligent comment analysis and responses

---

### 🎉 NEW in v1.5.1: Enhanced WordPress Management!
**AI agent that automatically detects the correct website for your content!**

```python
from praisonaiwp.ai.smart_agent import SmartContentAgent
from praisonaiwp import WPClient, SSHManager, Config

# Initialize
config = Config()
ssh = SSHManager.from_config(config, 'biblerevelation')
client = WPClient(ssh, config.get_server('biblerevelation')['wp_path'])

# Create smart agent
agent = SmartContentAgent(client, config.data)

# Auto-detect server from content
result = agent.create_post_with_routing(
    title="Immanuel — God With Us",
    content="<p>Bible teaching for biblerevelation.org</p>",
    status='publish'
)
# → Automatically routes to biblerevelation server
# → Applies author='praison', category='AI'

# Get server suggestion with confidence
suggestion = agent.suggest_server({
    'title': 'Bible Study',
    'tags': ['bible', 'teaching']
})
# → {'server': 'biblerevelation', 'confidence': 0.9, 'reason': 'Matching tags: bible, teaching'}
```

**SmartContentAgent Features:**
- ✅ **Auto-Detection** - Detects server from title, content, or tags
- ✅ **Confidence Scoring** - Provides confidence level for suggestions
- ✅ **Tag Matching** - Matches content tags with server tags
- ✅ **Server Defaults** - Auto-applies author, category per server
- ✅ **Context-Aware AI** - Considers server description when generating
- ✅ **10 Tests** - 100% passing, fully tested

---

### 🚀 NEW in v1.4.0: Configuration v2.0 with Auto-Routing!
**Enhanced server configuration with website URLs and intelligent routing!**

```yaml
# ~/.praisonaiwp/config.yaml (v2.0)
version: '2.0'
servers:
  biblerevelation:
    website: https://biblerevelation.org      # NEW: Primary URL
    aliases:                                   # NEW: Alternative domains
      - https://www.biblerevelation.org
    description: "Bible revelation website"   # NEW: Human-readable
    tags: [bible, christian, teaching]        # NEW: For AI matching
    author: praison                            # NEW: Default author
    category: AI                               # NEW: Default category
    hostname: christsong.in
    username: biblerevelation
    # ... other settings

settings:
  auto_route: true  # NEW: Enable automatic server selection
```

**Configuration v2.0 Features:**
- ✅ **Website URLs** - Clear mapping of servers to websites
- ✅ **Aliases** - Support multiple domains per server
- ✅ **Descriptions** - Human-readable server information
- ✅ **Tags** - AI-friendly content classification
- ✅ **Server Defaults** - Per-server author and category
- ✅ **Auto-Migration** - Automatic upgrade from v1.0
- ✅ **Backward Compatible** - v1.0 configs still work
- ✅ **24 Tests** - Comprehensive test coverage

**ServerRouter API:**
```python
from praisonaiwp.core.router import ServerRouter

router = ServerRouter(config)

# Find server by website URL
server, config = router.find_server_by_website('biblerevelation.org')

# Find server by keywords in content
server, config = router.find_server_by_keywords(
    "Post for biblerevelation.org about Immanuel"
)

# Get server information
info = router.get_server_info('biblerevelation')
# → {'name': 'biblerevelation', 'website': 'https://biblerevelation.org', ...}
```

---

### 🎉 NEW in v1.1.0: Production-Ready AI Integration!
**AI-powered content generation with PraisonAI framework!**

```bash
# Install with AI features
pip install praisonaiwp[ai]

# Set your OpenAI API key
export OPENAI_API_KEY="sk-..."

# Generate content
praisonaiwp ai generate "AI Trends 2025"

# Generate and auto-publish
praisonaiwp ai generate "AI Trends" \
  --title "The Future of AI" \
  --auto-publish \
  --status publish
```

**AI Features:**
- ✅ **PraisonAI Integration** - Multi-agent content generation
- ✅ **Production-Ready** - API validation, retry logic, cost tracking
- ✅ **Cost-Effective** - Default gpt-4o-mini (~$0.0005 per 500-word post)
- ✅ **Quality Control** - Content validation, length checks, structure validation
- ✅ **Auto-Publish** - Direct WordPress publishing with one command
- ✅ **Rate Limiting** - Prevents API errors
- ✅ **58 Tests** - 100% passing, production-ready

See **[PRAISONAI.md](PRAISONAI.md)** for complete AI documentation.

---

### 🔌 NEW in v1.3.0: MCP (Model Context Protocol) Support!
**Connect PraisonAIWP to Claude Desktop, Cursor, VS Code, and other MCP clients!**

```bash
# Install with MCP support
pip install praisonaiwp[mcp]

# View available tools
praisonaiwp mcp info

# Run MCP server
praisonaiwp mcp run

# Install in Claude Desktop
praisonaiwp mcp install
```

**MCP Features:**
- ✅ **23 WordPress Tools** - Create, update, delete posts, manage users, plugins, themes
- ✅ **8 Resources** - Read-only access to WordPress data
- ✅ **4 Prompt Templates** - Blog post creation, SEO optimization, bulk updates
- ✅ **Multiple Transports** - stdio (default) and HTTP
- ✅ **Claude Desktop Integration** - One-command installation
- ✅ **57 Tests** - 100% passing, production-ready

**Available Tools:**
| Category | Tools |
|----------|-------|
| **Posts** | `create_post`, `update_post`, `delete_post`, `get_post`, `list_posts`, `find_text` |
| **Categories** | `list_categories`, `set_post_categories`, `create_term` |
| **Users** | `list_users`, `create_user`, `get_user` |
| **Plugins** | `list_plugins`, `activate_plugin`, `deactivate_plugin` |
| **Themes** | `list_themes`, `activate_theme` |
| **Media** | `import_media` |
| **System** | `flush_cache`, `get_core_version`, `db_query`, `search_replace`, `wp_cli` |

**Claude Desktop Configuration:**
```json
{
  "mcpServers": {
    "praisonaiwp": {
      "command": "praisonaiwp",
      "args": ["mcp", "run"]
    }
  }
}
```

---

### 🚀 NEW in v1.0.13: Universal WP-CLI Access!
**ALL 1000+ WP-CLI commands now supported via the generic `wp()` method!**

```python
from praisonaiwp import SSHManager, WPClient

ssh = SSHManager('example.com', 'username')
client = WPClient(ssh, '/var/www/html')

# Use ANY WP-CLI command!
client.wp('cache', 'flush')
client.wp('db', 'export', 'backup.sql')
client.wp('plugin', 'install', 'akismet')
posts = client.wp('post', 'list', status='publish', format='json')
```

See [GENERIC_WP_METHOD.md](GENERIC_WP_METHOD.md) for complete documentation.

### Core Features
- 🚀 **Universal WP-CLI** - Direct access to ALL WP-CLI commands via `wp()` method
- 🎯 **Convenience Methods** - 48 wrapper methods with IDE autocomplete for common operations
- ⚡ **Fast** - Auto-parallel mode for bulk operations (10x faster)
- 🔒 **Safe** - Auto-backup, preview mode, dry-run capabilities
- 🌐 **Multi-Server** - Manage multiple WordPress installations
- 📝 **Smart** - Auto JSON parsing, underscore-to-hyphen conversion

## All Supported Features

### 📝 Post Management (6 methods)
- `create_post()` - Create posts with metadata
- `update_post()` - Update post fields
- `list_posts()` - List with WP_Query filters
- `get_post()` - Get post details
- `delete_post()` - Delete posts (trash/force)
- `post_exists()` - Check post existence

### 🏷️ Post Meta (4 methods)
- `get_post_meta()` - Get meta values
- `set_post_meta()` - Add meta fields
- `update_post_meta()` - Update meta
- `delete_post_meta()` - Remove meta

### 📂 Category/Term Management (8 methods)
- `set_post_categories()` - Set categories
- `add_post_category()` - Add category
- `remove_post_category()` - Remove category
- `list_categories()` - List all categories
- `get_post_categories()` - Get post categories
- `create_term()` - Create new term
- `delete_term()` - Delete term
- `update_term()` - Update term

### 👥 User Management (9 methods)
- `list_users()` - List all users
- `get_user()` - Get user details
- `create_user()` - Create new user
- `update_user()` - Update user fields
- `delete_user()` - Delete user (with reassign)
- `get_user_meta()` - Get user meta
- `set_user_meta()` - Set user meta
- `update_user_meta()` - Update user meta
- `delete_user_meta()` - Delete user meta

### ⚙️ Option Management (3 methods)
- `get_option()` - Get option value
- `set_option()` - Set option value
- `delete_option()` - Delete option

### 🔌 Plugin Management (4 methods)
- `list_plugins()` - List all plugins
- `update_plugin()` - Update plugin(s)
- `activate_plugin()` - Activate plugin
- `deactivate_plugin()` - Deactivate plugin

### 🎨 Theme Management (2 methods)
- `list_themes()` - List all themes
- `activate_theme()` - Activate theme

### 📷 Media Management (1 method + CLI)
- `import_media()` - Import media with metadata
- **CLI**: `praisonaiwp media` - Upload media files

### 💬 Comment Management (6 methods)
- `list_comments()` - List comments
- `get_comment()` - Get comment details
- `create_comment()` - Create comment
- `update_comment()` - Update comment
- `delete_comment()` - Delete comment
- `approve_comment()` - Approve comment

### 🗄️ Cache Management (2 methods)
- `flush_cache()` - Flush object cache
- `get_cache_type()` - Get cache type

### ⏱️ Transient Management (3 methods)
- `get_transient()` - Get transient value
- `set_transient()` - Set transient with expiration
- `delete_transient()` - Delete transient

### 🧭 Menu Management (4 methods)
- `list_menus()` - List navigation menus
- `create_menu()` - Create new menu
- `delete_menu()` - Delete menu
- `add_menu_item()` - Add menu item

### 🌐 Core Commands (2 methods)
- `get_core_version()` - Get WordPress version
- `core_is_installed()` - Check installation

### 💾 Database (2 methods)
- `db_query()` - Execute SQL query
- `search_replace()` - Search and replace in database

### 🚀 Plus UNLIMITED via `wp()` Method!
Use ANY WP-CLI command directly:
```python
# Database operations
client.wp('db', 'export', 'backup.sql')
client.wp('db', 'import', 'backup.sql')
client.wp('db', 'optimize')

# Plugin operations
client.wp('plugin', 'install', 'akismet')
client.wp('plugin', 'update', '--all')

# Theme operations
client.wp('theme', 'install', 'twentytwentyfour')

# Cron management
client.wp('cron', 'event', 'list', format='json')
client.wp('cron', 'event', 'run', 'wp_version_check')

# Core management
client.wp('core', 'update')
client.wp('core', 'verify-checksums')

# Media operations
client.wp('media', 'regenerate', '--yes')

# Export/Import
client.wp('export', author='admin')
client.wp('import', 'content.xml')

# ANY WP-CLI command works!
```

**Total: 48 convenience methods + 1000+ commands via `wp()`** 🎉

### Previous Updates (v1.0.2)
- 🔑 **SSH Config Support** - Use `~/.ssh/config` host aliases for simplified connection management
- 🔧 **WP-CLI Auto-Installer** - One-command WP-CLI installation with automatic OS detection (Ubuntu, Debian, CentOS, RHEL, Fedora, Alpine, macOS)
- 🔍 **WordPress Auto-Detection** - Automatically find WordPress installations on your server with multiple search strategies
- ⚡ **UV Package Manager** - 10-100x faster dependency management with modern tooling
- 🛡️ **Enhanced Error Handling** - Helpful error messages with installation instructions and troubleshooting
- 📊 **Installation Verification** - Automatic checks for WP-CLI and WordPress validity on startup

## Installation

### Using pip (Recommended)

```bash
# Core only (WordPress management)
pip install praisonaiwp

# With AI features (recommended)
pip install praisonaiwp[ai]

# With MCP support (for Claude Desktop, Cursor, etc.)
pip install praisonaiwp[mcp]

# With development tools
pip install praisonaiwp[dev]

# Everything
pip install praisonaiwp[all]
```

### Using uv (10x faster!)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone https://github.com/MervinPraison/PraisonAI-WPcli.git
cd PraisonAI-WPcli
uv sync

# Run commands
uv run praisonaiwp init
```

### From source

```bash
git clone https://github.com/MervinPraison/PraisonAI-WPcli.git
cd PraisonAI-WPcli
pip install -e ".[ai]"  # With AI features
```

## Quick Start

### 1. Initialize Configuration

```bash
praisonaiwp init
```

**💡 Pro Tips:**
- Use SSH config alias (e.g., `wp-prod`) - connection details loaded automatically!
- Press Enter for WordPress path - auto-detection will find it for you
- PHP binary is auto-detected, or specify for Plesk: `/opt/plesk/php/8.3/bin/php`

**🔑 SSH Config Support:**

PraisonAIWP automatically reads from `~/.ssh/config`. If you have multiple hosts configured:

```ssh-config
# ~/.ssh/config
Host wp-prod
    HostName production.example.com
    User prod_user
    IdentityFile ~/.ssh/id_prod

Host wp-staging
    HostName staging.example.com
    User staging_user
    IdentityFile ~/.ssh/id_staging

Host wp-dev
    HostName localhost
    User dev_user
    Port 2222
    IdentityFile ~/.ssh/id_dev
```

Just enter the host alias (e.g., `wp-prod`, `wp-staging`, or `wp-dev`) when prompted for hostname, and PraisonAIWP will automatically load all connection details from your SSH config!

**Choosing Between Multiple Configs:**
- Each host alias is independent
- Use `--server` flag to specify which server to use:
  ```bash
  praisonaiwp create "Post" --server production
  praisonaiwp create "Post" --server staging
  ```
- Configure multiple servers in `~/.praisonaiwp/config.yaml`:
  ```yaml
  servers:
    # Method 1: Using ssh_host (recommended)
    production:
      ssh_host: wp-prod  # Reference SSH config host
      wp_path: /var/www/html
      wp_cli: /usr/local/bin/wp
    
    # Method 2: Direct specification (traditional)
    staging:
      hostname: staging.example.com
      username: staging_user
      key_file: ~/.ssh/id_staging
      port: 22
      wp_path: /var/www/staging
      wp_cli: /usr/local/bin/wp
    
    # Method 3: Mix both (direct values override ssh_host)
    dev:
      ssh_host: wp-dev
      username: custom_user  # Override SSH config username
      wp_path: /var/www/dev
      wp_cli: /usr/local/bin/wp
  ```
  
  **New in v1.0.5:** Use `ssh_host` to reference SSH config hosts! Connection details (hostname, username, key_file, port) are automatically loaded from `~/.ssh/config`. You can also specify connection details directly (traditional method) or mix both approaches - direct values always take precedence.

This will prompt you for:
- **Server hostname** - Can be IP, hostname, or SSH config alias (e.g., `wp-prod`)
- **SSH username** - Auto-loaded from SSH config if using alias
- **SSH key path** - Auto-loaded from SSH config if using alias  
- **WordPress path** - Press Enter to auto-detect, or specify manually
- **PHP binary** - Auto-detected, or specify custom path

### 2. Auto-Install WP-CLI (Optional)

If WP-CLI is not installed on your server:

```bash
# Automatically detect OS and install WP-CLI
praisonaiwp install-wp-cli -y

# Install with dependencies (curl, php)
praisonaiwp install-wp-cli --install-deps -y

# Custom installation path
praisonaiwp install-wp-cli --install-path /usr/bin/wp

# For Plesk servers
praisonaiwp install-wp-cli --php-bin /opt/plesk/php/8.3/bin/php -y
```

**Supported Operating Systems:**
- ✅ Ubuntu (18.04, 20.04, 22.04, 24.04)
- ✅ Debian (9, 10, 11, 12)
- ✅ CentOS (7, 8, 9)
- ✅ RHEL (7, 8, 9)
- ✅ Fedora (35+)
- ✅ Alpine Linux
- ✅ macOS (with Homebrew)

**What it does:**
1. Detects your server's operating system
2. Downloads WP-CLI from official source
3. Tests the download
4. Makes it executable
5. Installs to system path
6. Verifies installation
7. Updates your config automatically

### 3. Auto-Detect WordPress (Optional)

If you don't know your WordPress installation path:

```bash
# Find all WordPress installations
praisonaiwp find-wordpress

# Interactive selection from multiple installations
praisonaiwp find-wordpress --interactive

# Find and update config automatically
praisonaiwp find-wordpress --update-config

# Find on different server
praisonaiwp find-wordpress --server staging
```

**Search Strategies:**
- Searches for `wp-config.php` in common directories
- Checks predefined paths (`/var/www/html`, `/var/www/vhosts/*/httpdocs`, etc.)
- Verifies each installation (wp-config, wp-content, wp-includes)
- Extracts WordPress version
- Interactive selection for multiple installations

**Example Output:**
```
✓ Found 2 WordPress installation(s)

┏━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ # ┃ Path                                ┃ Version ┃ Components              ┃
┡━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1 │ /var/www/html                       │ 6.4.2   │ config, content, includes│
│ 2 │ /var/www/vhosts/example.com/httpdocs│ 6.3.1   │ config, content, includes│
└───┴─────────────────────────────────────┴─────────┴─────────────────────────┘
```

## Gutenberg Block Format

WordPress uses Gutenberg blocks for content. By default, HTML content is auto-converted to blocks. Use `--no-block-conversion` to send raw Gutenberg block markup directly.

### Primary Blocks

```html
<!-- Paragraph -->
<!-- wp:paragraph -->
<p>Your text here</p>
<!-- /wp:paragraph -->

<!-- Heading (h2) -->
<!-- wp:heading -->
<h2 class="wp-block-heading">Title</h2>
<!-- /wp:heading -->

<!-- Heading (h3) -->
<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Subtitle</h3>
<!-- /wp:heading -->

<!-- Code block -->
<!-- wp:code -->
<pre class="wp-block-code"><code>your code here</code></pre>
<!-- /wp:code -->

<!-- Table -->
<!-- wp:table -->
<figure class="wp-block-table"><table><thead><tr><th>Header</th></tr></thead>
<tbody><tr><td>Cell</td></tr></tbody></table></figure>
<!-- /wp:table -->

<!-- Separator -->
<!-- wp:separator -->
<hr class="wp-block-separator has-alpha-channel-opacity"/>
<!-- /wp:separator -->

<!-- List (unordered) -->
<!-- wp:list -->
<ul class="wp-block-list"><li>Item 1</li><li>Item 2</li></ul>
<!-- /wp:list -->

<!-- List (ordered) -->
<!-- wp:list {"ordered":true} -->
<ol class="wp-block-list"><li>First</li><li>Second</li></ol>
<!-- /wp:list -->

<!-- Image -->
<!-- wp:image {"id":123} -->
<figure class="wp-block-image"><img src="URL" alt="Alt text"/></figure>
<!-- /wp:image -->

<!-- Quote -->
<!-- wp:quote -->
<blockquote class="wp-block-quote"><p>Quote text</p><cite>Author</cite></blockquote>
<!-- /wp:quote -->

<!-- Columns (2 columns) -->
<!-- wp:columns -->
<div class="wp-block-columns">
<!-- wp:column -->
<div class="wp-block-column"><!-- wp:paragraph --><p>Col 1</p><!-- /wp:paragraph --></div>
<!-- /wp:column -->
<!-- wp:column -->
<div class="wp-block-column"><!-- wp:paragraph --><p>Col 2</p><!-- /wp:paragraph --></div>
<!-- /wp:column -->
</div>
<!-- /wp:columns -->

<!-- Button -->
<!-- wp:buttons -->
<div class="wp-block-buttons">
<!-- wp:button -->
<div class="wp-block-button"><a class="wp-block-button__link">Click Me</a></div>
<!-- /wp:button -->
</div>
<!-- /wp:buttons -->
```

### Other Blocks

Same pattern `<!-- wp:NAME -->...<!-- /wp:NAME -->`:

`preformatted`, `pullquote`, `verse`, `audio`, `video`, `file`, `gallery`, `cover`, `media-text`, `group`, `spacer`, `embed`, `html`, `shortcode`, `details`

### Usage Examples

```bash
# Create post with HTML (auto-converts to blocks)
praisonaiwp create "My Post" --content "<h2>Title</h2><p>Content</p>"

# Create post with raw Gutenberg blocks
praisonaiwp create "My Post" --no-block-conversion --content "<!-- wp:paragraph --><p>Hello</p><!-- /wp:paragraph -->"

# Update post with raw Gutenberg blocks
praisonaiwp update 123 --no-block-conversion --post-content "<!-- wp:heading --><h2 class=\"wp-block-heading\">New Title</h2><!-- /wp:heading -->"
```

---

### 4. Create Posts

```bash
# Single post
praisonaiwp create "My Post Title" --content "Post content here"

# With author (NEW in v1.0.14)
praisonaiwp create "My Post" --content "Content" --author praison
praisonaiwp create "My Post" --content "Content" --author 1  # By user ID

# With categories
praisonaiwp create "My Post" --content "Hello" --category "Tech,AI"

# From file (auto-detects JSON/YAML/CSV)
praisonaiwp create posts.json

# Create 100 posts (automatically uses parallel mode!)
praisonaiwp create 100_posts.json
```

### 5. Update Posts

```bash
# Find and replace text
praisonaiwp update 123 "old text" "new text"

# Update specific line only
praisonaiwp update 123 "old text" "new text" --line 10

# Update 2nd occurrence only
praisonaiwp update 123 "old text" "new text" --nth 2

# Preview changes first
praisonaiwp update 123 "old text" "new text" --preview

# Update post fields directly (NEW in v1.0.14)
praisonaiwp update 123 --post-content "Full new content"
praisonaiwp update 123 --post-title "New Title"
praisonaiwp update 123 --post-status draft

# Update categories
praisonaiwp update 123 --category "Tech,AI"
```

### 6. Find Text

```bash
# Find in specific post
praisonaiwp find "search text" 123

# Find across all posts
praisonaiwp find "search text"

# Find in pages
praisonaiwp find "search text" --type page
```

### 7. List Posts

```bash
# List all posts
praisonaiwp list

# Search posts (NEW in v1.0.14)
praisonaiwp list --search "Pricing"
praisonaiwp list -s "keyword"

# List pages
praisonaiwp list --type page

# List drafts
praisonaiwp list --status draft

# Limit results
praisonaiwp list --limit 10
```

### 8. Manage Categories

```bash
# List all categories
praisonaiwp category list

# Search for categories
praisonaiwp category search "Technology"

# List categories for a specific post
praisonaiwp category list 123

# Set categories (replace all)
praisonaiwp category set 123 --category "Tech,AI"

# Add categories (append)
praisonaiwp category add 123 --category "Python"

# Remove categories
praisonaiwp category remove 123 --category "Uncategorized"

# Create post with categories
praisonaiwp create "My Post" --content "Hello" --category "Tech,AI"

# Update post categories
praisonaiwp update 123 --category "Tech,Python"
```

### 9. AI Content Generation (NEW in v1.1.0)

```bash
# Set your OpenAI API key (required)
export OPENAI_API_KEY="sk-..."

# Generate content (creates draft)
praisonaiwp ai generate "AI Trends 2025"

# Generate with custom title
praisonaiwp ai generate "AI Trends" --title "The Future of AI"

# Generate and auto-publish
praisonaiwp ai generate "AI Trends" \
  --title "The Future of AI" \
  --auto-publish \
  --status publish

# Verbose mode (see generation details)
praisonaiwp ai generate "AI Trends" --verbose

# Use different server
praisonaiwp ai generate "AI Trends" --server production
```

**AI Features:**
- Powered by PraisonAI multi-agent framework
- Default model: gpt-4o-mini (cost-effective)
- Automatic content validation
- Cost tracking
- Retry logic with exponential backoff
- Rate limiting to prevent API errors

**Programmatic Usage:**
```python
from praisonaiwp.ai.integration import PraisonAIWPIntegration
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient

# Setup
ssh = SSHManager(hostname="example.com", username="user", key_file="~/.ssh/id_rsa")
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
print(f"Duration: {result['duration']:.2f}s")
```

**See [PRAISONAI.md](PRAISONAI.md) for complete AI documentation.**

## AI Production Features

The AI integration includes enterprise-grade production features:

### 1. API Key Validation
- Validates OpenAI API key on initialization
- Clear error messages with setup instructions
- Format checking (must start with 'sk-')

### 2. Content Validation
- **Length checks**: Minimum 100 chars, maximum 10,000 chars (configurable)
- **Paragraph structure**: Requires at least 2 paragraph breaks
- **Placeholder detection**: Detects [INSERT], TODO, PLACEHOLDER text
- **Skip option**: Use `skip_validation=True` to bypass

### 3. Cost Tracking
- **Per-generation tracking**: Track cost for each post
- **Cumulative tracking**: Total cost across all generations
- **Model-specific pricing**: Accurate pricing for gpt-4o-mini, gpt-4o, etc.
- **Cost estimation**: See estimated cost before generation

**Example:**
```python
# Get cost summary
summary = integration.get_cost_summary()
print(f"Total cost: ${summary['total_cost']:.6f}")
print(f"Average cost: ${summary['average_cost']:.6f}")
```

### 4. Retry Logic with Exponential Backoff
- **Automatic retries**: 3 attempts on failure
- **Exponential backoff**: 1s, 2s, 4s delays
- **Smart error handling**: Distinguishes temporary vs permanent errors
- **Configurable**: Adjust max retries and delays

### 5. Rate Limiting
- **Default limits**: 10 requests per 60 seconds
- **Automatic waiting**: Waits when limit reached
- **Configurable**: Adjust limits per your needs
- **Can be disabled**: For unlimited usage

**Example:**
```python
integration = PraisonAIWPIntegration(
    wp_client,
    enable_rate_limiting=True,
    max_requests=10,
    time_window=60
)
```

### 6. Structured Logging
- **Generation metrics**: Duration, cost, word count
- **Progress tracking**: Real-time generation status
- **Error logging**: Detailed error messages
- **Verbose mode**: Use `--verbose` flag for details

### 7. Enhanced Result Metadata
Every generation returns comprehensive metadata:
```python
{
    'content': str,           # Generated content
    'post_id': int,           # WordPress post ID (if published)
    'cost': float,            # Estimated cost in USD
    'duration': float,        # Generation time in seconds
    'model': str,             # Model used (e.g., 'gpt-4o-mini')
    'metadata': {
        'topic': str,         # Original topic
        'title': str,         # Post title
        'length': int,        # Content length in chars
        'word_count': int     # Word count
    }
}
```

### Cost Comparison

| Model | Speed | Cost/500 words | Quality | Best For |
|-------|-------|----------------|---------|----------|
| **gpt-4o-mini** | **2-3s** | **$0.0005** | **Good** | **Most use cases** ✅ |
| gpt-4o | 5-8s | $0.011 | Excellent | Premium content |
| gpt-3.5-turbo | 1-2s | $0.0003 | Fair | High volume |

### Configuration Options

```python
integration = PraisonAIWPIntegration(
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

### Test Coverage
- **58 tests** - 100% passing
- **Test categories**: API validation, content validation, cost tracking, rate limiting, retry logic, integration, WordPress tools, CLI commands
- **Production-ready**: All edge cases covered

**See [PRAISONAI.md](PRAISONAI.md) for detailed production features documentation.**

## Complete CLI Reference

### `praisonaiwp create` - Create Posts

**All Options:**
```bash
praisonaiwp create [TITLE_OR_FILE] [OPTIONS]

Options:
  --content TEXT          Post content
  --status TEXT           Post status (publish, draft, private)
  --type TEXT             Post type (post, page)
  --category TEXT         Comma-separated category names/slugs
  --category-id TEXT      Comma-separated category IDs
  --author TEXT           Post author (user ID or login)
  --excerpt TEXT          Post excerpt
  --date TEXT             Post date (YYYY-MM-DD HH:MM:SS)
  --tags TEXT             Comma-separated tag names or IDs
  --meta TEXT             Post meta in JSON format: {"key":"value"}
  --comment-status TEXT   Comment status (open, closed)
  --convert-to-blocks     Auto-convert HTML to Gutenberg blocks (NEW in v1.0.17)
  --server TEXT           Server name from config
```

**Examples:**
```bash
# Basic post
praisonaiwp create "My Post" --content "Content here"

# With author and categories
praisonaiwp create "My Post" \
  --content "Full content" \
  --status publish \
  --author praison \
  --category "Tech,AI"

# With custom meta data (NEW in v1.0.15)
praisonaiwp create "My Post" \
  --content "Content" \
  --meta '{"custom_field":"value","price":"99.99"}'

# With excerpt and tags
praisonaiwp create "My Post" \
  --content "Full content" \
  --excerpt "Short summary" \
  --tags "python,wordpress,automation"

# With custom date and comment status
praisonaiwp create "My Post" \
  --content "Content" \
  --date "2024-01-15 10:30:00" \
  --comment-status closed

# All options combined
praisonaiwp create "My Post" \
  --content "Full content" \
  --status publish \
  --type post \
  --category "Tech,AI" \
  --author praison \
  --excerpt "Summary" \
  --date "2024-01-15 10:00:00" \
  --tags "python,ai" \
  --meta '{"views":"0","featured":"yes"}' \
  --comment-status open \
  --server production

# From file
praisonaiwp create posts.json

# Auto-convert HTML to Gutenberg blocks (NEW in v1.0.17)
praisonaiwp create "My Post" \
  --content "<h2>Title</h2><p>Content with <strong>HTML</strong></p>" \
  --convert-to-blocks
```

---

### `praisonaiwp update` - Update Posts

**All Options:**
```bash
praisonaiwp update POST_ID [FIND_TEXT] [REPLACE_TEXT] [OPTIONS]

Options:
  --line INTEGER         Update specific line number
  --nth INTEGER          Update nth occurrence
  --preview              Preview changes without applying
  --category TEXT        Comma-separated category names/slugs
  --category-id TEXT     Comma-separated category IDs
  --post-content TEXT    Replace entire post content
  --post-title TEXT      Update post title
  --post-status TEXT     Update post status (publish, draft, private)
  --post-excerpt TEXT    Update post excerpt
  --post-author TEXT     Update post author (user ID or login)
  --post-date TEXT       Update post date (YYYY-MM-DD HH:MM:SS)
  --tags TEXT            Update tags (comma-separated)
  --meta TEXT            Update post meta in JSON format
  --comment-status TEXT  Update comment status (open, closed)
  --convert-to-blocks    Auto-convert HTML to Gutenberg blocks (NEW in v1.0.17)
  --server TEXT          Server name from config
```

**Examples:**
```bash
# Find and replace
praisonaiwp update 123 "old text" "new text"

# Update specific line
praisonaiwp update 123 "old" "new" --line 10

# Update nth occurrence
praisonaiwp update 123 "old" "new" --nth 2

# Preview first
praisonaiwp update 123 "old" "new" --preview

# Update post fields directly
praisonaiwp update 123 --post-content "New full content"
praisonaiwp update 123 --post-title "New Title"
praisonaiwp update 123 --post-status draft

# Update excerpt and tags (NEW in v1.0.16)
praisonaiwp update 123 --post-excerpt "New summary"
praisonaiwp update 123 --tags "python,wordpress,automation"

# Update author and date
praisonaiwp update 123 --post-author praison
praisonaiwp update 123 --post-date "2024-01-15 10:00:00"

# Update custom meta
praisonaiwp update 123 --meta '{"views":"1000","featured":"yes"}'

# Update comment status
praisonaiwp update 123 --comment-status closed

# Update categories
praisonaiwp update 123 --category "Tech,AI"

# Combine multiple updates
praisonaiwp update 123 \
  --post-title "Updated Title" \
  --post-excerpt "New excerpt" \
  --tags "python,ai" \
  --meta '{"updated":"yes"}' \
  --comment-status open

# Update content with HTML to blocks conversion (NEW in v1.0.17)
praisonaiwp update 123 \
  --post-content "<h2>New Title</h2><p>Updated content</p>" \
  --convert-to-blocks
```

---

### `praisonaiwp list` - List Posts

**All Options:**
```bash
praisonaiwp list [OPTIONS]

Options:
  --type TEXT         Post type (post, page, all)
  --status TEXT       Post status (publish, draft, all)
  --limit INTEGER     Limit number of results
  -s, --search TEXT   Search posts by title/content
  --server TEXT       Server name from config
```

**Examples:**
```bash
# List all posts
praisonaiwp list

# Search (single word)
praisonaiwp list --search "Pricing"
praisonaiwp list -s "keyword"

# Search with spaces (use quotes)
praisonaiwp list --search "Test Post"

# List pages
praisonaiwp list --type page

# List drafts
praisonaiwp list --status draft

# Limit results
praisonaiwp list --limit 10

# Combine filters
praisonaiwp list --type post --status publish --limit 20
```

---

### `praisonaiwp find` - Search Text

**All Options:**
```bash
praisonaiwp find PATTERN [POST_ID] [OPTIONS]

Options:
  --type TEXT    Post type to search
  --server TEXT  Server name from config
```

**Examples:**
```bash
# Find in specific post
praisonaiwp find "search text" 123

# Find across all posts
praisonaiwp find "search text"

# Find in pages
praisonaiwp find "search text" --type page
```

---

### `praisonaiwp category` - Manage Categories

**Subcommands:**
- `list` - List categories (all or for specific post)
- `search` - Search for categories by name
- `set` - Set post categories (replace all existing)
- `add` - Add categories to post (append)
- `remove` - Remove categories from post

**Examples:**
```bash
# List all categories
praisonaiwp category list

# Search categories
praisonaiwp category search "Technology"

# List categories for a post
praisonaiwp category list 123

# Set categories (replace all)
praisonaiwp category set 123 --category "Tech,AI"
praisonaiwp category set 123 --category-id "1,2,3"

# Add categories (append)
praisonaiwp category add 123 --category "Python"

# Remove categories
praisonaiwp category remove 123 --category "Uncategorized"
# NEW in v1.5.1: Create, update, delete categories
praisonaiwp category create "Technology" --slug "tech" --description "Tech posts"
praisonaiwp category update 123 --name "New Name" --slug "new-slug"
praisonaiwp category delete 123
```

---

### `praisonaiwp option` - Manage WordPress Options (NEW in v1.5.1)

**Subcommands:**
- `get <key>` - Get WordPress option value
- `set <key> <value>` - Set WordPress option value
- `delete <key>` - Delete WordPress option

**Examples:**
```bash
# Get option value
praisonaiwp option get blogname

# Set option value
praisonaiwp option set blogname "My Blog"

# Delete option
praisonaiwp option delete transient_option
```

---

### `praisonaiwp meta` - Manage Post & User Metadata (NEW in v1.5.1)

**Post Meta Subcommands:**
- `post get <post_id> <key>` - Get post meta value
- `post set <post_id> <key> <value>` - Set post meta value
- `post update <post_id> <key> <value>` - Update post meta value
- `post delete <post_id> <key>` - Delete post meta value

**User Meta Subcommands:**
- `user get <user_id> <key>` - Get user meta value
- `user set <user_id> <key> <value>` - Set user meta value
- `user update <user_id> <key> <value>` - Update user meta value
- `user delete <user_id> <key>` - Delete user meta value

**Examples:**
```bash
# Post metadata
praisonaiwp meta post get 123 views
praisonaiwp meta post set 123 views 1000
praisonaiwp meta post delete 123 views

# User metadata
praisonaiwp meta user get 1 nickname
praisonaiwp meta user set 1 nickname "Admin"
```

---

### `praisonaiwp comment` - Manage Comments (NEW in v1.5.1)

**Subcommands:**
- `list` - List comments with filters
- `get <id>` - Get comment details
- `create` - Create new comment
- `update <id>` - Update existing comment
- `delete <id>` - Delete comment
- `approve <id>` - Approve comment
- `unapprove <id>` - Unapprove comment

**Examples:**
```bash
# List comments
praisonaiwp comment list
praisonaiwp comment list --post-id 123 --status approve

# Get comment
praisonaiwp comment get 456

# Create comment
praisonaiwp comment create 123 "Great post!" --author "John"

# Update comment
praisonaiwp comment update 456 --content "Updated comment"

# Delete comment
praisonaiwp comment delete 456

# Approve/unapprove
praisonaiwp comment approve 456
praisonaiwp comment unapprove 456
```

---

### `praisonaiwp system` - System Operations (NEW in v1.5.1)

**Subcommands:**
- `cache-flush` - Clear WordPress cache
- `cache-type` - Get cache type
- `version` - Get WordPress version
- `check-install` - Check WordPress installation

**Examples:**
```bash
# Clear cache
praisonaiwp system cache-flush

# Get cache type
praisonaiwp system cache-type

# Get WordPress version
praisonaiwp system version
praisonaiwp system version --detailed

# Check installation
praisonaiwp system check-install
```

---

### `praisonaiwp theme` - Manage Themes (NEW in v1.5.1)

**Subcommands:**
- `list` - List all themes
- `activate <slug>` - Activate theme

**Examples:**
```bash
# List themes
praisonaiwp theme list

# Activate theme
praisonaiwp theme activate twentytwentythree
praisonaiwp theme activate twentytwentythree --server production
```

---

### `praisonaiwp menu` - Manage Menus (NEW in v1.5.1)

**Subcommands:**
- `list` - List all menus
- `create <name>` - Create new menu
- `delete <id>` - Delete menu
- `add-item <id>` - Add item to menu

**Examples:**
```bash
# List menus
praisonaiwp menu list

# Create menu
praisonaiwp menu create "Main Menu"

# Delete menu
praisonaiwp menu delete 123

# Add menu item
praisonaiwp menu add-item 123 --title "Home" --url "https://example.com"
praisonaiwp menu add-item 123 --title "About" --url "https://example.com/about" --parent 456 --order 2
```

---

### `praisonaiwp transient` - Manage Transients (NEW in v1.5.1)

**Subcommands:**
- `get <key>` - Get transient value
- `set <key> <value>` - Set transient with expiration
- `delete <key>` - Delete transient

**Examples:**
```bash
# Get transient
praisonaiwp transient get cache_key

# Set transient (1 hour default)
praisonaiwp transient set cache_key "cached_data"

# Set with custom expiration
praisonaiwp transient set cache_key "data" --expire 7200

# Delete transient
praisonaiwp transient delete cache_key
```

---

### `praisonaiwp post` - Post Utilities (NEW in v1.5.1)

**Subcommands:**
- `delete <id>` - Delete post
- `exists <id>` - Check if post exists

**Examples:**
```bash
# Delete post
praisonaiwp post delete 123

# Check if post exists
praisonaiwp post exists 123
```

---

### `praisonaiwp db` - Database Operations (NEW in v1.5.1)

**Subcommands:**
- `query "<SQL>"` - Execute database queries

**Examples:**
```bash
# Simple query
praisonaiwp db query "SELECT COUNT(*) FROM wp_posts"

# Query with conditions
praisonaiwp db query "SELECT * FROM wp_posts WHERE post_status = 'publish' LIMIT 5"

# Query on specific server
praisonaiwp db query "SHOW TABLES" --server production
```

---

### `praisonaiwp media` - Upload Media (NEW in v1.0.23)

**All Options:**
```bash
praisonaiwp media FILE_PATH [OPTIONS]

Options:
  --post-id INTEGER  Post ID to attach media to
  --title TEXT       Media title
  --caption TEXT     Media caption
  --alt TEXT         Alt text for images
  --desc TEXT        Media description
  --server TEXT      Server name from config
```

**Examples:**
```bash
# Upload a local file
praisonaiwp media /path/to/image.jpg

# Upload from URL
praisonaiwp media https://example.com/image.jpg

# Upload and attach to a post
praisonaiwp media /path/to/image.jpg --post-id 123

# Upload with metadata
praisonaiwp media /path/to/image.jpg \
  --title "My Image" \
  --alt "Description of image" \
  --caption "Image caption"

# Upload with all options
praisonaiwp media /path/to/image.jpg \
  --post-id 123 \
  --title "Featured Image" \
  --alt "Alt text for SEO" \
  --caption "Photo caption" \
  --desc "Full description" \
  --server production
```

---

### `praisonaiwp plugin` - Manage Plugins (NEW in v1.4.0)

**Subcommands:**
```bash
praisonaiwp plugin list      # List installed plugins
praisonaiwp plugin update    # Update plugins
praisonaiwp plugin activate  # Activate a plugin
praisonaiwp plugin deactivate # Deactivate a plugin
```

**List Options:**
```bash
Options:
  --status [all|active|inactive]  Filter plugins by status (default: all)
  --server TEXT                   Server name from config
```

**Update Options:**
```bash
praisonaiwp plugin update [PLUGIN] [OPTIONS]

Arguments:
  PLUGIN  Plugin slug/path or "all" to update all plugins (default: all)

Options:
  --server TEXT  Server name from config
```

**Activate/Deactivate Options:**
```bash
praisonaiwp plugin activate PLUGIN [OPTIONS]
praisonaiwp plugin deactivate PLUGIN [OPTIONS]

Arguments:
  PLUGIN  Plugin slug or path (e.g., 'akismet' or 'akismet/akismet.php')

Options:
  --server TEXT  Server name from config
```

**Examples:**
```bash
# List all plugins
praisonaiwp plugin list

# List only active plugins
praisonaiwp plugin list --status active

# List inactive plugins
praisonaiwp plugin list --status inactive

# Update all plugins
praisonaiwp plugin update
praisonaiwp plugin update all

# Update specific plugin
praisonaiwp plugin update akismet
praisonaiwp plugin update woocommerce

# Activate a plugin
praisonaiwp plugin activate akismet
praisonaiwp plugin activate jetpack

# Deactivate a plugin
praisonaiwp plugin deactivate akismet
praisonaiwp plugin deactivate hello

# Use specific server
praisonaiwp plugin list --server production
praisonaiwp plugin update all --server staging
```

**Features:**
- List plugins with status and version information
- Show available updates
- Update single or all plugins
- Activate/deactivate plugins
- Multi-server support

---

### `praisonaiwp init` - Initialize Configuration

**Options:**
```bash
Options:
  --help  Show this message and exit.
```

**Examples:**
```bash
# Interactive configuration setup
praisonaiwp init
```

**What it does:**
- Prompts for server hostname (or SSH config alias)
- Prompts for SSH username
- Prompts for SSH key path
- Auto-detects WordPress installation path
- Auto-detects PHP binary
- Auto-detects WP-CLI path
- Creates `~/.praisonaiwp/config.yaml`

---

### `praisonaiwp install-wp-cli` - Install WP-CLI

**Options:**
```bash
Options:
  -y, --yes              Skip confirmation prompts
  --install-deps         Install dependencies (curl, php)
  --install-path TEXT    Custom installation path (default: /usr/local/bin/wp)
  --php-bin TEXT         Custom PHP binary path
  --server TEXT          Server name from config
```

**Examples:**
```bash
# Auto-install with confirmation
praisonaiwp install-wp-cli

# Auto-install without prompts
praisonaiwp install-wp-cli -y

# Install with dependencies
praisonaiwp install-wp-cli --install-deps -y

# Custom installation path
praisonaiwp install-wp-cli --install-path /usr/bin/wp -y

# For Plesk servers
praisonaiwp install-wp-cli --php-bin /opt/plesk/php/8.3/bin/php -y

# Install on specific server
praisonaiwp install-wp-cli --server production -y
```

---

### `praisonaiwp find-wordpress` - Find WordPress Installations

**Options:**
```bash
Options:
  --interactive      Interactive selection from multiple installations
  --update-config    Automatically update config with selected installation
  --server TEXT      Server name from config
```

**Examples:**
```bash
# Find all WordPress installations
praisonaiwp find-wordpress

# Interactive selection
praisonaiwp find-wordpress --interactive

# Find and update config automatically
praisonaiwp find-wordpress --update-config

# Find on specific server
praisonaiwp find-wordpress --server staging
```

---

### `praisonaiwp ai` - AI Content Generation (NEW in v1.1.0)

**Subcommand:**
```bash
praisonaiwp ai generate TOPIC [OPTIONS]
```

**Options:**
```bash
Options:
  --title TEXT           Post title (defaults to topic)
  --status TEXT          Post status (draft/publish/private)
  --type TEXT            Post type (post, page)
  --category TEXT        Comma-separated category names or slugs
  --category-id TEXT     Comma-separated category IDs
  --author TEXT          Post author (user ID or login)
  --excerpt TEXT         Post excerpt
  --date TEXT            Post date (YYYY-MM-DD HH:MM:SS)
  --tags TEXT            Comma-separated tag names or IDs
  --meta TEXT            Post meta in JSON format: {"key":"value"}
  --comment-status TEXT  Comment status (open, closed)
  --auto-publish         Automatically publish to WordPress
  --verbose              Verbose output
  --server TEXT          Server name from config
```

**Examples:**
```bash
# Basic generation (creates draft)
praisonaiwp ai generate "AI Trends 2025"

# With custom title
praisonaiwp ai generate "AI Trends" --title "The Future of AI"

# Auto-publish as draft
praisonaiwp ai generate "AI Trends" \
  --title "The Future of AI" \
  --auto-publish

# Auto-publish as published post
praisonaiwp ai generate "AI Trends" \
  --title "The Future of AI" \
  --auto-publish \
  --status publish

# With categories and tags
praisonaiwp ai generate "AI Trends" \
  --category "Technology,AI" \
  --tags "artificial-intelligence,machine-learning" \
  --auto-publish

# With author and excerpt
praisonaiwp ai generate "AI Trends" \
  --author praison \
  --excerpt "Discover the latest AI trends" \
  --auto-publish

# With custom meta fields
praisonaiwp ai generate "AI Trends" \
  --meta '{"featured":"yes","views":"0"}' \
  --auto-publish

# All options combined
praisonaiwp ai generate "AI Trends 2025" \
  --title "The Future of AI" \
  --status publish \
  --type post \
  --category "Technology,AI" \
  --author praison \
  --excerpt "Comprehensive AI trends analysis" \
  --date "2024-01-15 10:00:00" \
  --tags "ai,tech,trends" \
  --meta '{"featured":"yes"}' \
  --comment-status open \
  --auto-publish \
  --verbose

# Verbose mode (shows generation details, cost, duration)
praisonaiwp ai generate "AI Trends" --verbose

# Use specific server
praisonaiwp ai generate "AI Trends" --server production
```

**Requirements:**
- OpenAI API key: `export OPENAI_API_KEY="sk-..."`
- AI features installed: `pip install praisonaiwp[ai]`

**Features:**
- Default model: gpt-4o-mini (~$0.0005 per 500-word post)
- Automatic content validation
- Cost tracking and estimation
- Retry logic (3 attempts with exponential backoff)
- Rate limiting (10 requests/60s by default)
- Production-ready error handling

**See [PRAISONAI.md](PRAISONAI.md) for complete AI documentation.**

---

### `praisonaiwp mcp` - MCP Server (NEW in v1.3.0)

**Subcommands:**
```bash
praisonaiwp mcp run      # Run MCP server
praisonaiwp mcp install  # Install in Claude Desktop
praisonaiwp mcp dev      # Development mode with inspector
praisonaiwp mcp info     # Show available tools/resources
```

**Run Options:**
```bash
Options:
  -t, --transport [stdio|streamable-http]  Transport type (default: stdio)
  --host TEXT                              Host for HTTP transport (default: localhost)
  --port INTEGER                           Port for HTTP transport (default: 8000)
  -s, --server TEXT                        WordPress server name from config
```

**Examples:**
```bash
# Run with default stdio transport
praisonaiwp mcp run

# Run with HTTP transport
praisonaiwp mcp run -t streamable-http --port 8080

# Use specific WordPress server
praisonaiwp mcp run --server production

# Install in Claude Desktop
praisonaiwp mcp install
praisonaiwp mcp install --name "My WordPress"

# Development mode (opens MCP Inspector)
praisonaiwp mcp dev

# View all available tools and resources
praisonaiwp mcp info
```

**Available MCP Tools:**
| Tool | Description |
|------|-------------|
| `create_post` | Create a new WordPress post |
| `update_post` | Update an existing post |
| `delete_post` | Delete a post |
| `get_post` | Get post details |
| `list_posts` | List posts with filters |
| `find_text` | Find text in posts |
| `list_categories` | List all categories |
| `set_post_categories` | Set post categories |
| `create_term` | Create a new term |
| `list_users` | List WordPress users |
| `create_user` | Create a new user |
| `get_user` | Get user details |
| `list_plugins` | List installed plugins |
| `activate_plugin` | Activate a plugin |
| `deactivate_plugin` | Deactivate a plugin |
| `list_themes` | List installed themes |
| `activate_theme` | Activate a theme |
| `import_media` | Import media file |
| `flush_cache` | Flush WordPress cache |
| `get_core_version` | Get WordPress version |
| `db_query` | Execute database query |
| `search_replace` | Search and replace in database |
| `wp_cli` | Execute any WP-CLI command |

**Available MCP Resources:**
| Resource URI | Description |
|--------------|-------------|
| `wordpress://info` | WordPress installation info |
| `wordpress://posts/{post_id}` | Get specific post content |
| `wordpress://posts` | List of recent posts |
| `wordpress://categories` | All categories |
| `wordpress://users` | All users |
| `wordpress://plugins` | Installed plugins |
| `wordpress://themes` | Installed themes |
| `wordpress://config` | Server configuration |

**Available MCP Prompts:**
| Prompt | Description |
|--------|-------------|
| `create_blog_post_prompt` | Template for creating blog posts |
| `update_content_prompt` | Template for updating content |
| `bulk_update_prompt` | Template for bulk operations |
| `seo_optimize_prompt` | Template for SEO optimization |

**Claude Desktop Configuration:**

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "praisonaiwp": {
      "command": "praisonaiwp",
      "args": ["mcp", "run"],
      "env": {
        "PRAISONAIWP_SERVER": "production"
      }
    }
  }
}
```

**Requirements:**
- MCP SDK installed: `pip install praisonaiwp[mcp]`
- WordPress server configured: `praisonaiwp init`

---

### Important Notes for AI Agents

**⚠️ Quoting Rules:**
- Always quote arguments with spaces: `--search "multi word"`
- Single words don't need quotes: `--search keyword`
- Category names with commas: `--category "Tech,AI,Python"`

**✅ Correct Usage:**
```bash
praisonaiwp list --search "Test Post"
praisonaiwp create "My Title" --content "My content"
praisonaiwp update 123 --post-title "New Title"
praisonaiwp ai generate "AI Trends" --title "The Future"
```

**❌ Incorrect Usage:**
```bash
praisonaiwp list --search Test Post  # ERROR: Too many positional arguments
praisonaiwp create My Title --content My content  # ERROR: Ambiguous
praisonaiwp ai generate AI Trends --title The Future  # ERROR: Needs quotes
```

**🔧 All Available Options Summary:**

| Command | Key Options |
|---------|-------------|
| `init` | Interactive configuration setup |
| `install-wp-cli` | `-y/--yes`, `--install-deps`, `--install-path`, `--php-bin`, `--server` |
| `find-wordpress` | `--interactive`, `--update-config`, `--server` |
| `create` | `--content`, `--status`, `--type`, `--category`, `--category-id`, `--author`, `--excerpt`, `--date`, `--tags`, `--meta`, `--comment-status`, `--convert-to-blocks`, `--server` |
| `update` | `--line`, `--nth`, `--preview`, `--category`, `--category-id`, `--post-content`, `--post-title`, `--post-status`, `--post-excerpt`, `--post-author`, `--post-date`, `--tags`, `--meta`, `--comment-status`, `--convert-to-blocks`, `--server` |
| `list` | `--type`, `--status`, `--limit`, `-s/--search`, `--server` |
| `find` | `--type`, `--server` |
| `category` | Subcommands: `list`, `search`, `set`, `add`, `remove` with `--category`, `--category-id` |
| `media` | `--post-id`, `--title`, `--caption`, `--alt`, `--desc`, `--server` |
| `plugin list` | `--status`, `--server` |
| `plugin update` | `[PLUGIN]` (default: all), `--server` |
| `plugin activate` | `PLUGIN`, `--server` |
| `plugin deactivate` | `PLUGIN`, `--server` |
| `ai generate` | `--title`, `--status`, `--type`, `--category`, `--category-id`, `--author`, `--excerpt`, `--date`, `--tags`, `--meta`, `--comment-status`, `--auto-publish`, `--verbose`, `--server` |
| `mcp run` | `-t/--transport`, `--host`, `--port`, `-s/--server` |
| `mcp install` | `-n/--name`, `-s/--server` |
| `mcp dev` | `-s/--server` |
| `mcp info` | (no options) |

---

## File Formats

### JSON Format

```json
[
  {
    "title": "Post Title",
    "content": "<p>Post content</p>",
    "status": "publish",
    "type": "post"
  }
]
```

### YAML Format

```yaml
- title: Post Title
  content: <p>Post content</p>
  status: publish
  type: post
```

### CSV Format

```csv
title,content,status,type
"Post Title","<p>Post content</p>",publish,post
```

## Configuration

Configuration is stored in `~/.praisonaiwp/config.yaml`:

```yaml
version: "1.0"
default_server: default

servers:
  default:
    hostname: example.com
    username: user
    key_file: ~/.ssh/id_ed25519
    port: 22
    wp_path: /var/www/html
    php_bin: /opt/plesk/php/8.3/bin/php
    wp_cli: /usr/local/bin/wp

settings:
  auto_backup: true
  parallel_threshold: 10
  parallel_workers: 10
  ssh_timeout: 30
  log_level: INFO
```

## Advanced Usage

### Line-Specific Replacement

When the same text appears multiple times but you only want to replace it at a specific line:

```bash
# Replace only at line 10
praisonaiwp update 123 "Welcome" "My Website" --line 10
```

### Occurrence-Specific Replacement

Replace only the 1st, 2nd, or nth occurrence:

```bash
# Replace only the 2nd occurrence
praisonaiwp update 123 "Welcome" "My Website" --nth 2
```

### Bulk Operations

Create 100 posts in ~8 seconds (vs 50+ seconds sequential):

```bash
# Automatically uses parallel mode for files with >10 posts
praisonaiwp create 100_posts.json
```

## Troubleshooting

### SSH Connection Issues

```bash
# Test SSH connection manually
ssh -i ~/.ssh/id_ed25519 user@hostname

# Fix key permissions
chmod 600 ~/.ssh/id_ed25519
chmod 600 ~/.ssh/config
```

### WP-CLI Not Found

```bash
# Install WP-CLI automatically
praisonaiwp install-wp-cli -y

# Or check WP-CLI path manually
ssh user@hostname "which wp"
```

### PHP MySQL Extension Missing

```bash
# Use Plesk PHP binary (edit config.yaml)
php_bin: /opt/plesk/php/8.3/bin/php
```

### WordPress Path Not Found

```bash
# Auto-detect WordPress installation
praisonaiwp find-wordpress --update-config
```

### AI Features Issues

#### API Key Not Set
```
Error: OPENAI_API_KEY not set.
```
**Solution:**
```bash
export OPENAI_API_KEY="sk-..."
# Add to ~/.bashrc or ~/.zshrc for persistence
```

#### AI Features Not Available
```
Error: AI features not available.
Install with: pip install 'praisonaiwp[ai]'
```
**Solution:**
```bash
pip install --upgrade praisonaiwp[ai]
```

#### Content Validation Failed
```
Error: Content validation failed:
  - Content too short: 50 chars (minimum: 100)
```
**Solutions:**
```bash
# Option 1: Skip validation
praisonaiwp ai generate "Topic" --skip-validation

# Option 2: Adjust in code
integration = PraisonAIWPIntegration(wp_client, min_length=50)
```

#### Rate Limit Reached
```
WARNING: Rate limit reached (10 requests/60s). Waiting 15.3s...
```
**Solutions:**
```python
# Increase limits
integration = PraisonAIWPIntegration(
    wp_client,
    max_requests=20,
    time_window=60
)

# Or disable rate limiting
integration = PraisonAIWPIntegration(
    wp_client,
    enable_rate_limiting=False
)
```

#### Generation Failed After Retries
```
Error: Failed after 3 attempts: Connection timeout
```
**Solutions:**
- Check internet connection
- Verify OpenAI API status
- Try again later
- Check API key validity

## Documentation

### Core Documentation
- **[README.md](README.md)** - This file (main documentation)
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture and design
- **[TESTING.md](TESTING.md)** - Testing guide and best practices
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes

### AI Features (NEW in v1.1.0)
- **[PRAISONAI.md](PRAISONAI.md)** - Complete AI integration guide
- **[AI_DOCUMENTATION.md](AI_DOCUMENTATION.md)** - Quick AI navigation
- **[RELEASE_NOTES_v1.1.0.md](RELEASE_NOTES_v1.1.0.md)** - v1.1.0 release notes

## Development

```bash
# Clone repository
git clone https://github.com/MervinPraison/PraisonAI-WPcli.git
cd PraisonAI-WPcli

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=praisonaiwp

# Format code
black praisonaiwp/

# Lint
flake8 praisonaiwp/
```

## 🤖 AI Command Reference

### AI Mode Usage
```bash
# Enable AI-friendly JSON output
praisonaiwp --json <command> [options]

# Response format for AI integration
{
  "status": "success|error",
  "message": "Description",
  "data": {...},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Content Management Commands
```bash
# Create posts/pages
praisonaiwp --json create "Post Title" --content "<h2>Content</h2><p>Body</p>"
praisonaiwp --json create "About Us" --content "<p>About content</p>" --type page
praisonaiwp --json create "News" --content "<p>News content</p>" --category "News,Blog"

# List content
praisonaiwp --json list
praisonaiwp --json list --type page --limit 10
praisonaiwp --json list --status draft

# Update content
praisonaiwp --json update 123 --post-content "<p>New content</p>"
praisonaiwp --json update 123 --title "New Title" --status "publish"
```

### Configuration Management
```bash
# Get configuration
praisonaiwp --json config get DB_NAME
praisonaiwp --json config list
praisonaiwp --json config path

# Set configuration
praisonaiwp --json config set DB_PASSWORD "new_password"
```

### User Role Management
```bash
# List roles
praisonaiwp --json role list

# Get role information
praisonaiwp --json role get editor

# Create role
praisonaiwp --json role create custom_role "Custom Role"
praisonaiwp --json role create moderator "Moderator" --capabilities "edit_posts,moderate_comments"

# Delete role
praisonaiwp --json role delete custom_role
```

### Code Generation (Scaffold)
```bash
# Generate post type
praisonaiwp --json scaffold post-type book
praisonaiwp --json scaffold post-type book --label "Books" --public true --supports "title,editor,thumbnail"

# Generate taxonomy
praisonaiwp --json scaffold taxonomy genre
praisonaiwp --json scaffold taxonomy genre --label "Genres" --hierarchical true --post_types "book"

# Generate plugin
praisonaiwp --json scaffold plugin my-plugin --plugin_name "My Plugin" --author "Author Name"

# Generate theme
praisonaiwp --json scaffold theme my-theme --theme_name "My Theme" --author "Author Name"
```

### Core Management
```bash
# Check WordPress version
praisonaiwp --json core version
praisonaiwp --json core check-update

# Update WordPress
praisonaiwp --json core update
praisonaiwp --json core update --version 6.4.0
```

### Cron Management
```bash
# List scheduled events
praisonaiwp --json cron list

# Run cron event
praisonaiwp --json cron run my_hook

# Schedule event
praisonaiwp --json cron event schedule my_hook --hook_code "my_function()" --recurrence "hourly"
```

## 📋 Complete CLI Command Reference

### 🤖 AI Commands (v1.6.0)

#### `praisonaiwp ai` - AI-Powered Content Management
**Main AI command group with 13 subcommands:**

```bash
# Generate AI content
praisonaiwp ai generate "Topic" [OPTIONS]
Options:
  --content TEXT      Custom content prompt
  --word-count INTEGER Target word count
  --tone TEXT         Content tone (professional, casual, academic)
  --seo-optimize      Enable SEO optimization
  --auto-publish      Auto-publish generated content
  --server TEXT       Server name from config
  --author TEXT       Author name
  --category TEXT     Category name
  --tags TEXT         Comma-separated tags
  --status TEXT       Post status (publish, draft)
  --json              Output in JSON format

# Content summarization
praisonaiwp ai summarize [OPTIONS]
Subcommands:
  post                Summarize existing post
  content             Summarize custom content
Options:
  --post-id INTEGER   Post ID to summarize
  --content TEXT      Custom content to summarize
  --length TEXT       Summary length (short, medium, long)
  --format TEXT       Output format (paragraph, bullets)
  --excerpt           Generate excerpt
  --social TEXT       Generate social posts (twitter,linkedin,facebook)
  --json              Output in JSON format

# Content optimization
praisonaiwp ai optimize [OPTIONS]
Subcommands:
  post                Optimize existing post
  content             Optimize custom content
Options:
  --post-id INTEGER   Post ID to optimize
  --content TEXT      Custom content to optimize
  --seo               Enable SEO optimization
  --readability       Improve readability
  --engagement        Optimize for engagement
  --apply             Apply optimizations directly
  --json              Output in JSON format

# Content translation
praisonaiwp ai translate [OPTIONS]
Subcommands:
  post                Translate existing post
  content             Translate custom content
Options:
  --post-id INTEGER   Post ID to translate
  --content TEXT      Custom content to translate
  --to TEXT           Target languages (comma-separated)
  --from TEXT         Source language (auto-detect if not specified)
  --preserve-formatting Preserve HTML formatting
  --create-new        Create new posts for translations
  --json              Output in JSON format

# Content scheduling
praisonaiwp ai schedule [OPTIONS]
Subcommands:
  analyze             Analyze scheduling patterns
  suggest             Suggest optimal times
  calendar            Generate content calendar
Options:
  --days INTEGER      Analysis period in days
  --category TEXT     Filter by category
  --timezone TEXT     Timezone for scheduling
  --frequency TEXT    Posting frequency (daily, weekly, monthly)
  --json              Output in JSON format

# Comment moderation
praisonaiwp ai moderate [OPTIONS]
Subcommands:
  comments            Moderate comments
  analyze             Analyze comment patterns
  respond             Generate responses
Options:
  --post-id INTEGER   Moderate comments for specific post
  --auto-approve      Auto-approve safe comments
  --spam-detection    Enable spam detection
  --sentiment-analysis Analyze sentiment
  --generate-responses Generate AI responses
  --json              Output in JSON format

# Content curation
praisonaiwp ai curate [OPTIONS]
Subcommands:
  related             Find related content
  suggest             Suggest content ideas
  trending            Get trending topics
Options:
  --post-id INTEGER   Find content related to post
  --category TEXT     Filter by category
  --count INTEGER     Number of suggestions
  --trending          Get trending topics
  --json              Output in JSON format

# Research assistant
praisonaiwp ai research [OPTIONS]
Subcommands:
  topic               Research a topic
  citations           Generate citations
  outline             Create content outline
Options:
  --topic TEXT        Research topic
  --depth TEXT        Research depth (basic, comprehensive, detailed)
  --sources INTEGER   Number of sources to include
  --format TEXT       Output format (markdown, html, plain)
  --citations         Include citations
  --json              Output in JSON format

# Image generation
praisonaiwp ai image [OPTIONS]
Subcommands:
  generate            Generate images
  optimize            Optimize existing images
  alt-text            Generate alt text
Options:
  --prompt TEXT       Image generation prompt
  --style TEXT        Image style (photorealistic, artistic, cartoon)
  --size TEXT         Image size (small, medium, large)
  --media-id INTEGER  Optimize existing media
  --alt-text          Generate alt text for images
  --json              Output in JSON format

# Chatbot integration
praisonaiwp ai chatbot [OPTIONS]
Subcommands:
  deploy              Deploy chatbot
  train               Train chatbot
  analytics           Get chatbot analytics
Options:
  --widget-style TEXT Widget style (modern, classic, minimal)
  --position TEXT     Widget position (bottom-right, bottom-left)
  --color TEXT        Widget color
  --content-type TEXT Training content type
  --model TEXT        AI model to use
  --days INTEGER      Analytics period
  --json              Output in JSON format

# Performance analysis
praisonaiwp ai analyze [OPTIONS]
Subcommands:
  performance         Analyze content performance
  predict             Predict performance
  compare             Compare performance
Options:
  --post-id INTEGER   Analyze specific post
  --metrics TEXT      Metrics to analyze (views, engagement, seo)
  --timeframe TEXT    Analysis timeframe
  --days INTEGER      Comparison period
  --json              Output in JSON format

# SEO audit
praisonaiwp ai seo [OPTIONS]
Subcommands:
  audit               Perform SEO audit
  keywords            Analyze keywords
  meta                Analyze meta tags
Options:
  --post-id INTEGER   Audit specific post
  --depth TEXT        Audit depth (basic, comprehensive)
  --focus-keyword TEXT Focus keyword for analysis
  --competitors       Analyze competitors
  --json              Output in JSON format

# Workflow automation
praisonaiwp ai workflow [OPTIONS]
Subcommands:
  create              Create workflow
  list                List workflows
  run                 Run workflow
Options:
  --name TEXT         Workflow name
  --description TEXT  Workflow description
  --trigger TEXT      Workflow trigger (schedule, manual, event)
  --workflow-id TEXT  Workflow ID
  --json              Output in JSON format

# Bulk operations
praisonaiwp ai bulk [OPTIONS]
Subcommands:
  process             Process bulk operations
  optimize            Bulk optimize
  translate           Bulk translate
Options:
  --posts TEXT        Post IDs or range (1,2,3 or 1-10)
  --category TEXT     Process by category
  --status TEXT       Filter by status
  --limit INTEGER     Limit number of posts
  --operation TEXT    Operation type (optimize, translate, summarize)
  --params TEXT       Operation parameters (JSON)
  --json              Output in JSON format
```

### 📝 Core Content Commands

#### `praisonaiwp create` - Create Posts
```bash
praisonaiwp create TITLE [OPTIONS]

Options:
  --content TEXT      Post content (HTML or plain text)
  --status TEXT       Post status (publish, draft, private)
  --author TEXT       Author username
  --category TEXT     Category name or ID
  --tags TEXT         Comma-separated tag names
  --excerpt TEXT      Post excerpt
  --date TEXT         Publication date (YYYY-MM-DD HH:MM:SS)
  --meta TEXT         Custom meta data (JSON format)
  --comment-status TEXT Comment status (open, closed)
  --server TEXT       Server name from config
  --no-block-conversion Send raw Gutenberg blocks
  --json              Output in JSON format

Examples:
praisonaiwp create "My Post" --content "<p>Content here</p>"
praisonaiwp create "Draft Post" --content "Content" --status draft
praisonaiwp create "Tech Post" --content "Content" --category "Technology" --tags "tech,ai"
```

#### `praisonaiwp update` - Update Posts
```bash
praisonaiwp update POST_ID [OPTIONS]

Options:
  OLD_TEXT            Text to find and replace
  NEW_TEXT            Replacement text
  --line INTEGER      Specific line to update
  --nth INTEGER       Update nth occurrence
  --preview           Preview changes before applying
  --post-content TEXT Replace entire content
  --post-title TEXT   Update title
  --post-status TEXT  Update status
  --post-excerpt TEXT Update excerpt
  --tags TEXT         Update tags (comma-separated)
  --post-author TEXT  Update author
  --post-date TEXT    Update date
  --meta TEXT         Update custom meta (JSON)
  --comment-status TEXT Update comment status
  --category TEXT     Update categories
  --convert-to-blocks Convert HTML to Gutenberg blocks
  --json              Output in JSON format

Examples:
praisonaiwp update 123 "old text" "new text"
praisonaiwp update 123 --post-title "New Title"
praisonaiwp update 123 --post-content "<h2>New Content</h2>"
```

#### `praisonaiwp list` - List Posts
```bash
praisonaiwp list [OPTIONS]

Options:
  --type TEXT         Post type (post, page, all)
  --status TEXT       Post status (publish, draft, all)
  --limit INTEGER     Limit number of results
  -s, --search TEXT   Search posts by title/content
  --server TEXT       Server name from config
  --json              Output in JSON format

Examples:
praisonaiwp list
praisonaiwp list --type page --status draft
praisonaiwp list --search "keyword" --limit 10
```

#### `praisonaiwp find` - Search Text
```bash
praisonaiwp find PATTERN [POST_ID] [OPTIONS]

Options:
  --case-sensitive    Case-sensitive search
  --whole-word        Match whole words only
  --context INTEGER   Show context lines
  --server TEXT       Server name from config
  --json              Output in JSON format

Examples:
praisonaiwp find "search term"
praisonaiwp find "term" 123 --context 3
```

### 👥 User Management

#### `praisonaiwp user` - Manage Users
```bash
# Subcommands:
list                 List all users
get <id>            Get user details
create              Create new user
update <id>         Update user
delete <id>         Delete user

# Create user options:
--email TEXT         User email
--username TEXT      Username
--password TEXT      Password
--role TEXT          User role
--first-name TEXT    First name
--last-name TEXT     Last name

# Examples:
praisonaiwp user create --email "user@example.com" --username "newuser" --role "author"
praisonaiwp user list
praisonaiwp user get 123
```

### 📁 Media Management

#### `praisonaiwp media` - Manage Media
```bash
# Subcommands:
upload <file>        Upload media file
url <url>            Upload media from URL
get <id>            Get media details
list                List media files

# Upload options:
--title TEXT         Media title
--caption TEXT       Media caption
--alt TEXT           Alt text
--description TEXT  Media description

# Examples:
praisonaiwp media upload image.jpg --title "My Image" --alt "Description"
praisonaiwp media list
praisonaiwp media get 123
```

### 🏷️ Category Management

#### `praisonaiwp category` - Manage Categories
```bash
# Subcommands:
list                List categories
get <id>            Get category details
set <post-id> <cat-id> Set post category
add <post-id> <cat-id> Add category to post
remove <post-id> <cat-id> Remove category from post
create              Create new category
delete <id>         Delete category

# Create options:
--name TEXT         Category name
--slug TEXT         Category slug
--description TEXT  Category description
--parent INTEGER    Parent category ID

# Examples:
praisonaiwp category list
praisonaiwp category create --name "Technology" --description "Tech posts"
praisonaiwp category set 123 5
```

### 🔌 Plugin Management

#### `praisonaiwp plugin` - Manage Plugins
```bash
# Subcommands:
list                List plugins
activate <plugin>   Activate plugin
deactivate <plugin> Deactivate plugin
update <plugin>     Update plugin
delete <plugin>     Delete plugin

# Examples:
praisonaiwp plugin list
praisonaiwp plugin activate hello-dolly
praisonaiwp plugin update akismet
```

### ⚙️ Configuration Management

#### `praisonaiwp config` - Manage WordPress Config
```bash
# Subcommands:
get <key>           Get config value
set <key> <value>   Set config value
list                List all config

# Examples:
praisonaiwp config get DB_NAME
praisonaiwp config set SITE_URL "https://example.com"
praisonaiwp config list
```

### 🎭 Role Management

#### `praisonaiwp role` - Manage User Roles
```bash
# Subcommands:
list                List roles
get <role>          Get role details
create              Create new role
delete <role>       Delete role

# Create options:
--name TEXT         Role name
--display-name TEXT Display name

# Examples:
praisonaiwp role list
praisonaiwp role get administrator
```

### 🛠️ Scaffold Commands

#### `praisonaiwp scaffold` - Generate WordPress Code
```bash
# Subcommands:
post-type <name>    Generate post type
taxonomy <name>     Generate taxonomy
plugin <name>       Generate plugin
theme <name>        Generate theme
child-theme <parent> <name> Generate child theme

# Examples:
praisonaiwp scaffold post-type book
praisonaiwp scaffold plugin my-plugin
praisonaiwp scaffold child-theme twentytwentyfour my-child
```

### 🔧 WordPress Core Management

#### `praisonaiwp core` - Manage WordPress Core
```bash
# Subcommands:
version             Get WordPress version
check-update        Check for updates
update [version]    Update WordPress
install <version>   Install specific version
config              Generate wp-config.php

# Examples:
praisonaiwp core version
praisonaiwp core update
praisonaiwp core check-update
```

### ⏰ Cron Management

#### `praisonaiwp cron` - Manage WordPress Cron
```bash
# Subcommands:
list                List scheduled events
run <hook>          Run cron event
test                Test cron system
event               Manage cron events

# Event subcommands:
schedule <hook>     Schedule event
delete <hook>       Delete event

# Examples:
praisonaiwp cron list
praisonaiwp cron run my_hook
praisonaiwp cron event schedule my_hook --recurrence hourly
```

### 🏷️ Taxonomy Management

#### `praisonaiwp taxonomy` - Manage Taxonomies
```bash
# Subcommands:
list                List taxonomies
get <taxonomy>      Get taxonomy details

# Examples:
praisonaiwp taxonomy list
praisonaiwp taxonomy get category
```

### 📄 Term Management

#### `praisonaiwp term` - Manage Taxonomy Terms
```bash
# Subcommands:
list <taxonomy>     List terms in taxonomy
get <taxonomy> <id> Get term details
create <taxonomy>   Create new term
update <taxonomy> <id> Update term
delete <taxonomy> <id> Delete term

# Examples:
praisonaiwp term list category
praisonaiwp term create category --name "New Category"
```

### 🎨 Widget Management

#### `praisonaiwp widget` - Manage Widgets
```bash
# Subcommands:
list                List widgets
add <widget>        Add widget
update <id>         Update widget
delete <id>         Delete widget

# Examples:
praisonaiwp widget list
praisonaiwp widget add text --title "My Widget"
```

### 🗂️ Post Utilities

#### `praisonaiwp post` - Post Utilities
```bash
# Subcommands:
meta <post-id>      Manage post meta
thumbnail <post-id> Manage post thumbnail
revisions <post-id> List post revisions

# Meta subcommands:
get <key>           Get meta value
set <key> <value>   Set meta value
delete <key>        Delete meta value

# Examples:
praisonaiwp post meta 123 get views
praisonaiwp post meta 123 set views 1000
praisonaiwp post revisions 123
```

### 💾 Database Operations

#### `praisonaiwp db` - Database Operations
```bash
# Subcommands:
export              Export database
import <file>       Import database
optimize            Optimize database
repair              Repair database
size                Get database size

# Examples:
praisonaiwp db export
praisonaiwp db import backup.sql
praisonaiwp db optimize
```

### 🔍 Help and Information

#### `praisonaiwp help` - Get Help
```bash
praisonaiwp help [COMMAND]

Examples:
praisonaiwp help
praisonaiwp help create
praisonaiwp help ai
```

#### `praisonaiwp eval` - Execute PHP Code
```bash
praisonaiwp eval "PHP_CODE"
praisonaiwp eval --file <file>

Examples:
praisonaiwp eval "echo 'Hello World';"
praisonaiwp eval --file script.php
```

### 🛠️ Maintenance Mode

#### `praisonaiwp maintenance-mode` - Maintenance Mode
```bash
# Subcommands:
status              Check status
activate            Activate maintenance mode
deactivate          Deactivate maintenance mode

# Examples:
praisonaiwp maintenance-mode status
praisonaiwp maintenance-mode activate
praisonaiwp maintenance-mode deactivate
```

### 📤 Import/Export

#### `praisonaiwp import` - Import Data
```bash
praisonaiwp import <file> [OPTIONS]

Options:
  --type TEXT        Import type (posts, pages, users)
  --author-map TEXT  Author mapping (JSON)

Examples:
praisonaiwp import posts.xml --type posts
```

#### `praisonaiwp export` - Export Data
```bash
praisonaiwp export [OPTIONS]

Options:
  --type TEXT        Export type (posts, pages, users)
  --format TEXT      Export format (xml, json, csv)
  --file TEXT        Output file

Examples:
praisonaiwp export --type posts --format xml
praisonaiwp export --type users --file users.json
```

## 🌐 Global Options

All commands support these global options:
```bash
--json              Output in JSON format
--version, -v       Show version and exit
--help, -h          Show help message
```

## 🔧 Configuration

### Server Configuration
```yaml
# ~/.praisonaiwp/config.yaml
servers:
  mysite:
    host: example.com
    user: username
    key_file: ~/.ssh/id_rsa
    wp_path: /var/www/html
    author: praison
    category: AI
    tags: ai,automation
```

### Environment Variables
```bash
export PRAISONAIWP_CONFIG_PATH=~/.praisonaiwp/config.yaml
export OPENAI_API_KEY=your_openai_key
```

### Error Handling for AI
| Error Code | Description | AI Response |
|------------|-------------|-------------|
| `CONNECTION_ERROR` | SSH/WP-CLI connection failed | Check server config, credentials |
| `PERMISSION_ERROR` | Insufficient permissions | Check user roles, file permissions |
| `VALIDATION_ERROR` | Invalid parameters | Check parameter formats |
| `NOT_FOUND` | Item doesn't exist | Verify item exists |
| `WPCLI_ERROR` | WP-CLI command failed | Check WP-CLI installation |

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Author

Praison

## Links

- GitHub: https://github.com/MervinPraison/PraisonAI-WPcli
- Documentation: https://praisonaiwp.readthedocs.io
- PyPI: https://pypi.org/project/praisonaiwp
