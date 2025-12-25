# Integration Tests

## Overview

This directory contains both **unit tests** (with mocks) and **real integration tests** (without mocks).

## Test Types

### Unit Tests (196 tests)
- **Location:** All `test_*.py` files except `test_real_integration.py`
- **Speed:** Fast (~1-2 seconds)
- **Mocks:** Yes - uses mocked SSH and WP-CLI responses
- **CI/CD:** ✅ Always runs
- **Purpose:** Test code logic and error handling

### Integration Tests (2 tests)
- **Location:** `test_real_integration.py`
- **Speed:** Slower (~5 seconds per test)
- **Mocks:** No - uses real SSH connection and WordPress
- **CI/CD:** ⏭️ Skipped (no credentials)
- **Purpose:** Test actual WordPress functionality

## Running Tests

### Run All Tests (Local Development)
```bash
# Runs all 198 tests (196 unit + 2 integration)
pytest tests/ -v
```

### Run Only Unit Tests (Fast)
```bash
# Runs 196 unit tests, skips integration
pytest tests/ -v -m "not integration"
```

### Run Only Integration Tests
```bash
# Runs 2 integration tests with detailed output
pytest tests/test_real_integration.py -v -s
```

### Run Specific Integration Test
```bash
pytest tests/test_real_integration.py::TestRealIntegration::test_real_category_assignment -v -s
```

## CI/CD Behavior

### GitHub Actions
Integration tests are **automatically skipped** in CI/CD because:
1. `CI=true` environment variable is set by GitHub Actions
2. No `~/.praisonaiwp/config.yaml` file exists in CI
3. No SSH credentials available

### Test Results in CI/CD
```
✅ 196 unit tests passed
⏭️ 2 integration tests skipped (CI environment)
```

## Local Development

### Prerequisites
To run integration tests locally, you need:
1. `~/.praisonaiwp/config.yaml` with valid server configuration
2. SSH access to a WordPress site
3. WP-CLI installed on the remote server

### Configuration Example
```yaml
# ~/.praisonaiwp/config.yaml
default_server: default
servers:
  default:
    hostname: your-server.com
    username: your-username
    wp_path: /path/to/wordpress
    php_bin: php
    wp_cli: /usr/local/bin/wp
```

## Why Integration Tests Matter

### The v1.0.21 Bug Story
**Problem:** v1.0.21 broke category assignment
- ❌ Unit tests passed (mocks didn't catch the bug)
- ❌ Released broken version
- ❌ Categories were not being set

**Solution:** Real integration tests
- ✅ Would have caught the bug before release
- ✅ Verifies actual WordPress functionality
- ✅ Tests real SSH connection and WP-CLI commands

### What Integration Tests Verify
1. **Real SSH Connection** - Connects to actual server
2. **Real WP-CLI Commands** - Executes actual WordPress commands
3. **Real Post Creation** - Creates actual posts in WordPress
4. **Real Category Assignment** - Sets actual categories
5. **Real Verification** - Checks categories were actually set
6. **Automatic Cleanup** - Deletes test posts after verification

## Test Coverage

### Unit Tests Cover
- ✅ Error handling
- ✅ Command construction
- ✅ Response parsing
- ✅ Edge cases
- ✅ Exception handling

### Integration Tests Cover
- ✅ Actual WordPress operations
- ✅ Real SSH connectivity
- ✅ WP-CLI command execution
- ✅ Category assignment verification
- ✅ End-to-end workflows

## Best Practices

### When to Run Integration Tests
- ✅ Before releasing a new version
- ✅ After making changes to core functionality
- ✅ When debugging category/post issues
- ✅ During local development (optional)

### When to Skip Integration Tests
- ⏭️ During rapid development iterations
- ⏭️ In CI/CD pipelines (no credentials)
- ⏭️ When only changing documentation
- ⏭️ For quick syntax checks

## Troubleshooting

### Integration Tests Skipped Locally
**Problem:** Tests show as skipped even though you have config
```
SKIPPED [2] Skip real integration tests in CI/CD or if config not found
```

**Solutions:**
1. Check config file exists: `ls ~/.praisonaiwp/config.yaml`
2. Verify CI env var not set: `echo $CI` (should be empty)
3. Check SSH connectivity: `ssh your-server.com`

### Integration Tests Fail
**Problem:** Tests fail with SSH or WP-CLI errors

**Solutions:**
1. Verify SSH access: `ssh your-server.com`
2. Check WP-CLI: `ssh your-server.com "wp --info"`
3. Verify WordPress path in config
4. Check server credentials

## Adding New Integration Tests

### Template
```python
def test_new_integration_feature(self, wp_client):
    """
    Test description - NO MOCKS
    """
    # Create test data
    post_id = wp_client.create_post(
        post_title="Test Post",
        post_content="<p>Test content</p>",
        post_status="draft"
    )
    
    try:
        # Test your feature
        result = wp_client.your_feature(post_id)
        
        # Verify result
        assert result is not None
        
        # Print success
        print(f"\n✅ Test passed!")
        
    finally:
        # Cleanup
        wp_client.delete_post(post_id, force=True)
```

### Guidelines
1. Always use `try/finally` for cleanup
2. Use `draft` status for test posts
3. Delete test posts after verification
4. Print detailed success messages
5. Use descriptive test names
6. Add comments explaining what's being tested

## Maintenance

### Keeping Tests Updated
- Update integration tests when adding new features
- Verify tests still pass after WordPress updates
- Keep test data minimal (avoid large content)
- Clean up test posts even if tests fail

### Monitoring
- Check integration test results before releases
- Run integration tests after major changes
- Keep track of test execution times
- Update documentation when tests change
