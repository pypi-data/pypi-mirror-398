# Changelog

All notable changes to PraisonAI WPcli will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.0] - 2025-12-22

### 🎉 MAJOR RELEASE - Complete WPClient Coverage

#### Added
- **34 New CLI Commands**: Complete implementation of all missing WPClient methods
- **100% Coverage**: All 61 WPClient methods now exposed as CLI commands
- **Test-Driven Development**: 68 new tests with 100% pass rate

#### New Command Groups

**Options Management** (`praisonaiwp option`)
- `get <key>` - Get WordPress option value
- `set <key> <value>` - Set WordPress option value  
- `delete <key>` - Delete WordPress option

**Meta Management** (`praisonaiwp meta`)
- **Post Meta**: `get`, `set`, `update`, `delete` for post metadata
- **User Meta**: `get`, `set`, `update`, `delete` for user metadata

**Comment Management** (`praisonaiwp comment`)
- `list` - List comments with filters
- `get <id>` - Get comment details
- `create` - Create new comment
- `update <id>` - Update existing comment
- `delete <id>` - Delete comment
- `approve <id>` / `unapprove <id>` - Approve/unapprove comments

**System Commands** (`praisonaiwp system`)
- `cache-flush` - Clear WordPress cache
- `cache-type` - Get cache type
- `version` - Get WordPress version
- `check-install` - Check WordPress installation

**Enhanced Category Management** (`praisonaiwp category`)
- `create <name>` - Create new category
- `update <id>` - Update existing category
- `delete <id>` - Delete category
- Existing commands: `list`, `set`, `add`, `remove`, `search`

**Theme Management** (`praisonaiwp theme`)
- `list` - List all themes
- `activate <slug>` - Activate theme

**Menu Management** (`praisonaiwp menu`)
- `list` - List all menus
- `create <name>` - Create new menu
- `delete <id>` - Delete menu
- `add-item <id>` - Add item to menu

**Transient Management** (`praisonaiwp transient`)
- `get <key>` - Get transient value
- `set <key> <value>` - Set transient with expiration
- `delete <key>` - Delete transient

**Post Utilities** (`praisonaiwp post`)
- `delete <id>` - Delete post
- `exists <id>` - Check if post exists

**Database Operations** (`praisonaiwp db`)
- `query "<SQL>"` - Execute database queries

#### Technical Improvements
- **Rich Output**: All commands use Rich library for beautiful formatting
- **Error Handling**: Comprehensive error handling and user feedback
- **Server Support**: All commands support multiple server configurations
- **Confirmation Prompts**: Destructive operations require confirmation
- **Table Formatting**: Data displayed in formatted tables where appropriate

#### Files Added/Modified
- **New Command Files**: 10 new CLI command modules
- **Test Files**: 10 comprehensive test suites
- **Enhanced Main**: Updated CLI registration for all new commands
- **Documentation**: Complete command documentation and examples

#### Statistics
- **Total Methods**: 61/61 (100% coverage)
- **New Commands**: 15 command groups
- **New Tests**: 68 tests passing
- **Lines of Code**: 2000+ lines of new functionality

## [1.4.3] - 2025-12-22

### Documentation
- **Coverage Analysis**: Documented WPClient method coverage status
  - Current coverage: 28/61 methods (45.9%)
  - Exposed methods: User management, Media, Categories, Plugins, Posts, Search
  - Missing methods: 34 (Options, Meta, Comments, System, Themes, Menus, Transients)
- **Roadmap Created**: Detailed TDD implementation plan for remaining 34 methods
  - 10 priorities with test-first approach
  - Estimated 10-15 hours for complete implementation
  - Target: 100% WPClient coverage (61/61 methods)

### Analysis
- **Identified Gaps**: Comprehensive analysis of missing CLI commands
  - Options management (3 methods)
  - Post/User meta (8 methods)
  - Comment management (6 methods)
  - System commands (4 methods)
  - Theme/Menu/Transient management (9 methods)
  - Post utilities (4 methods)

## [1.4.2] - 2025-12-22

