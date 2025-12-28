# kiarina-lib-anthropic

A Python library for Anthropic API integration with configuration management using pydantic-settings-manager.

## Features

- **Configuration Management**: Use `pydantic-settings-manager` for flexible configuration
- **Type Safety**: Full type hints and Pydantic validation
- **Secure Credential Handling**: API keys are protected using `SecretStr`
- **Multiple Configurations**: Support for multiple named configurations (e.g., different projects/environments)
- **Environment Variable Support**: Configure via environment variables with `KIARINA_LIB_ANTHROPIC_` prefix
- **Custom Base URL**: Support for custom Anthropic-compatible API endpoints

## Installation

```bash
pip install kiarina-lib-anthropic
```

## Quick Start

### Basic Usage

```python
from kiarina.lib.anthropic import AnthropicSettings, settings_manager

# Configure Anthropic API
settings_manager.user_config = {
    "default": {
        "api_key": "sk-ant-your-api-key-here"
    }
}

# Get settings
settings = settings_manager.settings
print(f"API Key configured: {settings.api_key.get_secret_value()[:10]}...")
```

### Environment Variable Configuration

Configure authentication using environment variables:

```bash
export KIARINA_LIB_ANTHROPIC_API_KEY="sk-ant-your-api-key-here"
```

```python
from kiarina.lib.anthropic import settings_manager

# Settings are automatically loaded from environment variables
settings = settings_manager.settings
print(f"API Key configured: {settings.api_key.get_secret_value()[:10]}...")
```

### Multiple Configurations

Manage multiple Anthropic configurations (e.g., different projects or environments):

```python
from kiarina.lib.anthropic import settings_manager

# Configure multiple projects
settings_manager.user_config = {
    "project_a": {
        "api_key": "sk-ant-project-a-key"
    },
    "project_b": {
        "api_key": "sk-ant-project-b-key"
    }
}

# Switch between configurations
settings_manager.active_key = "project_a"
project_a_settings = settings_manager.settings
print(f"Project A API Key: {project_a_settings.api_key.get_secret_value()[:10]}...")

settings_manager.active_key = "project_b"
project_b_settings = settings_manager.settings
print(f"Project B API Key: {project_b_settings.api_key.get_secret_value()[:10]}...")
```

### Custom Base URL

Use with Anthropic-compatible APIs:

```python
from kiarina.lib.anthropic import settings_manager

settings_manager.user_config = {
    "custom": {
        "api_key": "your-custom-key",
        "base_url": "https://custom.anthropic-compatible.api.com"
    }
}

settings = settings_manager.settings
print(f"Base URL: {settings.base_url}")
```

## Configuration

This library uses [pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager) for flexible configuration management.

### AnthropicSettings

The `AnthropicSettings` class provides the following configuration fields:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `api_key` | `SecretStr` | Yes | - | Anthropic API key (masked in logs) |
| `base_url` | `str \| None` | No | `None` | Custom base URL for Anthropic-compatible APIs |

### Environment Variables

All settings can be configured via environment variables with the `KIARINA_LIB_ANTHROPIC_` prefix:

```bash
# API Key (required)
export KIARINA_LIB_ANTHROPIC_API_KEY="sk-ant-your-api-key"

# Custom Base URL (optional)
export KIARINA_LIB_ANTHROPIC_BASE_URL="https://api.anthropic.com"
```

### Programmatic Configuration

```python
from pydantic import SecretStr
from kiarina.lib.anthropic import AnthropicSettings, settings_manager

# Direct settings object
settings = AnthropicSettings(
    api_key=SecretStr("sk-ant-your-api-key")
)

# Via settings manager
settings_manager.user_config = {
    "default": {
        "api_key": "sk-ant-your-api-key"  # Automatically converted to SecretStr
    }
}
```

### Runtime Overrides

```python
from kiarina.lib.anthropic import settings_manager

# Override specific settings at runtime
settings_manager.cli_args = {
    "base_url": "https://custom.api.com"
}

settings = settings_manager.settings
print(f"Base URL: {settings.base_url}")  # Uses overridden value
```

## Security

### API Key Protection

API keys are stored using Pydantic's `SecretStr` type, which provides the following security benefits:

- **Masked in logs**: Keys are displayed as `**********` in string representations
- **Prevents accidental exposure**: Keys won't appear in debug output or error messages
- **Explicit access required**: Must use `.get_secret_value()` to access the actual key

```python
from kiarina.lib.anthropic import settings_manager

settings = settings_manager.settings

# API key is masked in string representation
print(settings)  # api_key=SecretStr('**********')

# Explicit access to get the actual key
api_key = settings.api_key.get_secret_value()
```

## API Reference

### AnthropicSettings

```python
class AnthropicSettings(BaseSettings):
    api_key: SecretStr
    base_url: str | None = None
```

Pydantic settings model for Anthropic API configuration.

**Fields:**
- `api_key` (SecretStr): Anthropic API key (protected)
- `base_url` (str | None): Optional custom base URL for Anthropic-compatible APIs

### settings_manager

```python
settings_manager: SettingsManager[AnthropicSettings]
```

Global settings manager instance for Anthropic configuration.
See: [pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager)

## Development

### Prerequisites

- Python 3.12+

### Setup

```bash
# Clone the repository
git clone https://github.com/kiarina/kiarina-python.git
cd kiarina-python

# Setup development environment
mise run setup
```

### Running Tests

```bash
# Run format, lint, type checks and tests
mise run package kiarina-lib-anthropic

# Coverage report
mise run package:test kiarina-lib-anthropic --coverage
```

## Dependencies

- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) - Settings management
- [pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager) - Advanced settings management

## License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.

## Contributing

This is a personal project, but contributions are welcome! Please feel free to submit issues or pull requests.

## Related Projects

- [kiarina-python](https://github.com/kiarina/kiarina-python) - The main monorepo containing this package
- [pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager) - Configuration management library used by this package
- [kiarina-lib-openai](https://github.com/kiarina/kiarina-python/tree/main/packages/kiarina-lib-openai) - Similar library for OpenAI API
