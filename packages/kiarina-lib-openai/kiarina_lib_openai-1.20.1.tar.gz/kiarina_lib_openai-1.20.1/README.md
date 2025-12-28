# kiarina-lib-openai

A Python library for OpenAI API integration with configuration management using pydantic-settings-manager.

## Features

- **Configuration Management**: Use `pydantic-settings-manager` for flexible configuration
- **Type Safety**: Full type hints and Pydantic validation
- **Secure Credential Handling**: API keys are protected using `SecretStr`
- **Multiple Configurations**: Support for multiple named configurations (e.g., different projects/environments)
- **Environment Variable Support**: Configure via environment variables with `KIARINA_LIB_OPENAI_` prefix
- **Custom Base URL**: Support for custom OpenAI-compatible API endpoints

## Installation

```bash
pip install kiarina-lib-openai
```

## Quick Start

### Basic Usage

```python
from kiarina.lib.openai import OpenAISettings, settings_manager

# Configure OpenAI API
settings_manager.user_config = {
    "default": {
        "api_key": "sk-your-api-key-here"
    }
}

# Get settings
settings = settings_manager.settings
print(f"API Key configured: {settings.api_key.get_secret_value()[:10]}...")
```

### Environment Variable Configuration

Configure authentication using environment variables:

```bash
export KIARINA_LIB_OPENAI_API_KEY="sk-your-api-key-here"
export KIARINA_LIB_OPENAI_ORGANIZATION_ID="org-your-org-id"  # Optional
```

```python
from kiarina.lib.openai import settings_manager

# Settings are automatically loaded from environment variables
settings = settings_manager.settings
print(f"API Key configured: {settings.api_key.get_secret_value()[:10]}...")
```

### Multiple Configurations

Manage multiple OpenAI configurations (e.g., different projects or environments):

```python
from kiarina.lib.openai import settings_manager

# Configure multiple projects
settings_manager.user_config = {
    "project_a": {
        "api_key": "sk-project-a-key",
        "organization_id": "org-project-a"
    },
    "project_b": {
        "api_key": "sk-project-b-key",
        "organization_id": "org-project-b"
    }
}

# Switch between configurations
settings_manager.active_key = "project_a"
project_a_settings = settings_manager.settings
print(f"Project A Org: {project_a_settings.organization_id}")

settings_manager.active_key = "project_b"
project_b_settings = settings_manager.settings
print(f"Project B Org: {project_b_settings.organization_id}")
```

### Custom Base URL

Use with OpenAI-compatible APIs (e.g., Azure OpenAI, local models):

```python
from kiarina.lib.openai import settings_manager

settings_manager.user_config = {
    "azure": {
        "api_key": "your-azure-key",
        "base_url": "https://your-resource.openai.azure.com/openai/deployments/your-deployment"
    }
}

settings = settings_manager.settings
print(f"Base URL: {settings.base_url}")
```

## Configuration

This library uses [pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager) for flexible configuration management.

### OpenAISettings

The `OpenAISettings` class provides the following configuration fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `api_key` | `SecretStr` | Yes | OpenAI API key (masked in logs) |
| `organization_id` | `str \| None` | No | OpenAI organization ID |
| `base_url` | `str \| None` | No | Custom base URL for OpenAI-compatible APIs |

### Environment Variables

All settings can be configured via environment variables with the `KIARINA_LIB_OPENAI_` prefix:

```bash
# API Key (required)
export KIARINA_LIB_OPENAI_API_KEY="sk-your-api-key"

# Organization ID (optional)
export KIARINA_LIB_OPENAI_ORGANIZATION_ID="org-your-org-id"

# Custom Base URL (optional)
export KIARINA_LIB_OPENAI_BASE_URL="https://api.openai.com/v1"
```

### Programmatic Configuration

```python
from pydantic import SecretStr
from kiarina.lib.openai import OpenAISettings, settings_manager

# Direct settings object
settings = OpenAISettings(
    api_key=SecretStr("sk-your-api-key"),
    organization_id="org-your-org-id"
)

# Via settings manager
settings_manager.user_config = {
    "default": {
        "api_key": "sk-your-api-key",  # Automatically converted to SecretStr
        "organization_id": "org-your-org-id"
    }
}
```

### Runtime Overrides

```python
from kiarina.lib.openai import settings_manager

# Override specific settings at runtime
settings_manager.cli_args = {
    "organization_id": "org-override-id"
}

settings = settings_manager.settings
print(f"Organization ID: {settings.organization_id}")  # Uses overridden value
```

## Security

### API Key Protection

API keys are stored using Pydantic's `SecretStr` type, which provides the following security benefits:

- **Masked in logs**: Keys are displayed as `**********` in string representations
- **Prevents accidental exposure**: Keys won't appear in debug output or error messages
- **Explicit access required**: Must use `.get_secret_value()` to access the actual key

```python
from kiarina.lib.openai import settings_manager

settings = settings_manager.settings

# API key is masked in string representation
print(settings)  # api_key=SecretStr('**********')

# Explicit access to get the actual key
api_key = settings.api_key.get_secret_value()
```

## API Reference

### OpenAISettings

```python
class OpenAISettings(BaseSettings):
    api_key: SecretStr
    organization_id: str | None = None
    base_url: str | None = None
```

Pydantic settings model for OpenAI API configuration.

**Fields:**
- `api_key` (SecretStr): OpenAI API key (protected)
- `organization_id` (str | None): Optional organization ID
- `base_url` (str | None): Optional custom base URL for OpenAI-compatible APIs

### settings_manager

```python
settings_manager: SettingsManager[OpenAISettings]
```

Global settings manager instance for OpenAI configuration.
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
mise run package kiarina-lib-openai

# Coverage report
mise run package:test kiarina-lib-openai --coverage
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
