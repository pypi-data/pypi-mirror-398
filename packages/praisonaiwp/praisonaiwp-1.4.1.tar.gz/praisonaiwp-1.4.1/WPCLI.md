# WP-CLI Commands Reference

## PraisonAI WP Support Status

| WP-CLI Command | Supported | Feature |
|---|---|---|
| **wp post create** | ✅ | Create new posts |
| **wp post update** | ✅ | Update existing posts |
| **wp post list** | ✅ | List posts with filters |
| **wp post get** | ✅ | Get post details |
| **wp post delete** | ✅ | Delete posts (trash or force) |
| **wp post edit** | ❌ | Launch editor for post |
| **wp post exists** | ✅ | Check if post exists |
| **wp post generate** | ❌ | Generate dummy posts |
| **wp post meta** | ✅ | Manage post meta (get, set, update, delete, list) |
| **wp post term** | ✅ | Manage post terms/categories |
| **wp post url-to-id** | ❌ | Convert URL to post ID |

## Post Parameters (wp post list)

| Parameter | Supported | Feature |
|---|---|---|
| `--post_type` | ✅ | Filter by post type |
| `--post_status` | ✅ | Filter by status (publish, draft, etc) |
| `--s` | ✅ | Search posts (server-side) |
| `--author` | ✅ | Filter by author ID |
| `--author_name` | ✅ | Filter by author name |
| `--cat` | ✅ | Filter by category ID |
| `--category_name` | ✅ | Filter by category slug |
| `--tag` | ✅ | Filter by tag slug |
| `--tag_id` | ✅ | Filter by tag ID |
| `--post__in` | ✅ | Specific post IDs |
| `--post__not_in` | ✅ | Exclude post IDs |
| `--posts_per_page` | ✅ | Limit results |
| `--paged` | ✅ | Pagination |
| `--offset` | ✅ | Skip posts |
| `--order` | ✅ | ASC or DESC |
| `--orderby` | ✅ | Sort by field |
| `--year` | ✅ | Filter by year |
| `--monthnum` | ✅ | Filter by month |
| `--day` | ✅ | Filter by day |
| `--meta_key` | ✅ | Filter by meta key |
| `--meta_value` | ✅ | Filter by meta value |
| `--meta_compare` | ✅ | Meta comparison operator |
| `--fields` | ✅ | Limit output fields |
| `--format` | ✅ | Output format (json, csv, table) |

## Term/Category Commands

| WP-CLI Command | Supported | Feature |
|---|---|---|
| **wp term create** | ✅ | Create new term |
| **wp term delete** | ✅ | Delete term |
| **wp term list** | ✅ | List terms in taxonomy |
| **wp term get** | ✅ | Get term details |
| **wp term update** | ✅ | Update term |
| **wp term meta** | ❌ | Manage term meta |
| **wp term migrate** | ❌ | Migrate term to another taxonomy |
| **wp term recount** | ❌ | Recount term posts |
| **wp post term add** | ✅ | Add term to post |
| **wp post term remove** | ✅ | Remove term from post |
| **wp post term list** | ✅ | List post terms |
| **wp post term set** | ✅ | Set post terms (replace all) |

## Database Commands

| WP-CLI Command | Supported | Feature |
|---|---|---|
| **wp db query** | ✅ | Execute SQL query |
| **wp db export** | ❌ | Export database |
| **wp db import** | ❌ | Import database |
| **wp db optimize** | ❌ | Optimize database |
| **wp db repair** | ❌ | Repair database |
| **wp db reset** | ❌ | Reset database |
| **wp db search** | ❌ | Search database |
| **wp db tables** | ❌ | List database tables |

## Search & Replace

| WP-CLI Command | Supported | Feature |
|---|---|---|
| **wp search-replace** | ✅ | Search and replace in database |
| **--dry-run** | ✅ | Preview changes |
| **--precise** | ❌ | Match whole words only |
| **--regex** | ❌ | Use regex patterns |
| **--all-tables** | ❌ | Include all tables |

## Core Commands

| WP-CLI Command | Supported | Feature |
|---|---|---|
| **wp core version** | ✅ | Check WP version |
| **wp core update** | ❌ | Update WordPress |
| **wp core download** | ❌ | Download WordPress |
| **wp core install** | ❌ | Install WordPress |
| **wp core is-installed** | ✅ | Check if WP is installed |

## Plugin Commands

