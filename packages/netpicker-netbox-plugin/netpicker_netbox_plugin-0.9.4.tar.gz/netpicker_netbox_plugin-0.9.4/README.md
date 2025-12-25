# Support & Community
If you need help, Join our Discord server: https://discord.com/invite/utv9qWsnRY
or e-mail us on: support@netpicker.io

# NetBox Automation & Config Backup Plugin
[Netbox](https://github.com/netbox-community/netbox) plugin to automatically Automate & Backup your Network with [Netpicker](https://netpicker.io).

## Compatibility

| NetBox Version | Plugin Version |
|----------------|----------------|
|   NetBox 4.3   |    >= 0.8.x    |
|   NetBox 4.4   |    >= 0.9.x    |

## Features

- **Netpicker Configuration View**: Integrated interface for managing Netpicker configurations within Netbox
- **Simple Automation**: Streamlined automation workflows for network operations

## Installation

### Option 1: PyPI Installation

The plugin is available as a Python package on PyPI and can be installed with pip:

```bash
# Activate your Netbox virtual environment
source /opt/netbox/venv/bin/activate

# Install the plugin
pip install --no-cache-dir netpicker-netbox-plugin
```

### Option 2: Development Installation

For development or custom modifications:

```bash
# Clone the repository
git clone <repository-url>
cd netpicker-netbox-plugin

# Install dependencies
poetry install

# Install in development mode
poetry run pip install -e .
```

## Configuration

### 1. Add to Netbox Configuration

Add the plugin to your `netbox.conf.py` or environment variables:

```python
PLUGINS = [
    'netpicker',
]
```

### 2. Run Database Migrations

```bash
python manage.py migrate
```

### 3. Create Super User (if needed)

```bash
python manage.py createsuperuser
```

### 4. Restart Netbox

Restart your Netbox service to load the plugin:

```bash
# If using systemd
sudo systemctl restart netbox

# If using Docker
docker compose restart netbox
```

## Docker Deployment

The project includes Docker support for easy deployment:

```bash
# Start all services
docker compose up -d --build

# View logs
docker compose logs -f netbox

# Stop services
docker compose down
```

The Docker setup includes:
- Netbox application
- Netbox worker for background tasks
- Netbox housekeeping
- PostgreSQL database
- Redis for caching and sessions

## Usage

Once installed and configured, the Netpicker plugin will be available in your Netbox interface:

1. Navigate to the Netpicker section in the Netbox navigation
2. Access configuration views and automation tools
3. Use the API endpoints for programmatic access

## API Endpoints

The plugin provides REST API endpoints accessible at `/api/plugins/netpicker/`.

## Development

For development information, see [DEVELOPMENT.md](DEVELOPMENT.md).

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions:
- Create an issue in the repository
- Contact the maintainers
- Send an email to support@netpicker.io