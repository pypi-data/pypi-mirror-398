"""Tests for ServerRouter - automatic server routing based on website URLs"""

import yaml
from praisonaiwp.core.router import ServerRouter


class TestServerRouter:
    """Test ServerRouter class for auto-routing to correct server"""

    def test_find_server_by_website_exact_match(self, tmp_path):
        """Test finding server by exact website URL"""
        config = {
            'servers': {
                'biblerevelation': {
                    'website': 'https://biblerevelation.org',
                    'hostname': 'christsong.in',
                },
                'default': {
                    'website': 'https://mer.vin',
                    'hostname': 'ionos',
                }
            }
        }

        router = ServerRouter(config)
        server_name, server_config = router.find_server_by_website('https://biblerevelation.org')

        assert server_name == 'biblerevelation'
        assert server_config['hostname'] == 'christsong.in'

    def test_find_server_by_website_without_protocol(self, tmp_path):
        """Test finding server by domain without https://"""
        config = {
            'servers': {
                'biblerevelation': {
                    'website': 'https://biblerevelation.org',
                    'hostname': 'christsong.in',
                }
            }
        }

        router = ServerRouter(config)
        server_name, _ = router.find_server_by_website('biblerevelation.org')

        assert server_name == 'biblerevelation'

    def test_find_server_by_website_with_www(self, tmp_path):
        """Test finding server handles www. prefix correctly"""
        config = {
            'servers': {
                'test': {
                    'website': 'https://example.com',
                    'hostname': 'test.com',
                }
            }
        }

        router = ServerRouter(config)

        # Should match with or without www.
        server_name1, _ = router.find_server_by_website('https://www.example.com')
        server_name2, _ = router.find_server_by_website('https://example.com')

        assert server_name1 == 'test'
        assert server_name2 == 'test'

    def test_find_server_by_website_using_aliases(self, tmp_path):
        """Test finding server by alias domain"""
        config = {
            'servers': {
                'default': {
                    'website': 'https://mer.vin',
                    'aliases': [
                        'https://praison.com',
                        'https://www.praison.com'
                    ],
                    'hostname': 'ionos',
                }
            }
        }

        router = ServerRouter(config)

        # Should find by primary website
        server_name1, _ = router.find_server_by_website('mer.vin')
        assert server_name1 == 'default'

        # Should find by alias
        server_name2, _ = router.find_server_by_website('praison.com')
        assert server_name2 == 'default'

        server_name3, _ = router.find_server_by_website('www.praison.com')
        assert server_name3 == 'default'

    def test_find_server_by_website_not_found(self, tmp_path):
        """Test that None is returned when server not found"""
        config = {
            'servers': {
                'test': {
                    'website': 'https://example.com',
                }
            }
        }

        router = ServerRouter(config)
        server_name, server_config = router.find_server_by_website('https://notfound.com')

        assert server_name is None
        assert server_config is None

    def test_find_server_by_keywords_in_title(self, tmp_path):
        """Test finding server by domain mentioned in text"""
        config = {
            'servers': {
                'biblerevelation': {
                    'website': 'https://biblerevelation.org',
                    'hostname': 'christsong.in',
                }
            }
        }

        router = ServerRouter(config)
        text = "Post for biblerevelation.org about Immanuel"
        server_name, _ = router.find_server_by_keywords(text)

        assert server_name == 'biblerevelation'

    def test_find_server_by_keywords_in_content(self, tmp_path):
        """Test finding server by domain in content"""
        config = {
            'servers': {
                'default': {
                    'website': 'https://mer.vin',
                    'aliases': ['https://praison.com'],
                }
            }
        }

        router = ServerRouter(config)
        text = "Check out my blog at praison.com for more updates"
        server_name, _ = router.find_server_by_keywords(text)

        assert server_name == 'default'

    def test_find_server_by_keywords_case_insensitive(self, tmp_path):
        """Test keyword matching is case-insensitive"""
        config = {
            'servers': {
                'test': {
                    'website': 'https://Example.COM',
                }
            }
        }

        router = ServerRouter(config)
        text = "Visit EXAMPLE.com for details"
        server_name, _ = router.find_server_by_keywords(text)

        assert server_name == 'test'

    def test_find_server_by_keywords_not_found(self, tmp_path):
        """Test that None is returned when no domain found in text"""
        config = {
            'servers': {
                'test': {
                    'website': 'https://example.com',
                }
            }
        }

        router = ServerRouter(config)
        text = "This is a post with no domain mentioned"
        server_name, server_config = router.find_server_by_keywords(text)

        assert server_name is None
        assert server_config is None

    def test_get_server_info_single_server(self, tmp_path):
        """Test getting info for a single server"""
        config = {
            'servers': {
                'biblerevelation': {
                    'website': 'https://biblerevelation.org',
                    'description': 'Bible revelation website',
                    'hostname': 'christsong.in',
                }
            }
        }

        router = ServerRouter(config)
        info = router.get_server_info('biblerevelation')

        assert info['name'] == 'biblerevelation'
        assert info['website'] == 'https://biblerevelation.org'
        assert info['description'] == 'Bible revelation website'
        assert info['hostname'] == 'christsong.in'

    def test_get_server_info_all_servers(self, tmp_path):
        """Test getting info for all servers"""
        config = {
            'servers': {
                'default': {
                    'website': 'https://mer.vin',
                    'description': 'Main blog',
                },
                'biblerevelation': {
                    'website': 'https://biblerevelation.org',
                    'description': 'Bible site',
                }
            }
        }

        router = ServerRouter(config)
        info = router.get_server_info()

        assert 'default' in info
        assert 'biblerevelation' in info
        assert info['default']['website'] == 'https://mer.vin'
        assert info['biblerevelation']['website'] == 'https://biblerevelation.org'

    def test_auto_route_setting_enabled(self, tmp_path):
        """Test that auto_route setting is accessible"""
        config = {
            'servers': {'test': {}},
            'settings': {
                'auto_route': True
            }
        }

        router = ServerRouter(config)

        assert router.auto_route is True

    def test_auto_route_setting_disabled_by_default(self, tmp_path):
        """Test that auto_route defaults to False if not set"""
        config = {
            'servers': {'test': {}},
            'settings': {}
        }

        router = ServerRouter(config)

        assert router.auto_route is False
