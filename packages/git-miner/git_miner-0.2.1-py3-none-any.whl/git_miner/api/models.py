from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Repository(BaseModel):
    """GitHub repository model."""

    id: int
    name: str
    full_name: str
    owner: dict[str, Any]
    private: bool
    description: str | None = None
    fork: bool
    language: str | None = None
    stargazers_count: int = Field(alias="stars")
    watchers_count: int
    forks_count: int
    open_issues_count: int
    license: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime | None = None
    size: int
    html_url: str
    url: str
    topics: list[str] = []
    archived: bool
    disabled: bool

    class Config:
        populate_by_name = True


class SearchResponse(BaseModel):
    """GitHub search API response model."""

    total_count: int
    incomplete_results: bool
    items: list[Repository]


class CommitActivity(BaseModel):
    """Repository commit activity summary."""

    total: int
    additions: int
    deletions: int


class ContributorStats(BaseModel):
    """Repository contributor statistics."""

    total_contributors: int
    top_contributors: list[dict[str, Any]]


class IssueStats(BaseModel):
    """Repository issue statistics."""

    open_issues: int
    closed_issues: int


class PullRequestStats(BaseModel):
    """Repository pull request statistics."""

    open_prs: int
    closed_prs: int
    merged_prs: int