### Added
- **Media URL Retrieval**: New commands to get media/attachment information
  - `praisonaiwp media url <ID>` - Get media URL directly
  - `praisonaiwp media get <ID>` - Get full attachment information
  - `praisonaiwp media list` - List all attachments with filters
  - `--post-id` filter to list attachments for specific post
  - `--mime-type` filter to list by file type
  - Rich table display for media listings

### Enhanced
- **WPClient Methods**: Added media retrieval methods
  - `get_media_info()` - Get attachment data
  - `get_media_url()` - Get attachment URL
  - `list_media()` - List attachments with filters
- **Media Command**: Converted to command group with subcommands
  - `upload` - Upload media (previously default)
  - `get` - Get attachment info
  - `url` - Get attachment URL
  - `list` - List attachments

### Fixed
- Media URL retrieval no longer requires manual SSH commands
- Easy access to uploaded file URLs for AI agents and automation

## [1.4.1] - 2025-12-21

### Added
- **SmartContentAgent**: AI agent with intelligent server routing
  - `detect_server_from_context()`: Auto-detect server from title, content, or tags
  - `suggest_server()`: Suggest server with confidence score
  - `create_post_with_routing()`: Create posts with automatic routing
  - `generate_content()`: AI content generation with server context
  - Tag-based server matching for AI content classification
  - Applies server-specific defaults (author, category)
  - Respects `auto_route` setting

- **Test Coverage**: 10 new tests for SmartContentAgent (34 total, 100% passing)
  - Server detection from title/content
  - Tag-based matching
  - Explicit server override
  - Confidence scoring
  - WordPress integration

### Enhanced
- **AI Integration**: Seamless integration with ServerRouter
- **Context-Aware**: AI considers server description and tags when generating
- **Intelligent Defaults**: Auto-applies server-specific author and category

## [1.4.0] - 2025-12-21

### 🎉 Major Release: Configuration v2.0 with Auto-Routing

### Added
- **Configuration v2.0 Schema**: Enhanced server configuration with website identification
  - `website` field: Primary website URL for each server (e.g., `https://biblerevelation.org`)
  - `aliases` field: Alternative domains for the same server
  - `description` field: Human-readable server description
  - `tags` field: Searchable tags for AI-based server matching
  - `author` and `category` fields: Default post metadata per server
  - `auto_route` setting: Enable/disable automatic server selection

- **ServerRouter Class**: Intelligent server routing based on context
  - `find_server_by_website()`: Route by explicit website URL or domain
  - `find_server_by_keywords()`: Auto-detect server from content text
  - `get_server_info()`: Get human-readable server information
  - Case-insensitive matching with www. normalization
  - Support for domain aliases

- **Configuration Migration**: Automatic v1.0 to v2.0 migration
  - `migrate_config_v1_to_v2()`: Upgrades old configs automatically
  - `extract_website_from_wp_path()`: Extracts domain from WordPress paths
  - `needs_migration()`: Checks if migration is needed
  - Backward compatible with v1.0 configs

- **Test Coverage**: 24 new tests for v2.0 features
  - 11 tests for config schema and migration
  - 13 tests for ServerRouter functionality
  - 100% test pass rate

### Enhanced
- **AI-Friendly Configuration**: Clear website mapping for intelligent routing
- **User Experience**: Servers now self-documenting with website URLs
- **Safety**: Auto-route defaults to False, requires explicit enablement

### Benefits
- **For Users**: Immediately see which website each server manages
- **For AI Assistants**: Can auto-detect correct server from content context
- **For Developers**: Extensible routing strategies with isolated, testable logic

### Migration Guide
Existing v1.0 configs continue to work. To upgrade to v2.0:
1. Add `website` field to each server configuration
2. Optionally add `aliases`, `description`, and `tags`
3. Set `auto_route: true` in settings to enable auto-routing
4. Update `version: '2.0'`

## [1.1.6] - 2025-12-14

### Added
- **Media CLI Command**: `praisonaiwp media` for uploading media files via WP-CLI
  - Upload local files (auto-uploads via SFTP): `praisonaiwp media /path/to/image.jpg`
  - Import from URL: `praisonaiwp media https://example.com/image.jpg`
  - Attach to posts: `--post-id 123`
  - Set metadata: `--title`, `--caption`, `--alt`, `--desc`
