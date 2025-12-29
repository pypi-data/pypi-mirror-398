import asyncio
from importlib.metadata import version as get_version
from pathlib import Path
from typing import Any, Literal

import typer

from .api.client import GitHubAPIClient
from .config import Config
from .datasets.builder import DatasetBuilder
from .datasets.export import DatasetExporter
from .search.query import SearchOptions, SearchQueryBuilder
from .token_cache import TokenCache

PACKAGE_VERSION = get_version("git-miner")

app = typer.Typer(
    name="git-miner",
    help="Mine GitHub repository metadata and activity data",
    no_args_is_help=True,
    add_completion=False,
)


@app.command()
def version():
    """Show version."""
    typer.echo(f"git-miner {PACKAGE_VERSION}")

state: dict[str, Any] = {
    "token": None,
    "config": None,
    "output_dir": None,
    "format": None,
}


def get_client() -> GitHubAPIClient:
    """Get configured API client."""
    config = state["config"]
    token = state["token"] or (config.github_token if config else None)

    if not token:
        cache = TokenCache()
        token = cache.get_token("default")

    return GitHubAPIClient(token=token)


@app.callback()
def main(
    token: str | None = typer.Option(
        None, "--token", "-t", envvar="GITHUB_TOKEN", help="GitHub API token"
    ),
    config: str | None = typer.Option(None, "--config", "-c", help="Path to config file"),
    output_dir: str | None = typer.Option(None, "--output-dir", "-o", help="Output directory"),
    format: Literal["csv", "json", "parquet"] | None = typer.Option(
        None, "--format", "-f", help="Export format (csv, json, parquet)"
    ),
):
    """Git Miner - Mine GitHub repository metadata and activity data."""
    state["token"] = token

    if config and isinstance(config, (str, Path)):
        state["config"] = Config(config)
        if not output_dir and state["config"]:
            output_dir = state["config"].output_dir
        if not format and state["config"]:
            format = state["config"].default_format

    if output_dir and isinstance(output_dir, (str, Path)):
        state["output_dir"] = Path(output_dir)
    else:
        state["output_dir"] = Path(".")

    state["format"] = format if format and isinstance(format, str) else None


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    language: str | None = typer.Option(
        None, "--language", "-l", help="Filter by programming language"
    ),
    min_stars: int | None = typer.Option(None, "--min-stars", help="Minimum star count"),
    max_stars: int | None = typer.Option(None, "--max-stars", help="Maximum star count"),
    min_forks: int | None = typer.Option(None, "--min-forks", help="Minimum fork count"),
    max_forks: int | None = typer.Option(None, "--max-forks", help="Maximum fork count"),
    license: str | None = typer.Option(None, "--license", help="Filter by license type"),
    topics: str | None = typer.Option(None, "--topics", help="Filter by topics (comma-separated)"),
    is_fork: bool | None = typer.Option(
        None, "--fork/--no-fork", help="Filter for forks or non-forks"
    ),
    is_archived: bool | None = typer.Option(
        None, "--archived/--no-archived", help="Filter for archived repositories"
    ),
    sort: str | None = typer.Option(None, "--sort", help="Sort by (stars, forks, updated)"),
    max_results: int | None = typer.Option(None, "--max-results", help="Maximum number of results"),
):
    """Search and export GitHub repositories."""
    builder = SearchQueryBuilder()
    builder.query(query)

    if language:
        builder.language(language)
    if min_stars is not None or max_stars is not None:
        builder.stars(min_stars, max_stars)
    if min_forks is not None or max_forks is not None:
        builder.forks(min_forks, max_forks)
    if license:
        builder.license(license)
    if topics:
        for topic in topics.split(","):
            builder.topic(topic.strip())
    if is_fork is not None:
        builder.is_fork(is_fork)
    if is_archived is not None:
        builder.is_archived(is_archived)

    options = SearchOptions(
        sort=sort,
        max_results=max_results,
    )

    asyncio.run(_search_and_export(builder, options))


