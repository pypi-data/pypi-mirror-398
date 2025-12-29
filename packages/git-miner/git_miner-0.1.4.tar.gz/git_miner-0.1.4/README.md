# Git Miner

Search GitHub repositories and export their data to CSV, JSON, or Parquet.

## Installation

```bash
pip install git-miner
```

## Quick Start

Search and export repositories:

```bash
git-miner search "python web framework" --language python --min-stars 1000
```

Add your GitHub token for higher rate limits:

```bash
export GITHUB_TOKEN=your_token
git-miner search "data science" --format json
```

## Use Cases

- **Research**: Study open-source trends, language adoption, repository patterns
- **Data Science**: Build datasets for ML model training on code repositories
- **Academic**: Analyze collaboration patterns, project lifecycles
- **Analytics**: Track repository growth, contributor engagement
- **Tooling**: Find repositories matching specific criteria for automation
- **Market Research**: Identify popular libraries and frameworks

## Commands

### Search

```bash
git-miner search QUERY [OPTIONS]
```

**Filters:**
- `--language, -l`: Programming language
- `--min-stars / --max-stars`: Star count range
- `--min-forks / --max-forks`: Fork count range
- `--license`: License type (e.g., mit, apache-2.0)
- `--topics`: Topics to include (comma-separated)
- `--fork / --no-fork`: Include or exclude forks
- `--archived / --no-archived`: Include or exclude archived repos
- `--sort`: Sort by stars, forks, or updated
- `--max-results`: Limit number of results

**Output:**
- `--format, -f`: csv, json, or parquet
- `--output-dir, -o`: Output directory

**Examples:**

```bash
# Python repos with 1000+ stars
git-miner search "web framework" --language python --min-stars 1000

# MIT-licensed repos
git-miner search "data science" --license mit

# Exclude forks and archived
git-miner search "api" --no-fork --no-archived

# Top 50 by stars, export to Parquet
git-miner search "machine learning" --sort stars --max-results 50 --format parquet
```

### Extract

Get detailed stats for repositories:

```bash
git-miner extract owner/repo
```

**Options:**
- `--activity / --no-activity`: Include commit/issue/PR stats
- `--contributors / --no-contributors`: Include contributor stats

## Output Formats

| Format | Best For |
|--------|-----------|
| CSV | Excel, traditional tools |
| JSON | Web apps, APIs |
| Parquet | Big data, analytics |

## Configuration

Create `gitminer.toml`:

```toml
[github]
token = "your_token"

[output]
dir = "./datasets"
format = "parquet"

[api]
max_retries = 3
timeout = 30.0
```

Use it:

```bash
git-miner --config gitminer.toml search "web framework"
```

## Rate Limits

- **No token**: 60 requests/hour
- **With token**: 5,000 requests/hour

The tool respects rate limits automatically.

## Dataset Fields

**Repository Metadata:**
- repository_id, name, owner, description
- primary_language, stars, forks, open_issues
- license, created_at, updated_at, pushed_at
- size_kb, url, is_fork, is_archived, topics

**Activity Statistics:**
- commit_total, commit_additions, commit_deletions
- issues_open, issues_closed, prs_open, prs_closed, prs_merged

## Coming Soon

- Direct code extraction from repositories into datasets
- GraphQL API support
- Incremental dataset updates
- Pre-built public datasets
- Plugin-based extractor system
- Cloud storage outputs (S3, GCS)

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint and format
make lint
make format
```

## License

Apache License 2.0