- **SFTP Upload**: Added `upload_file()` method to SSHManager for file transfers

### Fixed
- Fixed media command failing with local files (now uploads via SFTP first)

## [1.1.0] - 2025-11-19

### 🎉 Major Release: Production-Ready AI Integration

### Added
- **PraisonAI Integration**: Full integration with PraisonAI framework for AI-powered content generation
  - WordPress tools for PraisonAI agents (create, update, list posts)
  - Integration class with task callbacks
  - CLI commands: `praisonaiwp ai generate`
  - Optional dependencies: `pip install praisonaiwp[ai]`

- **Production Features**:
  - ✅ API key validation (validates OpenAI API key on initialization)
  - ✅ Content validation (length, paragraph structure, placeholder detection)
  - ✅ Cost tracking (per-generation and cumulative with model-specific pricing)
  - ✅ Retry logic (3 automatic retries with exponential backoff)
  - ✅ Rate limiting (configurable limits to prevent API errors)
  - ✅ Structured logging (detailed metrics and progress tracking)

- **New Modules**:
  - `praisonaiwp/ai/integration.py` - Main AI integration class
  - `praisonaiwp/ai/tools/wordpress_tools.py` - WordPress tools for agents
  - `praisonaiwp/ai/utils/validators.py` - API key & content validation
  - `praisonaiwp/ai/utils/cost_tracker.py` - Cost tracking
  - `praisonaiwp/ai/utils/retry.py` - Retry with exponential backoff
  - `praisonaiwp/ai/utils/rate_limiter.py` - Rate limiting
  - `praisonaiwp/cli/commands/ai_commands.py` - AI CLI commands

### Enhanced
- **Test Coverage**: Added 40 new tests (58 total AI tests, 100% passing)
  - API key validation tests
  - Content validation tests
  - Cost tracking tests
  - Rate limiting tests
  - Retry logic tests
  - Integration tests
  - CLI command tests

- **Documentation**: Comprehensive guides added
  - `AI_IMPLEMENTATION_SUMMARY.md` - Complete implementation details
  - `PRODUCTION_READY_SUMMARY.md` - Production deployment guide
  - `PRODUCTION_ENHANCEMENTS.md` - Enhancement recommendations
  - `QUICK_START_AI.md` - Quick start guide
  - `AI_FEATURES_README.md` - Feature overview

### Technical Details
- **Default Model**: gpt-4o-mini (cost-effective, ~$0.0005 per 500-word post)
- **Backward Compatible**: All new features are optional
- **Test-Driven Development**: All features implemented with TDD approach
- **Error Handling**: Comprehensive error handling with clear messages

### Usage
```bash
# Install with AI features
pip install praisonaiwp[ai]

# Set API key
export OPENAI_API_KEY="sk-..."

# Generate content
praisonaiwp ai generate "AI Trends 2025"

# Generate and publish
praisonaiwp ai generate "AI Trends" \
  --title "The Future of AI" \
  --auto-publish \
  --status publish
```

### Breaking Changes
None - Fully backward compatible

### Migration
No migration needed. AI features are opt-in via `pip install praisonaiwp[ai]`

## [1.0.22] - 2025-11-19

### Fixed
- **Reverted v1.0.21**: Fixed regression where categories were not being set
  - v1.0.21 suppressed errors too aggressively, breaking category assignment
  - Restored v1.0.20 approach: catch error, verify category was set, continue
  - Categories now work correctly again
  
### Lesson Learned
- Warning messages are cosmetic but the error handling is functional
- Suppressing at lower levels (SSH/WP client) breaks the verification logic
- The v1.0.20 approach is correct: handle at the business logic level

### Status
- ⚠️ Warning messages still appear (cosmetic only)
- ✅ Categories set correctly
- ✅ All functionality preserved
- ✅ 196 tests passing

## [1.0.21] - 2025-11-19 [YANKED - DO NOT USE]

### Fixed
- **Complete Warning Suppression**: Fully suppressed "Term doesn't exist" warnings
  - Fixed at SSH manager level (suppresses WARNING message)
  - Fixed at WP client level (suppresses ERROR message)
  - Categories still set correctly
  - Clean, professional output with no confusing messages

