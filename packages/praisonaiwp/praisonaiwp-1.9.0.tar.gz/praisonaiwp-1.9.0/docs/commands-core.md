---
layout: default
title: Core Commands
---

# Core Commands Reference

## create

Create WordPress posts/pages with Gutenberg blocks.

```bash
praisonaiwp create "Title" [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--content TEXT` | string | - | Post content (Gutenberg blocks or HTML) |
| `--status TEXT` | string | publish | Post status: publish, draft, private |
| `--type TEXT` | string | post | Content type: post, page |
| `--category TEXT` | string | - | Category names (comma-separated) |
| `--category-id TEXT` | string | - | Category IDs (comma-separated) |
| `--author TEXT` | string | - | Author username or ID |
| `--excerpt TEXT` | string | - | Post excerpt |
| `--date TEXT` | string | - | Publish date (YYYY-MM-DD HH:MM:SS) |
| `--tags TEXT` | string | - | Tag names/IDs (comma-separated) |
| `--meta TEXT` | string | - | Custom fields (JSON format) |
| `--comment-status TEXT` | string | open | Comment status: open, closed |
| `--featured-image TEXT` | string | - | Featured image URL or path |
| `--no-block-conversion` | flag | false | Send raw Gutenberg blocks |
| `--server TEXT` | string | - | Server name from config |
| `--json` | flag | false | Output JSON format |

### Examples

```bash
# Basic post
praisonaiwp create "My Post" --content "<!-- wp:paragraph --><p>Hello</p><!-- /wp:paragraph -->"

# With categories and tags
praisonaiwp create "My Post" --content "<p>Content</p>" --category "Tech,AI" --tags "python,cli"

# Draft with date
praisonaiwp create "Draft Post" --content "<p>Draft</p>" --status draft --date "2024-12-31 10:00:00"

# With metadata
praisonaiwp create "Post" --content "<p>Text</p>" --meta '{"custom_field":"value"}'

# JSON output
praisonaiwp --json create "Post" --content "<p>Text</p>"
```

---

## update

Update existing WordPress posts/pages.

```bash
praisonaiwp update POST_ID [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--content TEXT` | string | - | New content (Gutenberg blocks or HTML) |
| `--title TEXT` | string | - | New title |
| `--status TEXT` | string | - | New status: publish, draft, private |
| `--category TEXT` | string | - | Category names (comma-separated) |
| `--category-id TEXT` | string | - | Category IDs (comma-separated) |
| `--author TEXT` | string | - | Author username or ID |
| `--excerpt TEXT` | string | - | Post excerpt |
| `--date TEXT` | string | - | Publish date (YYYY-MM-DD HH:MM:SS) |
| `--tags TEXT` | string | - | Tag names/IDs (comma-separated) |
| `--meta TEXT` | string | - | Custom fields (JSON format) |
| `--comment-status TEXT` | string | - | Comment status: open, closed |
| `--featured-image TEXT` | string | - | Featured image URL or path |
| `--no-block-conversion` | flag | false | Send raw Gutenberg blocks |
| `--server TEXT` | string | - | Server name from config |
| `--json` | flag | false | Output JSON format |

### Examples

```bash
# Update content
praisonaiwp update 123 --content "<!-- wp:paragraph --><p>Updated</p><!-- /wp:paragraph -->"

# Update title and status
praisonaiwp update 123 --title "New Title" --status publish

# Update categories
praisonaiwp update 123 --category "Tech,News"

# Update metadata
praisonaiwp update 123 --meta '{"views":"1000"}'
```

---

## list

List WordPress posts/pages.

```bash
praisonaiwp list [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--type TEXT` | string | post | Post type: post, page, any |
| `--status TEXT` | string | publish | Status: publish, draft, private, any |
| `--author TEXT` | string | - | Filter by author |
| `--category TEXT` | string | - | Filter by category |
| `--tag TEXT` | string | - | Filter by tag |
| `--search TEXT` | string | - | Search term |
| `--orderby TEXT` | string | date | Order by: date, title, modified, id |
| `--order TEXT` | string | desc | Order: asc, desc |
| `--per-page INTEGER` | int | 10 | Posts per page |
| `--page INTEGER` | int | 1 | Page number |
| `--fields TEXT` | string | - | Fields to return (comma-separated) |
| `--server TEXT` | string | - | Server name from config |
| `--json` | flag | false | Output JSON format |

### Examples

```bash
# List all posts
praisonaiwp list

# List drafts
praisonaiwp list --status draft

# List pages
praisonaiwp list --type page

# Search posts
praisonaiwp list --search "wordpress"

# List with pagination
praisonaiwp list --per-page 20 --page 2

# Filter by category
praisonaiwp list --category "Tech"

# Custom fields
praisonaiwp list --fields "id,title,date"
```

---

## find

Find WordPress posts by ID or slug.

```bash
praisonaiwp find IDENTIFIER [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--by TEXT` | string | id | Search by: id, slug |
| `--type TEXT` | string | post | Post type: post, page |
| `--fields TEXT` | string | - | Fields to return (comma-separated) |
| `--server TEXT` | string | - | Server name from config |
| `--json` | flag | false | Output JSON format |

### Examples

```bash
# Find by ID
praisonaiwp find 123

# Find by slug
praisonaiwp find "my-post-slug" --by slug

# Find page
praisonaiwp find 456 --type page

# Custom fields
praisonaiwp find 123 --fields "id,title,content,date"
```

---

## delete

Delete WordPress posts/pages.

```bash
praisonaiwp delete POST_ID [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--force` | flag | false | Permanently delete (skip trash) |
| `--server TEXT` | string | - | Server name from config |
| `--json` | flag | false | Output JSON format |

### Examples

```bash
# Move to trash
praisonaiwp delete 123

# Permanently delete
praisonaiwp delete 123 --force
```
