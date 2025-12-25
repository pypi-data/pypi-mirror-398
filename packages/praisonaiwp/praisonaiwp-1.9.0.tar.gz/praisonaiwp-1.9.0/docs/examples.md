---
layout: default
title: Examples
---

# Code Examples

## Basic Operations

### Create Post

```bash
# Simple post
praisonaiwp create "Hello World" --content "<p>My first post</p>"

# With Gutenberg blocks
praisonaiwp create "My Post" --content "<!-- wp:paragraph --><p>Content</p><!-- /wp:paragraph -->"

# Multiple blocks
praisonaiwp create "Article" --content "
<!-- wp:heading -->
<h2>Introduction</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Article content here.</p>
<!-- /wp:paragraph -->

<!-- wp:code -->
<pre><code>print('hello')</code></pre>
<!-- /wp:code -->
"

# With metadata
praisonaiwp create "Post" \
  --content "<p>Text</p>" \
  --category "Tech,AI" \
  --tags "python,cli" \
  --author admin \
  --status publish \
  --date "2024-12-31 10:00:00"
```

### Update Post

```bash
# Update content
praisonaiwp update 123 --content "<p>Updated content</p>"

# Update multiple fields
praisonaiwp update 123 \
  --title "New Title" \
  --status publish \
  --category "News"

# Update metadata
praisonaiwp update 123 --meta '{"views":"1000","rating":"5"}'
```

### List Posts

```bash
# All posts
praisonaiwp list

# Filter by status
praisonaiwp list --status draft

# Filter by category
praisonaiwp list --category "Tech" --per-page 20

# Search
praisonaiwp list --search "wordpress" --orderby date --order desc

# Custom fields
praisonaiwp list --fields "id,title,date,status"
```

### Find Post

```bash
# By ID
praisonaiwp find 123

# By slug
praisonaiwp find "my-post-slug" --by slug

# Get specific fields
praisonaiwp find 123 --fields "id,title,content,meta"
```

### Delete Post

```bash
# Move to trash
praisonaiwp delete 123

# Permanent delete
praisonaiwp delete 123 --force
```

## Gutenberg Blocks

### Paragraph

```bash
praisonaiwp create "Post" --content "
<!-- wp:paragraph -->
<p>Simple paragraph text.</p>
<!-- /wp:paragraph -->
"
```

### Heading

```bash
praisonaiwp create "Post" --content "
<!-- wp:heading -->
<h2>Heading Level 2</h2>
<!-- /wp:heading -->

<!-- wp:heading {\"level\":3} -->
<h3>Heading Level 3</h3>
<!-- /wp:heading -->
"
```

### List

```bash
praisonaiwp create "Post" --content "
<!-- wp:list -->
<ul>
  <li>Item 1</li>
  <li>Item 2</li>
  <li>Item 3</li>
</ul>
<!-- /wp:list -->

<!-- wp:list {\"ordered\":true} -->
<ol>
  <li>First</li>
  <li>Second</li>
</ol>
<!-- /wp:list -->
"
```

### Code Block

```bash
praisonaiwp create "Post" --content "
<!-- wp:code -->
<pre class=\"wp-block-code\"><code>def hello():
    print('Hello World')</code></pre>
<!-- /wp:code -->
"
```

### Image

```bash
praisonaiwp create "Post" --content "
<!-- wp:image {\"id\":123} -->
<figure class=\"wp-block-image\">
  <img src=\"image.jpg\" alt=\"Description\"/>
</figure>
<!-- /wp:image -->
"
```

### Quote

```bash
praisonaiwp create "Post" --content "
<!-- wp:quote -->
<blockquote class=\"wp-block-quote\">
  <p>Quote text here.</p>
  <cite>Author Name</cite>
</blockquote>
<!-- /wp:quote -->
"
```

### Table

```bash
praisonaiwp create "Post" --content "
<!-- wp:table -->
<figure class=\"wp-block-table\">
  <table>
    <thead>
      <tr><th>Header 1</th><th>Header 2</th></tr>
    </thead>
    <tbody>
      <tr><td>Cell 1</td><td>Cell 2</td></tr>
      <tr><td>Cell 3</td><td>Cell 4</td></tr>
    </tbody>
  </table>
</figure>
<!-- /wp:table -->
"
```

### Columns

```bash
praisonaiwp create "Post" --content "
<!-- wp:columns -->
<div class=\"wp-block-columns\">
  <!-- wp:column -->
  <div class=\"wp-block-column\">
    <!-- wp:paragraph -->
    <p>Left column</p>
    <!-- /wp:paragraph -->
  </div>
  <!-- /wp:column -->
  
  <!-- wp:column -->
  <div class=\"wp-block-column\">
    <!-- wp:paragraph -->
    <p>Right column</p>
    <!-- /wp:paragraph -->
  </div>
  <!-- /wp:column -->
</div>
<!-- /wp:columns -->
"
```

## Media Management

### Upload Media

