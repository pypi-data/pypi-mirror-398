---
layout: default
title: Installation Guide
description: Complete installation instructions for PraisonAIWP
---

# Installation Guide

Follow these steps to install and set up PraisonAIWP on your system.

## System Requirements

- **Python 3.8+** - Required for the CLI tool
- **WP-CLI** - Must be installed on target WordPress servers
- **SSH access** - For remote WordPress management
- **OpenAI API key** - For AI content generation features

## Installation Methods

### Method 1: Install via pip (Recommended)

```bash
# Install the latest version
pip install praisonaiwp

# Or install a specific version
pip install praisonaiwp==1.5.0
```

### Method 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/mervinpraison/praisonaiwp.git
cd praisonaiwp

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

### Method 3: Install with pipx (Isolated Environment)

```bash
# Install pipx if not already installed
pip install --user pipx
pipx ensurepath

# Install praisonaiwp with pipx
pipx install praisonaiwp
```

## Post-Installation Setup

### 1. Verify Installation

```bash
# Check if praisonaiwp is installed
praisonaiwp --version

# Should output: PraisonAIWP v1.5.0
```

### 2. Initialize Configuration

```bash
# Create initial configuration file
praisonaiwp init

# This creates ~/.praisonaiwp/config.yaml
```

### 3. Configure WordPress Server

```bash
# Add your first WordPress server
praisonaiwp config add-server production user@example.com /var/www/html

# Test the connection
praisonaiwp config test-server production
```

### 4. Set Up AI Features (Optional)

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="your-api-key-here"

# Or add to configuration
praisonaiwp config set openai_api_key "your-api-key-here"
```

## Server Requirements

### Target WordPress Server Setup

Ensure your WordPress servers have the following:

#### 1. WP-CLI Installation

```bash
# Download WP-CLI
curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar

# Make it executable
chmod +x wp-cli.phar

# Move to global location
sudo mv wp-cli.phar /usr/local/bin/wp
```

#### 2. PHP Requirements

- PHP 7.4+ (recommended 8.0+)
- Required PHP extensions for WordPress
- Sufficient memory limits (256MB+)

#### 3. Database Access

- MySQL/MariaDB access
- Appropriate user permissions
- Backup capabilities

#### 4. File System Permissions

```bash
# WordPress directory should be writable
sudo chown -R www-data:www-data /var/www/html
sudo chmod -R 755 /var/www/html
```

### SSH Configuration

#### 1. SSH Key Setup

```bash
# Generate SSH key if you don't have one
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"

# Copy public key to server
ssh-copy-id user@your-server.com
```

#### 2. Test SSH Connection

```bash
# Test SSH connection
ssh user@your-server.com "wp --info"

# Should return WP-CLI information
```

## Configuration File

The configuration file is located at `~/.praisonaiwp/config.yaml`:

```yaml
servers:
  production:
    hostname: example.com
    username: wpuser
    key_file: ~/.ssh/id_rsa
    port: 22
    wp_path: /var/www/html
    php_bin: php
    wp_cli: /usr/local/bin/wp

settings:
  default_server: production
  openai_api_key: your-api-key-here
  log_level: INFO
```

## Verification

### Test Basic Commands

```bash
# Test WP-CLI connection
praisonaiwp core version --server production

# Test plugin listing
praisonaiwp plugin list --server production

# Test user listing
praisonaiwp user list --server production
```

### Test AI Features

```bash
# Test AI content generation
praisonaiwp ai generate-content --topic "WordPress Security" --dry-run

# Test auto-publishing
praisonaiwp ai create-post --title "Test Post" --dry-run
```

## Troubleshooting

### Common Issues

#### 1. Command Not Found

```bash
# If praisonaiwp command is not found
# Check Python installation
python -m praisonaiwp --version

# Or add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

#### 2. SSH Connection Failed

```bash
# Test SSH connection manually
ssh user@server.com "wp --info"

# Check SSH key permissions
chmod 600 ~/.ssh/id_rsa
```

#### 3. WP-CLI Not Found

```bash
# Check WP-CLI installation on server
ssh user@server.com "which wp"

# Install WP-CLI if missing
ssh user@server.com "curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar && chmod +x wp-cli.phar && sudo mv wp-cli.phar /usr/local/bin/wp"
```

#### 4. Permission Denied

```bash
# Check file permissions
ssh user@server.com "ls -la /var/www/html"

# Fix WordPress permissions
ssh user@server.com "sudo chown -R www-data:www-data /var/www/html && sudo chmod -R 755 /var/www/html"
```

### Getting Help

- **Documentation**: [Full documentation]({{ '/' | relative_url }})
- **Issues**: [GitHub Issues](https://github.com/mervinpraison/praisonaiwp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/mervinpraison/praisonaiwp/discussions)

## Next Steps

After successful installation:

1. Read the [Quick Start Guide]({{ '/quickstart/' | relative_url }})
2. Explore the [Command Reference]({{ '/commands/' | relative_url }})
3. Set up [AI Features]({{ '/commands/ai/' | relative_url }})
4. Configure [Multiple Servers]({{ '/advanced/multisite/' | relative_url }})
