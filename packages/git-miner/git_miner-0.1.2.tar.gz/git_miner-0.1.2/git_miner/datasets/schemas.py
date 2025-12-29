from typing import Any

from pydantic import BaseModel, Field


class RepositoryMetadataSchema(BaseModel):
    """Schema for repository metadata dataset."""

    repository_id: int
    name: str = Field(description="Repository name")
    owner: str = Field(description="Repository owner/organization")
    full_name: str = Field(description="Full repository name (owner/repo)")
    description: str | None = Field(default=None, description="Repository description")
    primary_language: str | None = Field(default=None, description="Primary programming language")
    stars: int = Field(ge=0, description="Number of stars")
    forks: int = Field(ge=0, description="Number of forks")
    open_issues: int = Field(ge=0, description="Number of open issues")
    license: str | None = Field(default=None, description="License name")
    license_key: str | None = Field(default=None, description="License SPDX identifier")
    created_at: str = Field(description="ISO 8601 creation timestamp")
    updated_at: str = Field(description="ISO 8601 last update timestamp")
    pushed_at: str | None = Field(default=None, description="ISO 8601 last push timestamp")
    size_kb: int = Field(ge=0, description="Repository size in kilobytes")
    url: str = Field(description="Repository HTML URL")
    api_url: str = Field(description="Repository API URL")
    is_fork: bool = Field(description="Whether this is a fork")
    is_archived: bool = Field(description="Whether this is archived")
    topics: str | None = Field(default=None, description="Comma-separated topics/tags")

    model_config = {
        "json_schema_extra": {
            "example": {
                "repository_id": 1296269,
                "name": "Hello-World",
                "owner": "octocat",
                "full_name": "octocat/Hello-World",
                "description": "My first repository",
                "primary_language": "Python",
                "stars": 100,
                "forks": 50,
                "open_issues": 10,
                "license": "MIT License",
                "license_key": "mit",
                "created_at": "2011-01-26T19:01:12Z",
                "updated_at": "2024-01-01T12:00:00Z",
                "pushed_at": "2024-01-01T12:00:00Z",
                "size_kb": 1024,
                "url": "https://github.com/octocat/Hello-World",
                "api_url": "https://api.github.com/repos/octocat/Hello-World",
                "is_fork": False,
                "is_archived": False,
                "topics": "github,api,example",
            }
        }
    }


class RepositoryActivitySchema(BaseModel):
    """Schema for repository activity dataset."""

    repository_id: int
    full_name: str
    commit_total: int = Field(ge=0, description="Total number of commits")
    commit_additions: int = Field(ge=0, description="Total lines added")
    commit_deletions: int = Field(ge=0, description="Total lines deleted")
    issues_open: int = Field(ge=0, description="Number of open issues")
    issues_closed: int = Field(ge=0, description="Number of closed issues")
    issues_total: int = Field(ge=0, description="Total number of issues")
    prs_open: int = Field(ge=0, description="Number of open pull requests")
    prs_closed: int = Field(ge=0, description="Number of closed pull requests")
    prs_merged: int = Field(ge=0, description="Number of merged pull requests")
    prs_total: int = Field(ge=0, description="Total number of pull requests")
    extracted_at: str = Field(description="ISO 8601 extraction timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "repository_id": 1296269,
                "full_name": "octocat/Hello-World",
                "commit_total": 1000,
                "commit_additions": 50000,
                "commit_deletions": 20000,
                "issues_open": 10,
                "issues_closed": 100,
                "issues_total": 110,
                "prs_open": 5,
                "prs_closed": 50,
                "prs_merged": 45,
                "prs_total": 100,
                "extracted_at": "2024-01-01T12:00:00Z",
            }
        }
    }


class ContributorStatsSchema(BaseModel):
    """Schema for contributor statistics dataset."""

    repository_id: int
    full_name: str
    total_contributors: int = Field(ge=0, description="Total number of contributors")
    top_contributors: list[dict[str, Any]] = Field(description="Top 10 contributors")
    extracted_at: str = Field(description="ISO 8601 extraction timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "repository_id": 1296269,
                "full_name": "octocat/Hello-World",
                "total_contributors": 50,
                "top_contributors": [
                    {"login": "octocat", "contributions": 100, "url": "https://github.com/octocat"}
                ],
                "extracted_at": "2024-01-01T12:00:00Z",
            }
        }
    }
