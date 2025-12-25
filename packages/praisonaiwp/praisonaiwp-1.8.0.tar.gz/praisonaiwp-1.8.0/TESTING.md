# PraisonAIWP Testing Guide

## Table of Contents
- [Quick Start](#quick-start)
- [Test Types](#test-types)
- [Running Tests](#running-tests)
- [Test Structure](#test-structure)
- [Integration Tests](#integration-tests)
- [Manual Testing](#manual-testing)
- [CI/CD](#cicd-behavior)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Quick Start

### Install Test Dependencies

**Using uv (Recommended):**
```bash
uv sync --extra dev
```

**Or using pip:**
```bash
pip install -e ".[dev]"
```

### Run All Tests
```bash
# All tests (unit + integration if config exists)
pytest tests/ -v

# Only unit tests (fast, skip integration)
pytest tests/ -v -m "not integration"

# Only integration tests (real WordPress)
pytest tests/test_real_integration.py -v -s
```

## Test Types

### Unit Tests (196 tests)
- **Location:** All `test_*.py` files except `test_real_integration.py`
- **Speed:** Fast (~1-2 seconds total)
- **Mocks:** Yes - uses mocked SSH and WP-CLI responses
- **CI/CD:** ✅ Always runs
- **Purpose:** Test code logic and error handling

### Integration Tests (2 tests)
- **Location:** `test_real_integration.py`
- **Speed:** Slower (~5 seconds per test)
- **Mocks:** No - uses real SSH connection and WordPress
- **CI/CD:** ⏭️ Automatically skipped (no credentials)
- **Purpose:** Test actual WordPress functionality

**Total:** 198 tests (196 unit + 2 integration)

## Running Tests

### Basic Commands

**Using uv:**
```bash
uv run pytest
```

**Or with activated venv:**
```bash
source .venv/bin/activate
pytest
```

### Run with Coverage
```bash
pytest --cov=praisonaiwp --cov-report=html
```

### Run Specific Test File
```bash
pytest tests/test_content_editor.py
pytest tests/test_config.py
pytest tests/test_wp_client.py
pytest tests/test_real_integration.py
```

### Run Specific Test
```bash
# Unit test
pytest tests/test_content_editor.py::TestContentEditor::test_replace_at_line

# Integration test
pytest tests/test_real_integration.py::TestRealIntegration::test_real_category_assignment -v -s
```

### Run with Verbose Output
```bash
pytest -v
```

### Run with Print Statements
```bash
pytest -s
```

### Filter by Markers
```bash
# Skip integration tests (fast)
pytest tests/ -v -m "not integration"

# Only integration tests
pytest tests/ -v -m "integration"
```

### Simulate CI/CD Environment
```bash
# Tests integration tests will be skipped
CI=true pytest tests/ -v
```

## Test Structure

```
tests/
├── conftest.py                   # Pytest fixtures
├── test_content_editor.py        # ContentEditor tests (unit)
├── test_config.py                # Config tests (unit)
├── test_wp_client.py             # WPClient tests (unit, mocked)
├── test_real_integration.py      # Integration tests (NO mocks)
└── README_INTEGRATION_TESTS.md   # Integration tests documentation
```

## Test Coverage

### Unit Tests Coverage

- ✅ **ContentEditor**: 100% coverage
  - Line-specific replacement
  - Nth occurrence replacement
  - Range replacement
  - Context-aware replacement
  - Find occurrences
  - Preview changes

- ✅ **Config**: 100% coverage
  - Initialize default config
  - Save and load
  - Add/get servers
  - Settings management
  - Error handling

- ✅ **WPClient**: 90% coverage (mocked)
  - Execute WP-CLI commands
  - Create/update/list posts
  - Database queries
  - Search and replace
  - Error handling

### Integration Tests Coverage

- ✅ **Real WordPress Operations**
  - SSH connection to actual server
  - WP-CLI command execution
  - Post creation and deletion
  - Category assignment and verification
  - End-to-end workflows

## Integration Tests

### Overview

Integration tests verify actual WordPress functionality without mocks. They connect to a real WordPress server via SSH and execute real WP-CLI commands.

### Prerequisites

To run integration tests locally:
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

### Running Integration Tests

```bash
# Run all integration tests
pytest tests/test_real_integration.py -v -s

# Run specific integration test
pytest tests/test_real_integration.py::TestRealIntegration::test_real_category_assignment -v -s

# Skip integration tests (for fast testing)
pytest tests/ -v -m "not integration"
```

### What Integration Tests Verify

1. **Real SSH Connection** - Connects to actual server
2. **Real WP-CLI Commands** - Executes actual WordPress commands
3. **Real Post Creation** - Creates actual posts in WordPress
4. **Real Category Assignment** - Sets actual categories
5. **Real Verification** - Checks categories were actually set
6. **Automatic Cleanup** - Deletes test posts after verification

### Why Integration Tests Matter

#### The v1.0.21 Bug Story

**Problem:** v1.0.21 broke category assignment
- ❌ Unit tests passed (mocks didn't catch the bug)
- ❌ Released broken version
- ❌ Categories were not being set

**Solution:** Real integration tests
- ✅ Would have caught the bug before release
- ✅ Verifies actual WordPress functionality
- ✅ Tests real SSH connection and WP-CLI commands

### Adding New Integration Tests

Template for new integration tests:

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

### Integration Test Guidelines

1. Always use `try/finally` for cleanup
2. Use `draft` status for test posts
3. Delete test posts after verification
4. Print detailed success messages
5. Use descriptive test names
6. Add comments explaining what's being tested

## CI/CD Behavior

### GitHub Actions

Integration tests are **automatically skipped** in CI/CD because:
1. `CI=true` environment variable is set by GitHub Actions
2. No `~/.praisonaiwp/config.yaml` file exists in CI
3. No SSH credentials available

### Test Results in CI/CD

```bash
# CI/CD runs:
✅ 196 unit tests passed
⏭️ 2 integration tests skipped (CI environment)

# Local development runs:
✅ 196 unit tests passed
✅ 2 integration tests passed
Total: 198 tests passed
```

### Simulating CI/CD Locally

```bash
# Test what CI/CD will see
CI=true pytest tests/ -v

# Expected output:
# 196 passed, 2 skipped
```

## Manual Testing

### Test CLI Commands

```bash
# Initialize
praisonaiwp init

# Create single post
praisonaiwp create "Test Post" --content "Test content"

# Update post
praisonaiwp update 123 "old" "new" --line 10 --preview

# Find text
praisonaiwp find "search text"

# List posts
praisonaiwp list --type page
```

### Test with Real WordPress Server

1. **Setup test server**:
   ```bash
   praisonaiwp init
   # Enter test server details
   ```

2. **Create test post**:
   ```bash
   praisonaiwp create "Test Post $(date +%s)" --content "Test content"
   ```

3. **Update test post**:
   ```bash
   praisonaiwp update <POST_ID> "Test" "UPDATED" --preview
   ```

4. **Clean up**:
   ```bash
   # Delete test posts manually via WordPress admin
   ```

### Test Parallel Execution

1. **Install Node.js dependencies**:
   ```bash
   cd praisonaiwp/parallel/nodejs
   npm install
   ```

2. **Create test file with 20 posts**:
   ```bash
   cat > test_posts.json << 'EOF'
   [
     {"title": "Test 1", "content": "<p>Content 1</p>"},
     {"title": "Test 2", "content": "<p>Content 2</p>"},
     ...
     {"title": "Test 20", "content": "<p>Content 20</p>"}
   ]
   EOF
   ```

3. **Create posts (should use parallel mode)**:
   ```bash
   time praisonaiwp create test_posts.json
   # Should complete in ~5-8 seconds
   ```

## Integration Tests

### Test SSH Connection

```python
from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager

config = Config()
server = config.get_server()

with SSHManager(
    server['hostname'],
    server['username'],
    server['key_file']
) as ssh:
    stdout, stderr = ssh.execute('echo "Hello"')
    assert stdout.strip() == "Hello"
```

### Test WP-CLI Access

```python
from praisonaiwp.core.wp_client import WPClient

# ... (setup ssh as above)

wp = WPClient(ssh, server['wp_path'], server['php_bin'])
posts = wp.list_posts(post_type='post')
assert isinstance(posts, list)
```

### Test Content Editor

```python
from praisonaiwp.editors.content_editor import ContentEditor

content = "line1\nline2\nline3"
editor = ContentEditor()

result = editor.replace_at_line(content, 2, "line2", "LINE2")
assert "LINE2" in result
assert result.count("line") == 2  # line1 and line3 unchanged
```

## Performance Testing

### Benchmark Sequential vs Parallel

```bash
# Create 100 test posts
python -c "
import json
posts = [{'title': f'Test {i}', 'content': f'<p>Content {i}</p>'} 
         for i in range(100)]
with open('100_posts.json', 'w') as f:
    json.dump(posts, f)
"

# Test sequential (disable parallel)
# Edit config: parallel_threshold: 1000
time praisonaiwp create 100_posts.json

# Test parallel (enable parallel)
# Edit config: parallel_threshold: 10
time praisonaiwp create 100_posts.json
```

## Continuous Integration

### GitHub Actions (Example)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -e ".[dev]"
    
    - name: Run tests
      run: |
        pytest --cov=praisonaiwp --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

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
4. Verify config has required fields (hostname, username, wp_path)

### Integration Tests Fail

**Problem:** Tests fail with SSH or WP-CLI errors

**Solutions:**
1. Verify SSH access: `ssh your-server.com`
2. Check WP-CLI: `ssh your-server.com "wp --info"`
3. Verify WordPress path in config
4. Check server credentials
5. Ensure WP-CLI is installed on remote server

### SSH Connection Tests Failing

```bash
# Check SSH key permissions
chmod 600 ~/.ssh/id_ed25519

# Test SSH manually
ssh -i ~/.ssh/id_ed25519 user@hostname

# Check config
cat ~/.praisonaiwp/config.yaml

# Test SSH config
ssh -G hostname | grep -E "hostname|user|identityfile"
```

### WP-CLI Tests Failing

```bash
# Test WP-CLI manually
ssh user@hostname "cd /path/to/wp && wp --info"

# Check PHP binary
ssh user@hostname "which php"
ssh user@hostname "/opt/plesk/php/8.3/bin/php --version"

# Test WP-CLI command
ssh user@hostname "cd /path/to/wp && wp post list --format=count"
```

### Unit Tests Failing

```bash
# Clear pytest cache
pytest --cache-clear

# Run with verbose output
pytest -vv

# Run specific failing test
pytest tests/test_wp_client.py::TestWPClient::test_create_post -vv

# Check for import errors
python -c "from praisonaiwp.core.wp_client import WPClient"
```

### Parallel Tests Failing

```bash
# Check Node.js installation
node --version  # Should be 14+

# Install Node.js dependencies
cd praisonaiwp/parallel/nodejs
npm install

# Test Node.js script manually
echo '{"operation":"create","data":[],"server":{},"workers":10}' | node index.js
```

### Coverage Report Issues

```bash
# Clear coverage data
rm -rf .coverage htmlcov/

# Run with fresh coverage
pytest --cov=praisonaiwp --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Test Data Cleanup

After testing, clean up test data:

```bash
# List test posts
praisonaiwp list --search "Test"

# Delete via WordPress admin or WP-CLI
ssh user@hostname "cd /path/to/wp && wp post delete <ID> --force"
```

## Best Practices

### General Testing

1. **Always use test server** - Never test on production
2. **Clean up test data** - Delete test posts after testing
3. **Run tests before commits** - Catch issues early
4. **Test edge cases** - Invalid inputs, network errors, etc.
5. **Performance test** - Benchmark before and after changes

### Unit Tests

1. **Use mocking** - Mock SSH/WP-CLI for unit tests
2. **Fast execution** - Unit tests should run in seconds
3. **Isolated tests** - Each test should be independent
4. **Clear assertions** - Make test failures obvious
5. **Good coverage** - Aim for >90% code coverage

### Integration Tests

1. **Run before releases** - Always run integration tests before releasing
2. **Test real scenarios** - Use actual WordPress operations
3. **Clean up properly** - Use `try/finally` blocks
4. **Use draft posts** - Avoid publishing test content
5. **Verify thoroughly** - Check actual results, not just success codes
6. **Document failures** - Note any issues for investigation

### When to Run What

**During Development (Fast Iteration):**
```bash
# Only unit tests (fast)
pytest tests/ -v -m "not integration"
```

**Before Committing:**
```bash
# All tests including integration
pytest tests/ -v
```

**Before Releasing:**
```bash
# All tests with coverage
pytest tests/ -v --cov=praisonaiwp --cov-report=html

# Verify integration tests pass
pytest tests/test_real_integration.py -v -s
```

**In CI/CD:**
```bash
# Unit tests only (integration skipped automatically)
pytest tests/ -v
# Result: 196 passed, 2 skipped
```

### Test Maintenance

1. **Update tests when adding features** - Keep tests in sync with code
2. **Fix failing tests immediately** - Don't let tests rot
3. **Review test coverage** - Check coverage reports regularly
4. **Refactor tests** - Keep test code clean and maintainable
5. **Document test behavior** - Explain complex test scenarios

### Integration Test Maintenance

1. **Keep tests minimal** - Avoid large content or many operations
2. **Monitor execution time** - Watch for slow tests
3. **Update after WordPress changes** - Verify compatibility
4. **Check cleanup** - Ensure test posts are deleted
5. **Verify credentials** - Keep config up to date

## Summary

### Test Strategy Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Testing Strategy                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Unit Tests (196 tests)                                 │
│  ├─ Fast (~1-2 seconds)                                 │
│  ├─ Mocked SSH/WP-CLI                                   │
│  ├─ Always run in CI/CD                                 │
│  └─ Test code logic                                     │
│                                                          │
│  Integration Tests (2 tests)                            │
│  ├─ Slower (~5 seconds each)                            │
│  ├─ Real WordPress operations                           │
│  ├─ Skipped in CI/CD                                    │
│  └─ Test actual functionality                           │
│                                                          │
│  Total: 198 tests                                       │
│  ├─ Local: 198 passed                                   │
│  └─ CI/CD: 196 passed, 2 skipped                        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Quick Reference

```bash
# Fast development testing
pytest tests/ -v -m "not integration"

# Full local testing
pytest tests/ -v

# Only integration tests
pytest tests/test_real_integration.py -v -s

# Simulate CI/CD
CI=true pytest tests/ -v

# With coverage
pytest --cov=praisonaiwp --cov-report=html

# Specific test
pytest tests/test_wp_client.py::TestWPClient::test_create_post -v
```

### Key Takeaways

1. ✅ **Unit tests** catch code logic errors (fast, always run)
2. ✅ **Integration tests** catch real-world issues (slower, local only)
3. ✅ **CI/CD** runs unit tests automatically (integration skipped)
4. ✅ **Before release** run both unit and integration tests
5. ✅ **The v1.0.21 bug** would have been caught by integration tests
