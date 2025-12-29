from collections.abc import AsyncIterator

from ..api.client import GitHubAPIClient
from ..api.models import Repository
from .query import SearchOptions, SearchQueryBuilder


class SearchEngine:
    """Engine for searching GitHub repositories with pagination support."""

    def __init__(self, client: GitHubAPIClient):
        self.client = client

    async def search(
        self,
        query: str,
        options: SearchOptions | None = None,
    ) -> AsyncIterator[Repository]:
        """Search repositories and yield results asynchronously.

        Args:
            query: GitHub search query string
            options: Search options including sort, order, pagination

        Yields:
            Repository objects matching the search criteria

        Raises:
            GitHubAPIError: If the API request fails
        """
        if options is None:
            options = SearchOptions()

        page = 1
        total_fetched = 0

        while True:
            response = await self.client.search_repositories(
                query=query,
                sort=options.sort,
                order=options.order,
                per_page=options.per_page,
                page=page,
            )

            for item in response.get("items", []):
                if options.max_results is not None and total_fetched >= options.max_results:
                    return

                yield Repository(**item)
                total_fetched += 1

            if len(response.get("items", [])) < options.per_page:
                break

            if options.max_results is not None and total_fetched >= options.max_results:
                break

            page += 1

    async def search_builder(
        self,
        builder: SearchQueryBuilder,
        options: SearchOptions | None = None,
    ) -> AsyncIterator[Repository]:
        """Search using a SearchQueryBuilder.

        Args:
            builder: SearchQueryBuilder instance
            options: Search options

        Yields:
            Repository objects matching the search criteria
        """
        query = builder.build()
        async for repo in self.search(query, options):
            yield repo
