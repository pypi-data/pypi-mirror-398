# CMS Commands Reference

Complete reference for all `rhamaa cms` commands.

## Project Creation

### `rhamaa cms start <project>`

Create a new Wagtail project using RhamaaCMS template.

```bash
rhamaa cms start MyProject
```

**Features:**
- Downloads RhamaaCMS template from GitHub
- Creates project with best practices structure
- Includes development and production settings
- Ready for immediate development

## App Management

### `rhamaa cms startapp <name>`

Create Django apps or install prebuilt applications.

#### Options:
- `--type minimal` - Standard Django app (default)
- `--type wagtail` - Wagtail app with models/templates
- `--prebuild <key>` - Install prebuilt app from registry
- `--list` - Show available prebuilt apps
- `--force` - Overwrite existing app

#### Examples:
```bash
# Create minimal Django app
rhamaa cms startapp blog

# Create Wagtail app
rhamaa cms startapp pages --type wagtail

# Install prebuilt app
rhamaa cms startapp iot --prebuild mqtt

# List available prebuilt apps
rhamaa cms startapp --list

# Force overwrite existing app
rhamaa cms startapp users --prebuild users --force
```

## Development Server

### `rhamaa cms run`

Start development or production server.

#### Options:
- `--host <host>` - Host to bind to (default: 127.0.0.1)
- `--port <port>` - Port to bind to (default: 8000)
- `--prod` - Run with Gunicorn for production

#### Examples:
```bash
# Start development server
rhamaa cms run

# Custom host and port
rhamaa cms run --host 0.0.0.0 --port 8080

# Production server with Gunicorn
rhamaa cms run --prod
```

## Database Management

### `rhamaa cms migrate`

Run database migrations.

```bash
rhamaa cms migrate
```

### `rhamaa cms makemigrations`

Create new migrations.

```bash
# Create migrations for all apps
rhamaa cms makemigrations

# Create migrations for specific app
rhamaa cms makemigrations myapp
```

## Development Tools

### `rhamaa cms check`

Run Django system checks.

```bash
rhamaa cms check
```

### `rhamaa cms test`

Run tests.

```bash
# Run all tests
rhamaa cms test

# Run tests for specific app
rhamaa cms test myapp
```

### `rhamaa cms shell`

Open Django shell.

```bash
rhamaa cms shell
```

## User Management

### `rhamaa cms createsuperuser`

Create superuser account.

```bash
rhamaa cms createsuperuser
```

## Static Files & Assets

### `rhamaa cms collectstatic`

Collect static files.

```bash
rhamaa cms collectstatic
```

## Wagtail-Specific Commands

### `rhamaa cms update_index`

Update Wagtail search index.

```bash
rhamaa cms update_index
```

## Project Information

### `rhamaa cms status`

Show quick project status.

```bash
rhamaa cms status
```

**Output includes:**
- Project path
- manage.py status
- apps/ directory status
- Requirements file status

### `rhamaa cms info`

Show detailed project information.

```bash
rhamaa cms info
```

**Output includes:**
- Django version
- Wagtail version
- Installation status

## Command Workflow Examples

### New Project Setup
```bash
# Create project
rhamaa cms start MyBlog
cd MyBlog

# Install dependencies
pip install -r requirements.txt

# Install prebuilt blog app
rhamaa cms startapp articles --prebuild articles

# Run migrations
rhamaa cms makemigrations
rhamaa cms migrate

# Create admin user
rhamaa cms createsuperuser

# Start development server
rhamaa cms run
```

### Daily Development
```bash
# Check project health
rhamaa cms check

# Run tests
rhamaa cms test

# Create new app
rhamaa cms startapp products

# Make migrations for new models
rhamaa cms makemigrations products

# Apply migrations
rhamaa cms migrate

# Start server
rhamaa cms run
```

### Production Deployment
```bash
# Collect static files
rhamaa cms collectstatic

# Run system checks
rhamaa cms check

# Update search index
rhamaa cms update_index

# Start production server
rhamaa cms run --prod
```

## Error Handling

All CMS commands include comprehensive error handling:

- **Project Detection**: Automatically detects if you're in a Django/Wagtail project
- **Dependency Checks**: Verifies required packages are installed
- **Clear Messages**: Provides helpful error messages and suggestions
- **Graceful Failures**: Commands fail safely without corrupting your project

## Integration with Django

Rhamaa CMS commands are designed to complement, not replace, Django's management commands. You can still use:

```bash
# Django commands still work
python manage.py runserver
python manage.py migrate
python manage.py shell

# Rhamaa commands provide enhanced experience
rhamaa cms run
rhamaa cms migrate
rhamaa cms shell
```

## Next Steps

- Learn about [Available Apps](../apps/index.md)
- Check [Troubleshooting Guide](../help/troubleshooting.md)
- See [Development Best Practices](../development/contributing.md)