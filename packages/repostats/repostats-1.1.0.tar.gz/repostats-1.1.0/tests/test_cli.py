from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from cli import main


def test_cli_success():
    """Test successful CLI execution"""
    runner = CliRunner()

    # Mock the GitHub API response
    mock_stats = {
        "name": "test/repo",
        "stars": 100,
        "forks": 50,
        "open_issues": 10,
        "watchers": 25,
        "language": "Python",
        "created_at": "2022-01-01T00:00:00Z",
        "updated_at": "2022-02-01T00:00:00Z",
    }

    with patch("cli.GitHubClient") as mock_client:
        mock_instance = MagicMock()
        mock_instance.get_repo_stats.return_value = mock_stats
        mock_client.return_value = mock_instance

        result = runner.invoke(main, ["test/repo"])

        assert result.exit_code == 0
        assert "test/repo statistics" in result.output
        assert "Stars       : 100" in result.output
        assert "Forks       : 50" in result.output


def test_cli_invalid_repo_format():
    """Test CLI with invalid repository format"""
    runner = CliRunner()

    result = runner.invoke(main, ["invalid-repo"])

    assert result.exit_code == 1
    assert "Error: Repository should be in the format 'owner/repo'" in result.output


def test_cli_with_token():
    """Test CLI with token parameter"""
    runner = CliRunner()

    mock_stats = {
        "name": "test/repo",
        "stars": 100,
        "forks": 50,
        "open_issues": 10,
        "watchers": 25,
        "language": "Python",
        "created_at": "2022-01-01T00:00:00Z",
        "updated_at": "2022-02-01T00:00:00Z",
    }

    with patch("cli.GitHubClient") as mock_client:
        mock_instance = MagicMock()
        mock_instance.get_repo_stats.return_value = mock_stats
        mock_client.return_value = mock_instance

        result = runner.invoke(main, ["test/repo", "--token", "test_token"])

        assert result.exit_code == 0
        mock_client.assert_called_once_with("test_token")


def test_cli_api_error():
    """Test CLI when GitHub API returns an error"""
    runner = CliRunner()

    with patch("cli.GitHubClient") as mock_client:
        mock_instance = MagicMock()
        mock_instance.get_repo_stats.side_effect = Exception("API Error")
        mock_client.return_value = mock_instance

        result = runner.invoke(main, ["test/repo"])

        assert result.exit_code == 1
        assert "Error: Failed to fetch repository stats: API Error" in result.output


def test_cli_json_output():
    """Test CLI JSON output format"""
    runner = CliRunner()

    mock_stats = {
        "name": "test/repo",
        "stars": 100,
        "forks": 50,
        "open_issues": 10,
        "watchers": 25,
        "language": "Python",
        "created_at": "2022-01-01T00:00:00Z",
        "updated_at": "2022-02-01T00:00:00Z",
    }

    with patch("cli.GitHubClient") as mock_client:
        mock_instance = MagicMock()
        mock_instance.get_repo_stats.return_value = mock_stats
        mock_client.return_value = mock_instance

        result = runner.invoke(main, ["test/repo", "--format", "json"])

        assert result.exit_code == 0
        assert '"name": "test/repo"' in result.output
        assert '"stars": 100' in result.output


def test_cli_yaml_output():
    """Test CLI YAML output format"""
    runner = CliRunner()

    mock_stats = {
        "name": "test/repo",
        "stars": 100,
        "forks": 50,
        "open_issues": 10,
        "watchers": 25,
        "language": "Python",
        "created_at": "2022-01-01T00:00:00Z",
        "updated_at": "2022-02-01T00:00:00Z",
    }

    with patch("cli.GitHubClient") as mock_client:
        mock_instance = MagicMock()
        mock_instance.get_repo_stats.return_value = mock_stats
        mock_client.return_value = mock_instance

        result = runner.invoke(main, ["test/repo", "--format", "yaml"])

        assert result.exit_code == 0
        assert "name: test/repo" in result.output
        assert "stars: 100" in result.output
