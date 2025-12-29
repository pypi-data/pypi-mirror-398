from typing import Any

from .base import BaseExtractor


class ContributorExtractor(BaseExtractor):
    """Extractor for contributor statistics."""

    async def extract(self, owner: str, repo: str) -> dict[str, Any]:
        """Extract contributor statistics.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Dictionary with contributor statistics
        """
        page = 1
        all_contributors: list[dict[str, Any]] = []

        while True:
            contributors = await self.client.get_contributors(owner, repo, page=page)
            if not contributors:
                break

            all_contributors.extend(contributors)

            if len(contributors) < 100:
                break

            page += 1

        total_contributors = len(all_contributors)

        top_contributors = sorted(
            all_contributors, key=lambda c: c.get("contributions", 0), reverse=True
        )[:10]

        top_contributors_list = [
            {
                "login": c.get("login"),
                "contributions": c.get("contributions"),
                "url": c.get("html_url"),
            }
            for c in top_contributors
        ]

        return {
            "total_contributors": total_contributors,
            "top_contributors": top_contributors_list,
        }
