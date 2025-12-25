---
layout: default
title: WP-CLI Commands
---

# WP-CLI Commands Reference

## admin

Manage WordPress admin users.

```bash
praisonaiwp admin [COMMAND] [OPTIONS]
```

### Subcommands

- `list` - List admin users
- `create` - Create admin user
- `delete` - Delete admin user

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--username TEXT` | string | Admin username |
| `--email TEXT` | string | Admin email |
| `--password TEXT` | string | Admin password |
| `--role TEXT` | string | User role (default: administrator) |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp admin list
praisonaiwp admin create --username admin --email admin@example.com --password pass123
praisonaiwp admin delete --username oldadmin
```

---

## backup

Backup WordPress database and files.

```bash
praisonaiwp backup [OPTIONS]
```

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--type TEXT` | string | Backup type: db, files, all (default: all) |
| `--destination TEXT` | string | Backup destination path |
| `--compress` | flag | Compress backup |
| `--exclude TEXT` | string | Exclude patterns (comma-separated) |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp backup --type db --destination /backups
praisonaiwp backup --type all --compress
praisonaiwp backup --exclude "wp-content/uploads/*.mp4"
```

---

## block

Manage Gutenberg blocks.

```bash
praisonaiwp block [COMMAND] [OPTIONS]
```

### Subcommands

- `list` - List registered blocks
- `validate` - Validate block content

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--content TEXT` | string | Block content to validate |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp block list
praisonaiwp block validate --content "<!-- wp:paragraph --><p>Text</p><!-- /wp:paragraph -->"
```

---

## cache

Manage WordPress object cache.

```bash
praisonaiwp cache [COMMAND] [OPTIONS]
```

### Subcommands

- `flush` - Flush cache
- `add` - Add cache item
- `get` - Get cache item
- `delete` - Delete cache item
- `list` - List cache groups

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--type TEXT` | string | Cache type: all, object, transient |
| `--key TEXT` | string | Cache key |
| `--value TEXT` | string | Cache value |
| `--group TEXT` | string | Cache group |
| `--expire INTEGER` | int | Expiration time (seconds) |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp cache flush
praisonaiwp cache flush --type transient
praisonaiwp cache add --key mykey --value myvalue --group mygroup --expire 3600
praisonaiwp cache get --key mykey --group mygroup
praisonaiwp cache delete --key mykey --group mygroup
praisonaiwp cache list
```

---

## cap

Manage user capabilities.

```bash
praisonaiwp cap [COMMAND] [OPTIONS]
```

### Subcommands

- `list` - List capabilities
- `add` - Add capability to role
- `remove` - Remove capability from role

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--role TEXT` | string | Role name |
| `--cap TEXT` | string | Capability name |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp cap list --role editor
praisonaiwp cap add --role editor --cap publish_pages
praisonaiwp cap remove --role editor --cap delete_others_posts
```

---

## category

Manage post categories.

```bash
praisonaiwp category [COMMAND] [OPTIONS]
```

### Subcommands

- `list` - List categories
- `create` - Create category
- `update` - Update category
- `delete` - Delete category
- `get` - Get category details

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--name TEXT` | string | Category name |
| `--slug TEXT` | string | Category slug |
| `--description TEXT` | string | Category description |
| `--parent INTEGER` | int | Parent category ID |
| `--id INTEGER` | int | Category ID |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp category list
praisonaiwp category create --name "Technology" --slug tech
praisonaiwp category update --id 5 --name "Tech News"
praisonaiwp category delete --id 5
praisonaiwp category get --id 5
```

---

## comment

Manage post comments.

```bash
praisonaiwp comment [COMMAND] [OPTIONS]
```

### Subcommands

- `list` - List comments
- `get` - Get comment
- `create` - Create comment
- `update` - Update comment
- `delete` - Delete comment
- `approve` - Approve comment
- `unapprove` - Unapprove comment
- `spam` - Mark as spam
- `unspam` - Unmark spam
- `trash` - Move to trash
- `untrash` - Restore from trash

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--post-id INTEGER` | int | Post ID |
| `--comment-id INTEGER` | int | Comment ID |
| `--author TEXT` | string | Comment author |
| `--email TEXT` | string | Author email |
| `--content TEXT` | string | Comment content |
| `--status TEXT` | string | Comment status |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp comment list --post-id 123
praisonaiwp comment create --post-id 123 --author "John" --email "john@example.com" --content "Great post!"
praisonaiwp comment approve --comment-id 456
praisonaiwp comment spam --comment-id 789
praisonaiwp comment delete --comment-id 789
```

