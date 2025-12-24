# Colab Client

A professional Python client for programmatically interacting with Google Colab. Execute code on Google Colab runtimes directly from your Python applications.

## Features

- OAuth2 authentication with automatic token refresh
- Server assignment management (CPU, GPU, TPU)
- Session and kernel management
- Code execution via WebSocket
- Keep-alive functionality to prevent timeout
- Type hints and modern Python practices
- CLI interface for quick operations

## Installation

First, install [uv](https://docs.astral.sh/uv/getting-started/installation/) if you haven't:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install from source:

```bash
git clone https://github.com/sachnun/colab-client.git
cd colab-client
uv sync
```

Then run:

```bash
uv run colab-client
```

## Quick Start

### As a Library

```python
from src import ColabClient, RuntimeVariant

with ColabClient() as client:
    client.login()
    client.get_or_create_server(variant=RuntimeVariant.DEFAULT)
    client.get_or_create_session()
    
    result = client.execute("print('Hello from Colab!')")
    print(result.stdout)
```

### Command Line

```
$ uv run colab-client --help
usage: colab-client [-h] [-v] [-c CODE]
                    [--variant {DEFAULT,STANDARD_GPU,PREMIUM_GPU,TPU,CASCADE_LAKE,SKYLAKE}]
                    [--unassign] [--list]

Python client for Google Colab

options:
  -h, --help            show this help message and exit
  -v, --verbose         Enable verbose logging
  -c CODE, --code CODE  Execute code and exit
  --variant {DEFAULT,STANDARD_GPU,PREMIUM_GPU,TPU,CASCADE_LAKE,SKYLAKE}
                        Runtime variant (default: DEFAULT)
  --unassign            Unassign current server and exit
  --list                List current assignments and exit
```

## Configuration

Configuration can be done via environment variables or programmatically:

### Environment Variables

| Variable | Description | Default |
|----------|-------------|--------|
| `COLAB_CLIENT_ID` | OAuth2 client ID | Built-in |
| `COLAB_CLIENT_SECRET` | OAuth2 client secret | Built-in |
| `COLAB_TOKEN_PATH` | Path to token cache | `~/.colab_token.json` |
| `OAUTHLIB_INSECURE_TRANSPORT` | Allow HTTP for OAuth (dev only) | `0` |

### Programmatic Configuration

```python
from src import ColabClient, Config

config = Config(
    http_timeout=60,
    execution_timeout=120,
    keep_alive_interval=30,
)

client = ColabClient(config)
```

## Runtime Variants

```python
from src import RuntimeVariant

client.get_or_create_server(variant=RuntimeVariant.DEFAULT)
client.get_or_create_server(variant=RuntimeVariant.STANDARD_GPU)
client.get_or_create_server(variant=RuntimeVariant.PREMIUM_GPU)
client.get_or_create_server(variant=RuntimeVariant.TPU)
```

## Execution Results

```python
result = client.execute(code)

print(result.stdout)
print(result.stderr)
print(result.result)
print(result.display_data)

if result.error:
    print(f"Error: {result.error.name}: {result.error.value}")

if result.success:
    print("Execution successful!")
```

## Keep-Alive

```python
client.start_keep_alive(interval=60)

client.stop_keep_alive()
```

## Error Handling

```python
from src import (
    ColabError,
    AuthenticationError,
    QuotaDeniedError,
    UsageQuotaExceededError,
    ExecutionTimeoutError,
)

try:
    client.assign_server(variant=RuntimeVariant.PREMIUM_GPU)
except QuotaDeniedError:
    print("GPU quota exceeded, falling back to CPU")
    client.assign_server(variant=RuntimeVariant.DEFAULT)
except UsageQuotaExceededError:
    print("Usage time exceeded")
```

## Development

```bash
git clone https://github.com/sachnun/colab-client.git
cd colab-client
uv sync --extra dev

uv run pytest

uv run ruff check src/
uv run mypy src/
```

## License

MIT License - see [LICENSE](LICENSE) for details.
