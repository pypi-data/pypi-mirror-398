from ..api.models import Repository
from .base import BaseExtractor


class RepositoryExtractor(BaseExtractor):
    """Extractor for repository metadata."""

    async def extract(self, owner: str, repo: str) -> Repository:
        """Extract repository metadata.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Repository object with full metadata
        """
        return await self.client.get_repository(owner, repo)

    def from_search_result(self, repo: Repository) -> dict:
        """Convert search result to dictionary format.

        Args:
            repo: Repository object from search

        Returns:
            Dictionary with repository metadata
        """
        return {
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