### Improved
- Multi-layer error handling for cosmetic WP-CLI warnings
- Better logging - warnings logged as debug messages
- Cleaner user experience

### User Impact
**Before v1.0.21:**
```
WARNING: Command stderr: Error: Term doesn't exist.
ERROR: WP-CLI error: Error: Term doesn't exist.
```

**After v1.0.21:**
```
✓ Created post ID: 49006
Title: Test v1.0.21
Categories: Other
```

## [1.0.20] - 2025-11-19

### Fixed
- **Category Warning Suppressed**: Fixed cosmetic "Term doesn't exist" warning when setting categories
  - WP-CLI sometimes reports this warning even when category is set successfully
  - Added error handling to verify category was set and suppress warning
  - Improves user experience with cleaner output
  
- **Windows CI/CD**: Fixed test failure on Windows platform
  - File permissions test now skipped on Windows (platform-specific)
  - Windows uses ACLs instead of Unix rwx permissions
  - CI/CD now passes on all platforms (Ubuntu, macOS, Windows)

### Improved
- Better error handling in `set_post_categories()` method
- Verifies category assignment even when WP-CLI reports warnings
- More robust cross-platform testing

### Testing
- ✅ 196 tests passing on Unix (macOS, Linux)
- ✅ 195 tests passing on Windows (1 skipped - permissions test)
- ✅ CI/CD fully green on all platforms
- ✅ Multi-Python compatibility (3.8-3.12)

## [1.0.19] - 2025-11-19

### Changed
- **BREAKING**: Block conversion is now **enabled by default** (opt-out instead of opt-in)
  - Changed `--convert-to-blocks` flag → `--no-block-conversion` flag
  - HTML content automatically converts to Gutenberg blocks
  - Use `--no-block-conversion` to disable if you want raw HTML
  
### Improved
- **Better Default Behavior**: Most users want blocks, so it's now automatic
- **Cleaner API**: Opt-out design is more intuitive
- **Zero Configuration**: Works out of the box with best practices
- **Smart Detection**: Auto-detects existing blocks, won't double-convert

### Added
- Auto-conversion messages show when converting or skipping
- Integration tests for opt-out design (3 new tests)
- Comprehensive CI/CD pipeline with multi-OS and multi-Python testing

### Migration from v1.0.18
**Old (v1.0.18):**
```bash
praisonaiwp create "Post" --content "<h2>Title</h2>" --convert-to-blocks
```

**New (v1.0.19):**
```bash
# Auto-converts by default - just remove the flag!
praisonaiwp create "Post" --content "<h2>Title</h2>"

# Disable if you want raw HTML
praisonaiwp create "Post" --content "<h2>Title</h2>" --no-block-conversion
```

### Testing
- 193 total tests passing (35 integration + 58 block converter + 100 existing)
- CI/CD pipeline tests across Ubuntu, macOS, Windows
- Python 3.8, 3.9, 3.10, 3.11, 3.12 compatibility

## [1.0.18] - 2025-11-19

### Fixed
- **Critical Import Error**: Fixed `ModuleNotFoundError` in v1.0.17
  - Corrected import path in `update.py`: `praisonaiwp.core.content_editor` → `praisonaiwp.editors.content_editor`
  - v1.0.17 was broken and unusable
  - v1.0.18 restores full functionality

### Note
- All v1.0.17 features (HTML to Gutenberg blocks converter) are working correctly in v1.0.18
- If you installed v1.0.17, please upgrade to v1.0.18 immediately

## [1.0.17] - 2025-11-19 [BROKEN - DO NOT USE]

### Added
- **HTML to Gutenberg Blocks Converter**: Automatic conversion of HTML to WordPress blocks
  - `--convert-to-blocks` flag for both `create` and `update` commands
  - Safe, conservative conversion approach - only converts well-known patterns
  - Wraps complex HTML in `<!-- wp:html -->` blocks to prevent content loss
  - Auto-detects if content already has blocks (idempotent)
  - Preserves custom HTML, CSS, JavaScript, inline styles, and complex structures

### Features
- Converts: Headings (H1-H6), simple paragraphs, code blocks, simple lists
- Preserves: Custom HTML, nested structures, tables, forms, scripts, styles, iframes
- Handles: Empty content, malformed HTML, special characters, Unicode, HTML entities
- User-friendly: Handles common mistakes (unclosed tags, mixed case, extra whitespace)

