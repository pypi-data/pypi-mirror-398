# AI Agent Guide for PraisonAIWP CLI

This guide provides comprehensive instructions for AI agents to effectively use the PraisonAIWP CLI tool for WordPress management.

## Quick Start for AI Agents

### Basic Usage Pattern
```bash
# Enable AI-friendly JSON output
praisonaiwp --ai <command> [options]

# Or use per-command AI output
praisonaiwp <command> --ai [options]
```

### Response Format
All AI responses follow this structure:
```json
{
  "status": "success|error",
  "message": "Human-readable description",
  "data": {...},  // Response data
  "timestamp": "2024-01-01T00:00:00Z",
  "ai_friendly": true,
  "error_code": "ERROR_CODE",  // Only for errors
  "suggestions": [...]         // Only for errors
}
```

## Command Reference for AI Agents

### Content Management

#### Create Posts/Pages
```bash
# Create a post
praisonaiwp --ai create "Post Title" --content "<h2>Content</h2><p>Body</p>"

# Create a page
praisonaiwp --ai create "About Us" --content "<p>About content</p>" --type page

# Create with categories
praisonaiwp --ai create "News" --content "<p>News content</p>" --category "News,Blog"
```

#### List Content
```bash
# List posts
praisonaiwp --ai list

# List pages
praisonaiwp --ai list --type page --limit 10

# List drafts
praisonaiwp --ai list --status draft
```

#### Update Content
```bash
# Update post content
praisonaiwp --ai update 123 --post-content "<p>New content</p>"

# Update post metadata
praisonaiwp --ai update 123 --title "New Title" --status "publish"
```

### Configuration Management

#### Get Configuration
```bash
# Get specific config value
praisonaiwp --ai config get DB_NAME

# List all configuration
praisonaiwp --ai config list

# Get config file path
praisonaiwp --ai config path
```

#### Set Configuration
```bash
# Set config value
praisonaiwp --ai config set DB_PASSWORD "new_password"
```

### User Role Management

#### List Roles
```bash
# List all roles
praisonaiwp --ai role list
```

#### Get Role Information
```bash
# Get specific role
praisonaiwp --ai role get editor
```

#### Create Role
```bash
# Create basic role
praisonaiwp --ai role create custom_role "Custom Role"

# Create role with capabilities
praisonaiwp --ai role create moderator "Moderator" --capabilities "edit_posts,moderate_comments"
```

#### Delete Role
```bash
# Delete role
praisonaiwp --ai role delete custom_role
```

### Code Generation (Scaffold)

#### Generate Post Type
```bash
# Create basic post type
praisonaiwp --ai scaffold post-type book

# Create with options
praisonaiwp --ai scaffold post-type book --label "Books" --public true --supports "title,editor,thumbnail"
```

#### Generate Taxonomy
```bash
# Create basic taxonomy
praisonaiwp --ai scaffold taxonomy genre

# Create with options
praisonaiwp --ai scaffold taxonomy genre --label "Genres" --hierarchical true --post_types "book"
```

#### Generate Plugin
```bash
# Create plugin
praisonaiwp --ai scaffold plugin my-plugin --plugin_name "My Plugin" --author "Author Name"
```

#### Generate Theme
```bash
# Create theme
praisonaiwp --ai scaffold theme my-theme --theme_name "My Theme" --author "Author Name"
```

### Core Management

#### Check WordPress Version
```bash
# Get current version
praisonaiwp --ai core version

# Check for updates
praisonaiwp --ai core check-update
```

#### Update WordPress
```bash
# Update to latest
praisonaiwp --ai core update

# Update to specific version
praisonaiwp --ai core update --version 6.4.0
```

### Cron Management

#### List Scheduled Events
```bash
# List all cron events
praisonaiwp --ai cron list
```

#### Run Cron Event
```bash
# Run specific event
praisonaiwp --ai cron run my_hook
```

#### Schedule Event
```bash
# Schedule recurring event
praisonaiwp --ai cron event schedule my_hook --hook_code "my_function()" --recurrence "hourly"
```

## Error Handling for AI Agents

### Common Error Codes

| Error Code | Description | Suggested Actions |
|------------|-------------|------------------|
| `CONNECTION_ERROR` | SSH/WP-CLI connection failed | Check server config, credentials, network |
| `PERMISSION_ERROR` | Insufficient permissions | Check user roles, file permissions |
| `VALIDATION_ERROR` | Invalid parameters | Check parameter formats, required fields |
| `NOT_FOUND` | Item doesn't exist | Verify item exists, check spelling |
| `WPCLI_ERROR` | WP-CLI command failed | Check WP-CLI installation, WordPress status |