```bash
# Upload image
praisonaiwp media upload --file image.jpg

# Upload and attach to post
praisonaiwp media upload --file image.jpg --post-id 123

# With metadata
praisonaiwp media upload \
  --file image.jpg \
  --title "My Image" \
  --caption "Image caption" \
  --alt "Alt text"
```

### Import from URL

```bash
praisonaiwp media import --url "https://example.com/image.jpg"
praisonaiwp media import --url "https://example.com/image.jpg" --post-id 123
```

### List Media

```bash
praisonaiwp media list
praisonaiwp media list --per-page 50
```

### Get Media URL

```bash
praisonaiwp media url --media-id 456
```

## User Management

### Create User

```bash
praisonaiwp user create \
  --username john \
  --email john@example.com \
  --password SecurePass123 \
  --role editor \
  --first-name John \
  --last-name Doe
```

### List Users

```bash
praisonaiwp user list
praisonaiwp user list --role administrator
```

### Update User

```bash
praisonaiwp user update --user-id 5 --role administrator
praisonaiwp user update --user-id 5 --email newemail@example.com
```

### User Meta

```bash
praisonaiwp user meta list --user-id 1
praisonaiwp user meta update --user-id 1 --key nickname --value "Admin"
```

## Plugin Management

### List Plugins

```bash
praisonaiwp plugin list
praisonaiwp plugin list --status active
```

### Install Plugin

```bash
praisonaiwp plugin install --plugin woocommerce
praisonaiwp plugin install --plugin akismet --activate
praisonaiwp plugin install --plugin myplugin --version 2.0.0
```

### Activate/Deactivate

```bash
praisonaiwp plugin activate --plugin woocommerce
praisonaiwp plugin deactivate --plugin akismet
```

### Update Plugin

```bash
praisonaiwp plugin update --plugin woocommerce
praisonaiwp plugin update --all
```

## Theme Management

### List Themes

```bash
praisonaiwp theme list
```

### Install Theme

```bash
praisonaiwp theme install --theme twentytwentyfour
praisonaiwp theme install --theme mytheme --activate
```

### Activate Theme

```bash
praisonaiwp theme activate --theme twentytwentyfour
```

### Theme Mods

```bash
praisonaiwp theme mod get --key header_textcolor
praisonaiwp theme mod set --key header_textcolor --value "#000000"
```

## Database Operations

### Query Database

```bash
praisonaiwp db query --query "SELECT * FROM wp_posts WHERE post_status='publish' LIMIT 10"
```

### Export Database

```bash
praisonaiwp db export --file backup.sql
praisonaiwp db export --file backup.sql --tables "wp_posts,wp_postmeta"
```

### Import Database

```bash
praisonaiwp db import --file backup.sql
```

### Optimize Database

```bash
praisonaiwp db optimize
```

## Search and Replace

### Basic Replace

```bash
praisonaiwp search-replace "oldsite.com" "newsite.com"
```

### Dry Run

```bash
praisonaiwp search-replace "oldsite.com" "newsite.com" --dry-run
```

### Skip Tables

```bash
praisonaiwp search-replace "old" "new" --skip-tables "wp_users,wp_usermeta"
```

### Network-Wide

```bash
praisonaiwp search-replace "oldsite.com" "newsite.com" --network
```

## Cache Management

### Flush Cache

```bash
praisonaiwp cache flush
praisonaiwp cache flush --type object
praisonaiwp cache flush --type transient
```

### Cache Operations

```bash
# Add to cache
praisonaiwp cache add --key mykey --value myvalue --group mygroup --expire 3600

# Get from cache
praisonaiwp cache get --key mykey --group mygroup

# Delete from cache
praisonaiwp cache delete --key mykey --group mygroup
```

## Options Management

### Get Option

```bash
praisonaiwp option get --key blogname
praisonaiwp option get --key siteurl
```

### Update Option

```bash
praisonaiwp option update --key blogname --value "My Blog"
praisonaiwp option update --key posts_per_page --value 20
```

### List Options

```bash
praisonaiwp option list
praisonaiwp option list --search "theme"
```

## AI Operations

### Generate Content

```bash
praisonaiwp ai generate \
  --prompt "Write a blog post about WordPress security" \
  --length 1000 \
  --create-post \
  --category "Tech"
```

### Optimize Content

```bash
praisonaiwp ai-optimizer --post-id 123 --type seo --apply
praisonaiwp ai-optimizer --post-id 123 --type readability --apply
```

### Translate Content

```bash
praisonaiwp ai-translator --post-id 123 --target-lang es --create-post
praisonaiwp ai-translator --post-id 123 --target-lang "es,fr,de" --create-post
```

### Summarize Content

```bash
praisonaiwp ai-summarizer --post-id 123 --length short --update-excerpt
```

### Generate Images

```bash
praisonaiwp ai-image --prompt "Modern tech illustration" --size 1024x1024
praisonaiwp ai-image --prompt "Header image" --post-id 123 --set-featured
```

### Bulk AI Operations

```bash
# Optimize all posts in category
praisonaiwp ai-bulk \
  --operation optimize \
  --category "Tech" \
  --batch-size 5 \
  --delay 2

# Translate posts
praisonaiwp ai-bulk \
  --operation translate \
  --target-lang es \
  --post-ids "1,2,3,4,5"
```

