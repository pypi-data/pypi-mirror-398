"""Tests for enhanced configuration schema v2.0 with website URLs"""

import yaml

from praisonaiwp.core.config import Config


class TestConfigSchemaV2:
    """Test enhanced config schema with website, aliases, and description fields"""

    def test_config_with_website_field(self, tmp_path):
        """Test that config can store and retrieve website field"""
        config_file = tmp_path / "config.yaml"
        config_data = {
            'version': '2.0',
            'default_server': 'test',
            'servers': {
                'test': {
                    'website': 'https://example.com',
                    'hostname': 'test.com',
                    'username': 'user',
                    'port': 22,
                }
            }
        }

        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        config = Config(str(config_file))
        server = config.get_server('test')

        assert server['website'] == 'https://example.com'

    def test_config_with_aliases_field(self, tmp_path):
        """Test that config can store and retrieve aliases field"""
        config_file = tmp_path / "config.yaml"
        config_data = {
            'version': '2.0',
            'default_server': 'test',
            'servers': {
                'test': {
                    'website': 'https://example.com',
                    'aliases': [
                        'https://www.example.com',
                        'https://example.org'
                    ],
                    'hostname': 'test.com',
                    'username': 'user',
                }
            }
        }

        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        config = Config(str(config_file))
        server = config.get_server('test')

        assert 'aliases' in server
        assert len(server['aliases']) == 2
        assert 'https://www.example.com' in server['aliases']

    def test_config_with_description_field(self, tmp_path):
        """Test that config can store and retrieve description field"""
        config_file = tmp_path / "config.yaml"
        config_data = {
            'version': '2.0',
            'default_server': 'test',
            'servers': {
                'test': {
                    'website': 'https://example.com',
                    'description': 'Test website for development',
                    'hostname': 'test.com',
                    'username': 'user',
                }
            }
        }

        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        config = Config(str(config_file))
        server = config.get_server('test')

        assert server['description'] == 'Test website for development'

    def test_config_with_tags_field(self, tmp_path):
        """Test that config can store and retrieve tags field for AI matching"""
        config_file = tmp_path / "config.yaml"
        config_data = {
            'version': '2.0',
            'default_server': 'test',
            'servers': {
                'test': {
                    'website': 'https://biblerevelation.org',
                    'tags': ['bible', 'christian', 'teaching'],
                    'hostname': 'test.com',
                    'username': 'user',
                }
            }
        }

        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        config = Config(str(config_file))
        server = config.get_server('test')

        assert 'tags' in server
        assert 'bible' in server['tags']
        assert len(server['tags']) == 3

    def test_config_with_auto_route_setting(self, tmp_path):
        """Test that config can store auto_route setting"""
        config_file = tmp_path / "config.yaml"
        config_data = {
            'version': '2.0',
            'default_server': 'test',
            'servers': {'test': {}},
            'settings': {
                'auto_route': True,
                'auto_backup': True,
            }
        }

        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        config = Config(str(config_file))

        assert config.get_setting('auto_route') is True

    def test_backward_compatibility_with_v1_config(self, tmp_path):
        """Test that v1.0 config without website field still works"""
        config_file = tmp_path / "config.yaml"
        config_data = {
            'version': '1.0',
            'default_server': 'test',
            'servers': {
                'test': {
                    'hostname': 'test.com',
                    'username': 'user',
                    'port': 22,
                    'wp_path': '/var/www/vhosts/example.com/httpdocs',
                }
            }
        }

        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        config = Config(str(config_file))
        server = config.get_server('test')

        # Should work without website field
        assert server['hostname'] == 'test.com'
        assert 'wp_path' in server


class TestConfigMigration:
    """Test configuration migration from v1.0 to v2.0"""

    def test_extract_website_from_wp_path(self):
        """Test extracting domain from wp_path"""
        from praisonaiwp.core.config_migration import extract_website_from_wp_path

        wp_path = '/var/www/vhosts/example.com/httpdocs'
        website = extract_website_from_wp_path(wp_path)

        assert website == 'https://example.com'

    def test_extract_website_from_wp_path_with_wordpress_subdir(self):
        """Test extracting domain from wp_path with wordpress subdirectory"""
        from praisonaiwp.core.config_migration import extract_website_from_wp_path

        wp_path = '/var/www/vhosts/biblerevelation.org/httpdocs/wordpress'
        website = extract_website_from_wp_path(wp_path)

        assert website == 'https://biblerevelation.org'

    def test_migrate_config_v1_to_v2(self, tmp_path):
        """Test full migration from v1.0 to v2.0"""
        from praisonaiwp.core.config_migration import migrate_config_v1_to_v2

        config_data = {
            'version': '1.0',
            'default_server': 'default',
            'servers': {
                'default': {
                    'hostname': 'ionos',
                    'username': 'praison',
                    'wp_path': '/var/www/vhosts/praison.com/httpdocs',
                },
                'biblerevelation': {
                    'hostname': 'christsong.in',
                    'username': 'biblerevelation',
                    'wp_path': '/var/www/vhosts/biblerevelation.org/httpdocs/wordpress',
                }
            }
        }

        migrated = migrate_config_v1_to_v2(config_data)

        # Check version updated
        assert migrated['version'] == '2.0'

        # Check website fields added
        assert migrated['servers']['default']['website'] == 'https://praison.com'
        assert migrated['servers']['biblerevelation']['website'] == 'https://biblerevelation.org'

        # Check original fields preserved
        assert migrated['servers']['default']['hostname'] == 'ionos'
        assert migrated['servers']['biblerevelation']['username'] == 'biblerevelation'

    def test_migrate_config_preserves_existing_website(self, tmp_path):
        """Test that migration doesn't overwrite existing website field"""
        from praisonaiwp.core.config_migration import migrate_config_v1_to_v2

        config_data = {
            'version': '1.0',
            'servers': {
                'test': {
                    'website': 'https://custom.com',
                    'wp_path': '/var/www/vhosts/example.com/httpdocs',
                }
            }
        }

        migrated = migrate_config_v1_to_v2(config_data)

        # Should preserve existing website field
        assert migrated['servers']['test']['website'] == 'https://custom.com'

    def test_migrate_config_adds_auto_route_setting(self):
        """Test that migration adds auto_route setting"""
        from praisonaiwp.core.config_migration import migrate_config_v1_to_v2

        config_data = {
            'version': '1.0',
            'servers': {'test': {}},
            'settings': {
                'auto_backup': True,
            }
        }

        migrated = migrate_config_v1_to_v2(config_data)

        # Should add auto_route setting with default value
        assert 'auto_route' in migrated['settings']
        assert migrated['settings']['auto_route'] is False  # Default to False for safety
