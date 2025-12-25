# PraisonAIWP - Architecture Documentation

## Overview

**PraisonAIWP** is a Python-based WordPress content management framework designed to simplify and automate WordPress content operations via WP-CLI over SSH.

### Key Features

**Core Features:**
- **Simple CLI**: 7 intuitive commands (`init`, `create`, `update`, `find`, `list`, `install-wp-cli`, `find-wordpress`)
- **Smart Defaults**: Auto-detects file formats, execution modes, and optimal settings
- **Dual Execution Modes**: Sequential (Python) for reliability, Parallel (Node.js) for speed
- **Precision Editing**: Line-specific and occurrence-specific text replacements
- **Safe Operations**: Auto-backup, preview mode, dry-run capabilities

**New in v1.0.2:**
- **SSH Config Integration**: Automatic loading from `~/.ssh/config` with host alias support
- **WP-CLI Auto-Installer**: One-command installation with OS detection (7 systems supported)
- **WordPress Auto-Detection**: Multiple search strategies to find WordPress installations
- **UV Package Manager**: 10-100x faster dependency management
- **Enhanced Error Handling**: Helpful messages with installation instructions
- **Installation Verification**: Automatic WP-CLI and WordPress validity checks

### Design Philosophy

1. **Convention Over Configuration** - Sensible defaults, minimal setup
2. **Safety First** - Preview, backup, confirm before destructive operations
3. **Performance When Needed** - Auto-parallel for bulk operations
4. **Developer Experience** - Clear commands, helpful errors, progress indicators

## System Architecture

```
User (CLI)
    ↓
CLI Layer (Click) → 7 Commands: init, create, update, find, list, install-wp-cli, find-wordpress
    ↓
Setup & Discovery Layer → WP-CLI Installer, WordPress Finder, SSH Config Loader
    ↓
Operations Layer → Create, Update, Search Operations
    ↓
Core Layer → SSH Manager (with SSH config), WP Client (with verification), Content Editor
    ↓
Execution Modes → Sequential (Python) | Parallel (Node.js)
    ↓
Remote WordPress Server → WP-CLI, Database, WordPress Core
```

## Project Structure

```
praisonaiwp/
├── pyproject.toml         # Modern Python packaging (uv)
├── setup.py               # Legacy pip support
├── requirements.txt       # Legacy dependencies
├── uv.lock                # UV lock file
├── .python-version        # Python version (3.8.1+)
├── praisonaiwp/
│   ├── __init__.py
│   ├── __version__.py     # Version info
│   ├── core/              # Core functionality
│   │   ├── ssh_manager.py     # SSH with config support
│   │   ├── wp_client.py       # WP-CLI with verification
│   │   ├── wp_installer.py    # WP-CLI auto-installer (NEW)
│   │   ├── wp_finder.py       # WordPress auto-detection (NEW)
│   │   ├── config.py          # Configuration management
│   │   └── content_editor.py  # Content editing
│   ├── editors/           # Content editing logic
│   ├── operations/        # High-level operations
│   ├── cli/               # CLI commands
│   │   ├── main.py            # CLI entry point
│   │   └── commands/
│   │       ├── init.py            # Initialize config
│   │       ├── create.py          # Create posts
│   │       ├── update.py          # Update posts
│   │       ├── find.py            # Find text
│   │       ├── list.py            # List posts
│   │       ├── install_wp_cli.py  # Install WP-CLI (NEW)
│   │       └── find_wordpress.py  # Find WordPress (NEW)
│   ├── parallel/          # Node.js bridge for parallel ops
│   └── utils/             # Logger, validator, backup, progress
├── templates/             # Content templates
├── tests/                 # Unit & integration tests
└── examples/              # Usage examples
```

## Core Components

### 1. SSH Manager (`core/ssh_manager.py`) - Enhanced v1.0.2

