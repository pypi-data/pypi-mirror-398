# Quick Start

Get started with Rhamaa CLI in 5 minutes.

## 1. Install & Create Project

```bash
# Install with CMS support
pip install "rhamaa[cms]"

# Create project
rhamaa cms start MyBlog
cd MyBlog
```

## 2. Setup Environment

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

## 3. List Available Apps

```bash
rhamaa cms startapp --list
```

## 4. Install Prebuilt App

```bash
rhamaa cms startapp articles --prebuild articles
```

## 5. Configure App

Add to `settings.py`:
```python
INSTALLED_APPS = [
    # ... existing apps
    'apps.articles',
]
```

Run migrations:
```bash
rhamaa cms makemigrations
rhamaa cms migrate
rhamaa cms createsuperuser
```

## 6. Start Server

```bash
rhamaa cms run
```

Visit `http://127.0.0.1:8000/admin/`

## 7. Additional Commands

```bash
# Run system checks
rhamaa cms check

# Run tests
rhamaa cms test

# Collect static files
rhamaa cms collectstatic

# Project status
rhamaa cms status
```

## What's Next?

### Add More Apps

Explore other available apps:

```bash
# Add user management
rhamaa startapp users --prebuild users

# Add IoT capabilities
rhamaa startapp iot --prebuild mqtt

# Add LMS functionality
rhamaa startapp lms --prebuild lms
```

### Get App Information

Learn more about any app before installing:

```bash
rhamaa startapp --list
# Then open the app repo linked in the table for details
```

### Registry Commands

The standalone `registry` command group is deprecated. Use:

```bash
rhamaa startapp --list
```

## Common Workflows

### Starting a Blog Project

```bash
rhamaa start MyBlog
cd MyBlog
rhamaa startapp articles --prebuild articles
# Configure and run migrations
```

### Starting an IoT Project

```bash
rhamaa start IoTDashboard
cd IoTDashboard
rhamaa startapp iot --prebuild mqtt
rhamaa startapp users --prebuild users
# Configure MQTT settings and run migrations
```

### Starting an Educational Platform

```bash
rhamaa start EduPlatform
cd EduPlatform
rhamaa startapp lms --prebuild lms
rhamaa startapp users --prebuild users
# Configure LMS settings and run migrations
```

## Tips for Success

!!! tip "Project Structure"
    Rhamaa CLI creates apps in the `apps/` directory. This keeps your project organized and follows Django best practices.

!!! tip "Force Installation"
    If you need to reinstall a prebuilt app into the same folder, use the `--force` flag:
    ```bash
    rhamaa startapp articles --prebuild articles --force
    ```

!!! tip "Check Project Type"
    Rhamaa CLI automatically detects if you're in a Wagtail project before allowing app installation.

## Troubleshooting

### App Already Exists

If you see "App already exists" during prebuilt installation, use the `--force` flag to overwrite:

```bash
rhamaa startapp articles --prebuild articles --force
```

### Not a Wagtail Project

Make sure you're in the root directory of your Wagtail project (where `manage.py` is located).

### Download Issues

If downloads fail, check your internet connection and try again. The CLI will show detailed error messages.

## Next Steps

- Learn more about [Project Management](../commands/project-management.md)
- Explore [App Management](../commands/app-management.md) features
- Check out [Available Apps](../apps/index.md) in detail
- Read about [Contributing](../development/contributing.md) to the ecosystem