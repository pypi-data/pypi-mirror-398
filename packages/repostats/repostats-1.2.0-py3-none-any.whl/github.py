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
                status_code = exc_response.status_code
                try:
                    message = exc_response.json().get("message")
                except ValueError:
                    message = exc_response.text or None

                # Special handling for rate limiting
                if status_code == 403:
                    rate_limit = exc_response.headers.get("X-RateLimit-Remaining")
                    if rate_limit == "0":
                        reset_time = exc_response.headers.get("X-RateLimit-Reset", "")
                        error_detail = (
                            "GitHub API rate limit exceeded. "
                            "Try authenticating with a token: "
                            "repostats --token YOUR_TOKEN owner/repo"
                        )
                        if reset_time:
                            try:
                                from datetime import datetime

                                reset_dt = datetime.fromtimestamp(int(reset_time))
                                error_detail += (
                                    f" (resets at {reset_dt.strftime('%H:%M:%S')})"
                                )
                            except (ValueError, OverflowError):
                                pass
                    elif message:
                        error_detail = f"403 Forbidden: {message}"
                    else:
                        error_detail = "403 Forbidden"
                elif status_code == 404:
                    error_detail = f"Repository '{owner}/{repo}' not found. Check the repository name and your access."
                else:
                    status = f"{status_code} {exc_response.reason}"
                    if message:
                        error_detail = f"{status}: {message}"
                    else:
                        error_detail = status
            raise RuntimeError(error_detail) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError("GitHub returned invalid JSON") from exc

        # Get latest release info
        latest_release = self._get_latest_release(owner, repo)

        return {
            "name": data.get("full_name", f"{owner}/{repo}"),
            "stars": data.get("stargazers_count", 0),
            "forks": data.get("forks_count", 0),
            "open_issues": data.get("open_issues_count", 0),
            "watchers": data.get("subscribers_count", 0),
            "created_at": data.get("created_at", "Unknown"),
            "updated_at": data.get("updated_at", "Unknown"),
            "language": data.get("language") or "Unknown",
            "license": data.get("license", {}).get("spdx_id") or "Unknown",
            "size": data.get("size", 0),  # Size in KB
            "default_branch": data.get("default_branch", "Unknown"),
            "open_pull_requests": data.get("open_issues_count", 0)
            - data.get("open_issues", 0),  # Approximation
            "latest_release": latest_release,
        }

    def _get_latest_release(self, owner: str, repo: str) -> Union[str, None]:
        """Get the latest release tag name.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Latest release tag name or None if no releases
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/releases/latest"
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            if response.status_code == 404:
                # No releases found
                return None
            response.raise_for_status()
            data = response.json()
            tag_name = data.get("tag_name")
            return tag_name if tag_name else None
        except requests.RequestException:
            # If release fetch fails, don't fail the whole request
            return None