| WP-CLI Command | Supported | Feature |
|---|---|---|
| **wp plugin list** | ✅ | List plugins with filters |
| **wp plugin install** | ❌ | Install plugin |
| **wp plugin activate** | ✅ | Activate plugin |
| **wp plugin deactivate** | ✅ | Deactivate plugin |
| **wp plugin delete** | ❌ | Delete plugin |
| **wp plugin update** | ❌ | Update plugin |

## Theme Commands

| WP-CLI Command | Supported | Feature |
|---|---|---|
| **wp theme list** | ✅ | List themes with filters |
| **wp theme install** | ❌ | Install theme |
| **wp theme activate** | ✅ | Activate theme |
| **wp theme delete** | ❌ | Delete theme |
| **wp theme update** | ❌ | Update theme |

## User Commands

| WP-CLI Command | Supported | Feature |
|---|---|---|
| **wp user list** | ✅ | List users with filters |
| **wp user create** | ✅ | Create user with role and fields |
| **wp user update** | ✅ | Update user fields |
| **wp user delete** | ✅ | Delete user with reassign option |
| **wp user meta** | ✅ | Manage user meta (get, set, update, delete, list) |

## Option Commands

| WP-CLI Command | Supported | Feature |
|---|---|---|
| **wp option get** | ✅ | Get option value |
| **wp option set** | ✅ | Set option value |
| **wp option delete** | ✅ | Delete option |
| **wp option list** | ❌ | List options |

## Media Commands

| WP-CLI Command | Supported | Feature |
|---|---|---|
| **wp media import** | ✅ | Import media with metadata |
| **wp media regenerate** | ❌ | Regenerate thumbnails |

## Comment Commands

| WP-CLI Command | Supported | Feature |
|---|---|---|
| **wp comment list** | ✅ | List comments with filters |
| **wp comment create** | ✅ | Create comment on post |
| **wp comment update** | ✅ | Update comment fields |
| **wp comment delete** | ✅ | Delete comment (trash or force) |
| **wp comment approve** | ✅ | Approve comment |
| **wp comment unapprove** | ❌ | Unapprove comment |
| **wp comment spam** | ❌ | Mark as spam |
| **wp comment trash** | ❌ | Move to trash |

## Menu Commands

| WP-CLI Command | Supported | Feature |
|---|---|---|
| **wp menu list** | ✅ | List menus |
| **wp menu create** | ✅ | Create menu |
| **wp menu delete** | ✅ | Delete menu |
| **wp menu item add** | ✅ | Add custom menu item |

## Cache Commands

| WP-CLI Command | Supported | Feature |
|---|---|---|
| **wp cache flush** | ✅ | Flush cache |
| **wp cache type** | ✅ | Get cache type |

## Transient Commands

| WP-CLI Command | Supported | Feature |
|---|---|---|
| **wp transient delete** | ✅ | Delete transient |
| **wp transient get** | ✅ | Get transient |
| **wp transient set** | ✅ | Set transient with expiration |

## Cron Commands

| WP-CLI Command | Supported | Feature |
|---|---|---|
| **wp cron event list** | ❌ | List cron events |
| **wp cron event run** | ❌ | Run cron event |

## Export/Import

| WP-CLI Command | Supported | Feature |
|---|---|---|
| **wp export** | ❌ | Export content |
| **wp import** | ❌ | Import content |

## 🚀 IMPORTANT: Generic `wp()` Method

**ALL WP-CLI commands are now supported via the generic `wp()` method!**

Even if a command is marked as ❌ below, you can still use it:

```python
# Any WP-CLI command works!
client.wp('db', 'export', 'backup.sql')
client.wp('plugin', 'install', 'akismet')
client.wp('cron', 'event', 'list', format='json')
client.wp('media', 'regenerate', '--yes')
```

See **README.md** (Universal WP-CLI Access section) for complete documentation.

The table below shows **convenience methods** (with IDE autocomplete and docs).
For everything else, use the powerful `wp()` method!

---

## Design Philosophy: Why Two Approaches?

### Convenience Methods (✅) vs Generic `wp()` Method (❌)

We provide **both** approaches for different use cases:

#### **Convenience Methods (✅)** - High-Level API
**When:** Frequently used operations (80% of use cases)