---

## config

Manage WordPress configuration.

```bash
praisonaiwp config [COMMAND] [OPTIONS]
```

### Subcommands

- `get` - Get config value
- `set` - Set config value
- `list` - List all config
- `has` - Check if config exists
- `delete` - Delete config value

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--key TEXT` | string | Config key |
| `--value TEXT` | string | Config value |
| `--type TEXT` | string | Value type: constant, variable |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp config get --key DB_NAME
praisonaiwp config set --key WP_DEBUG --value true
praisonaiwp config list
praisonaiwp config has --key WP_CACHE
praisonaiwp config delete --key OLD_CONSTANT
```

---

## core

Manage WordPress core.

```bash
praisonaiwp core [COMMAND] [OPTIONS]
```

### Subcommands

- `check-update` - Check for updates
- `download` - Download WordPress
- `install` - Install WordPress
- `update` - Update WordPress
- `version` - Show version
- `verify-checksums` - Verify checksums

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--version TEXT` | string | WordPress version |
| `--path TEXT` | string | Installation path |
| `--locale TEXT` | string | Locale (default: en_US) |
| `--force` | flag | Force operation |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp core version
praisonaiwp core check-update
praisonaiwp core update
praisonaiwp core download --version 6.4 --path /var/www/html
praisonaiwp core verify-checksums
```

---

## cron

Manage WordPress cron.

```bash
praisonaiwp cron [COMMAND] [OPTIONS]
```

### Subcommands

- `event list` - List cron events
- `event run` - Run cron event
- `event schedule` - Schedule event
- `event delete` - Delete event
- `test` - Test cron

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--hook TEXT` | string | Hook name |
| `--next-run TEXT` | string | Next run time |
| `--recurrence TEXT` | string | Recurrence interval |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp cron event list
praisonaiwp cron event run --hook wp_scheduled_delete
praisonaiwp cron event schedule --hook my_custom_hook --next-run "+1 hour"
praisonaiwp cron event delete --hook old_hook
praisonaiwp cron test
```

---

## db

Manage WordPress database.

```bash
praisonaiwp db [COMMAND] [OPTIONS]
```

### Subcommands

- `query` - Execute SQL query
- `export` - Export database
- `import` - Import database
- `optimize` - Optimize database
- `repair` - Repair database
- `check` - Check database
- `cli` - Open database CLI
- `size` - Show database size
- `tables` - List tables
- `prefix` - Show table prefix

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--query TEXT` | string | SQL query |
| `--file TEXT` | string | SQL file path |
| `--tables TEXT` | string | Table names (comma-separated) |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp db query --query "SELECT * FROM wp_posts LIMIT 10"
praisonaiwp db export --file backup.sql
praisonaiwp db import --file backup.sql
praisonaiwp db optimize
praisonaiwp db size
praisonaiwp db tables
```

---

## embed

Manage oEmbed cache.

```bash
praisonaiwp embed [COMMAND] [OPTIONS]
```

### Subcommands

- `fetch` - Fetch embed
- `cache-clear` - Clear embed cache
- `cache-find` - Find cached embed
- `provider list` - List providers
- `provider match` - Match provider

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--url TEXT` | string | URL to embed |
| `--post-id INTEGER` | int | Post ID |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp embed fetch --url "https://youtube.com/watch?v=..."
praisonaiwp embed cache-clear --post-id 123
praisonaiwp embed provider list
```

---

## i18n

Manage translations.

```bash
praisonaiwp i18n [COMMAND] [OPTIONS]
```

### Subcommands

- `make-pot` - Generate POT file
- `make-json` - Generate JSON translations
- `make-mo` - Generate MO file

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--domain TEXT` | string | Text domain |
| `--source TEXT` | string | Source directory |
| `--destination TEXT` | string | Destination file |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp i18n make-pot --source wp-content/themes/mytheme --destination mytheme.pot
praisonaiwp i18n make-json --source languages
praisonaiwp i18n make-mo --source mytheme.po
```

