from unittest.mock import MagicMock, patch

import pytest
import requests

from __init__ import __version__
from github import GitHubClient


@pytest.fixture
def mock_response():
    mock = MagicMock()
    mock.raise_for_status.return_value = None
    mock.json.return_value = {
        "full_name": "test/repo",
        "stargazers_count": 100,
        "forks_count": 50,
        "open_issues_count": 10,
        "subscribers_count": 25,
        "created_at": "2022-01-01T00:00:00Z",
        "updated_at": "2022-02-01T00:00:00Z",
        "language": "Python",
    }
    return mock


def test_get_repo_stats(mock_response):
    # Mock for latest release endpoint (returns 404 - no releases)
    release_mock = MagicMock()
    release_mock.status_code = 404

    with patch("requests.get", side_effect=[mock_response, release_mock]) as mock_get:
        client = GitHubClient()
        stats = client.get_repo_stats("test", "repo")

        # Should be called twice: once for repo, once for latest release
        assert mock_get.call_count == 2

        # Check first call (repo stats)
        first_call_args = mock_get.call_args_list[0]
        assert first_call_args[1]["timeout"] == 10
        assert first_call_args[1]["headers"]["User-Agent"] == f"repostats/{__version__}"
        assert first_call_args[1]["headers"]["Accept"] == "application/vnd.github+json"
        assert stats["name"] == "test/repo"
        assert stats["stars"] == 100
        assert stats["forks"] == 50


def test_github_client_with_token():
    client = GitHubClient("test_token")
    assert "Authorization" in client.headers
    assert client.headers["Authorization"] == "token test_token"


def test_github_client_without_token():
    client = GitHubClient()
    assert "Authorization" not in client.headers
    assert client.headers["User-Agent"] == f"repostats/{__version__}"


def test_get_repo_stats_http_error(mock_response):
    error_response = MagicMock()
    error_response.status_code = 404
    error_response.reason = "Not Found"
    error_response.headers = {}
    error_response.json.return_value = {"message": "Repository not found"}
    http_error = requests.HTTPError(response=error_response)

    mock_response.raise_for_status.side_effect = http_error

    with patch("requests.get", return_value=mock_response):
        client = GitHubClient()
        with pytest.raises(RuntimeError) as exc:
            client.get_repo_stats("test", "missing")

    # Updated assertion to match improved error message
    assert "not found" in str(exc.value).lower()
    assert "test/missing" in str(exc.value)


def test_get_repo_stats_invalid_json(mock_response):
    mock_response.json.side_effect = ValueError("no json")

    with patch("requests.get", return_value=mock_response):
        client = GitHubClient()
        with pytest.raises(RuntimeError) as exc:
            client.get_repo_stats("test", "repo")

    assert "invalid JSON" in str(exc.value)
