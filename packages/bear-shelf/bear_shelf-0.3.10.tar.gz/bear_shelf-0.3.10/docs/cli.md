# CLI Reference

The `bear-shelf` command provides several utilities for working with your project.

## Available Commands

### `version`
Display the current version of JSONL Database.

```bash
bear-shelf version
```

### `debug_info`
Show detailed environment and system information.

```bash
bear-shelf debug_info
```

Options:
- `--no-color, -n`: Disable colored output

### `bump`
Bump the project version and create a git tag.

```bash
bear-shelf bump <version_type>
```

Arguments:
- `version_type`: One of `patch`, `minor`, or `major`

Examples:
```bash
# Bump patch version (1.0.0 -> 1.0.1)
bear-shelf bump patch

# Bump minor version (1.0.1 -> 1.1.0)  
bear-shelf bump minor

# Bump major version (1.1.0 -> 2.0.0)
bear-shelf bump major
```



## Global Options

- `--version, -V`: Show version information and exit
- `--help`: Show help message and exit