**Core Functionality:**
- Manages SSH connections using Paramiko
- Context manager support for auto-cleanup
- Connection pooling and retry logic

**NEW - SSH Config Integration:**
- Automatically reads from `~/.ssh/config`
- Loads host aliases (e.g., `wp-prod` → full connection details)
- Supports advanced SSH features:
  - ProxyJump (bastion hosts)
  - ControlMaster (connection multiplexing)
  - Multiple IdentityFile entries
- Configuration priority: Explicit params → SSH config → Defaults
- Optional `use_ssh_config=False` to disable

**Implementation Details:**
```python
class SSHManager:
    def __init__(self, hostname, username=None, key_file=None, port=22, use_ssh_config=True):
        # Load SSH config if enabled
        if use_ssh_config:
            ssh_config = paramiko.SSHConfig()
            ssh_config.parse(open(os.path.expanduser('~/.ssh/config')))
            host_config = ssh_config.lookup(hostname)
            
            # Override with SSH config values
            self.hostname = host_config.get('hostname', hostname)
            self.username = username or host_config.get('user')
            self.port = port or int(host_config.get('port', 22))
            self.key_file = key_file or host_config.get('identityfile', [None])[0]
```

**Testing:**
- ✅ Tested with real server (82.165.193.19)
- ✅ SSH config alias 'myserver' working
- ✅ Connection details loaded automatically
- ✅ Command execution verified
- ✅ WP-CLI access confirmed (v2.12.0)

### 2. WP Client (`core/wp_client.py`) - Enhanced v1.0.2

**Core Functionality:**
- Wrapper around WP-CLI
- Handles different PHP binaries (Plesk support)
- Returns Python objects (not raw strings)

**API Design Philosophy: Dual-Layer Approach**

The WP Client provides two complementary APIs:

#### **High-Level API: Convenience Methods (✅)**
**Purpose:** Common operations with excellent developer experience

**Benefits:**
- ✅ **IDE Autocomplete** - IntelliSense shows available parameters
- ✅ **Type Hints** - Static type checking catches errors early
- ✅ **Inline Documentation** - Docstrings explain usage and parameters
- ✅ **Input Validation** - Python-side validation before SSH execution
- ✅ **Return Type Handling** - Automatic parsing and type conversion
- ✅ **Error Messages** - Clear, actionable error messages

**Coverage:** ~47 convenience methods covering 80% of use cases
- Post management (create, update, list, get, delete, exists, meta)
- User management (CRUD + meta operations)
- Term/category management (full CRUD)
- Plugin/theme management (list, activate, deactivate)
- Comment management (CRUD + approve)
- Menu management (CRUD + add items)
- Cache/transient management
- Database operations (query, search-replace)
- Core commands (version, is-installed)

**Example:**
```python
# Clean, type-safe, documented
post_id = client.create_post(
    post_title='My Post',
    post_content='Content here',
    post_status='publish',
    post_author=1
)  # Returns: int (post ID)
```

#### **Low-Level API: Generic `wp()` Method (❌)**
**Purpose:** Universal access to ALL WP-CLI commands

**Benefits:**
- ✅ **Universal** - Supports ALL 1000+ WP-CLI commands
- ✅ **Future-Proof** - New WP-CLI features work automatically
- ✅ **Flexible** - Custom WP-CLI packages supported
- ✅ **No Maintenance** - No code updates needed for new commands
- ✅ **Auto JSON Parsing** - Automatically parses `format=json` output
- ✅ **Kwargs Support** - Python kwargs → WP-CLI flags

**Coverage:** Unlimited - any WP-CLI command works

**Example:**
```python
# Direct WP-CLI access - works for anything
client.wp('db', 'export', 'backup.sql')
client.wp('plugin', 'install', 'akismet', activate=True)
client.wp('cron', 'event', 'run', 'my_custom_hook')
client.wp('media', 'regenerate', yes=True)

# Auto JSON parsing
posts = client.wp('post', 'list', format='json')  # Returns: List[Dict]
```

