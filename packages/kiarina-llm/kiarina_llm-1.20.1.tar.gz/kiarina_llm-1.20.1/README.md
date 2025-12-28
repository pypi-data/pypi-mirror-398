# kiarina-llm

A Python library for LLM utilities and context management with type safety and configuration management.

## Features

- **RunContext Management**: Structured context information for LLM pipeline processing
- **Type Safety**: Full type hints and Pydantic validation
- **Configuration Management**: Use `pydantic-settings-manager` for flexible configuration
- **Filesystem Safe Names**: Validated names for cross-platform compatibility
- **ID Validation**: Structured ID types with pattern validation

## Installation

```bash
pip install kiarina-llm
```

## Quick Start

### Basic RunContext Usage

```python
from kiarina.llm.run_context import create_run_context

# Create a run context with default settings
context = create_run_context(
    tenant_id="tenant-123",
    user_id="user-456",
    agent_id="my-agent",
    time_zone="Asia/Tokyo",
    language="ja",
    currency="JPY"
)

print(f"User: {context.user_id}")
print(f"Agent: {context.agent_id}")
print(f"Time Zone: {context.time_zone}")
print(f"Language: {context.language}")
print(f"Currency: {context.currency}")
```

### Configuration Management

```python
from kiarina.llm.run_context import settings_manager

# Configure default values
settings_manager.user_config = {
    "app_author": "MyCompany",
    "app_name": "MyAIApp",
    "tenant_id": "default-tenant",
    "user_id": "default-user",
    "time_zone": "America/New_York",
    "language": "en"
}

# Create context with configured defaults
context = create_run_context(
    agent_id="specialized-agent"  # Override only specific values
)
```

### Environment Variable Configuration

Configure defaults using environment variables:

```bash
export KIARINA_LLM_RUN_CONTEXT_APP_AUTHOR="MyCompany"
export KIARINA_LLM_RUN_CONTEXT_APP_NAME="MyAIApp"
export KIARINA_LLM_RUN_CONTEXT_TENANT_ID="prod-tenant"
export KIARINA_LLM_RUN_CONTEXT_TIME_ZONE="Asia/Tokyo"
export KIARINA_LLM_RUN_CONTEXT_LANGUAGE="ja"
```

## RunContext Fields

The `RunContext` model includes the following fields:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `app_author` | `FSName` | Application author (filesystem safe) | `"MyCompany"` |
| `app_name` | `FSName` | Application name (filesystem safe) | `"MyAIApp"` |
| `tenant_id` | `IDStr` | Tenant identifier | `"tenant-123"` |
| `user_id` | `IDStr` | User identifier | `"user-456"` |
| `agent_id` | `IDStr` | Agent identifier | `"my-agent"` |
| `runner_id` | `IDStr` | Runner identifier | `"linux"` (auto-detected) |
| `time_zone` | `str` | IANA time zone | `"Asia/Tokyo"` |
| `language` | `str` | ISO 639-1 language code | `"ja"` |
| `currency` | `str` | ISO 4217 currency code | `"USD"` |
| `metadata` | `dict[str, Any]` | Additional metadata | `{"version": "1.0"}` |

## Type Validation

### FSName (Filesystem Safe Name)

The `FSName` type ensures names are safe for use across different filesystems:

```python
from kiarina.llm.run_context import create_run_context

# Valid names
context = create_run_context(
    app_author="My Company",      # Spaces allowed
    app_name="My-App_v1.0"       # Hyphens, underscores, dots allowed
)

# Invalid names (will raise ValidationError)
try:
    create_run_context(app_author="My App.")  # Ends with dot
except ValueError as e:
    print(f"Validation error: {e}")

try:
    create_run_context(app_author=".hidden")  # Starts with dot
except ValueError as e:
    print(f"Validation error: {e}")

try:
    create_run_context(app_author="CON")  # Windows reserved name
except ValueError as e:
    print(f"Validation error: {e}")
```

### IDStr (ID String)

