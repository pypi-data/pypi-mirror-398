"""Pytest configuration and fixtures"""

import pytest
from pathlib import Path
from praisonaiwp.core.config import Config


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary config directory"""
    config_dir = tmp_path / ".praisonaiwp"
    config_dir.mkdir()
    (config_dir / "logs").mkdir()
    (config_dir / "backups").mkdir()
    return config_dir


@pytest.fixture
def sample_config(temp_config_dir):
    """Create sample configuration"""
    config = Config(str(temp_config_dir / "config.yaml"))
    config.initialize_default_config()
    config.add_server('test', {
        'hostname': 'test.example.com',
        'username': 'testuser',
        'key_file': '~/.ssh/id_test',
        'port': 22,
        'wp_path': '/var/www/html',
        'php_bin': 'php',
        'wp_cli': '/usr/local/bin/wp'
    })
    config.save()
    return config


@pytest.fixture
def sample_post_content():
    """Sample WordPress post content"""
    return """<!-- wp:heading -->
<h2>Welcome to Our Site</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>This is a sample website.</p>
<!-- /wp:paragraph -->

<!-- wp:heading -->
<h2>Welcome to Our Site</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Join us for worship.</p>
<!-- /wp:paragraph -->"""


@pytest.fixture
def sample_posts_json(tmp_path):
    """Create sample posts JSON file"""
    import json
    
    posts = [
        {
            "title": "Test Post 1",
            "content": "<p>Content 1</p>",
            "status": "publish"
        },
        {
            "title": "Test Post 2",
            "content": "<p>Content 2</p>",
            "status": "draft"
        }
    ]
    
    file_path = tmp_path / "posts.json"
    with open(file_path, 'w') as f:
        json.dump(posts, f)
    
    return file_path