async def _search_and_export(builder: SearchQueryBuilder, options: SearchOptions):
    """Async search and export."""
    client = get_client()
    dataset_builder = DatasetBuilder(client)
    exporter = DatasetExporter(state["output_dir"])

    typer.echo("Searching repositories...")
    try:
        dataset = await dataset_builder.build_full_dataset(
            builder, options, include_activity=False, include_contributors=False
        )

        typer.echo(f"Found {len(dataset['repositories'])} repositories")

        if state["format"]:
            exporter.export_dataset(dataset, format=state["format"])
        else:
            exporter.export_dataset(dataset, format="csv")
    except Exception as e:
        typer.echo(f"Error: {e}")
        raise


@app.command()
def extract(
    query: str = typer.Argument(..., help="Search query or repository (owner/repo)"),
    include_activity: bool = typer.Option(
        True, "--activity/--no-activity", help="Include activity statistics"
    ),
    include_contributors: bool = typer.Option(
        True, "--contributors/--no-contributors", help="Include contributor statistics"
    ),
):
    """Extract detailed data from repositories."""
    asyncio.run(_extract(query, include_activity, include_contributors))


async def _extract(query: str, include_activity: bool, include_contributors: bool):
    """Async extraction."""
    client = get_client()
    builder = DatasetBuilder(client)
    exporter = DatasetExporter(state["output_dir"])

    typer.echo(f"Extracting data for: {query}")
    dataset = await builder.build_full_dataset(
        query, include_activity=include_activity, include_contributors=include_contributors
    )

    typer.echo(f"Extracted {len(dataset['repositories'])} repositories")

    if state["format"]:
        exporter.export_dataset(dataset, format=state["format"])
    else:
        exporter.export_dataset(dataset, format="csv")


@app.command()
def export(
    repositories_file: Path = typer.Argument(..., help="Path to repositories JSON file"),  # noqa: B008
    include_activity: bool = typer.Option(
        True, "--activity/--no-activity", help="Include activity statistics",
    ),
    include_contributors: bool = typer.Option(
        True, "--contributors/--no-contributors", help="Include contributor statistics",
    ),
):
    """Export datasets from existing repository list."""
    asyncio.run(_export(repositories_file, include_activity, include_contributors))


async def _export(repositories_file: Path, include_activity: bool, include_contributors: bool):
    """Async export."""
    import json

    with open(repositories_file) as f:
        repositories = json.load(f)

    client = get_client()
    builder = DatasetBuilder(client)
    exporter = DatasetExporter(state["output_dir"])

    typer.echo(f"Processing {len(repositories)} repositories...")

    if include_activity:
        activities = await builder.build_activity_dataset(repositories)
        exporter.export_activity_stats(activities, format=state["format"] or "csv")

    if include_contributors:
        contributors = await builder.build_contributor_dataset(repositories)
        exporter.export_contributor_stats(contributors, format=state["format"] or "csv")


@app.command()
def auth(
    action: Literal["list", "add", "remove", "show"] = typer.Argument(..., help="Action to perform"),
    name: str = typer.Option("default", "--name", "-n", help="Token name (for multiple tokens)"),
    token: str = typer.Option(None, "--token", "-t", help="GitHub API token"),
):
    """Manage GitHub authentication tokens."""
    cache = TokenCache()

    if action == "list":
        tokens = cache.list_tokens()
        if not tokens:
            typer.echo("No tokens stored in cache.")
        else:
            typer.echo("Stored tokens:")
            for t in tokens:
                typer.echo(f"  - {t['name']} (created: {t['created_at']})")

    elif action == "add":
        if not token:
            typer.echo("Error: --token is required for add action")
            raise typer.Exit(1)
        cache.set_token(token, name)
        typer.echo(f"Token '{name}' stored successfully.")
        typer.echo("You can now use it without passing --token flag.")

    elif action == "remove":
        cache.delete_token(name)
        typer.echo(f"Token '{name}' removed successfully.")

    elif action == "show":
        stored_token = cache.get_token(name)
        if stored_token:
            typer.echo(f"Token '{name}': {stored_token}")
        else:
            typer.echo(f"Token '{name}' not found in cache.")
            raise typer.Exit(1)


if __name__ == "__main__":
    app()