The `IDStr` type validates identifiers:

```python
# Valid IDs
context = create_run_context(
    tenant_id="tenant-123",
    user_id="user.456",
    agent_id="agent_v1.0"
)

# Invalid IDs (will raise ValidationError)
try:
    create_run_context(tenant_id="")  # Empty string
except ValueError as e:
    print(f"Validation error: {e}")

try:
    create_run_context(user_id="user@domain")  # Invalid character
except ValueError as e:
    print(f"Validation error: {e}")
```

## Advanced Usage

### Custom Metadata

```python
context = create_run_context(
    tenant_id="tenant-123",
    user_id="user-456",
    metadata={
        "session_id": "session-789",
        "request_id": "req-abc123",
        "version": "1.0.0",
        "features": ["feature-a", "feature-b"]
    }
)

print(f"Session: {context.metadata['session_id']}")
print(f"Features: {context.metadata['features']}")
```

### Integration with PlatformDirs

The `app_author` and `app_name` fields are designed to work with libraries like `platformdirs`:

```python
from platformdirs import user_data_dir
from kiarina.llm.run_context import create_run_context

context = create_run_context(
    app_author="MyCompany",
    app_name="MyAIApp"
)

# Use with platformdirs
data_dir = user_data_dir(
    appname=context.app_name,
    appauthor=context.app_author
)
print(f"Data directory: {data_dir}")
```

## Configuration Reference

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| `app_author` | `KIARINA_LLM_RUN_CONTEXT_APP_AUTHOR` | `"kiarina"` | Default application author |
| `app_name` | `KIARINA_LLM_RUN_CONTEXT_APP_NAME` | `"myaikit"` | Default application name |
| `tenant_id` | `KIARINA_LLM_RUN_CONTEXT_TENANT_ID` | `""` | Default tenant ID |
| `user_id` | `KIARINA_LLM_RUN_CONTEXT_USER_ID` | `""` | Default user ID |
| `agent_id` | `KIARINA_LLM_RUN_CONTEXT_AGENT_ID` | `""` | Default agent ID |
| `runner_id` | `KIARINA_LLM_RUN_CONTEXT_RUNNER_ID` | `platform.system().lower()` | Default runner ID |
| `time_zone` | `KIARINA_LLM_RUN_CONTEXT_TIME_ZONE` | `"UTC"` | Default time zone |
| `language` | `KIARINA_LLM_RUN_CONTEXT_LANGUAGE` | `"en"` | Default language |
| `currency` | `KIARINA_LLM_RUN_CONTEXT_CURRENCY` | `"USD"` | Default currency code |

## Development

### Prerequisites

- Python 3.12+

### Setup

```bash
# Clone the repository
git clone https://github.com/kiarina/kiarina-python.git
cd kiarina-python

# Setup development environment (installs tools, syncs dependencies, downloads test data)
mise run setup
```

### Running Tests

```bash
# Run format, lint, type checks and tests
mise run package kiarina-llm

# Coverage report
mise run package:test kiarina-llm --coverage

# Run specific tests
uv run --group test pytest packages/kiarina-llm/tests/run_context/
```

## Dependencies

- [pydantic](https://docs.pydantic.dev/) - Data validation using Python type hints
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) - Settings management
- [pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager) - Advanced settings management

## Roadmap

This package is in active development. Planned features include:

- **Chat Model Management**: Unified interface for different LLM providers
- **Agent Framework**: Tools for building LLM agents
- **Pipeline Management**: Workflow management for LLM processing
- **Memory Management**: Context and conversation memory handling
- **Tool Integration**: Framework for LLM tool calling

## License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.

## Contributing

This is a personal project, but contributions are welcome! Please feel free to submit issues or pull requests.

## Related Projects

- [kiarina-python](https://github.com/kiarina/kiarina-python) - The main monorepo containing this package
- [pydantic-settings-manager](https://github.com/kiarina/pydantic-settings-manager) - Configuration management library used by this package
