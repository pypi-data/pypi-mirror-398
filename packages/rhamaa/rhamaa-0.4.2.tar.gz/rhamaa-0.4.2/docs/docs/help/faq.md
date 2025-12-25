# Frequently Asked Questions

Find answers to common questions about Rhamaa CLI. If you don't find what you're looking for, check our [Troubleshooting Guide](troubleshooting.md) or create an issue on GitHub.

## General Questions

### What is Rhamaa CLI?

Rhamaa CLI is a command-line tool designed to accelerate Wagtail web development by providing:

- **Quick Project Setup**: Generate new Wagtail projects using proven templates
- **Prebuilt Applications**: Install ready-to-use apps for common use cases
- **App Registry**: Centralized catalog of available applications
- **Developer Experience**: Beautiful terminal interface with progress indicators

### Who should use Rhamaa CLI?

Rhamaa CLI is perfect for:

- **Wagtail Developers** looking to bootstrap projects quickly
- **Development Teams** wanting standardized project structures
- **IoT Developers** needing CMS integration with real-time capabilities
- **Educational Institutions** requiring LMS functionality
- **Anyone** who wants to speed up Wagtail development

### Is Rhamaa CLI free?

Yes! Rhamaa CLI is completely free and open-source. It's released under the MIT license, and all prebuilt applications are also open-source.

## Installation Questions

### What are the system requirements?

- **Python 3.7+**: Required for Rhamaa CLI
- **pip**: Python package manager
- **Wagtail**: Required for creating projects
- **Git**: For downloading apps (usually pre-installed)
- **Internet Connection**: For downloading templates and apps

### Can I use Rhamaa CLI with existing projects?

Yes! You can use `rhamaa add` to install prebuilt applications in existing Wagtail projects. Just make sure you're in the project's root directory (where `manage.py` is located).

### Do I need to install Wagtail separately?

Yes, you need to install Wagtail to create new projects:

```bash
pip install wagtail rhamaa
```

### Can I use Rhamaa CLI in virtual environments?

Absolutely! In fact, we recommend using virtual environments:

```bash
python -m venv myproject-env
source myproject-env/bin/activate  # Linux/Mac
pip install rhamaa wagtail
```

## Project Creation Questions

### What template does `rhamaa start` use?

