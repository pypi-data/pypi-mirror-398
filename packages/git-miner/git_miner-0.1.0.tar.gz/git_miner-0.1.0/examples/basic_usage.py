"""
Basic usage examples for Git Miner.
"""

import asyncio

from git_miner.api.client import GitHubAPIClient
from git_miner.datasets.builder import DatasetBuilder
from git_miner.datasets.export import DatasetExporter
from git_miner.search.query import SearchQueryBuilder, SearchOptions


async def search_and_export():
    """Search for repositories and export to CSV."""
    client = GitHubAPIClient(token="your_github_token_here")
    builder = DatasetBuilder(client)
    exporter = DatasetExporter(output_dir="./output")

    query_builder = (
        SearchQueryBuilder()
        .query("machine learning")
        .language("python")
        .stars(min_stars=1000)
        .license("mit")
        .is_fork(False)
    )

    options = SearchOptions(
        sort="stars",
        max_results=10,
    )

    dataset = await builder.build_repository_dataset(query_builder, options)

    print(f"Found {len(dataset)} repositories")

    exporter.export_repository_metadata(dataset, filename="python_ml_repos", format="csv")

    await client.__aexit__(None, None, None)


async def full_dataset_example():
    """Build a full dataset with all available data."""
    client = GitHubAPIClient(token="your_github_token_here")
    builder = DatasetBuilder(client)
    exporter = DatasetExporter(output_dir="./output")

    query_builder = (
        SearchQueryBuilder()
        .query("web framework")
        .language("python")
        .stars(min_stars=500)
    )

    options = SearchOptions(max_results=5)

    dataset = await builder.build_full_dataset(
        query_builder,
        options,
        include_activity=True,
        include_contributors=True,
    )

    exporter.export_dataset(dataset, format="parquet", prefix="web_frameworks")

    print(f"Exported:")
    print(f"  - {len(dataset['repositories'])} repositories")
    print(f"  - {len(dataset.get('activities', []))} activity records")
    print(f"  - {len(dataset.get('contributors', []))} contributor records")

    await client.__aexit__(None, None, None)


async def main():
    """Run examples."""
    print("Example 1: Search and export")
    await search_and_export()

    print("\nExample 2: Full dataset")
    await full_dataset_example()


if __name__ == "__main__":
    asyncio.run(main())
