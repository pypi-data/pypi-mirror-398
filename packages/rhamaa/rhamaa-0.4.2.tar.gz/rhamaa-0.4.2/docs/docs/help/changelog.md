# Changelog

All notable changes to Rhamaa CLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned Features

#### Short Term (v0.4.x)
- **Optional Dependencies (Extras)** - Installation variants like `pip install "rhamaa[cms]"`
  - `rhamaa[cms]` - Include Wagtail and CMS dependencies
  - `rhamaa[full]` - All dependencies for complete setup
  - `rhamaa[dev]` - Development tools and testing utilities
- Remote registry support
- App update management
- Custom registry sources

#### Medium Term (v0.5.x - v0.6.x)
- **Multi-Framework Support** - Expand beyond Wagtail
  - Django projects without CMS
  - FastAPI projects for APIs
  - Flask projects for microservices
- **Project Templates** - Framework-specific scaffolding
  - `rhamaa start MyAPI --type fastapi`
  - `rhamaa start MyApp --type django`
  - `rhamaa start MyService --type flask`
- Version management for apps
- Dependency resolution
- Configuration templates

## [0.4.1] - 2025-09-09

### Fixed
- Package structure for modular CMS commands
- Import paths for cms command modules
- Documentation consistency across all files

### Changed
- Enhanced documentation with comprehensive CMS commands reference
- Updated MkDocs navigation structure
- Improved installation guide with extras examples

### Technical
- Verified all command imports work correctly
- Updated package metadata for PyPI deployment
- Comprehensive documentation review and updates

## [0.4.0] - 2025-09-09

### Added
- **Optional Dependencies (Extras)** - Installation variants
  - `rhamaa[cms]` - Include Wagtail and CMS dependencies
  - `rhamaa[cv]` - Computer Vision with Ultralytics and OpenCV
  - `rhamaa[dev]` - Development tools and testing utilities
- **Modular CMS Commands** - Organized command structure
  - `rhamaa cms start` - Project creation
  - `rhamaa cms startapp` - App creation and prebuilt installation
  - `rhamaa cms run` - Development and production server
  - `rhamaa cms migrate` - Database migrations
  - `rhamaa cms check` - System checks
  - `rhamaa cms test` - Run tests
  - `rhamaa cms status` - Project status
  - `rhamaa cms info` - Detailed project information

### Changed
- **BREAKING**: All commands moved under `cms` namespace
  - `rhamaa start` → `rhamaa cms start`
  - `rhamaa startapp` → `rhamaa cms startapp`
- **Modular Architecture** - Split cms.py into organized modules
  - `rhamaa/commands/cms/start.py`
  - `rhamaa/commands/cms/startapp.py`
  - `rhamaa/commands/cms/server.py`
  - `rhamaa/commands/cms/database.py`
  - `rhamaa/commands/cms/management.py`
  - `rhamaa/commands/cms/info.py`
- Removed Wagtail from core dependencies (now in `[cms]` extra)

### Technical
- Cleaner code organization with separated concerns
- Better maintainability with modular structure
- Enhanced error handling and user feedback
- Comprehensive documentation updates

## [0.3.1] - 2025-09-09

### Fixed
- Package deployment configuration for PyPI
- Updated README.md with current functionality and simplified examples
- Improved documentation structure and clarity

### Changed
- Enhanced package metadata for better PyPI presentation
- Streamlined getting started documentation

### Technical
- Fixed PyPI deployment process
- Updated version references across all files
- Improved package distribution configuration

## [0.3.0] - 2025-09-09

### Added
- JSON-based app registry in `rhamaa/templates/app_list.json`
- New prebuilt apps: `lms` and `ecommerce`
- Categorized app display in `--list` command
- Enhanced error handling for registry loading

### Changed
- **BREAKING**: Consolidated all functionality into `startapp` command
- **BREAKING**: Default app type changed from `wagtail` to `minimal`
- All apps now created in `apps/` directory by default
- Simplified command structure (only `start` and `startapp`)
- Updated documentation to be more concise and focused

### Removed
- **BREAKING**: `rhamaa registry` command group (use `startapp --list`)
- **BREAKING**: `rhamaa add` command (use `startapp --prebuild`)
- Deprecated registry.py and commands/registry.py files
- Deprecated commands/add.py file

### Fixed
- Apps.py configuration now correctly uses `apps.{app_name}` format
- JSON registry loading with proper error handling
- Package data configuration for JSON files

### Technical
- Migrated from hardcoded registry to JSON file
- Improved package structure and data inclusion
- Updated version to 0.3.0 for stable release

## [0.2.0b1] - 2025-09-07

### Added
- `startapp`: dukungan template `--type` dengan opsi `wagtail` (default) dan `minimal`
- `startapp`: instalasi prebuilt via `--prebuild <key>` dan daftar registry via `--list`
- Packaging: sertakan template baru di `rhamaa/templates/APPS_TEMPLATES/**/*`

### Changed
- Dokumentasi: migrasi seluruh contoh dari `rhamaa add`/`rhamaa registry` ke alur `rhamaa startapp`
- CLI help: hanya menampilkan perintah utama `start` dan `startapp`

### Deprecated
- Perintah `rhamaa registry` (fungsi list pindah ke `startapp --list`)
- Perintah `rhamaa add` (digantikan `startapp --prebuild`)

### Removed
- Folder template lama `rhamaa/templates/APPS_TEMPLATE/`

### Fixed
- `startapp`: FileNotFoundError untuk beberapa template yang hilang (menambahkan `.tpl` yang diperlukan untuk `wagtail` dan `minimal`)
- Dokumentasi `INSTALLED_APPS` diperbaiki ke `apps.<nama_app>`