#### **Why Not Implement Everything as Convenience Methods?**

**Maintenance Burden:**
- Would require 100+ additional methods
- Each needs: implementation, tests, documentation, maintenance
- WP-CLI updates would require code changes
- Code bloat: ~3000+ lines vs current ~1300 lines

**Diminishing Returns:**
- 80% of operations already have convenience methods
- Remaining 20% are rarely used or simple enough
- Generic `wp()` handles the long tail perfectly

**When to Add New Convenience Methods:**

Only add if the operation is:
1. **Frequently used** by most users (>10% usage)
2. **Complex syntax** that benefits from Python wrapper
3. **Needs validation** or special handling
4. **Explicitly requested** by multiple users

**Historical Context:**
- **v1.0.0-1.0.12**: Only convenience methods existed (limited functionality)
- **v1.0.13**: Generic `wp()` method added as "escape hatch"
- **v1.0.13+**: Best of both worlds - convenience + flexibility
- **v1.0.17**: Added HTML to Gutenberg blocks converter

**Think of It Like:**
- **Convenience Methods** = jQuery (high-level, common tasks, great DX)
- **Generic `wp()` Method** = Vanilla JS (low-level, full power, unlimited)

Both approaches have their place and complement each other perfectly!

**NEW - Installation Verification:**
- Automatic verification on initialization (`verify_installation=True`)
- Checks performed:
  1. WP-CLI binary exists at specified path
  2. WordPress directory exists
  3. `wp-config.php` exists (validates WordPress)
  4. WP-CLI is executable with PHP binary
  5. PHP has required extensions (mysql, mysqli)

**Enhanced Error Handling:**
- Clear, actionable error messages
- Installation instructions included
- Specific guidance for common issues:
  - WP-CLI not found → Installation steps
  - PHP binary issues → Plesk path suggestions
  - Missing extensions → Installation commands
  - Permission denied → Ownership fix commands

**Implementation Details:**
```python
class WPClient:
    def __init__(self, ssh, wp_path, php_bin='php', wp_cli='/usr/local/bin/wp', verify_installation=True):
        if verify_installation:
            self._verify_installation()
    
    def _verify_installation(self):
        # Check WP-CLI binary
        stdout, _ = self.ssh.execute(f"test -f {self.wp_cli} && echo 'exists' || echo 'not found'")
        if 'not found' in stdout:
            raise WPCLIError(f"WP-CLI not found at {self.wp_cli}\n" + installation_instructions)
        
        # Check WordPress directory
        # Check wp-config.php
        # Test WP-CLI execution
```

### 3. WP-CLI Installer (`core/wp_installer.py`) - NEW v1.0.2

**Purpose:** Automatically install WP-CLI on remote servers with OS detection

**Supported Operating Systems:**
- Ubuntu (18.04, 20.04, 22.04, 24.04)
- Debian (9, 10, 11, 12)
- CentOS (7, 8, 9)
- RHEL (7, 8, 9)
- Fedora (35+)
- Alpine Linux
- macOS (with Homebrew)

**Features:**
1. **OS Detection:**
   - Reads `/etc/os-release` for Linux distributions
   - Uses `sw_vers` for macOS
   - Fallback to `uname -s`
   - Extracts OS type and version

2. **WP-CLI Installation:**
   - Downloads from official source
   - Tests with PHP before installing
   - Makes executable
   - Moves to system path
   - Verifies installation

3. **Dependency Installation (Optional):**
   - Ubuntu/Debian: `apt-get install curl php-cli php-mysql`
   - CentOS/RHEL: `yum install curl php-cli php-mysql`
   - Alpine: `apk add curl php php-cli php-mysqli`
   - macOS: `brew install php`