### Test Coverage
- 58 comprehensive test cases covering all edge cases
- Tests for basic conversions, edge cases, complex structures, custom HTML preservation
- Real-world scenarios: blog posts, documentation, landing pages
- Safety & robustness tests: long content, deep nesting, empty tags
- Integration tests: full article conversion, idempotent conversion

### Documentation
- Complete inline documentation in block_converter.py
- Comprehensive test documentation with use case descriptions

### Design Philosophy
- **Safety First**: Never break content - use wp:html blocks for uncertain cases
- **WordPress-Native**: Uses official WordPress block format
- **Extensible**: Easy to add more conversions in the future
- **Well-Tested**: 156 total tests passing (58 new + 98 existing)

## [1.0.16] - 2025-11-18

### Added
- **Advanced Post Update Options**: Full WP-CLI post update support
  - `--post-excerpt` - Update post excerpt
  - `--post-author` - Update post author (user ID or login)
  - `--post-date` - Update post date (YYYY-MM-DD HH:MM:SS)
  - `--tags` - Update tags (comma-separated)
  - `--meta` - Update post meta in JSON format
  - `--comment-status` - Update comment status (open/closed)

### Documentation
- Updated README with all update command options
- Added examples for updating excerpt, author, date, tags, and meta
- Updated options summary table

### Notes
- `update` command now has feature parity with WP-CLI `post update`
- Both `create` and `update` commands support full post customization
- All WP-CLI post parameters accessible via CLI

## [1.0.15] - 2025-11-18

### Added
- **Advanced Post Creation Options**: Full WP-CLI post create support
  - `--excerpt` - Add post excerpt/summary
  - `--date` - Set custom post date (YYYY-MM-DD HH:MM:SS)
  - `--tags` - Add tags (comma-separated names or IDs)
  - `--meta` - Add custom post meta in JSON format `{"key":"value"}`
  - `--comment-status` - Control comments (open/closed)

### Documentation
- Added comprehensive CLI reference section for AI agents
- Documented all available options for each command
- Added proper quoting examples for multi-word arguments
- Added options summary table
- Included examples for custom meta data, tags, excerpt, and dates

### Notes
- Core `WPClient.create_post()` accepts any WP-CLI parameter via **kwargs
- CLI now exposes the most commonly used advanced options
- Custom taxonomies can be added via `--meta` in JSON format

## [1.0.14] - 2025-11-18

### Added
- **CLI Enhancements**: New options for better post management
  - `--author` option in `create` command - Set post author by user ID or login
  - `--post-content` option in `update` command - Replace entire post content
  - `--post-title` option in `update` command - Update post title
  - `--post-status` option in `update` command - Change post status
  - `--search` / `-s` option in `list` command - Search posts by title/content

### Fixed
- Issue #1: Author can now be set when creating posts via CLI
- Issue #2: Post content can be updated directly without find/replace
- Issue #3: Posts can be searched/filtered in list command

### Testing
- Added 3 test cases verifying core functionality
- All 71/72 tests passing (98.6% pass rate)

### Notes
- Core WPClient already supported these features
- This release adds CLI layer access to existing functionality

## [1.0.13] - 2025-11-17

### Added
- **Generic `wp()` Method**: Universal WP-CLI command executor
  - Supports ALL WP-CLI commands (1000+ commands)
  - Automatic JSON parsing with `format='json'`
  - Underscore to hyphen conversion (dry_run → --dry-run)
  - Boolean flag support (porcelain=True → --porcelain)
  - No need to wait for wrapper methods
  - See GENERIC_WP_METHOD.md for comprehensive guide

### Changed
- Hybrid approach: Keep convenience methods + add generic wp() method
- Users can now use ANY WP-CLI command directly
- Enhanced flexibility for power users

### Testing
- Added 4 new unit tests for wp() method
- All 68/69 tests passing (99% pass rate)

### Documentation
- Added GENERIC_WP_METHOD.md with examples and best practices
- Documented when to use convenience methods vs wp()

## [1.0.12] - 2025-11-17