## [0.1.0b1] - 2024-01-15

### Added
- Initial beta release of Rhamaa CLI
- Project creation with `rhamaa start` command
- App installation with `rhamaa add` command
- Registry management with `rhamaa registry` commands
- Built-in app registry with 4 prebuilt applications
- Rich terminal UI with ASCII art branding
- Progress indicators for downloads and installations
- Force installation option with `--force` flag
- Comprehensive error handling and validation
- Project detection and validation
- GitHub repository integration for app downloads

### Applications Added
- **mqtt**: IoT MQTT integration for Wagtail
- **users**: Advanced user management system
- **articles**: Blog and article management system
- **lms**: Complete Learning Management System

### Commands Added
- `rhamaa start <ProjectName>`: Create new Wagtail project
- `rhamaa add <AppName>`: Install prebuilt applications
- `rhamaa add --list`: List available applications
- `rhamaa registry list`: Display registry contents by category
- `rhamaa registry info <AppName>`: Show detailed app information
- `rhamaa help`: Display help information with logo

### Features
- **Project Management**: Create Wagtail projects using RhamaaCMS template
- **App Installation**: Download and install apps from GitHub repositories
- **Registry System**: Centralized catalog of available applications
- **Progress Tracking**: Real-time download and installation progress
- **Error Handling**: Comprehensive error messages and troubleshooting
- **Project Validation**: Automatic detection of Wagtail projects
- **Force Installation**: Overwrite existing apps when needed
- **Rich UI**: Beautiful ASCII art branding and colored output

### Technical Details
- **Python Support**: Python 3.7+
- **Dependencies**: Click, Rich, Requests, GitPython
- **Package Structure**: Modular command architecture
- **Distribution**: Available on PyPI as beta release
- **License**: MIT License

### Documentation
- Complete documentation with MkDocs Material
- Installation and quick start guides
- Command reference and examples
- App catalog with detailed descriptions
- Troubleshooting and FAQ sections
- Contributing guidelines for developers

## [0.0.1] - 2024-01-01

### Added
- Initial project structure
- Basic CLI framework with Click
- Rich console integration
- Project scaffolding setup

---

## Release Notes

### Version 0.1.0b1 - Beta Release

This is the first beta release of Rhamaa CLI, introducing the core functionality for accelerating Wagtail development.

#### Key Features

**Project Creation**
- Create new Wagtail projects with a single command
- Uses the proven RhamaaCMS template
- Automatic project structure setup

**App Ecosystem**
- 4 prebuilt applications ready for installation
- Covers IoT, authentication, content management, and education
- Easy installation with automatic GitHub integration

**Developer Experience**
- Beautiful terminal interface with Rich library
- Real-time progress indicators
- Comprehensive error handling
- Intuitive command structure

#### Available Applications

1. **MQTT Apps** (`mqtt`)
   - IoT device integration
   - Real-time messaging
   - Dashboard and monitoring

2. **User Management** (`users`)
   - Advanced authentication
   - User profiles and permissions
   - Social login integration

3. **Article System** (`articles`)
   - Blog and content management
   - SEO optimization
   - Comment system

4. **Learning Management System** (`lms`)
   - Course creation and management
   - Student enrollment
   - Assessment tools

#### Installation

```bash
pip install rhamaa==0.1.0b1
```

#### Basic Usage

```bash
# Create a new project
rhamaa start MyProject

# Add applications
rhamaa add mqtt
rhamaa add users

# Explore the registry
rhamaa registry list
```

#### Known Issues

- Registry updates require CLI updates
- No automatic app update mechanism
- Limited to GitHub-hosted applications
- No dependency resolution between apps

#### Feedback

This is a beta release. Please report issues and provide feedback on our [GitHub repository](https://github.com/RhamaaCMS/RhamaaCLI/issues).

---

## Upgrade Guide

### From 0.0.1 to 0.1.0b1

This is a major update with breaking changes:

1. **Install New Version**
   ```bash
   pip install --upgrade rhamaa
   ```

2. **New Commands Available**
   - All previous functionality has been redesigned
   - Use `rhamaa --help` to see new command structure

3. **Project Structure Changes**
   - Apps are now installed in `apps/` directory
   - Follow new installation procedures

### Future Upgrades

We'll provide detailed upgrade guides for future releases, including:

- Migration scripts for breaking changes
- Compatibility information
- Feature deprecation notices

---

## Contributing to Changelog

When contributing to Rhamaa CLI, please update this changelog:

### Format

```markdown
## [Version] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security improvements
```

### Categories

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements

### Guidelines

1. **Keep entries concise** but descriptive
2. **Group similar changes** together
3. **Use present tense** ("Add feature" not "Added feature")
4. **Include issue/PR numbers** when relevant
5. **Highlight breaking changes** clearly

---

## Release Schedule

### Current Release Cycle

- **Beta Releases**: Monthly during development
- **Stable Releases**: Quarterly
- **Patch Releases**: As needed for critical fixes

### Upcoming Releases

#### 0.2.0 (Planned - Q2 2024)
- Remote registry support
- App update management
- Enhanced error handling
- Performance improvements

#### 0.3.0 (Planned - Q3 2024)
- Custom registry sources
- Dependency resolution
- Configuration templates
- Plugin system

#### 1.0.0 (Planned - Q4 2024)
- Stable API
- Complete feature set
- Production-ready
- Long-term support

---

## Support

For questions about releases or changelog:

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and feedback
- **Documentation**: Detailed guides and references

Stay updated with Rhamaa CLI development by watching our [GitHub repository](https://github.com/RhamaaCMS/RhamaaCLI)!