# JSONL Database

A JSON LOG based database that attempts to establish a more lightweight database that is meant to be used for small scale settings/info for smaller apps.

## Installation

```bash
pip install bear-shelf
```

## Quick Start

After installation, you can use the CLI:

```bash
bear-shelf --help
```

### Available Commands

```bash
# Get version information
bear-shelf version

# Show debug information
bear-shelf debug_info

# Version management
bear-shelf bump patch|minor|major

```


## Development

Clone the repository and install dependencies:

```bash
git clone <your-repo-url>
cd bear-shelf
uv sync
```

Run tests:

```bash
nox -s tests
```

## License

This project is licensed under the  License.