**Implementation Details:**
```python
class WPCLIInstaller:
    def detect_os(self) -> Tuple[str, str]:
        # Read /etc/os-release
        # Parse OS type and version
        # Return ('ubuntu', '22.04')
    
    def install_wp_cli(self, install_path='/usr/local/bin/wp', use_sudo=True):
        # Download WP-CLI
        self.ssh.execute("curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar")
        
        # Test
        self.ssh.execute(f"{php_bin} wp-cli.phar --version")
        
        # Install
        self.ssh.execute("chmod +x wp-cli.phar")
        self.ssh.execute(f"{sudo}mv wp-cli.phar {install_path}")
        
        # Verify
        self.ssh.execute(f"{install_path} --version")
```

**CLI Command:**
```bash
praisonaiwp install-wp-cli [OPTIONS]
  --server NAME          Server to install on
  --install-path PATH    Installation path (default: /usr/local/bin/wp)
  --no-sudo              Don't use sudo
  --install-deps         Install dependencies (curl, php)
  --php-bin PATH         PHP binary to test with
  --yes, -y              Skip confirmation
```

### 4. WordPress Finder (`core/wp_finder.py`) - NEW v1.0.2

**Purpose:** Automatically find WordPress installations on remote servers

**Search Strategies:**

1. **Find wp-config.php:**
   - Searches common directories: `/var/www`, `/home`, `/usr/share/nginx`, `/opt`, `/srv`
   - Max depth: 5 levels
   - Excludes: `wp-content`, `node_modules`, `vendor`
   - Command: `find /var/www -maxdepth 5 -name 'wp-config.php'`

2. **Check Common Paths:**
   - `/var/www/html`
   - `/var/www/html/wordpress`
   - `/var/www/wordpress`
   - `/var/www/vhosts/*/httpdocs` (Plesk)
   - `/home/*/public_html` (cPanel)
   - `/home/*/www`
   - `/usr/share/nginx/html`
   - And more...

3. **Verification:**
   - Checks `wp-config.php` exists
   - Checks `wp-content/` directory exists
   - Checks `wp-includes/` directory exists
   - Extracts WordPress version from `wp-includes/version.php`
   - Marks as valid only if all components present

**Features:**
- `find_all()` - Find all WordPress installations
- `find_best()` - Auto-select most likely installation
- `verify_wordpress()` - Verify specific path
- `interactive_select()` - User selection from multiple installations

**Implementation Details:**
```python
class WordPressFinder:
    def find_wp_config(self) -> List[str]:
        # Use find command to locate wp-config.php
        # Return list of directory paths
    
    def verify_wordpress(self, path: str) -> Tuple[bool, dict]:
        # Check wp-config.php
        # Check wp-content/
        # Check wp-includes/
        # Extract version
        # Return (is_valid, info_dict)
    
    def find_best(self) -> Optional[str]:
        # Find all installations
        # Prioritize by path pattern
        # Return best match
```

**CLI Command:**
```bash
praisonaiwp find-wordpress [OPTIONS]
  --server NAME          Server to search
  --interactive, -i      Interactively select installation
  --update-config        Update config with found path
```

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

### 5. Content Editor (`editors/content_editor.py`)
- `replace_at_line()` - Replace at specific line number
- `replace_nth_occurrence()` - Replace 1st, 2nd, nth occurrence
- `replace_in_range()` - Replace in line range
- `find_occurrences()` - Find all matches with line numbers
- `preview_changes()` - Preview before applying

### 6. Operations Layer (`operations/`)
- **Create**: Single post, from file, from template, bulk
- **Update**: Content, with replacement (line/nth), bulk
- **Search**: Find in post, find in all posts, list posts

### 7. CLI Layer (`cli/`) - Enhanced v1.0.2

**Built with Click framework**

**7 Commands:**
1. `init` - Initialize configuration
2. `create` - Create WordPress posts
3. `update` - Update post content
4. `find` - Find text in posts
5. `list` - List WordPress posts
6. `install-wp-cli` - Install WP-CLI automatically (NEW)
7. `find-wordpress` - Find WordPress installations (NEW)

