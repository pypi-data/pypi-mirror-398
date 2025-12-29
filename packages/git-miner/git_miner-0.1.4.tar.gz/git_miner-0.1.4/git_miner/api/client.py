import asyncio
import time
from typing import Any

import httpx

from ..constants import (
    DEFAULT_TIMEOUT,
    GITHUB_API_BASE_URL,
    GITHUB_RATE_LIMIT,
    GITHUB_RATE_LIMIT_UNAUTHENTICATED,
    MAX_RETRIES,
)
from .exceptions import (
    AuthenticationError,
    GitHubAPIError,
    RateLimitError,
    ResourceNotFoundError,
)
from .models import Repository


class GitHubAPIClient:
    """GitHub API client with rate limiting and retry logic."""

    def __init__(
        self,
        token: str | None = None,
        base_url: str = GITHUB_API_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ):
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: httpx.AsyncClient | None = None
        self._rate_limit = GITHUB_RATE_LIMIT if token else GITHUB_RATE_LIMIT_UNAUTHENTICATED
        self._remaining = self._rate_limit
        self._reset_at: float = 0

    async def __aenter__(self):
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    async def _ensure_client(self):
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)

    def _get_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def _check_rate_limit(self, response: httpx.Response):
        self._remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
        self._reset_at = int(response.headers.get("X-RateLimit-Reset", 0))

        if self._remaining <= 1:
            now = time.time()
            if self._reset_at > now:
                self._rate_limit = int(response.headers.get("X-RateLimit-Limit", 0))
                raise RateLimitError(
                    limit=self._rate_limit, remaining=self._remaining, reset_at=self._reset_at
                )

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        await self._ensure_client()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()

        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = await self._client.request(
                    method, url, headers=headers, params=params, json=json
                )
                await self._check_rate_limit(response)

                if response.status_code == 401:
                    raise AuthenticationError()
                elif response.status_code == 404:
                    raise ResourceNotFoundError(endpoint)
                elif response.status_code == 403:
                    if "rate limit" in response.text.lower():
                        reset_at = int(response.headers.get("X-RateLimit-Reset", 0))
                        now = time.time()
                        if reset_at > now:
                            await asyncio.sleep(reset_at - now + 1)
                            continue
                    raise GitHubAPIError(f"Forbidden: {response.text}")
                elif response.status_code >= 400:
                    raise GitHubAPIError(f"API error {response.status_code}: {response.text}")

                response.raise_for_status()
                return response.json()

            except (RateLimitError, httpx.TimeoutException) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    backoff = min(2**attempt, 30)
                    await asyncio.sleep(backoff)
                continue

        if last_error:
            raise last_error
        raise GitHubAPIError(f"Request failed after {self.max_retries} attempts")

    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request("GET", endpoint, params=params)

    async def post(self, endpoint: str, json: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", endpoint, json=json)

    async def search_repositories(
        self,
        query: str,
        sort: str | None = None,
        order: str = "desc",
        per_page: int = 100,
        page: int = 1,
    ) -> dict[str, Any]:
        params = {"q": query, "page": page, "per_page": per_page, "order": order}
        if sort:
            params["sort"] = sort
        return await self.get("/search/repositories", params=params)

    async def get_repository(self, owner: str, repo: str) -> Repository:
        data = await self.get(f"/repos/{owner}/{repo}")
        return Repository(**data)

    async def get_commits(
        self, owner: str, repo: str, per_page: int = 100, page: int = 1
    ) -> list[dict[str, Any]]:
        return await self.get(
            f"/repos/{owner}/{repo}/commits", params={"per_page": per_page, "page": page}
        )

    async def get_contributors(
        self, owner: str, repo: str, per_page: int = 100, page: int = 1
    ) -> list[dict[str, Any]]:
        return await self.get(
            f"/repos/{owner}/{repo}/contributors", params={"per_page": per_page, "page": page}
        )

    async def get_issues(
        self, owner: str, repo: str, state: str = "open", per_page: int = 100, page: int = 1
    ) -> list[dict[str, Any]]:
        return await self.get(
            f"/repos/{owner}/{repo}/issues",
            params={"state": state, "per_page": per_page, "page": page},
        )

    async def get_pull_requests(
        self, owner: str, repo: str, state: str = "open", per_page: int = 100, page: int = 1
    ) -> list[dict[str, Any]]:
        return await self.get(
            f"/repos/{owner}/{repo}/pulls",
            params={"state": state, "per_page": per_page, "page": page},
        )
