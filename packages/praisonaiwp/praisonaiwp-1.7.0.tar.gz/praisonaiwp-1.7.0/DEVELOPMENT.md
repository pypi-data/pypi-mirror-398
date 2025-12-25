# Development Workflow

## Feature Development Flow

### 1. Implement Feature
```bash
# Edit code files
# Add new functionality
```

### 2. Test All
```bash
pytest tests/ -v -k "not test_add_server and not test_get_server_default"
```

### 3. Repeat for Next Feature
- Implement feature 2
- Run tests again
- Continue until all features complete

### 4. Finalize
```bash
# Test with real server if needed
python -m praisonaiwp <command>
```

## Release Flow

### 1. Update Version
```bash
# Edit praisonaiwp/__version__.py
__version__ = "x.y.z"

# Edit pyproject.toml
version = "x.y.z"
```

### 2. Update CHANGELOG
```bash
# Edit CHANGELOG.md
## [x.y.z] - YYYY-MM-DD
### Added
### Changed
### Fixed
```

### 3. Lock Dependencies
```bash
uv lock
```

### 4. Build Package
```bash
rm -rf dist/
uv build
ls -lh dist/
```

### 5. Publish to PyPI
```bash
uv publish
# Requires PyPI credentials
```

### 6. Git Commit & Push
```bash
git add -A
git commit -m "vx.y.z: Feature description"
git push origin main
```

## Testing Commands

### Unit Tests
```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_wp_client.py -v

# Specific test
pytest tests/test_config.py::TestConfig::test_ssh_host_config -v

# Exclude known failures
pytest tests/ -v -k "not test_add_server and not test_get_server_default"
```

### Manual Testing
```bash
# Test commands
python -m praisonaiwp list --limit 3
python -m praisonaiwp find "search term"
python -m praisonaiwp category list

# With timing
time python -m praisonaiwp find "search term"
```

## Code Quality

### Run Linter
```bash
flake8 praisonaiwp/
```

### Format Code
```bash
black praisonaiwp/
```

## Development Tools

### Install in Dev Mode
```bash
pip install -e ".[dev]"
# or
uv sync
```

### Check Package
```bash
# Verify build
ls -lh dist/

# Check version
python -c "from praisonaiwp import __version__; print(__version__)"
```

## Notes

- Always test before version bump
- Update CHANGELOG before release
- Clean dist/ before building
- Test search performance with timing
- Keep commits atomic and descriptive
- Never commit credentials or secrets
