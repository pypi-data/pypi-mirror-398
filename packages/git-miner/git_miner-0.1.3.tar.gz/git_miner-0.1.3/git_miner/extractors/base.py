from abc import ABC, abstractmethod

from ..api.client import GitHubAPIClient


class BaseExtractor(ABC):
    """Base class for data extractors."""

    def __init__(self, client: GitHubAPIClient):
        self.client = client

    @abstractmethod
    async def extract(self, owner: str, repo: str):
        """Extract data from the repository.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Extracted data (specific to each extractor)
        """
        pass
