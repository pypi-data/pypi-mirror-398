from datetime import datetime

from ..api.client import GitHubAPIClient
from ..api.models import Repository
from ..extractors.activity import ActivityExtractor
from ..extractors.contributors import ContributorExtractor
from ..search.engine import SearchEngine
from ..search.query import SearchOptions, SearchQueryBuilder


class DatasetBuilder:
    """Builder for creating datasets from GitHub repositories."""

    def __init__(self, client: GitHubAPIClient):
        self.client = client
        self.search_engine = SearchEngine(client)
        self.activity_extractor = ActivityExtractor(client)
        self.contributor_extractor = ContributorExtractor(client)

    async def build_repository_dataset(
        self, query: str | SearchQueryBuilder, options: SearchOptions | None = None
    ) -> list[dict]:
        """Build a repository metadata dataset.

        Args:
            query: Search query string or SearchQueryBuilder
            options: Search options

        Returns:
            List of repository metadata dictionaries
        """
        if isinstance(query, SearchQueryBuilder):
            repositories: list[Repository] = []
            async for repo in self.search_engine.search_builder(query, options):
                repositories.append(repo)
        else:
            repositories: list[Repository] = []
            async for repo in self.search_engine.search(query, options):
                repositories.append(repo)

        return [
            {
                "repository_id": repo.id,
                "name": repo.name,
                "owner": repo.full_name.split("/")[0],
                "full_name": repo.full_name,
                "description": repo.description,
                "primary_language": repo.language,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "open_issues": repo.open_issues_count,
                "license": repo.license.get("name") if repo.license else None,
                "license_key": repo.license.get("key") if repo.license else None,
                "created_at": repo.created_at.isoformat(),
                "updated_at": repo.updated_at.isoformat(),
                "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
                "size_kb": repo.size,
                "url": repo.html_url,
                "api_url": repo.url,
                "is_fork": repo.fork,
                "is_archived": repo.archived,
                "topics": ",".join(repo.topics) if repo.topics else None,
            }
            for repo in repositories
        ]

    async def build_activity_dataset(
        self, repositories: list[dict], skip_on_error: bool = True
    ) -> list[dict]:
        """Build an activity dataset from repositories.

        Args:
            repositories: List of repository metadata dicts
            skip_on_error: Skip repositories on extraction errors

        Returns:
            List of activity statistics dictionaries
        """
        activities = []

        for repo_data in repositories:
            owner = repo_data["owner"]
            repo = repo_data["name"]

            try:
                activity_stats = await self.activity_extractor.extract(owner, repo)

                activities.append(
                    {
                        "repository_id": repo_data["repository_id"],
                        "full_name": repo_data["full_name"],
                        **activity_stats,
                        "extracted_at": datetime.utcnow().isoformat(),
                    }
                )
            except Exception as e:
                if not skip_on_error:
                    raise
                print(f"Error extracting activity for {owner}/{repo}: {e}")

        return activities

    async def build_contributor_dataset(
        self, repositories: list[dict], skip_on_error: bool = True
    ) -> list[dict]:
        """Build a contributor dataset from repositories.

        Args:
            repositories: List of repository metadata dicts
            skip_on_error: Skip repositories on extraction errors

        Returns:
            List of contributor statistics dictionaries
        """
        contributors = []

        for repo_data in repositories:
            owner = repo_data["owner"]
            repo = repo_data["name"]

            try:
                contributor_stats = await self.contributor_extractor.extract(owner, repo)

                contributors.append(
                    {
                        "repository_id": repo_data["repository_id"],
                        "full_name": repo_data["full_name"],
                        **contributor_stats,
                        "extracted_at": datetime.utcnow().isoformat(),
                    }
                )
            except Exception as e:
                if not skip_on_error:
                    raise
                print(f"Error extracting contributors for {owner}/{repo}: {e}")

        return contributors

    async def build_full_dataset(
        self,
        query: str | SearchQueryBuilder,
        options: SearchOptions | None = None,
        include_activity: bool = True,
        include_contributors: bool = True,
        skip_on_error: bool = True,
    ) -> dict[str, list[dict]]:
        """Build a full dataset with all available data.

        Args:
            query: Search query string or SearchQueryBuilder
            options: Search options
            include_activity: Include activity statistics
            include_contributors: Include contributor statistics
            skip_on_error: Skip repositories on extraction errors

        Returns:
            Dictionary with repository, activity, and contributor datasets
        """
        repositories = await self.build_repository_dataset(query, options)

        result = {"repositories": repositories}

        if include_activity:
            activities = await self.build_activity_dataset(repositories, skip_on_error)
            result["activities"] = activities

        if include_contributors:
            contributors = await self.build_contributor_dataset(repositories, skip_on_error)
            result["contributors"] = contributors

        return result
