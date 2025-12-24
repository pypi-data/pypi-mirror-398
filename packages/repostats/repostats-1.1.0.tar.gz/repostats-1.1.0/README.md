# ⚡️ repostats

A CLI tool to fetch GitHub repository statistics.

## Installation

```bash
pip install repostats
```

## Usage

```bash
# Basic usage
repostats python/cpython

# With GitHub token for higher rate limits
export GITHUB_TOKEN=your_token_here
repostats python/cpython

# Or pass token directly
repostats python/cpython --token your_token_here
```

### Example output

```text
python/cpython statistics
-------------------------
Stars       : 58,000
Forks       : 29,000
Open issues : 992
Watchers    : 3,400
Language    : Python
Created     : 2007-02-20T00:00:00Z
Updated     : 2024-01-15T12:34:56Z
```

The command exits with code `1` when the GitHub API request fails (for example, when the repository is missing or you hit a rate limit), which makes it easy to integrate into scripts.

## Features

- Fetch repository statistics including stars, forks, issues, and more
- Support for GitHub API token authentication
- Clean, accessible output that works well in plain-text terminals
- Helpful error messages and non-zero exit codes on failure
- Cross-platform compatibility

## Development

```bash
# Clone the repository
git clone https://github.com/sahansera/repostats.git
cd repostats

# Create virtual environment
uv venv
source .venv/bin/activate

# Install in development mode
make install-dev

# Run tests
make test

# Format code
make format

# Type checking
make type-check

# See all available commands
make help
```

## License

MIT