---

## language

Manage language packs.

```bash
praisonaiwp language [COMMAND] [OPTIONS]
```

### Subcommands

- `core list` - List core languages
- `core install` - Install core language
- `core activate` - Activate language
- `core uninstall` - Uninstall language
- `plugin list` - List plugin languages
- `plugin install` - Install plugin language
- `theme list` - List theme languages
- `theme install` - Install theme language

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--locale TEXT` | string | Language locale (e.g., es_ES) |
| `--plugin TEXT` | string | Plugin slug |
| `--theme TEXT` | string | Theme slug |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp language core list
praisonaiwp language core install --locale es_ES
praisonaiwp language core activate --locale es_ES
praisonaiwp language plugin install --plugin woocommerce --locale es_ES
praisonaiwp language theme install --theme twentytwentyfour --locale es_ES
```

---

## maintenance-mode

Manage maintenance mode.

```bash
praisonaiwp maintenance-mode [COMMAND] [OPTIONS]
```

### Subcommands

- `activate` - Enable maintenance mode
- `deactivate` - Disable maintenance mode
- `status` - Check status

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp maintenance-mode activate
praisonaiwp maintenance-mode deactivate
praisonaiwp maintenance-mode status
```

---

## media

Manage media files.

```bash
praisonaiwp media [COMMAND] [OPTIONS]
```

### Subcommands

- `upload` - Upload media
- `list` - List media
- `get` - Get media details
- `url` - Get media URL
- `regenerate` - Regenerate thumbnails
- `import` - Import from URL

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--file TEXT` | string | File path |
| `--url TEXT` | string | File URL |
| `--post-id INTEGER` | int | Attach to post |
| `--title TEXT` | string | Media title |
| `--caption TEXT` | string | Media caption |
| `--alt TEXT` | string | Alt text |
| `--description TEXT` | string | Description |
| `--media-id INTEGER` | int | Media ID |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp media upload --file image.jpg --post-id 123
praisonaiwp media list
praisonaiwp media get --media-id 456
praisonaiwp media url --media-id 456
praisonaiwp media import --url "https://example.com/image.jpg"
praisonaiwp media regenerate --media-id 456
```

---

## menu

Manage navigation menus.

```bash
praisonaiwp menu [COMMAND] [OPTIONS]
```

### Subcommands

- `list` - List menus
- `create` - Create menu
- `delete` - Delete menu
- `item add` - Add menu item
- `item delete` - Delete menu item
- `item list` - List menu items
- `location list` - List menu locations
- `location assign` - Assign menu to location

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--menu-id INTEGER` | int | Menu ID |
| `--name TEXT` | string | Menu name |
| `--slug TEXT` | string | Menu slug |
| `--title TEXT` | string | Item title |
| `--url TEXT` | string | Item URL |
| `--position INTEGER` | int | Item position |
| `--location TEXT` | string | Menu location |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp menu list
praisonaiwp menu create --name "Main Menu"
praisonaiwp menu item add --menu-id 1 --title "Home" --url "/"
praisonaiwp menu item list --menu-id 1
praisonaiwp menu location assign --menu-id 1 --location primary
```

---

## meta

Manage post/user metadata.

```bash
praisonaiwp meta [COMMAND] [OPTIONS]
```

### Subcommands

- `get` - Get meta value
- `add` - Add meta value
- `update` - Update meta value
- `delete` - Delete meta value
- `list` - List all meta

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--type TEXT` | string | Meta type: post, user, comment, term |
| `--id INTEGER` | int | Object ID |
| `--key TEXT` | string | Meta key |
| `--value TEXT` | string | Meta value |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp meta list --type post --id 123
praisonaiwp meta get --type post --id 123 --key custom_field
praisonaiwp meta add --type post --id 123 --key views --value 1000
praisonaiwp meta update --type post --id 123 --key views --value 2000
praisonaiwp meta delete --type post --id 123 --key old_field
```

---

## network

Manage multisite network.

```bash
praisonaiwp network [COMMAND] [OPTIONS]
```

### Subcommands

- `meta get` - Get network meta
- `meta set` - Set network meta
- `meta delete` - Delete network meta
- `meta list` - List network meta
- `option get` - Get network option
- `option set` - Set network option
- `option delete` - Delete network option
- `option list` - List network options

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--key TEXT` | string | Meta/option key |
| `--value TEXT` | string | Meta/option value |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp network meta list
praisonaiwp network meta get --key site_name
praisonaiwp network meta set --key site_name --value "My Network"
praisonaiwp network option list
praisonaiwp network option get --key registration
```

---

## option

Manage WordPress options.

```bash
praisonaiwp option [COMMAND] [OPTIONS]
```

### Subcommands

- `get` - Get option value
- `add` - Add option
- `update` - Update option
- `delete` - Delete option
- `list` - List options
- `patch` - Patch option (JSON)

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--key TEXT` | string | Option name |
| `--value TEXT` | string | Option value |
| `--autoload TEXT` | string | Autoload: yes, no |
| `--format TEXT` | string | Format: json, yaml |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp option list
praisonaiwp option get --key blogname
praisonaiwp option update --key blogname --value "My Blog"
praisonaiwp option add --key custom_option --value "value"
praisonaiwp option delete --key old_option
```

---

## plugin

Manage WordPress plugins.

```bash
praisonaiwp plugin [COMMAND] [OPTIONS]
```

### Subcommands

- `list` - List plugins
- `install` - Install plugin
- `activate` - Activate plugin
- `deactivate` - Deactivate plugin
- `delete` - Delete plugin
- `update` - Update plugin
- `get` - Get plugin details
- `search` - Search plugins
- `status` - Check plugin status

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--plugin TEXT` | string | Plugin slug |
| `--version TEXT` | string | Plugin version |
| `--activate` | flag | Activate after install |
| `--force` | flag | Force operation |
| `--all` | flag | Apply to all plugins |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp plugin list
praisonaiwp plugin install --plugin woocommerce --activate
praisonaiwp plugin activate --plugin akismet
praisonaiwp plugin deactivate --plugin akismet
praisonaiwp plugin update --plugin woocommerce
praisonaiwp plugin delete --plugin old-plugin
praisonaiwp plugin search --query "seo"
```

---

## post-type

Manage custom post types.

```bash
praisonaiwp post-type [COMMAND] [OPTIONS]
```

### Subcommands

- `list` - List post types
- `get` - Get post type details

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--post-type TEXT` | string | Post type slug |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp post-type list
praisonaiwp post-type get --post-type product
```

---

## rewrite

Manage rewrite rules.

```bash
praisonaiwp rewrite [COMMAND] [OPTIONS]
```

### Subcommands

- `list` - List rewrite rules
- `flush` - Flush rewrite rules
- `structure` - Get/set permalink structure

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--structure TEXT` | string | Permalink structure |
| `--hard` | flag | Hard flush |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp rewrite list
praisonaiwp rewrite flush
praisonaiwp rewrite flush --hard
praisonaiwp rewrite structure --structure "/%postname%/"
```

---

## role

Manage user roles.

```bash
praisonaiwp role [COMMAND] [OPTIONS]
```

### Subcommands

- `list` - List roles
- `create` - Create role
- `delete` - Delete role
- `reset` - Reset role to defaults

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--role TEXT` | string | Role name |
| `--display-name TEXT` | string | Display name |
| `--clone TEXT` | string | Clone from role |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp role list
praisonaiwp role create --role custom_role --display-name "Custom Role" --clone editor
praisonaiwp role delete --role old_role
praisonaiwp role reset --role editor
```

---

## search-replace

Search and replace in database.

```bash
praisonaiwp search-replace OLD NEW [OPTIONS]
```

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--dry-run` | flag | Preview changes |
| `--network` | flag | Run on all sites |
| `--all-tables` | flag | Include all tables |
| `--skip-tables TEXT` | string | Tables to skip (comma-separated) |
| `--skip-columns TEXT` | string | Columns to skip (comma-separated) |
| `--include-columns TEXT` | string | Only these columns |
| `--precise` | flag | Force precise matching |
| `--regex` | flag | Use regex |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
# Dry run
praisonaiwp search-replace "oldsite.com" "newsite.com" --dry-run

