# Installation Guide

## Requirements

- Python 3.9 or higher
- pip or pipx

## Installation Methods

### Using pip (Recommended for users)

```bash
pip install dremio-cli
```

### Using pipx (Isolated environment)

```bash
pipx install dremio-cli
```

### From Source (For developers)

```bash
git clone https://github.com/your-org/dremio-cli
cd dremio-cli
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/your-org/dremio-cli
cd dremio-cli
pip install -e ".[dev]"
```

## Verify Installation

```bash
dremio --version
```

## Next Steps

See the [Quick Start Guide](quickstart.md) to configure your first profile and start using the CLI.
