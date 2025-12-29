import pytest
from httpx import Response


@pytest.fixture
def github_token():
    return "test_token"


@pytest.fixture
def mock_github_response():
    def _create_response(json_data, status_code=200):
        return Response(status_code, json=json_data)

    return _create_response


@pytest.fixture
def mock_repository():
    return {
        "id": 1296269,
        "name": "Hello-World",
        "full_name": "octocat/Hello-World",
        "owner": {"login": "octocat"},
        "private": False,
        "description": "My first repository",
        "fork": False,
        "language": "Python",
        "stargazers_count": 100,
        "watchers_count": 100,
        "forks_count": 50,
        "fork_count": 50,
        "open_issues_count": 10,
        "license": {"key": "mit", "name": "MIT License"},
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z",
        "pushed_at": "2024-01-01T12:00:00Z",
        "size": 1024,
        "html_url": "https://github.com/octocat/Hello-World",
        "url": "https://api.github.com/repos/octocat/Hello-World",
        "topics": ["github", "api"],
        "archived": False,
        "disabled": False,
    }


@pytest.fixture
def mock_search_response():
    return {
        "total_count": 1,
        "incomplete_results": False,
        "items": [
            {
                "id": 1296269,
                "name": "Hello-World",
                "full_name": "octocat/Hello-World",
                "owner": {"login": "octocat"},
                "private": False,
                "description": "My first repository",
                "fork": False,
                "language": "Python",
                "stargazers_count": 100,
                "watchers_count": 100,
                "forks_count": 50,
                "fork_count": 50,
                "open_issues_count": 10,
                "license": {"key": "mit", "name": "MIT License"},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
                "pushed_at": "2024-01-01T12:00:00Z",
                "size": 1024,
                "html_url": "https://github.com/octocat/Hello-World",
                "url": "https://api.github.com/repos/octocat/Hello-World",
                "topics": ["github", "api"],
                "archived": False,
                "disabled": False,
            }
        ],
    }