### Added
- **Term Management**: Complete CRUD operations
  - create_term() - Create new term with options
  - delete_term() - Delete term from taxonomy
  - update_term() - Update term fields
- **Core Commands**: WordPress core information
  - get_core_version() - Get WordPress version
  - core_is_installed() - Check installation status

### Changed
- Updated WPCLI.md with term and core command support
- Enhanced category/term management documentation

### Testing
- Added 5 new unit tests
- All 64/65 tests passing (98% pass rate)

## [1.0.11] - 2025-11-17

### Added
- **Cache Management**: flush_cache(), get_cache_type()
- **Transient Management**: Complete CRUD operations
  - get_transient() - Get transient value
  - set_transient() - Set with optional expiration
  - delete_transient() - Remove transient
- **Menu Management**: Complete menu operations
  - list_menus() - List all menus
  - create_menu() - Create new menu
  - delete_menu() - Remove menu
  - add_menu_item() - Add custom menu item

### Changed
- Updated WPCLI.md with cache, transient, and menu support
- Enhanced summary with all management features

### Testing
- Added 9 new unit tests
- All 59/60 tests passing (98% pass rate)

## [1.0.10] - 2025-11-17

### Added
- **Plugin Activation**: activate_plugin(), deactivate_plugin()
- **Theme Activation**: activate_theme()
- **User Meta Management**: Complete CRUD operations
  - get_user_meta() - Get single or all meta values
  - set_user_meta() - Set meta value
  - update_user_meta() - Update existing meta
  - delete_user_meta() - Remove meta field

### Changed
- Updated WPCLI.md with plugin/theme activation and user meta support
- Enhanced summary with all activation features

### Testing
- Added 7 new unit tests
- All 50/51 tests passing (98% pass rate)

## [1.0.9] - 2025-11-17

### Added
- **Media Management**: import_media() with metadata and post attachment
- **Comment Management**: Complete CRUD operations
  - list_comments() - List comments with filters
  - get_comment() - Get comment details
  - create_comment() - Create comment on post
  - update_comment() - Update comment fields
  - delete_comment() - Delete with force option
  - approve_comment() - Approve comment

### Changed
- Updated WPCLI.md with media and comment support
- Enhanced summary with all management features

### Testing
- Added 8 new unit tests
- All 43/44 tests passing (98% pass rate)

## [1.0.8] - 2025-11-17

### Added
- **User CRUD Operations**: Complete user management
  - create_user() - Create users with role and custom fields
  - update_user() - Update user fields
  - delete_user() - Delete users with post reassignment option
- **Plugin Management**: list_plugins() with status filters
- **Theme Management**: list_themes() with status filters

### Changed
- Updated WPCLI.md with comprehensive user/plugin/theme support
- Enhanced summary section with all management features

### Testing
- Added 5 new unit tests
- All 36/37 tests passing

## [1.0.7] - 2025-11-17

### Added
- **Post Deletion**: delete_post() with force option
- **Post Exists Check**: post_exists() to verify post existence
- **Post Meta Management**: Complete CRUD operations
  - get_post_meta() - Get single or all meta values
  - set_post_meta() - Set meta value
  - update_post_meta() - Update existing meta
  - delete_post_meta() - Remove meta field
- **User Management**: Basic user operations
  - list_users() - List users with filters
  - get_user() - Get user details
- **Option Management**: WordPress options CRUD
  - get_option() - Get option value
  - set_option() - Set option value
  - delete_option() - Remove option

### Changed
- Updated WPCLI.md with comprehensive feature matrix
- Enhanced summary section with all implemented features

### Testing
- Added 15+ new unit tests
- All tests passing (31/31)

## [1.0.6] - 2025-11-17

### Added
- **Fast Search**: Optimized find command with WP_Query 's' parameter
  - Server-side MySQL LIKE search (10x faster)
  - Search 800+ posts in 4 seconds instead of 50+ seconds
  - Only fetches matching posts instead of all posts

### Changed
- Consolidated documentation (removed 10 redundant docs)
- Keep only specialized docs: ARCHITECTURE.md, TESTING.md, CHANGELOG.md
- Enhanced README with category examples and troubleshooting