## Multisite Operations

### List Sites

```bash
praisonaiwp site list
```

### Create Site

```bash
praisonaiwp site create \
  --url blog.example.com \
  --title "My Blog" \
  --email admin@example.com
```

### Network Options

```bash
praisonaiwp network option list
praisonaiwp network option get --key registration
praisonaiwp network option set --key registration --value all
```

### Super Admin

```bash
praisonaiwp super-admin list
praisonaiwp super-admin add --username admin
```

## Automation Scripts

### Daily Backup

```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
praisonaiwp db export --file "backup-$DATE.sql"
praisonaiwp backup --type files --destination "/backups/$DATE"
```

### Bulk Post Creation

```bash
#!/bin/bash
for title in "Post 1" "Post 2" "Post 3"; do
  praisonaiwp create "$title" \
    --content "<p>Content for $title</p>" \
    --category "Blog" \
    --status publish
  sleep 1
done
```

### Site Migration

```bash
#!/bin/bash
# Export from old site
praisonaiwp --server old db export --file migration.sql

# Search replace
praisonaiwp search-replace "oldsite.com" "newsite.com" --dry-run

# Import to new site
praisonaiwp --server new db import --file migration.sql

# Flush cache
praisonaiwp --server new cache flush
```

### Content Pipeline

```bash
#!/bin/bash
# Generate content
POST_ID=$(praisonaiwp ai generate \
  --prompt "Write about AI trends" \
  --create-post \
  --status draft \
  --json | jq -r '.post_id')

# Optimize
praisonaiwp ai-optimizer --post-id $POST_ID --type all --apply

# Generate image
praisonaiwp ai-image \
  --prompt "AI technology illustration" \
  --post-id $POST_ID \
  --set-featured

# Publish
praisonaiwp update $POST_ID --status publish
```

## JSON Output

### Parse with jq

```bash
# Get post ID
POST_ID=$(praisonaiwp --json create "Title" --content "<p>Text</p>" | jq -r '.post_id')

# Get all post titles
praisonaiwp --json list | jq -r '.posts[].title'

# Filter posts
praisonaiwp --json list --category "Tech" | jq '.posts[] | select(.status=="publish")'

# Count posts
praisonaiwp --json list | jq '.posts | length'
```

### Python Integration

```python
import subprocess
import json

# Create post
result = subprocess.run(
    ['praisonaiwp', '--json', 'create', 'My Post', '--content', '<p>Text</p>'],
    capture_output=True,
    text=True
)
data = json.loads(result.stdout)
post_id = data['post_id']

# List posts
result = subprocess.run(
    ['praisonaiwp', '--json', 'list', '--category', 'Tech'],
    capture_output=True,
    text=True
)
posts = json.loads(result.stdout)['posts']
for post in posts:
    print(f"{post['id']}: {post['title']}")
```

## Advanced Examples

### Conditional Updates

```bash
#!/bin/bash
# Update only if post is draft
STATUS=$(praisonaiwp --json find 123 | jq -r '.status')
if [ "$STATUS" = "draft" ]; then
  praisonaiwp update 123 --status publish
fi
```

### Batch Processing

```bash
#!/bin/bash
# Process posts in batches
praisonaiwp --json list --per-page 100 | jq -r '.posts[].id' | while read POST_ID; do
  praisonaiwp ai-optimizer --post-id $POST_ID --type seo --apply
  sleep 2
done
```

### Error Handling

```bash
#!/bin/bash
if praisonaiwp create "Post" --content "<p>Text</p>" 2>/dev/null; then
  echo "Success"
else
  echo "Failed to create post" >&2
  exit 1
fi
```

### Multi-Server Deployment

```bash
#!/bin/bash
SERVERS=("prod" "staging" "dev")
for SERVER in "${SERVERS[@]}"; do
  echo "Deploying to $SERVER..."
  praisonaiwp --server $SERVER plugin update --all
  praisonaiwp --server $SERVER cache flush
done
```

### Scheduled Tasks

```bash
# Crontab entry
# Daily backup at 2 AM
0 2 * * * /usr/local/bin/praisonaiwp db export --file /backups/daily-$(date +\%Y\%m\%d).sql

# Weekly optimization at 3 AM Sunday
0 3 * * 0 /usr/local/bin/praisonaiwp db optimize

# Hourly cache flush
0 * * * * /usr/local/bin/praisonaiwp cache flush
```

## Testing

### Dry Run Operations

```bash
# Test search-replace
praisonaiwp search-replace "old" "new" --dry-run

# Test bulk operations
praisonaiwp ai-bulk --operation optimize --category "Tech" --dry-run
```

### Connection Test

```bash
praisonaiwp server test
praisonaiwp server test --server production
```

### Validation

```bash
# Validate config
praisonaiwp config validate

# Validate blocks
praisonaiwp block validate --content "<!-- wp:paragraph --><p>Text</p><!-- /wp:paragraph -->"
```
