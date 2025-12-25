# pyWATS Client - Headless Operation Guide

This guide covers running pyWATS Client without a GUI on headless systems like:
- Raspberry Pi
- Linux servers
- Embedded systems
- Docker containers

## Installation

### Option 1: Headless Only (No Qt/GUI)
```bash
pip install pywats-api[client-headless]
```

### Option 2: Full Installation (with GUI)
```bash
pip install pywats-api[client]
```

## Quick Start

### 1. Initialize Configuration
```bash
# Interactive setup
pywats-client config init

# Or non-interactive
pywats-client config init \
    --server-url https://wats.example.com \
    --api-token YOUR_TOKEN \
    --station-name RASPBERRY-PI-01 \
    --non-interactive
```

### 2. Test Connection
```bash
pywats-client test-connection
```

### 3. Start Service
```bash
# Foreground (for testing)
pywats-client start

# With HTTP API for remote management
pywats-client start --api --api-port 8765

# As daemon (background, Unix only)
pywats-client start --daemon
```

## CLI Commands

### Configuration Management
```bash
# Show all configuration
pywats-client config show

# Show as JSON (for scripting)
pywats-client config show --format json

# Show as environment variables
pywats-client config show --format env

# Get specific value
pywats-client config get server_url

# Set value
pywats-client config set station_name MY-STATION
pywats-client config set log_level DEBUG
```

### Service Control
```bash
# Show status
pywats-client status

# Start service
pywats-client start

# Start with options
pywats-client start --api --api-port 8080

# Stop daemon
pywats-client stop
```

### Converter Management
```bash
# List converters
pywats-client converters list

# Enable/disable converter
pywats-client converters enable my_converter
pywats-client converters disable my_converter
```

## HTTP Control API

When started with `--api`, the service exposes a REST API for remote management.

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info and available endpoints |
| GET | `/health` | Health check |
| GET | `/status` | Service status |
| GET | `/config` | Get configuration |
| POST | `/config` | Update configuration |
| GET | `/converters` | List converters |
| GET | `/queue` | Queue status |
| POST | `/queue/process` | Trigger queue processing |
| POST | `/start` | Start services |
| POST | `/stop` | Stop services |
| POST | `/restart` | Restart services |

### Examples

```bash
# Health check
curl http://localhost:8765/health

# Get status
curl http://localhost:8765/status

# Get configuration
curl http://localhost:8765/config

# Update configuration
curl -X POST http://localhost:8765/config \
    -H "Content-Type: application/json" \
    -d '{"station_name": "NEW-STATION"}'
```

### Security

By default, the API only binds to localhost (127.0.0.1). For remote access:

1. **Use a reverse proxy** (recommended):
   ```nginx
   location /pywats/ {
       proxy_pass http://127.0.0.1:8765/;
       auth_basic "pyWATS API";
       auth_basic_user_file /etc/nginx/.htpasswd;
   }
   ```

2. **Or bind to all interfaces** (less secure):
   ```bash
   pywats-client start --api --api-host 0.0.0.0
   ```

## Systemd Service (Linux)

### Installation

1. Copy the service file:
   ```bash
   sudo cp pywats-client.service /etc/systemd/system/
   ```

2. Edit the configuration:
   ```bash
   sudo nano /etc/systemd/system/pywats-client.service
   ```
   
   Update:
   - `User` and `Group`
   - `WorkingDirectory`
   - `ExecStart` path to your Python environment

3. Enable and start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable pywats-client
   sudo systemctl start pywats-client
   ```

### Management

```bash
# Check status
sudo systemctl status pywats-client

# View logs
journalctl -u pywats-client -f

# Restart service
sudo systemctl restart pywats-client

# Stop service
sudo systemctl stop pywats-client
```

## Raspberry Pi Setup

### Prerequisites
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3 python3-pip python3-venv -y
```

### Installation
```bash
# Create project directory
mkdir ~/pywats && cd ~/pywats

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install pyWATS (headless)
pip install pywats-api[client-headless]

# Initialize configuration
pywats-client config init
```

### Auto-start on Boot
```bash
# Install systemd service
sudo cp /path/to/pywats-client.service /etc/systemd/system/
sudo nano /etc/systemd/system/pywats-client.service  # Edit paths
sudo systemctl daemon-reload
sudo systemctl enable pywats-client
sudo systemctl start pywats-client
```

## Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install headless client
RUN pip install pywats-api[client-headless]

# Copy configuration (or mount as volume)
COPY config.json /root/.pywats_client/config.json

# Start with API
CMD ["pywats-client", "start", "--api", "--api-host", "0.0.0.0"]
```

Build and run:
```bash
docker build -t pywats-client .
docker run -d -p 8765:8765 -v $(pwd)/config:/root/.pywats_client pywats-client
```

## Environment Variables

Configuration can also be set via environment variables:

```bash
export PYWATS_SERVICE_ADDRESS=https://wats.example.com
export PYWATS_API_TOKEN=your-token
export PYWATS_STATION_NAME=MY-STATION
export PYWATS_LOG_LEVEL=DEBUG
```

## Troubleshooting

### Common Issues

1. **"No module named 'PySide6'"** when running without `--no-gui`:
   - Install full client: `pip install pywats-api[client]`
   - Or use headless mode: `pywats-client start` (uses CLI, no GUI)

2. **Connection refused**:
   - Check server URL: `pywats-client config get server_url`
   - Test connection: `pywats-client test-connection`

3. **Permission denied** (Linux):
   - Check file permissions
   - Ensure service user has access to config directory

4. **Service won't start**:
   - Check logs: `journalctl -u pywats-client -n 50`
   - Run manually first: `pywats-client start`

### Debug Mode
```bash
# Set debug logging
pywats-client config set log_level DEBUG

# Run in foreground to see logs
pywats-client start
```
