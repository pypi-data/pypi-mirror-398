from typing import Dict, Union

import requests

from __init__ import __version__


class GitHubClient:
    """A simple GitHub API client."""

    def __init__(self, token: Union[str, None] = None, timeout: Union[int, float] = 10):
        """Initialize the GitHub client.

        Args:
            token: Optional GitHub API token for authenticated requests
            timeout: Timeout (seconds) for HTTP requests
        """
        self.base_url: str = "https://api.github.com"
        self.headers: Dict[str, str] = {
            "Accept": "application/vnd.github+json",
            "User-Agent": f"repostats/{__version__}",
        }
        if token:
            self.headers["Authorization"] = f"token {token}"
        self.timeout = timeout

    def get_repo_stats(self, owner: str, repo: str) -> Dict[str, Union[str, int]]:
        """Get basic statistics for a repository.

        Args:
            owner: Repository owner (user or organization)
            repo: Repository name

        Returns:
            Dictionary with repository statistics
        """
        url = f"{self.base_url}/repos/{owner}/{repo}"
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            error_detail = "GitHub request failed"
            exc_response = getattr(exc, "response", None)
            if exc_response is not None:
                try:
                    message = exc_response.json().get("message")
                except ValueError:
                    message = exc_response.text or None
                status = f"{exc_response.status_code} {exc_response.reason}"
                if message:
                    error_detail = f"{status}: {message}"
                else:
                    error_detail = status or error_detail
            raise RuntimeError(error_detail) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError("GitHub returned invalid JSON") from exc

        return {
            "name": data.get("full_name", f"{owner}/{repo}"),
            "stars": data.get("stargazers_count", 0),
            "forks": data.get("forks_count", 0),
            "open_issues": data.get("open_issues_count", 0),
            "watchers": data.get("subscribers_count", 0),
            "created_at": data.get("created_at", "Unknown"),
            "updated_at": data.get("updated_at", "Unknown"),
            "language": data.get("language") or "Unknown",
        }
