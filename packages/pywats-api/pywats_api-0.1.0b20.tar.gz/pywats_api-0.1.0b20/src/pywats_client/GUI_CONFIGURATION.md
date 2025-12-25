# PyWATS Client GUI Configuration

This document explains how to configure the PyWATS Client GUI, including tab visibility and logging integration.

## Table of Contents
- [GUI Tab Visibility](#gui-tab-visibility)
- [Logging Configuration](#logging-configuration)
- [Configuration File](#configuration-file)
- [Examples](#examples)

## GUI Tab Visibility

The PyWATS Client GUI supports modular tab configuration, allowing you to show or hide specific tabs based on your needs.

### Available Tabs

The following tabs can be configured:

| Tab | Config Key | Default | Description |
|-----|-----------|---------|-------------|
| Setup | (always shown) | ✓ | Initial setup and connection management |
| General | (always shown) | ✓ | General settings and tab visibility control |
| Connection | (always shown) | ✓ | Connection status and controls |
| Location | `show_location_tab` | ✓ | Station location configuration |
| Converters | `show_converters_tab` | ✓ | Report converter management |
| SN Handler | `show_sn_handler_tab` | ✓ | Serial number handler settings |
| Proxy Settings | `show_proxy_tab` | ✓ | Network proxy configuration |
| Software | `show_software_tab` | ✓ | Software distribution settings |

### Configuring Tab Visibility

#### Option 1: Using the GUI

1. Launch the PyWATS Client
2. Navigate to **General** → **GUI Tab Visibility**
3. Check/uncheck the tabs you want to show/hide
4. Click **Save**
5. **Restart the application** for changes to take effect

#### Option 2: Editing Configuration File

Edit your configuration file (typically at `%APPDATA%/pyWATS_Client/config.json`):

```json
{
  "show_location_tab": true,
  "show_converters_tab": true,
  "show_sn_handler_tab": false,
  "show_proxy_tab": true,
  "show_software_tab": false
}
```

Save and restart the application.

## Logging Configuration

The PyWATS Client integrates with the PyWATS library logging system, providing comprehensive debugging capabilities.

### Log Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| DEBUG | Detailed diagnostic info | Development, troubleshooting |
| INFO | General informational messages | Normal operation monitoring |
| WARNING | Warning messages | Potential issues |
| ERROR | Error messages only | Production, minimal logging |

### Setting Log Level

#### Option 1: Using the GUI

1. Navigate to **General** → **Logging**
2. Select desired log level from dropdown
3. Click **Save**
4. Restart application (or logs will use new level for new operations)

#### Option 2: Configuration File

```json
{
  "log_level": "DEBUG"
}
```

### PyWATS Library Logging Integration

When the client's log level is set to **DEBUG**, it automatically enables debug logging for the underlying PyWATS library. This provides detailed insights into:

- HTTP requests and responses
- API calls to the WATS server
- Data serialization/deserialization
- Error handling and retries
- Repository and service layer operations

### Log File Location

Logs are written to:
- **Windows**: `%APPDATA%/pyWATS_Client/pywats_client.log`
- **Linux/Mac**: `~/.config/pywats_client/pywats_client.log`

### Example Log Output (DEBUG level)

```
2025-12-12 14:30:15,123 - pywats_client.core.client - INFO - Initializing PyWATS Client (instance: ABC123)
2025-12-12 14:30:15,125 - pywats_client.core.client - DEBUG - PyWATS library debug logging enabled
2025-12-12 14:30:15,234 - pywats.http_client - INFO - Initializing HttpClient for https://wats.example.com
2025-12-12 14:30:15,345 - pywats.http_client - DEBUG - GET https://wats.example.com/api/Product/1234
2025-12-12 14:30:15,456 - pywats.http_client - DEBUG - Response: 200 OK (1234 bytes)
2025-12-12 14:30:15,567 - pywats.domains.product.repository - DEBUG - Retrieved product: TestProduct (ID: 1234)
```

## Configuration File

### Full Configuration Example

```json
{
  "instance_id": "abc123",
  "instance_name": "Production Test Station",
  "service_address": "https://wats.example.com",
  "api_token": "your-token-here",
  
  "log_level": "INFO",
  "log_file": "pywats_client.log",
  
  "show_location_tab": true,
  "show_converters_tab": true,
  "show_sn_handler_tab": false,
  "show_proxy_tab": false,
  "show_software_tab": true,
  
  "start_minimized": false,
  "minimize_to_tray": true,
  "auto_connect": true
}
```

### Configuration Location

- **Windows**: `%APPDATA%\pyWATS_Client\config.json`
- **Linux**: `~/.config/pywats_client/config.json`
- **Mac**: `~/.config/pywats_client/config.json`

Multiple instances can be run by using different configuration files:
```
config.json          # Default instance
config_station1.json # Station 1
config_station2.json # Station 2
```

## Examples

### Minimal Configuration (Essential tabs only)

For a simple test station that only needs basic functionality:

```json
{
  "show_location_tab": false,
  "show_converters_tab": false,
  "show_sn_handler_tab": false,
  "show_proxy_tab": false,
  "show_software_tab": false
}
```

This shows only: Setup, General, Connection

### Production Line Station

For a production line with converters and serial number handling:

```json
{
  "show_location_tab": true,
  "show_converters_tab": true,
  "show_sn_handler_tab": true,
  "show_proxy_tab": false,
  "show_software_tab": true,
  "log_level": "INFO"
}
```

### Development/Debug Station

For development with full logging:

```json
{
  "show_location_tab": true,
  "show_converters_tab": true,
  "show_sn_handler_tab": true,
  "show_proxy_tab": true,
  "show_software_tab": true,
  "log_level": "DEBUG"
}
```

### Corporate Environment (Behind Proxy)

For stations behind corporate proxy:

```json
{
  "show_location_tab": true,
  "show_converters_tab": true,
  "show_sn_handler_tab": false,
  "show_proxy_tab": true,
  "show_software_tab": false,
  "log_level": "WARNING"
}
```

## Best Practices

### Tab Visibility
- **Show only needed tabs**: Reduces UI complexity for operators
- **Hide unused features**: Prevents confusion and accidental misconfiguration
- **Consider operator skill level**: Simpler UI for less technical users

### Logging
- **Production**: Use INFO or WARNING level to minimize log size
- **Development**: Use DEBUG level for detailed diagnostics
- **Troubleshooting**: Temporarily switch to DEBUG, then back to INFO
- **Monitor log file size**: DEBUG logging can generate large files

### Configuration Management
- **Version control**: Store sanitized config templates in version control
- **Remove sensitive data**: Never commit API tokens or passwords
- **Document customizations**: Note why certain tabs are hidden
- **Test changes**: Verify configuration in test environment first

## Troubleshooting

### Tabs Not Appearing After Configuration Change

**Problem**: Changed tab visibility settings, but tabs still show/hide incorrectly.

**Solution**: Restart the PyWATS Client application. Tab visibility is read at startup.

### Logs Too Verbose

**Problem**: Log file growing too large with DEBUG level.

**Solution**: Change `log_level` to `"INFO"` or `"WARNING"` in configuration.

### PyWATS Library Not Logging

**Problem**: Client logs work, but no PyWATS library logs appear.

**Solution**: Ensure log level is set to `"DEBUG"`. Library logging is only enabled at DEBUG level.

### Configuration Changes Not Saving

**Problem**: GUI changes don't persist after restart.

**Solution**: 
1. Check file permissions on configuration file
2. Verify path in logs: "Configuration saved to: ..."
3. Ensure application has write access to config directory

## Related Documentation

- [PyWATS Library Logging Strategy](../../LOGGING_STRATEGY.md)
- [Architecture Documentation](../../docs/ARCHITECTURE.md)
- [Client README](README.md)