## [1.0.5] - 2025-11-17

### Added
- **Category Management**: Full category support for WordPress posts
  - New `category` command group with subcommands: set, add, remove, list, search
  - `--category` and `--category-id` options for create and update commands
  - 7 new WPClient methods for category operations
  - Rich table output for category listings
  - Support for both category names and IDs
- **SSH Config Host Integration**: Reference SSH config hosts directly in config.yaml
  - New `ssh_host` parameter to reference `~/.ssh/config` hosts
  - Automatic loading of connection details from SSH config
  - Support for mixing SSH config and direct specification
  - Direct values override SSH config values
- **Enhanced Documentation**: Comprehensive README updates with all features

### Changed
- Updated repository name to PraisonAI-WPcli
- Improved README with category examples and troubleshooting section
- Enhanced configuration flexibility with multiple methods

### Fixed
- Config loading now properly supports both ssh_host and direct specification

## [1.0.4] - 2025-10-26

### Changed
- All examples now use neutral, professional terminology suitable for any WordPress site

## [1.0.3] - 2025-10-26

### Changed
- Updated documentation, examples, and test files with neutral terminology

## [1.0.2] - 2025-10-26

### Documentation
- Updated README.md with comprehensive feature documentation
- Added detailed examples for all new v1.0.1 features
- Enhanced Quick Start guide with auto-install and auto-detect workflows
- Added SSH config integration examples
- Improved feature descriptions with use cases

## [1.0.1] - 2025-10-26

### Added
- **SSH Config Support**: PraisonAIWP now supports `~/.ssh/config` for simplified connection management
  - Use host aliases instead of full connection details
  - Automatically loads username, hostname, port, and SSH key from SSH config
  - Supports advanced SSH features (ProxyJump, ControlMaster, etc.)
  - See `SSH_CONFIG_GUIDE.md` for complete documentation
- **UV Package Manager Support**: Migrated to `uv` for 10-100x faster dependency management
  - Added `pyproject.toml` as primary configuration
  - Added `.python-version` for Python version pinning
  - Created comprehensive `UV_GUIDE.md` documentation
  - Maintained backward compatibility with pip
- **Enhanced Security**: Removed all hardcoded credentials from test files
  - Test scripts now require config file or environment variables
  - Added `.env.example` with placeholder values
  - All documentation uses generic examples

### Changed
- Updated `SSHManager` to support optional parameters (username, key_file)
- SSH config is now loaded automatically by default (can be disabled with `use_ssh_config=False`)
- Improved error messages with helpful guidance for missing configuration

### Fixed
- Fixed `pyproject.toml` requires-python constraint (>=3.8.1 for flake8 compatibility)
- Improved test script configuration loading with better fallbacks

### Documentation
- Added `SSH_CONFIG_GUIDE.md` - Complete guide for SSH config integration
- Added `UV_GUIDE.md` - Comprehensive uv package manager guide
- Added `UV_MIGRATION.md` - Migration documentation and comparison
- Added `TEST_SETUP.md` - Test setup guide with multiple configuration options
- Updated `README.md` with SSH config feature
- Updated `QUICKSTART.md` with SSH config tip
- Added `CHANGELOG.md` - This file

## [1.0.0] - 2025-10-25

### Added
- Initial release of PraisonAIWP
- Core SSH connection management
- WP-CLI wrapper for WordPress operations
- Content editor with line-specific and occurrence-specific replacements
- Configuration management system
- 5 CLI commands: init, create, update, find, list
- Unit tests for core modules
- Node.js parallel executor for bulk operations
- Comprehensive documentation (ARCHITECTURE.md, README.md, QUICKSTART.md)
- Example scripts and files

### Features
- Line-specific text replacement (update line 10 without touching line 55)
- Nth occurrence replacement (update 2nd occurrence only)
- Auto-parallel mode for bulk operations (10x faster)
- Preview mode and dry-run capabilities
- Auto-backup before destructive operations
- Multi-server support
- Smart file format detection (JSON, YAML, CSV)
- Rich CLI output with colors and progress bars

[1.0.1]: https://github.com/MervinPraison/praisonaiwp/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/MervinPraison/praisonaiwp/releases/tag/v1.0.0