**Benefits:**
- ✅ **IDE Autocomplete** - See available parameters
- ✅ **Type Hints** - Catch errors before runtime
- ✅ **Inline Documentation** - Docstrings explain usage
- ✅ **Validation** - Python-side parameter validation
- ✅ **Return Type Handling** - Automatic parsing/conversion
- ✅ **Better Developer Experience** - Clean, intuitive API

**Example:**
```python
# Clean, type-safe, documented
post_id = client.create_post(
    post_title='My Post',
    post_content='Content here',
    post_status='publish'
)  # Returns: int (post ID)
```

#### **Generic `wp()` Method (❌)** - Low-Level API
**When:** Rarely used, simple, or future operations

**Benefits:**
- ✅ **Universal** - ALL 1000+ WP-CLI commands
- ✅ **Future-Proof** - Supports new WP-CLI features automatically
- ✅ **Flexible** - Custom WP-CLI packages work out of the box
- ✅ **No Maintenance** - No code updates needed for new commands
- ✅ **Simple Operations** - One-liners don't need wrappers

**Example:**
```python
# Direct WP-CLI access - works for anything
client.wp('db', 'export', 'backup.sql')
client.wp('plugin', 'install', 'akismet', activate=True)
client.wp('cron', 'event', 'run', 'my_custom_hook')
```

### Why Not Implement Everything as Convenience Methods?

**Maintenance Burden:**
- ❌ Would require 100+ additional methods
- ❌ Each needs: implementation, tests, docs, maintenance
- ❌ WP-CLI updates would require code changes
- ❌ Code bloat: ~3000+ lines vs current ~1300 lines

**Diminishing Returns:**
- ✅ 80% of operations already have convenience methods
- ✅ Remaining 20% are rarely used or simple enough
- ✅ Generic `wp()` handles the long tail perfectly

### When to Add New Convenience Methods?

Only add if the operation is:
1. **Frequently used** by most users
2. **Complex syntax** that benefits from Python wrapper
3. **Needs validation** or special handling
4. **Explicitly requested** by users

### Historical Context

- **v1.0.0-1.0.12**: Only convenience methods existed
- **v1.0.13**: Generic `wp()` method added as "escape hatch"
- **v1.0.13+**: Best of both worlds - convenience + flexibility

### Think of It Like:
- **Convenience Methods** = jQuery (high-level, common tasks)
- **Generic `wp()` Method** = Vanilla JS (low-level, full power)

Both have their place!

---

## Summary

### Currently Supported (✅)
- **Post Management**: create, update, list, get, delete, exists
- **Post Meta**: get, set, update, delete, list
- **Post Search**: WP_Query 's' parameter (server-side)
- **Category/Term Management**: set, add, remove, list, search, create, delete, update
- **User Management**: list, get, create, update, delete (with reassign)
- **User Meta**: get, set, update, delete, list
- **Option Management**: get, set, delete
- **Plugin Management**: list, activate, deactivate
- **Theme Management**: list, activate
- **Media Management**: import with metadata and post attachment
- **Comment Management**: list, get, create, update, delete, approve
- **Cache Management**: flush, get type
- **Transient Management**: get, set, delete
- **Menu Management**: list, create, delete, add items
- **Core Commands**: version check, installation check
- **Database**: queries, search-replace
- **All WP_Query parameters** via `wp post list`
- **HTML to Gutenberg Blocks Converter** (v1.0.17): Auto-convert HTML to WordPress blocks via `--convert-to-blocks` flag

### Not Supported as Convenience Methods (❌)

**But ALL are supported via `wp()` method!**

Commands without dedicated convenience methods:
- Post edit/generate/url-to-id → Use `client.wp('post', 'edit', ...)`
- Plugin install/delete/update → Use `client.wp('plugin', 'install', ...)`
- Theme install/delete/update → Use `client.wp('theme', 'install', ...)`
- Core install/update/download → Use `client.wp('core', 'update', ...)`
- Media regenerate → Use `client.wp('media', 'regenerate', ...)`
- Comment spam/trash → Use `client.wp('comment', 'spam', ...)`
- Term meta → Use `client.wp('term', 'meta', ...)`
- Cron management → Use `client.wp('cron', 'event', ...)`
- Export/import → Use `client.wp('export', ...)` or `client.wp('import', ...)`
- Database operations → Use `client.wp('db', 'export', ...)` etc.

**You're not limited anymore!** Use `wp()` for unlimited WP-CLI access.

### Implementation Priority
1. Media import
2. Comment management
3. Plugin/theme activation
4. Menu management
5. User meta
