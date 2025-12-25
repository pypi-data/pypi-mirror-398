# PraisonAIWP Documentation

This directory contains the complete documentation for PraisonAIWP, built with Jekyll and automatically deployed to GitHub Pages.

## 📚 Documentation Structure

```
docs/
├── _config.yml              # Jekyll configuration
├── Gemfile                  # Ruby dependencies
├── index.md                 # Homepage
├── installation.md          # Installation guide
├── quickstart.md           # Quick start tutorial
├── commands/               # Command documentation
├── advanced/               # Advanced topics
├── api/                    # API reference
├── contributing/           # Contributing guides
└── .github/workflows/docs.yml  # Auto-deployment
```

## 🚀 Local Development

### Prerequisites

- Ruby 2.7+
- Bundler gem

### Setup

```bash
# Navigate to docs directory
cd docs

# Install dependencies
bundle install

# Build and serve locally
bundle exec jekyll serve

# View at http://localhost:4000/praisonaiwp/
```

### Build Only

```bash
# Build static site
bundle exec jekyll build

# Output in _site/ directory
```

## 🔄 Auto-Deployment

Documentation is automatically deployed to GitHub Pages when:

- Changes are pushed to `main`/`master` branch
- Changes are made to files in the `docs/` directory
- Pull requests are opened (preview deployment)

### Deployment Workflow

1. **Trigger**: Push to main branch with docs changes
2. **Build**: GitHub Actions builds Jekyll site
3. **Deploy**: Automatic deployment to GitHub Pages
4. **Available**: Documentation live at `https://mervinpraison.github.io/praisonaiwp/`

## 📝 Writing Documentation

### Front Matter Required

All markdown files must include Jekyll front matter:

```yaml
---
layout: default
title: Page Title
description: Page description for SEO
---
```

### Internal Links

Use relative URLs with Jekyll filters:

```markdown
[Installation Guide]({{ '/installation/' | relative_url }})
[Quick Start]({{ '/quickstart/' | relative_url }})
```

### Code Examples

Use fenced code blocks with language specification:

```bash
# Bash commands
praisonaiwp plugin list

# Python code
import praisonaiwp
```

### Images and Assets

Place images in `docs/assets/images/`:

```markdown
![Screenshot]({{ '/assets/images/screenshot.png' | relative_url }})
```

## 🎯 Content Guidelines

### Writing Style

- **Clear and concise** instructions
- **Step-by-step** tutorials
- **Code examples** for every feature
- **Practical use cases** and scenarios

### Documentation Types

1. **Tutorials**: Step-by-step guides for beginners
2. **How-to Guides**: Specific task instructions
3. **Reference**: Complete command and API documentation
4. **Explanation**: Background and conceptual information

### Command Documentation

For each command, include:

- **Purpose**: What the command does
- **Syntax**: Command usage pattern
- **Options**: All available options
- **Examples**: Practical usage examples
- **Notes**: Important considerations

```markdown
# Command Name

Brief description of what the command does.

## Syntax

```bash
praisonaiwp command-name [options] [arguments]
```

## Options

- `--option1`: Description of option 1
- `--option2`: Description of option 2

## Examples

```bash
# Basic usage
praisonaiwp command-name --option1 value

# Advanced usage
praisonaiwp command-name --option1 value --option2 value
```

## Notes

- Important consideration 1
- Important consideration 2
```

## 🔧 Configuration

### Jekyll Configuration

Key settings in `_config.yml`:

- **Theme**: jekyll-theme-cayman
- **Base URL**: `/praisonaiwp`
- **Plugins**: SEO, sitemap, feed, GitHub metadata
- **Collections**: Commands, API documentation

### GitHub Pages Settings

Repository settings must enable:

- **GitHub Pages**: Source from `docs/` folder
- **Actions**: Allow GitHub Actions to run
- **Permissions**: Write access for deployments

## 🚨 Troubleshooting

### Common Issues

1. **Build Failures**: Check Ruby version and dependencies
2. **404 Errors**: Verify `baseurl` configuration
3. **Missing Styles**: Ensure theme is properly configured
4. **Link Issues**: Use relative URLs with Jekyll filters

### Debugging

```bash
# Check Jekyll version
bundle exec jekyll --version

# Build with verbose output
bundle exec jekyll build --verbose

# Serve with detailed logs
bundle exec jekyll serve --verbose --trace
```

## 📊 Analytics and SEO

### SEO Features

- **Meta tags**: Automatic generation from front matter
- **Sitemap**: Generated automatically
- **RSS Feed**: Available at `/feed.xml`
- **Open Graph**: Social media sharing support

### Google Analytics

Add to `_config.yml`:

```yaml
google_analytics: UA-XXXXXXXXX
```

## 🤝 Contributing

### Adding Documentation

1. Create new markdown files in appropriate directories
2. Include required front matter
3. Use relative URLs for internal links
4. Test locally before submitting PR

### Updating Commands

When adding new commands:

1. Update command reference documentation
2. Add examples to quick start guide
3. Update installation guide if needed
4. Test all examples work correctly

## 📋 Review Checklist

Before submitting documentation changes:

- [ ] All markdown files have front matter
- [ ] Internal links use relative URLs
- [ ] Code examples are tested and working
- [ ] Spelling and grammar checked
- [ ] Links are verified and working
- [ ] Images are optimized and accessible
- [ ] SEO meta descriptions are included
- [ ] Local build completes successfully

## 📞 Support

- **Documentation Issues**: [Create GitHub Issue](https://github.com/mervinpraison/praisonaiwp/issues)
- **Documentation Questions**: [GitHub Discussions](https://github.com/mervinpraison/praisonaiwp/discussions)
- **Live Documentation**: [https://mervinpraison.github.io/praisonaiwp/](https://mervinpraison.github.io/praisonaiwp/)

---

**This documentation is automatically updated with every change to the main branch.**