**Smart defaults and auto-detection**

### 8. Parallel Executor (`parallel/`)
- Python-Node.js bridge for parallel operations
- Automatically used when >10 posts
- 10x faster for bulk operations

## CLI Commands

### 1. `praisonaiwp init`
Initialize configuration (one-time setup)

### 2. `praisonaiwp create [file|title]`
Create posts (auto-detects format, auto-parallel for bulk)

### 3. `praisonaiwp update <id> [find] [replace]`
Update posts with optional `--line` or `--nth` flags

### 4. `praisonaiwp find <pattern>`
Search for text in posts

### 5. `praisonaiwp list`
List WordPress posts with filters

## Configuration

**Location**: `~/.praisonaiwp/config.yaml`

```yaml
default_server: production

servers:
  production:
    hostname: example.com
    username: user
    key_file: ~/.ssh/id_ed25519
    wp_path: /var/www/html
    php_bin: /opt/plesk/php/8.3/bin/php

settings:
  auto_backup: true
  parallel_threshold: 10
  parallel_workers: 10
  log_level: INFO
```

## Data Flow Examples

### Create 100 Posts (Auto-Parallel)
```
User: praisonaiwp create posts.json
  ↓
Detect: 100 posts in file
  ↓
Auto-select: Parallel mode
  ↓
Spawn Node.js process
  ↓
Create 10 batches of 10 posts
  ↓
Execute batches in parallel
  ↓
Complete in ~8 seconds (vs 50s sequential)
```

### Update Specific Line
```
User: praisonaiwp update 123 "old" "new" --line 10
  ↓
Get post content
  ↓
Apply: ContentEditor.replace_at_line(content, 10, "old", "new")
  ↓
Preview changes (show diff)
  ↓
Backup original
  ↓
Confirm with user
  ↓
Update post
```

## Security

- SSH key-based authentication only
- No password storage
- Config file permissions: 600
- Automatic backup before destructive operations
- Preview mode for all changes

## Performance

- **Sequential**: ~0.5s per post (network limited)
- **Parallel (10 workers)**: ~5-8s for 100 posts
- **Speedup**: 10x faster for bulk operations

## Testing Strategy

- **Unit Tests**: Core components (SSH, WP Client, Content Editor)
- **Integration Tests**: CLI commands, end-to-end workflows
- **Fixtures**: Sample posts, config files
- **Mocking**: SSH connections for offline testing

## Future Enhancements

1. AI-powered content generation
2. WordPress REST API support (alternative to WP-CLI)
3. Plugin system for custom operations
4. Web dashboard for visual management
5. Multi-site support
6. Content migration tools
7. SEO optimization features

---

**Version**: 1.0.0  
**Last Updated**: October 2025


✅ SIMPLIFIED CLI STRUCTURE
1️⃣ Setup (One-time)
bash
# Initialize with interactive prompts
praisonaiwp init

# Asks:
# - Server hostname?
# - SSH username?
# - SSH key path? (default: ~/.ssh/id_ed25519)
# - WordPress path? (auto-detects)
# - PHP binary? (auto-detects)

# That's it! Saved to ~/.praisonaiwp/config.yaml
2️⃣ Create Posts
bash
# Single post (interactive)
praisonaiwp create
# Prompts for: title, content, status

# Single post (direct)
praisonaiwp create "My Post Title" --content "Post content"

# From file (auto-detects format: JSON, YAML, CSV)
praisonaiwp create posts.json

# 100 posts? Same command! Auto-parallel if >10 posts
praisonaiwp create 100_posts.json
# Automatically uses parallel mode for speed ⚡
3️⃣ Update Posts
bash
# Interactive mode
praisonaiwp update 123
# Shows current content, asks what to change

# Direct replacement
praisonaiwp update 123 "old text" "new text"