# Replace in database
praisonaiwp search-replace "oldsite.com" "newsite.com"

# Skip tables
praisonaiwp search-replace "old" "new" --skip-tables "wp_users,wp_usermeta"

# Use regex
praisonaiwp search-replace "http://.*\.com" "https://newsite.com" --regex
```

---

## server

Manage remote servers.

```bash
praisonaiwp server [COMMAND] [OPTIONS]
```

### Subcommands

- `list` - List configured servers
- `add` - Add server
- `remove` - Remove server
- `test` - Test connection
- `start` - Start development server
- `stop` - Stop development server

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--name TEXT` | string | Server name |
| `--host TEXT` | string | Server hostname |
| `--user TEXT` | string | SSH username |
| `--port INTEGER` | int | SSH port |
| `--key TEXT` | string | SSH key path |
| `--wp-path TEXT` | string | WordPress path |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp server list
praisonaiwp server add --name prod --host example.com --user ubuntu --wp-path /var/www/html
praisonaiwp server test --server prod
praisonaiwp server remove --name old-server
```

---

## sidebar

Manage widget sidebars.

```bash
praisonaiwp sidebar [COMMAND] [OPTIONS]
```

### Subcommands

- `list` - List sidebars

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp sidebar list
```

---

## site

Manage multisite sites.

