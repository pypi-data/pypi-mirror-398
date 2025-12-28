import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from cli import main


def get_mock_stats(name="test/repo"):
    """Helper to get mock stats with all fields."""
    return {
        "name": name,
        "stars": 100,
        "forks": 50,
        "open_issues": 10,
        "watchers": 25,
        "language": "Python",
        "created_at": "2022-01-01T00:00:00Z",
        "updated_at": "2022-02-01T00:00:00Z",
        "license": "MIT",
        "size": 1024,
        "default_branch": "main",
        "open_pull_requests": 5,
        "latest_release": "v1.0.0",
    }


def test_cli_success():
    """Test successful CLI execution"""
    runner = CliRunner()

    with patch("cli.GitHubClient") as mock_client:
        mock_instance = MagicMock()
        mock_instance.get_repo_stats.return_value = get_mock_stats()
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
    assert "should be in the format 'owner/repo'" in result.output


def test_cli_with_token():
    """Test CLI with token parameter"""
    runner = CliRunner()

    with patch("cli.GitHubClient") as mock_client:
        mock_instance = MagicMock()
        mock_instance.get_repo_stats.return_value = get_mock_stats()
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
        assert "Error fetching test/repo: API Error" in result.output


def test_cli_json_output():
    """Test CLI JSON output format"""
    runner = CliRunner()

    with patch("cli.GitHubClient") as mock_client:
        mock_instance = MagicMock()
        mock_instance.get_repo_stats.return_value = get_mock_stats()
        mock_client.return_value = mock_instance

        result = runner.invoke(main, ["test/repo", "--format", "json"])

        assert result.exit_code == 0
        assert '"name": "test/repo"' in result.output
        assert '"stars": 100' in result.output


def test_cli_yaml_output():
    """Test CLI YAML output format"""
    runner = CliRunner()

    with patch("cli.GitHubClient") as mock_client:
        mock_instance = MagicMock()
        mock_instance.get_repo_stats.return_value = get_mock_stats()
        mock_client.return_value = mock_instance

        result = runner.invoke(main, ["test/repo", "--format", "yaml"])

        assert result.exit_code == 0
        assert "name: test/repo" in result.output
        assert "stars: 100" in result.output


def test_cli_multiple_repos():
    """Test CLI with multiple repositories"""
    runner = CliRunner()

    with patch("cli.GitHubClient") as mock_client:
        mock_instance = MagicMock()
        mock_instance.get_repo_stats.side_effect = [
            get_mock_stats("test/repo1"),
            get_mock_stats("test/repo2"),
        ]
        mock_client.return_value = mock_instance

        result = runner.invoke(main, ["test/repo1", "test/repo2"])

        assert result.exit_code == 0
        assert "test/repo1 statistics" in result.output
        assert "test/repo2 statistics" in result.output


def test_cli_output_file():
    """Test CLI with output file"""
    runner = CliRunner()

    with patch("cli.GitHubClient") as mock_client:
        mock_instance = MagicMock()
        mock_instance.get_repo_stats.return_value = get_mock_stats()
        mock_client.return_value = mock_instance

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            temp_path = f.name

        try:
            result = runner.invoke(
                main, ["test/repo", "--format", "json", "--output", temp_path]
            )

            assert result.exit_code == 0
            assert f"Output written to {temp_path}" in result.output

            # Verify file contents
            with open(temp_path) as f:
                content = f.read()
                assert '"name": "test/repo"' in content
                assert '"stars": 100' in content
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
