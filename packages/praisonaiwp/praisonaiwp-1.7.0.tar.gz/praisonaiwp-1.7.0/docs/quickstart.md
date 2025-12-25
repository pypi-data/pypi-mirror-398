---
layout: default
title: Quick Start Guide
description: Get started with PraisonAIWP in minutes
---

# Quick Start Guide

Get up and running with PraisonAIWP in just a few minutes. This guide will walk you through the essential commands to manage WordPress sites efficiently.

## 🚀 5-Minute Setup

### 1. Install PraisonAIWP

```bash
pip install praisonaiwp
```

### 2. Initialize Configuration

```bash
praisonaiwp init
```

### 3. Add Your WordPress Server

```bash
praisonaiwp config add-server mysite user@example.com /var/www/html
```

### 4. Test Connection

```bash
praisonaiwp core version --server mysite
```

## 🎯 Essential Commands

### WordPress Information

```bash
# Check WordPress version
praisonaiwp core version --server mysite

# Get site information
praisonaiwp core info --server mysite

# Check for updates
praisonaiwp core check-update --server mysite
```

### Plugin Management

```bash
# List all plugins
praisonaiwp plugin list --server mysite

# Install a plugin
praisonaiwp plugin install akismet --server mysite

# Activate a plugin
praisonaiwp plugin activate akismet --server mysite

# Update all plugins
praisonaiwp plugin update --server mysite
```

### Theme Management

```bash
# List themes
praisonaiwp theme list --server mysite

# Install a theme
praisonaiwp theme install twentytwentythree --server mysite

# Activate a theme
praisonaiwp theme activate twentytwentythree --server mysite
```

### User Management

```bash
# List users
praisonaiwp user list --server mysite

# Create a new user
praisonaiwp user create john john@example.com --role editor --server mysite

# Update user role
praisonaiwp user update john --role administrator --server mysite
```

### Post Management

```bash
# List posts
praisonaiwp post list --server mysite

# Create a post
praisonaiwp post create "My New Post" --content "Post content here" --server mysite

# Update a post
praisonaiwp post update 123 --title "Updated Title" --server mysite
```

## 🤖 AI-Powered Content Generation

### Set Up AI Features

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="your-api-key-here"

# Or add to config
praisonaiwp config set openai_api_key "your-api-key-here"
```

### Generate AI Content

```bash
# Generate content (dry run)
praisonaiwp ai generate-content --topic "WordPress Security" --dry-run

# Create and publish AI post
praisonaiwp ai create-post --title "10 WordPress Security Tips" --auto-publish --server mysite

# Generate multiple posts
praisonaiwp ai batch-create --topics "SEO Tips,Performance Optimization,Content Marketing" --server mysite
```

## 🗂️ File & Media Management

### Upload Media

```bash
# Upload an image
praisonaiwp media upload /path/to/image.jpg --title "My Image" --server mysite

# List media files
praisonaiwp media list --server mysite
```

### Database Operations

```bash
# Create database backup
praisonaiwp backup create --server mysite

# Export database
praisonaiwp backup export /path/to/backup.sql --server mysite

# Import database
praisonaiwp backup import /path/to/backup.sql --server mysite
```

## 🔧 Advanced Usage

### Multiple Server Management

```bash
# Add multiple servers
praisonaiwp config add-server staging user@staging.example.com /var/www/staging
praisonaiwp config add-server production user@prod.example.com /var/www/html

# Set default server
praisonaiwp config set default_server production

# Commands now use default server automatically
praisonaiwp plugin list

# Specify server when needed
praisonaiwp user list --server staging
```

### Batch Operations

```bash
# Update all plugins on all servers
praisonaiwp plugin update all --server production

# Update all themes
praisonaiwp theme update --server production

# Clear all caches
praisonaiwp cache flush --server production
```

### Comment Management

```bash
# List pending comments
praisonaiwp comment list --status pending --server mysite

# Approve a comment
praisonaiwp comment approve 123 --server mysite

# Mark as spam
praisonaiwp comment spam 124 --server mysite
```

## 📊 Monitoring & Maintenance

### System Status

```bash
# Check system status
praisonaiwp system status --server mysite

# Check disk usage
praisonaiwp system disk-usage --server mysite

# Check PHP info
praisonaiwp system php-info --server mysite
```

### Database Maintenance

```bash
# Optimize database
praisonaiwp db optimize --server mysite

# Repair database
praisonaiwp db repair --server mysite

# Clean up database
praisonaiwp db clean --server mysite
```

## 🔍 Search & Find

```bash
# Search posts
praisonaiwp post search "WordPress" --server mysite

# Find posts by author
praisonaiwp post list --author_id 1 --server mysite

# Search in content
praisonaiwp post search "security" --content --server mysite
```

## 🎛️ Configuration Management

```bash
# List all configuration
praisonaiwp config list

# Get specific setting
praisonaiwp config get default_server

# Set configuration
praisonaiwp config set log_level DEBUG

# Remove server
praisonaiwp config remove-server staging
```

## 📝 Tips & Best Practices

### 1. Use Server Aliases

```bash
# Add descriptive server names
praisonaiwp config add-server prod-main user@prod1.example.com /var/www/html
praisonaiwp config add-server prod-backup user@prod2.example.com /var/www/html
```

### 2. Backup Before Major Changes

```bash
# Always backup before updates
praisonaiwp backup create --filename pre-update-backup.sql --server mysite
praisonaiwp plugin update all --server mysite
```

### 3. Use JSON Output for Scripting

```bash
# Get JSON output for automation
praisonaiwp plugin list --json --server mysite > plugins.json

# Use in scripts
praisonaiwp user list --json --server mysite | jq '.[] | select(.roles == "administrator")'
```

### 4. Test on Staging First

```bash
# Test plugin installation on staging
praisonaiwp plugin install new-plugin --server staging
# Verify everything works
# Then install on production
praisonaiwp plugin install new-plugin --server production
```

## 🆘 Getting Help

### Built-in Help

```bash
# Get general help
praisonaiwp --help

# Get command-specific help
praisonaiwp plugin --help
praisonaiwp post create --help

# Get AI command help
praisonaiwp ai --help
```

### Common Issues

```bash
# Test connection if commands fail
praisonaiwp config test-server mysite

# Check WP-CLI on server
ssh user@example.com "wp --info"

# Check permissions
praisonaiwp system status --server mysite
```

## 🎯 Next Steps

Now that you're familiar with the basics:

1. **Explore AI Features**: Learn about [advanced AI content generation]({{ '/commands/ai/' | relative_url }})
2. **Set Up Automation**: Read about [scripting and automation]({{ '/advanced/scripting/' | relative_url }})
3. **Multisite Management**: Configure [WordPress multisite]({{ '/advanced/multisite/' | relative_url }})
4. **API Reference**: Check the [complete API documentation]({{ '/api/' | relative_url }})

## 📚 Additional Resources

- [Full Command Reference]({{ '/commands/' | relative_url }})
- [Configuration Guide]({{ '/configuration/' | relative_url }})
- [Troubleshooting Guide]({{ '/troubleshooting/' | relative_url }})
- [GitHub Repository](https://github.com/mervinpraison/praisonaiwp)

---

**Ready to take your WordPress management to the next level? Explore our advanced features and automation capabilities!**
