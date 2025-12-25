# Rhamaa CLI Documentation

This directory contains the complete documentation for Rhamaa CLI built with Material for MkDocs.

## Documentation Structure

```
docs/
├── mkdocs.yml              # MkDocs configuration
├── requirements.txt        # Documentation dependencies
├── docs/                   # Documentation content
│   ├── index.md           # Homepage (English)
│   ├── index.id.md        # Homepage (Indonesian)
│   ├── getting-started/   # Installation and quick start
│   ├── commands/          # Command reference
│   ├── apps/              # Available applications
│   ├── development/       # Contributing and API reference
│   └── help/              # Troubleshooting and FAQ
└── README.md              # This file
```

## Features

- **Bilingual Support**: English (default) and Indonesian
- **Material Design**: Modern, responsive design
- **Search**: Full-text search functionality
- **Code Highlighting**: Syntax highlighting for code blocks
- **Navigation**: Tabbed navigation with sections
- **Dark/Light Mode**: Theme toggle support

## Local Development

### Prerequisites

- Python 3.7+
- pip

### Setup

1. **Install Dependencies**
   ```bash
   cd docs
   pip install -r requirements.txt
   ```

2. **Serve Locally**
   ```bash
   mkdocs serve
   ```

3. **Open Browser**
   Navigate to `http://127.0.0.1:8000`

### Building

To build the static site:

```bash
mkdocs build
```

The built site will be in the `site/` directory.

## Language Support

The documentation supports two languages:

- **English** (default): `docs/page.md`
- **Indonesian**: `docs/page.id.md`

### Adding Translations

To add Indonesian translations:

1. Create `.id.md` version of the file
2. Translate the content
3. Update navigation translations in `mkdocs.yml`

Example:
```
docs/getting-started/installation.md     # English
docs/getting-started/installation.id.md # Indonesian
```

## Content Guidelines

### Writing Style

- **Clear and Concise**: Use simple, direct language
- **Code Examples**: Include working code examples
- **Screenshots**: Add screenshots where helpful
- **Cross-references**: Link to related sections

### Markdown Features

The documentation supports:

- **Admonitions**: `!!! tip`, `!!! warning`, etc.
- **Code Blocks**: With syntax highlighting
- **Tables**: For structured data
- **Tabs**: For multiple options
- **Task Lists**: For checklists

### Example Admonitions

```markdown
!!! tip "Pro Tip"
    Use virtual environments for better dependency management.

!!! warning "Important"
    Always backup your project before using `--force` flag.

!!! info "Note"
    This feature requires Python 3.7 or higher.
```

## Deployment

### GitHub Pages

The documentation can be deployed to GitHub Pages:

```bash
mkdocs gh-deploy
```

### Custom Domain

To use a custom domain, add a `CNAME` file to the `docs/` directory:

```
docs.rhamaacms.com
```

## Contributing

### Documentation Updates

1. **Fork the Repository**
2. **Make Changes** to documentation files
3. **Test Locally** with `mkdocs serve`
4. **Submit Pull Request**

### Translation Contributions

We welcome translations to additional languages:

1. **Create Language Files**: Follow the `.id.md` pattern
2. **Update Configuration**: Add language to `mkdocs.yml`
3. **Test Thoroughly**: Ensure all links work
4. **Submit Pull Request**

### Content Guidelines

- **Accuracy**: Ensure technical accuracy
- **Completeness**: Cover all features and use cases
- **Examples**: Include practical examples
- **Updates**: Keep content current with CLI changes

## Configuration

### MkDocs Configuration

Key configuration options in `mkdocs.yml`:

```yaml
theme:
  name: material
  language: en
  palette:
    - scheme: default
      primary: cyan
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - scheme: slate
      primary: cyan
      toggle:
        icon: material/brightness-4
        name: Switch to light mode

plugins:
  - search
  - i18n:
      docs_structure: suffix
      languages:
        - locale: en
          default: true
          name: English
        - locale: id
          name: Bahasa Indonesia
```

### Theme Customization

The documentation uses Material for MkDocs with:

- **Primary Color**: Cyan
- **Accent Color**: Blue
- **Font**: Roboto
- **Code Font**: Roboto Mono

## Maintenance

### Regular Updates

- **CLI Changes**: Update docs when CLI features change
- **Link Checking**: Verify all links work
- **Content Review**: Keep examples current
- **Translation Sync**: Keep translations up to date

### Version Management

- **Version Tags**: Tag documentation versions
- **Changelog**: Update changelog for doc changes
- **Migration Guides**: Provide upgrade instructions

## Support

For documentation issues:

- **GitHub Issues**: Report documentation bugs
- **Pull Requests**: Submit improvements
- **Discussions**: Ask questions about documentation

## License

The documentation is part of the Rhamaa CLI project and follows the same MIT license.