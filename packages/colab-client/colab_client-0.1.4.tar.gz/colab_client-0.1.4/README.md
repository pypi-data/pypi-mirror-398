# Colab Client

> **Note:** This is an unofficial client and is not affiliated with Google. Use at your own risk.

Python client for Google Colab. Execute code on Colab runtimes from your terminal or Python scripts.

## Installation

Install [uv](https://docs.astral.sh/uv/getting-started/installation/):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Clone and run:

```bash
git clone https://github.com/sachnun/colab-client.git
cd colab-client
uv sync
uv run colab-client
```

## Usage

### Command Line

```
$ uv run colab-client --help
usage: colab-client [-h] [-v] [-c CODE]
                    [--variant {DEFAULT,STANDARD_GPU,PREMIUM_GPU,TPU,CASCADE_LAKE,SKYLAKE}]
                    [--unassign] [--list]
                    {auth} ...

positional arguments:
  {auth}
    auth                Authentication commands

options:
  -h, --help            show this help message and exit
  -v, --verbose         Enable verbose logging
  -c CODE, --code CODE  Execute code and exit
  --variant             Runtime variant (default: DEFAULT)
  --unassign            Unassign current server and exit
  --list                List current assignments and exit
```

### As a Library

```bash
uv add colab-client
```

```python
from colab_client import ColabClient

client = ColabClient()
client.login()
client.connect()
client.open_session()

result = client.execute("print('Hello from Colab!')")
print(result.stdout)

client.close()
```

## Configuration

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `COLAB_TOKEN_PATH` | Path to token cache | `~/.colab_token.json` |

## License

MIT License - see [LICENSE](LICENSE) for details.