```bash
praisonaiwp site [COMMAND] [OPTIONS]
```

### Subcommands

- `list` - List sites
- `create` - Create site
- `delete` - Delete site
- `empty` - Empty site
- `activate` - Activate site
- `deactivate` - Deactivate site
- `archive` - Archive site
- `unarchive` - Unarchive site
- `spam` - Mark as spam
- `unspam` - Unmark spam
- `mature` - Mark as mature
- `unmature` - Unmark mature

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--url TEXT` | string | Site URL |
| `--title TEXT` | string | Site title |
| `--email TEXT` | string | Admin email |
| `--network-id INTEGER` | int | Network ID |
| `--site-id INTEGER` | int | Site ID |
| `--slug TEXT` | string | Site slug |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp site list
praisonaiwp site create --url blog.example.com --title "My Blog" --email admin@example.com
praisonaiwp site activate --site-id 2
praisonaiwp site delete --site-id 2
```

---

## super-admin

Manage network super admins.

```bash
praisonaiwp super-admin [COMMAND] [OPTIONS]
```

### Subcommands

- `list` - List super admins
- `add` - Add super admin
- `remove` - Remove super admin

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--username TEXT` | string | Username |
| `--email TEXT` | string | Email address |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp super-admin list
praisonaiwp super-admin add --username admin
praisonaiwp super-admin remove --username oldadmin
```

---

## tag

Manage post tags.

```bash
praisonaiwp tag [COMMAND] [OPTIONS]
```

### Subcommands

- `list` - List tags
- `create` - Create tag
- `update` - Update tag
- `delete` - Delete tag
- `get` - Get tag details

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--name TEXT` | string | Tag name |
| `--slug TEXT` | string | Tag slug |
| `--description TEXT` | string | Tag description |
| `--id INTEGER` | int | Tag ID |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp tag list
praisonaiwp tag create --name "Python" --slug python
praisonaiwp tag update --id 10 --name "Python Programming"
praisonaiwp tag delete --id 10
```

---

## taxonomy

Manage taxonomies.

```bash
praisonaiwp taxonomy [COMMAND] [OPTIONS]
```

### Subcommands

- `list` - List taxonomies
- `get` - Get taxonomy details

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--taxonomy TEXT` | string | Taxonomy slug |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp taxonomy list
praisonaiwp taxonomy get --taxonomy category
```

---

## term

Manage taxonomy terms.

```bash
praisonaiwp term [COMMAND] [OPTIONS]
```

### Subcommands

- `list` - List terms
- `create` - Create term
- `update` - Update term
- `delete` - Delete term
- `get` - Get term details

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--taxonomy TEXT` | string | Taxonomy slug |
| `--name TEXT` | string | Term name |
| `--slug TEXT` | string | Term slug |
| `--description TEXT` | string | Term description |
| `--parent INTEGER` | int | Parent term ID |
| `--id INTEGER` | int | Term ID |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp term list --taxonomy category
praisonaiwp term create --taxonomy category --name "Tech" --slug tech
praisonaiwp term update --taxonomy category --id 5 --name "Technology"
praisonaiwp term delete --taxonomy category --id 5
```