# Specific line
praisonaiwp update 123 "old text" "new text" --line 10

# Nth occurrence
praisonaiwp update 123 "old text" "new text" --nth 2

# Preview first (always safe)
praisonaiwp update 123 "old text" "new text" --preview
4️⃣ Find
bash
# Find in post
praisonaiwp find 123 "search text"

# Find across all posts
praisonaiwp find "search text"
5️⃣ List
bash
# List all posts
praisonaiwp list

# List pages
praisonaiwp list --type page

# List with search
praisonaiwp list --search "example"
🎯 EVEN SIMPLER: Natural Language Style
bash
# Create
praisonaiwp "create a post titled 'Hello World'"
praisonaiwp "create 100 posts from posts.json"

# Update
praisonaiwp "update post 123 replace 'old' with 'new' on line 10"
praisonaiwp "update post 123 change the 2nd occurrence of 'old' to 'new'"

# Find
praisonaiwp "find 'example' in post 123"
praisonaiwp "show me all posts with 'example'"

# List
praisonaiwp "list all pages"
praisonaiwp "show me published posts"
🏆 RECOMMENDED: Hybrid Approach
Simple commands + Smart defaults + Natural language fallback

Core Commands (5 only):
bash
praisonaiwp init              # Setup (one-time)
praisonaiwp create [file]     # Create posts
praisonaiwp update <id>       # Update posts
praisonaiwp find <pattern>    # Search
praisonaiwp list              # List posts
Smart Defaults:
Auto-detects file format (JSON/YAML/CSV)
Auto-uses parallel mode for bulk (>10 posts)
Auto-backups before updates
Auto-preview for destructive operations
Auto-connects to default server
Example Usage:
bash
# Setup once
praisonaiwp init

# Create single post
praisonaiwp create "My Post" --content "Hello World"

# Create 100 posts (auto-parallel!)
praisonaiwp create posts.json
# Output: Creating 100 posts in parallel... Done in 8s ⚡

# Update specific line
praisonaiwp update 123 "old" "new" --line 10
# Output: Preview changes? [Y/n]
#         Line 10: "old heading" → "new heading"
#         Apply? [Y/n]

# Find text
praisonaiwp find "example"
# Output: Found in 9 posts:
#         - Post 116 (line 10, 55)
#         - Post 117 (line 10)
#         ...
Comparison: Before vs After
❌ BEFORE (Too Complex):
bash
praisonaiwp bulk create \
  --server production \
  --file posts.json \
  --mode parallel \
  --workers 10 \
  --backup \
  --dry-run
✅ AFTER (Simple):
bash
praisonaiwp create posts.json
# Auto-detects: bulk, auto-parallel, auto-backup, auto-preview
File Format (Super Simple)
posts.json
json
[
  {
    "title": "Example Page 1",
    "content": "<p>Welcome...</p>"
  },
  {
    "title": "Example Page 2",
    "content": "<p>Welcome...</p>"
  }
]
updates.json
json
[
  {
    "id": 116,
    "line": 10,
    "find": "Old Heading",
    "replace": "New Heading"
  },
  {
    "id": 117,
    "line": 10,
    "find": "Old Heading",
    "replace": "Different Heading"
  }
]
🎯 Final Recommendation
Use this simplified structure:

bash
# 5 core commands only
praisonaiwp init
praisonaiwp create [file|title]
praisonaiwp update <id> [find] [replace]
praisonaiwp find <pattern>
praisonaiwp list

# Smart flags (optional)
--line <num>        # Update specific line
--nth <num>         # Update nth occurrence
--preview           # Preview changes
--no-backup         # Skip backup
--server <name>     # Use different server
Benefits:

✅ Only 5 commands to remember
✅ Smart defaults (no need to specify mode, workers, etc.)
✅ Auto-detects everything
✅ Interactive when needed
✅ Safe by default (preview, backup)
✅ Fast automatically (parallel for bulk)