### Error Response Example
```json
{
  "status": "error",
  "error": "Server 'production' not found in configuration",
  "error_code": "NOT_FOUND",
  "command": "role list",
  "timestamp": "2024-01-01T00:00:00Z",
  "ai_friendly": true,
  "suggestions": [
    "Check server configuration file",
    "Use --server flag with correct server name",
    "Run 'praisonaiwp init' to set up configuration"
  ]
}
```

## Best Practices for AI Agents

### 1. Always Use AI Mode
```bash
# Good - AI-friendly output
praisonaiwp --ai create "Title" --content "<p>Content</p>"

# Avoid - Human-readable output
praisonaiwp create "Title" --content "<p>Content</p>"
```

### 2. Check Response Status
Always check the `status` field before processing data:
```python
response = json.loads(command_output)
if response["status"] == "success":
    # Process response["data"]
else:
    # Handle error using response["error_code"] and response["suggestions"]
```

### 3. Handle Server Configuration
Always verify server configuration exists:
```bash
# Check available servers first
praisonaiwp --ai config list

# Use specific server
praisonaiwp --ai --server staging create "Title" --content "<p>Content</p>"
```

### 4. Validate Parameters
Use appropriate parameter formats:
- Dates: `YYYY-MM-DD HH:MM:SS`
- Categories: Comma-separated names
- Meta: JSON format `{"key":"value"}`
- Content: HTML or Gutenberg blocks

### 5. Batch Operations
For multiple operations, use AI mode consistently:
```bash
# Create multiple posts
for title in titles:
    praisonaiwp --ai create "$title" --content "<p>Content for $title</p>"
```

## Content Format Guidelines

### HTML Content
```bash
praisonaiwp --ai create "Title" --content "
<h2>Subtitle</h2>
<p>Paragraph content with <strong>bold</strong> text.</p>
<ul>
<li>List item 1</li>
<li>List item 2</li>
</ul>
"
```

### Gutenberg Blocks (Advanced)
```bash
praisonaiwp --ai create "Title" --no-block-conversion --content "
<!-- wp:paragraph -->
<p>Paragraph block</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Heading block</h2>
<!-- /wp:heading -->
"
```

### Meta Data
```bash
praisonaiwp --ai create "Title" --content "<p>Content</p>" --meta '{"featured":true,"priority":"high"}'
```

## Integration Examples

### Python Integration
```python
import subprocess
import json

def create_post(title, content):
    cmd = ['python', '-m', 'praisonaiwp', '--ai', 'create', title, '--content', content]
    result = subprocess.run(cmd, capture_output=True, text=True)
    response = json.loads(result.stdout)
    
    if response['status'] == 'success':
        return response['data']['id']
    else:
        raise Exception(f"Error: {response['error']}")

# Usage
post_id = create_post("My Post", "<p>Post content</p>")
```

### Node.js Integration
```javascript
const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

async function createPost(title, content) {
  const { stdout } = await execPromise(`python -m praisonaiwp --ai create "${title}" --content "${content}"`);
  const response = JSON.parse(stdout);
  
  if (response.status === 'success') {
    return response.data.id;
  } else {
    throw new Error(`Error: ${response.error}`);
  }
}

// Usage
const postId = await createPost('My Post', '<p>Post content</p>');
```

## Troubleshooting

### Common Issues

1. **Server Not Found**
   - Check configuration file exists
   - Verify server name spelling
   - Run `praisonaiwp init` if needed

2. **Permission Denied**
   - Check SSH key permissions
   - Verify WordPress user capabilities
   - Check file system permissions

3. **WP-CLI Not Found**
   - Install WP-CLI on remote server
   - Check WP-CLI path in configuration
   - Verify PHP installation

4. **Invalid Parameters**
   - Check parameter formats
   - Verify required parameters
   - Use AI mode to see validation errors

### Debug Mode
For debugging, use verbose output:
```bash
praisonaiwp --ai --verbose role list
```

## Complete Command List

| Command | Purpose | AI Example |
|---------|---------|-----------|
| `create` | Create posts/pages | `praisonaiwp --ai create "Title" --content "<p>Content</p>"` |
| `list` | List content | `praisonaiwp --ai list --type post` |
| `update` | Update content | `praisonaiwp --ai update 123 --post-content "<p>New</p>"` |
| `config` | Manage configuration | `praisonaiwp --ai config get DB_NAME` |
| `role` | Manage user roles | `praisonaiwp --ai role list` |
| `scaffold` | Generate code | `praisonaiwp --ai scaffold post-type book` |
| `core` | WordPress core | `praisonaiwp --ai core version` |
| `cron` | Scheduled tasks | `praisonaiwp --ai cron list` |
| `taxonomy` | Manage taxonomies | `praisonaiwp --ai taxonomy list` |
| `term` | Manage terms | `praisonaiwp --ai term list category` |
| `widget` | Manage widgets | `praisonaiwp --ai widget list` |

This guide provides AI agents with all necessary information to effectively use PraisonAIWP CLI for WordPress management tasks.