---

## theme

Manage WordPress themes.

```bash
praisonaiwp theme [COMMAND] [OPTIONS]
```

### Subcommands

- `list` - List themes
- `install` - Install theme
- `activate` - Activate theme
- `delete` - Delete theme
- `update` - Update theme
- `get` - Get theme details
- `search` - Search themes
- `status` - Check theme status
- `mod get` - Get theme mod
- `mod set` - Set theme mod
- `mod remove` - Remove theme mod

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--theme TEXT` | string | Theme slug |
| `--version TEXT` | string | Theme version |
| `--activate` | flag | Activate after install |
| `--force` | flag | Force operation |
| `--all` | flag | Apply to all themes |
| `--key TEXT` | string | Theme mod key |
| `--value TEXT` | string | Theme mod value |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp theme list
praisonaiwp theme install --theme twentytwentyfour --activate
praisonaiwp theme activate --theme twentytwentyfour
praisonaiwp theme update --theme mytheme
praisonaiwp theme delete --theme oldtheme
praisonaiwp theme mod get --key header_textcolor
praisonaiwp theme mod set --key header_textcolor --value "#000000"
```

---

## transient

Manage transients.

```bash
praisonaiwp transient [COMMAND] [OPTIONS]
```

### Subcommands

- `get` - Get transient
- `set` - Set transient
- `delete` - Delete transient
- `list` - List transients
- `delete-all` - Delete all transients
- `delete-expired` - Delete expired transients

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--key TEXT` | string | Transient key |
| `--value TEXT` | string | Transient value |
| `--expiration INTEGER` | int | Expiration (seconds) |
| `--network` | flag | Network transient |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp transient list
praisonaiwp transient get --key my_transient
praisonaiwp transient set --key my_transient --value "data" --expiration 3600
praisonaiwp transient delete --key my_transient
praisonaiwp transient delete-expired
```

---

## user

Manage WordPress users.

```bash
praisonaiwp user [COMMAND] [OPTIONS]
```

### Subcommands

- `list` - List users
- `create` - Create user
- `update` - Update user
- `delete` - Delete user
- `get` - Get user details
- `meta get` - Get user meta
- `meta update` - Update user meta
- `meta delete` - Delete user meta
- `meta list` - List user meta
- `session list` - List user sessions
- `session destroy` - Destroy user session

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--username TEXT` | string | Username |
| `--email TEXT` | string | Email address |
| `--password TEXT` | string | Password |
| `--role TEXT` | string | User role |
| `--first-name TEXT` | string | First name |
| `--last-name TEXT` | string | Last name |
| `--display-name TEXT` | string | Display name |
| `--user-id INTEGER` | int | User ID |
| `--key TEXT` | string | Meta key |
| `--value TEXT` | string | Meta value |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp user list
praisonaiwp user create --username john --email john@example.com --password pass123 --role editor
praisonaiwp user update --user-id 5 --role administrator
praisonaiwp user delete --user-id 5
praisonaiwp user get --user-id 1
praisonaiwp user meta list --user-id 1
praisonaiwp user meta update --user-id 1 --key nickname --value "John"
```

---

## widget

Manage widgets.

```bash
praisonaiwp widget [COMMAND] [OPTIONS]
```

### Subcommands

- `list` - List widgets
- `add` - Add widget
- `update` - Update widget
- `delete` - Delete widget
- `move` - Move widget
- `deactivate` - Deactivate widget
- `reset` - Reset widgets

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--widget TEXT` | string | Widget ID |
| `--sidebar TEXT` | string | Sidebar ID |
| `--position INTEGER` | int | Widget position |
| `--settings TEXT` | string | Widget settings (JSON) |
| `--server TEXT` | string | Server name |
| `--json` | flag | JSON output |

### Examples

```bash
praisonaiwp widget list
praisonaiwp widget add --widget text --sidebar sidebar-1 --settings '{"title":"Hello"}'
praisonaiwp widget move --widget text-1 --sidebar sidebar-2 --position 1
praisonaiwp widget delete --widget text-1
```
