# Troubleshooting

This guide helps you resolve common issues when using Rhamaa CLI. If you don't find your issue here, please check our [FAQ](faq.md) or create an issue on GitHub.

## Installation Issues

### Command Not Found

**Problem**: `rhamaa: command not found` after installation

**Solutions**:

1. **Check Installation Path**
   ```bash
   pip show rhamaa
   # Check if the installation directory is in your PATH
   ```

2. **Use Python Module**
   ```bash
   python -m rhamaa --help
   ```

3. **Install with User Flag**
   ```bash
   pip install --user rhamaa
   ```

4. **Check Virtual Environment**
   ```bash
   which python
   which pip
   # Ensure you're in the correct environment
   ```

### Permission Errors

**Problem**: Permission denied during installation

**Solutions**:

1. **Use User Installation**
   ```bash
   pip install --user rhamaa
   ```

2. **Use Virtual Environment**
   ```bash
   python -m venv rhamaa-env
   source rhamaa-env/bin/activate  # Linux/Mac
   pip install rhamaa
   ```

3. **Fix Permissions** (Linux/Mac)
   ```bash
   sudo chown -R $USER:$USER ~/.local
   ```

### Python Version Issues

**Problem**: Rhamaa CLI requires Python 3.7+

**Solutions**:

1. **Check Python Version**
   ```bash
   python --version
   python3 --version
   ```

2. **Use Specific Python Version**
   ```bash
   python3.8 -m pip install rhamaa
   python3.8 -m rhamaa --help
   ```

3. **Update Python**
   - Install Python 3.7+ from python.org
   - Use pyenv for version management

## Project Creation Issues

### Wagtail Not Found

**Problem**: `wagtail: command not found` when running `rhamaa start`

**Solutions**:

1. **Install Wagtail**
   ```bash
   pip install wagtail
   ```

2. **Check Wagtail Installation**
   ```bash
   wagtail --version
   ```

3. **Use Same Environment**
   ```bash
   # Ensure Wagtail and Rhamaa are in the same environment
   pip list | grep wagtail
   pip list | grep rhamaa
   ```

### Template Download Fails

**Problem**: Template download fails or times out

**Solutions**:

1. **Check Internet Connection**
   ```bash
   ping github.com
   ```

2. **Check GitHub Access**
   ```bash
   curl -I https://github.com/RhamaaCMS/RhamaaCMS
   ```

3. **Use VPN/Proxy**
   - If behind corporate firewall
   - Configure proxy settings

4. **Manual Download**
   ```bash
   # Download template manually
   wget https://github.com/RhamaaCMS/RhamaaCMS/archive/refs/heads/main.zip
   wagtail start --template=main.zip MyProject
   ```

### Project Already Exists

**Problem**: Directory with project name already exists

**Solutions**:

1. **Choose Different Name**
   ```bash
   rhamaa start MyProject2
   ```

2. **Remove Existing Directory**
   ```bash
   rm -rf MyProject
   rhamaa start MyProject
   ```

3. **Backup Existing**
   ```bash
   mv MyProject MyProject_backup
   rhamaa start MyProject
   ```

## App Installation Issues

### Not a Wagtail Project

**Problem**: "This doesn't appear to be a Wagtail project"

**Solutions**:

1. **Check Current Directory**
   ```bash
   ls -la
   # Look for manage.py or Django project files
   ```

2. **Navigate to Project Root**
   ```bash
   cd /path/to/your/wagtail/project
   rhamaa startapp iot --prebuild mqtt
   ```

3. **Verify Project Structure**
   ```bash
   # Should have manage.py and Django structure
   python manage.py --version
   ```

### App Not Found

**Problem**: "App 'appname' not found in registry"

**Solutions**:

1. **Check Available Apps**
   ```bash
   rhamaa startapp --list
   ```

2. **Check Spelling**
   ```bash
   # Correct: mqtt, users, articles, lms
   # Example install key usage is on the left; use exact lowercase keys
   ```

3. **Get App Information**
   ```bash
   rhamaa startapp --list
   ```

### App Already Exists

**Problem**: "App already exists in apps/ directory"

**Solutions**:

1. **Use Force Flag**
   ```bash
   rhamaa startapp iot --prebuild mqtt --force
   ```

2. **Remove Existing App**
   ```bash
   rm -rf apps/mqtt
   rhamaa add mqtt
   ```

3. **Backup Existing**
   ```bash
   mv apps/mqtt apps/mqtt_backup
   rhamaa add mqtt
   ```

### Download Failures

**Problem**: App download fails or is corrupted

**Solutions**:

1. **Check Internet Connection**
   ```bash
   ping github.com
   curl -I https://github.com/RhamaaCMS/mqtt-apps
   ```

2. **Clear Temporary Files**
   ```bash
   # Clear system temp directory
   rm -rf /tmp/rhamaa_*  # Linux/Mac
   ```

3. **Retry Installation**
   ```bash
   rhamaa add mqtt --force
   ```

4. **Manual Installation**
   ```bash
   # Download manually
   git clone https://github.com/RhamaaCMS/mqtt-apps.git apps/mqtt
   ```

## Runtime Issues

### Import Errors

**Problem**: ImportError when running Django

**Solutions**:

1. **Check INSTALLED_APPS**
   ```python
   # settings.py
   INSTALLED_APPS = [
       # ... other apps
       'apps.mqtt',  # Correct path
   ]
   ```

2. **Run Migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **Check App Structure**
   ```bash
   ls -la apps/mqtt/
   # Should have __init__.py and other Django files
   ```

### Migration Issues

**Problem**: Migration errors after installing apps

**Solutions**:

1. **Check Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Reset Migrations**
   ```bash
   # Remove migration files (be careful!)
   rm apps/mqtt/migrations/0*.py
   python manage.py makemigrations mqtt
   python manage.py migrate
   ```

3. **Fake Migrations**
   ```bash
   python manage.py migrate --fake-initial
   ```

### Static Files Issues

**Problem**: Static files not loading

**Solutions**:

1. **Collect Static Files**
   ```bash
   python manage.py collectstatic
   ```

2. **Check Static Settings**
   ```python
   # settings.py
   STATIC_URL = '/static/'
   STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
   ```

3. **Check App Static Directory**
   ```bash
   ls -la apps/mqtt/static/
   ```

## Network Issues

### Corporate Firewalls

**Problem**: Downloads fail behind corporate firewall

**Solutions**:

1. **Configure Proxy**
   ```bash
   export HTTP_PROXY=http://proxy.company.com:8080
   export HTTPS_PROXY=http://proxy.company.com:8080
   ```

2. **Use pip Proxy**
   ```bash
   pip install --proxy http://proxy.company.com:8080 rhamaa
   ```

3. **Download Manually**
   ```bash
   # Download ZIP files manually and extract
   ```

### DNS Issues

**Problem**: Cannot resolve GitHub domains

**Solutions**:

1. **Check DNS**
   ```bash
   nslookup github.com
   ```

2. **Use Different DNS**
   ```bash
   # Use Google DNS
   echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
   ```

3. **Use IP Address**
   ```bash
   # Add to /etc/hosts
   140.82.112.3 github.com
   ```

## Performance Issues

### Slow Downloads

**Problem**: App downloads are very slow

**Solutions**:

1. **Check Connection Speed**
   ```bash
   speedtest-cli
   ```

2. **Use Different Network**
   - Try different WiFi network
   - Use mobile hotspot

3. **Download During Off-Peak**
   - Try downloading at different times

### Memory Issues

**Problem**: Out of memory during installation

**Solutions**:

1. **Close Other Applications**
   - Free up system memory

2. **Increase Swap Space** (Linux)
   ```bash
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

3. **Use Smaller Apps**
   - Install apps one at a time

## Environment Issues

### Virtual Environment Problems

**Problem**: Apps not working in virtual environment

**Solutions**:

1. **Activate Environment**
   ```bash
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```

2. **Check Environment**
   ```bash
   which python
   which pip
   pip list
   ```

3. **Recreate Environment**
   ```bash
   deactivate
   rm -rf .venv
   python -m venv .venv
   source .venv/bin/activate
   pip install rhamaa wagtail
   ```

### Path Issues

**Problem**: Python can't find installed packages

**Solutions**:

1. **Check Python Path**
   ```python
   import sys
   print(sys.path)
   ```

2. **Install in Development Mode**
   ```bash
   pip install -e .
   ```

3. **Add to Python Path**
   ```bash
   export PYTHONPATH="${PYTHONPATH}:/path/to/your/project"
   ```

## Getting More Help

### Debug Information

When reporting issues, include:

```bash
# System information
python --version
pip --version
rhamaa --version  # or python -m rhamaa --version

# Environment information
pip list | grep -E "(rhamaa|wagtail|django)"

# Error messages
   # For detailed steps, re-run with --force and capture full output
   rhamaa startapp iot --prebuild mqtt --force
```

### Log Files

Check for log files in:

- `/tmp/rhamaa.log` (Linux/Mac)
- `%TEMP%\rhamaa.log` (Windows)
- Current directory

### Reporting Issues

When creating GitHub issues:

1. **Use Issue Template**: Follow the provided template
2. **Include Debug Info**: System and environment details
3. **Provide Steps**: How to reproduce the issue
4. **Include Logs**: Error messages and log files
5. **Be Specific**: Exact commands and error messages

### Community Support

- **GitHub Issues**: https://github.com/RhamaaCMS/RhamaaCLI/issues
- **Discussions**: https://github.com/RhamaaCMS/RhamaaCLI/discussions
- **Documentation**: Check this documentation thoroughly

## Prevention Tips

### Best Practices

1. **Use Virtual Environments**: Always use virtual environments
2. **Keep Updated**: Update Rhamaa CLI regularly
3. **Check Requirements**: Verify system requirements
4. **Backup Projects**: Backup before major changes
5. **Test First**: Test in development environment

### Regular Maintenance

```bash
# Update Rhamaa CLI
pip install --upgrade rhamaa

# Check for issues
   rhamaa --help
   rhamaa startapp --list

# Clean temporary files
rm -rf /tmp/rhamaa_*
```

If you continue to experience issues after trying these solutions, please create an issue on our [GitHub repository](https://github.com/RhamaaCMS/RhamaaCLI/issues) with detailed information about your problem.