Rhamaa CLI uses the [RhamaaCMS template](https://github.com/RhamaaCMS/RhamaaCMS), which includes:

- Modern Django/Wagtail setup
- Organized project structure
- Development and production settings
- Best practices configuration

### Can I use custom templates?

Currently, Rhamaa CLI uses the RhamaaCMS template. However, you can still use Wagtail's native template system:

```bash
wagtail start --template=https://github.com/your-org/template.git MyProject
```

### What's the difference between `rhamaa start` and `wagtail start`?

- `rhamaa start` uses the RhamaaCMS template automatically
- `wagtail start` uses the default Wagtail template
- Both create functional Wagtail projects

## App Management Questions

### What apps are available?

Current apps include:

- **mqtt**: IoT MQTT integration
- **users**: Advanced user management
- **articles**: Blog and article system
- **lms**: Learning Management System

Use `rhamaa add --list` to see all available apps.

### How do I know which apps to install?

Consider your project needs:

- **Blog/News Site**: `articles` + `users`
- **IoT Dashboard**: `mqtt` + `users`
- **E-Learning Platform**: `lms` + `users` + `articles`
- **Corporate Site**: `users` + `articles`

### Can I modify installed apps?

Yes! After installation, apps are in your `apps/` directory and can be customized:

- Modify templates
- Extend models
- Add custom views
- Override settings

### What happens if I reinstall an app?

Using `rhamaa add <app> --force` will:

- Remove the existing app directory
- Download and install the fresh version
- **Warning**: This will delete any local modifications

### Do apps have dependencies?

Some apps may require others:

- **lms** works best with **users**
- **articles** can use **users** for author management

Check each app's README for specific requirements.

## Technical Questions

### Where are apps installed?

Apps are installed in the `apps/` directory of your project:

```
your_project/
├── apps/
│   ├── mqtt/
│   ├── users/
│   └── articles/
└── manage.py
```

### How do I configure installed apps?

After installation:

1. **Add to INSTALLED_APPS**:
   ```python
   INSTALLED_APPS = [
       # ... existing apps
       'apps.mqtt',
   ]
   ```

2. **Run migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **Check app's README** for specific settings

### Can I use Rhamaa CLI with Docker?

Yes! You can use Rhamaa CLI in Docker containers:

```dockerfile
FROM python:3.9
RUN pip install rhamaa wagtail
# ... rest of your Dockerfile
```

### Does Rhamaa CLI work on Windows?

Yes! Rhamaa CLI works on:

- **Windows** (PowerShell, Command Prompt)
- **macOS** (Terminal)
- **Linux** (Bash, Zsh, etc.)

### How do I update Rhamaa CLI?

```bash
pip install --upgrade rhamaa
```

To check your current version:

```bash
pip show rhamaa
```

## Registry Questions

### How does the app registry work?

The registry is a catalog of available apps built into Rhamaa CLI. It contains:

- App names and descriptions
- GitHub repository URLs
- Installation instructions
- Category classifications

### Can I add my own apps to the registry?

Yes! To contribute an app:

1. Create a Django app following our standards
2. Host it on GitHub
3. Submit a pull request to add it to the registry

See our [Contributing Guide](../development/contributing.md) for details.

### How often is the registry updated?

The registry is updated with each Rhamaa CLI release. New apps and updates are included in new versions.

### Can I use apps not in the registry?

While Rhamaa CLI is designed for registry apps, you can manually install any Django app:

```bash
git clone https://github.com/someone/some-app.git apps/some-app
```

## Troubleshooting Questions

### Why do I get "command not found"?

This usually means:

1. Rhamaa CLI isn't installed: `pip install rhamaa`
2. Installation directory isn't in PATH: `pip install --user rhamaa`
3. Wrong virtual environment: Check with `which python`

### Why can't I install apps?

Common reasons:

1. **Not in Wagtail project**: Navigate to project root
2. **No internet connection**: Check connectivity
3. **App already exists**: Use `--force` flag
4. **Permissions**: Use virtual environment

### Apps aren't working after installation

Check these steps:

1. **Added to INSTALLED_APPS**: In Django settings
2. **Ran migrations**: `python manage.py migrate`
3. **Collected static files**: `python manage.py collectstatic`
4. **Checked app README**: For specific requirements

### Downloads are failing

Try these solutions:

1. **Check internet connection**
2. **Try different network**
3. **Check GitHub access**
4. **Use VPN if behind firewall**

## Best Practices Questions

### Should I commit apps to version control?

Yes! Commit installed apps to your repository:

```bash
git add apps/
git commit -m "Add MQTT and users apps"
```

This ensures all team members have the same apps.

### How do I keep apps updated?

Currently, reinstall apps to get updates:

```bash
rhamaa add mqtt --force
```

Future versions will include update management.

### Can I use Rhamaa CLI in production?

Yes! The apps are production-ready. However:

1. **Test thoroughly** in development
2. **Review app code** before deployment
3. **Configure properly** for production
4. **Monitor performance** after deployment

### Should I modify app code directly?

It's better to:

1. **Override templates** in your project
2. **Extend models** using inheritance
3. **Create custom views** that use app functionality
4. **Configure through settings** when possible

Direct modifications are lost when reinstalling apps.

## Community Questions

### How can I contribute?

You can contribute by:

- **Reporting bugs** on GitHub
- **Suggesting features** through issues
- **Creating apps** for the registry
- **Improving documentation**
- **Helping other users** in discussions

### Where can I get help?

- **Documentation**: This site and app READMEs
- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and ideas
- **Community**: Join the RhamaaCMS community

### How do I report bugs?

1. **Check existing issues** on GitHub
2. **Use the issue template**
3. **Include debug information**:
   ```bash
   python --version
   pip show rhamaa
   rhamaa --version
   ```
4. **Provide steps to reproduce**
5. **Include error messages**

### Can I request new apps?

Yes! Create a feature request on GitHub with:

- **App description** and use case
- **Features** you'd like to see
- **Similar apps** for reference
- **Willingness to contribute** (optional but helpful)

## Future Plans Questions

### What's coming next?

Planned features include:

- **App updates**: Built-in update management
- **Remote registry**: Fetch apps from external sources
- **Custom registries**: Add private app repositories
- **Version management**: Track app versions
- **Dependency resolution**: Handle app dependencies

### Will Rhamaa CLI always be free?

Yes! Rhamaa CLI will always be free and open-source. The core functionality and registry apps will remain available to everyone.

### How can I stay updated?

- **Watch the GitHub repository** for releases
- **Follow RhamaaCMS** on social media
- **Subscribe to release notifications**
- **Check the changelog** regularly

---

## Still Have Questions?

If you didn't find your answer here:

1. **Check the [Troubleshooting Guide](troubleshooting.md)**
2. **Search [GitHub Issues](https://github.com/RhamaaCMS/RhamaaCLI/issues)**
3. **Create a new issue** if needed
4. **Join the discussion** on GitHub Discussions

We're here to help make your Wagtail development experience as smooth as possible!