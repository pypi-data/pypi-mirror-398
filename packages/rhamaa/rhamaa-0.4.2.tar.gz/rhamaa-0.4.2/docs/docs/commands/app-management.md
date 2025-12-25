# CMS Commands

The `rhamaa cms` command group provides comprehensive CMS development tools.

## Project Management

### Create New Project
```bash
rhamaa cms start MyProject
```
Creates new Wagtail project using RhamaaCMS template.

### Create New Apps

#### Minimal Django App (Default)
```bash
rhamaa cms startapp blog
```
Creates standard Django app in `apps/blog/` using `django-admin startapp`.

#### Wagtail App
```bash
rhamaa cms startapp pages --type wagtail
```
Creates Wagtail-ready app with models, templates, and admin configuration.

## Install Prebuilt Apps

### Basic Installation
```bash
rhamaa cms startapp iot --prebuild mqtt
```
Downloads and installs MQTT app from GitHub into `apps/iot/`.

### Available Options
- `--list` - Show available prebuilt apps
- `--force` - Overwrite existing app
- `--type` - App template type (minimal/wagtail)

### Examples
```bash
# List all prebuilt apps
rhamaa cms startapp --list

# Install with force overwrite
rhamaa cms startapp users --prebuild users --force
```

## Development Server

### Start Development Server
```bash
rhamaa cms run
```

### Custom Host/Port
```bash
rhamaa cms run --host 0.0.0.0 --port 8080
```

### Production Server
```bash
rhamaa cms run --prod
```
Starts with Gunicorn for production deployment.

## Database Management

### Run Migrations
```bash
rhamaa cms migrate
```

### Create Migrations
```bash
rhamaa cms makemigrations
rhamaa cms makemigrations myapp
```

## Development Tools

### System Checks
```bash
rhamaa cms check
```

### Run Tests
```bash
rhamaa cms test
rhamaa cms test myapp
```

### Django Shell
```bash
rhamaa cms shell
```

### Create Superuser
```bash
rhamaa cms createsuperuser
```

## Static Files & Search

### Collect Static Files
```bash
rhamaa cms collectstatic
```

### Update Search Index (Wagtail)
```bash
rhamaa cms update_index
```

## Project Information

### Quick Status
```bash
rhamaa cms status
```

### Detailed Information
```bash
rhamaa cms info
```

## Listing Available Apps

### View All Apps

```bash
rhamaa startapp --list
```

This displays a formatted table showing:

- **App Name**: The identifier used for installation
- **Description**: Brief description of the app's functionality
- **Category**: The app's category (IoT, Authentication, Content, etc.)

### Example Output

```
┌──────────────┬────────────────────────────────────┬─────────────────┐
│ App Name     │ Description                        │ Category        │
├──────────────┼────────────────────────────────────┼─────────────────┤
│ mqtt         │ IoT MQTT integration for Wagtail  │ IoT             │
│ users        │ Advanced user management system    │ Authentication  │
│ articles     │ Blog and article management        │ Content         │
│ lms          │ Complete LMS solution for Wagtail │ Education       │
└──────────────┴────────────────────────────────────┴─────────────────┘
```

## Installation Process

When you install an app, Rhamaa CLI performs these steps:

### 1. Project Validation

- Checks if you're in a Wagtail project directory
- Looks for `manage.py` or other Django project indicators
- Displays error if not in a valid project

### 2. App Availability Check

- Verifies the app exists in the registry
- Shows error message if app is not found
- Suggests using `--list` to see available apps

### 3. Existing App Check

- Checks if app already exists in `apps/` directory
- Prompts to use `--force` flag if app exists
- Skips installation unless forced

### 4. Download Process

- Downloads the app repository from GitHub
- Shows progress bar with download status
- Handles network errors gracefully

### 5. Extraction and Installation

- Extracts the downloaded repository
- Places app files in `apps/<app_name>/` directory
- Cleans up temporary files
- Shows installation success message

## Post-Installation Steps

After installing an app, you need to:

### 1. Add to INSTALLED_APPS

Edit your Django settings file:

```python
# settings/base.py or settings.py
INSTALLED_APPS = [
    # ... existing apps
    'apps.mqtt',  # Add your installed app
]
```

### 2. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Collect Static Files (if needed)

```bash
python manage.py collectstatic
```

### 4. Additional Configuration

Check the app's README file for specific configuration requirements:

```bash
cat apps/mqtt/README.md
```

## App Directory Structure

Installed apps are placed in the `apps/` directory:

```
your_project/
├── apps/
│   ├── __init__.py
│   ├── mqtt/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── admin.py
│   │   ├── urls.py
│   │   ├── templates/
│   │   ├── static/
│   │   └── README.md
│   └── users/
│       ├── __init__.py
│       ├── models.py
│       └── ...
└── manage.py
```

## Force Installation

### When to Use `--force`

Use the `--force` flag when you want to:

- **Reinstall** an app with updates
- **Overwrite** a corrupted installation
- **Replace** a modified app with the original

### Example

```bash
rhamaa startapp mqtt --prebuild mqtt --force
```

### What Happens

- Removes the existing app directory
- Downloads and installs the fresh version
- Preserves your project's other files

!!! warning "Data Loss Warning"
    Using `--force` will delete any local modifications to the app. Make sure to backup any custom changes.

## Error Handling

### Common Errors and Solutions

#### "Not a Wagtail Project"

```
Error: This doesn't appear to be a Wagtail project.
Please run this command from the root of your Wagtail project.
```

**Solution**: Navigate to your project's root directory (where `manage.py` is located).

#### "App Not Found"

```
Error: App 'myapp' not found in registry.
Use 'rhamaa add --list' to see available apps.
```

**Solution**: Check available apps with `rhamaa startapp --list` and use the correct app name.

#### "App Already Exists"

```
Warning: App 'mqtt' already exists in apps/ directory.
Use --force flag to overwrite existing app.
```

**Solution**: Use `rhamaa add mqtt --force` to reinstall.

#### "Download Failed"

```
Failed to download repository.
Please check your internet connection and try again.
```

**Solution**: Check your internet connection and GitHub access.

## Best Practices

### Before Installation

1. **Backup Your Project**: Especially when using `--force`
2. **Check Dependencies**: Review app requirements
3. **Plan Integration**: Understand how the app fits your project

### After Installation

1. **Read Documentation**: Check the app's README file
2. **Test Functionality**: Verify the app works as expected
3. **Customize Settings**: Configure app-specific settings
4. **Update Requirements**: Add any new dependencies

### App Management

1. **Keep Apps Updated**: Reinstall apps periodically for updates
2. **Document Usage**: Note which apps you've installed
3. **Version Control**: Commit apps to your repository
4. **Environment Consistency**: Install same apps across environments

## Integration Examples

### Blog Setup

```bash
rhamaa start MyBlog
cd MyBlog
rhamaa startapp articles --prebuild articles
rhamaa startapp users --prebuild users
# Configure and run migrations
```

### IoT Dashboard

```bash
rhamaa start IoTDashboard
cd IoTDashboard
rhamaa startapp iot --prebuild mqtt
rhamaa startapp users --prebuild users
# Configure MQTT settings
```

### Educational Platform

```bash
rhamaa start EduPlatform
cd EduPlatform
rhamaa startapp lms --prebuild lms
rhamaa startapp users --prebuild users
rhamaa startapp articles --prebuild articles
# Configure LMS settings
```

## Next Steps

- Learn about the [Registry System](registry.md)
- Explore [Available Apps](../apps/index.md) in detail
- Check [Troubleshooting](../help/troubleshooting.md) for common issues