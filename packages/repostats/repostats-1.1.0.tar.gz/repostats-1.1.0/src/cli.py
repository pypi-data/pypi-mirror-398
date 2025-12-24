import json
from typing import Dict, Iterable, Tuple, Union

import click

from github import GitHubClient


def format_text_rows(stats: Dict[str, Union[str, int]]) -> Tuple[Tuple[str, str], ...]:
    """Produce label/value rows for text output."""
    return (
        ("Stars", f"{stats['stars']:,}"),
        ("Forks", f"{stats['forks']:,}"),
        ("Open issues", f"{stats['open_issues']:,}"),
        ("Watchers", f"{stats['watchers']:,}"),
        ("Language", str(stats["language"] or "Unknown")),
        ("Created", str(stats["created_at"])),
        ("Updated", str(stats["updated_at"])),
    )


@click.command()
@click.argument("repo")
@click.option("--token", help="GitHub API token", envvar="GITHUB_TOKEN")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "yaml"], case_sensitive=False),
    default="text",
    show_default=True,
    help="Output format",
)
def main(
    repo: str,
    token: Union[str, None] = None,
    output_format: str = "text",
):
    """Fetch statistics for a GitHub repository.

    REPO should be in the format 'owner/repo', e.g., 'python/cpython'
    """
    try:
        owner, repo_name = repo.split("/", 1)
    except ValueError:
        click.echo("Error: Repository should be in the format 'owner/repo'", err=True)
        raise SystemExit(1)

    client = GitHubClient(token)
    try:
        stats = client.get_repo_stats(owner, repo_name)
        normalized_format = output_format.lower()
        if normalized_format == "json":
            click.echo(json.dumps(stats, indent=2, sort_keys=False))
        elif normalized_format == "yaml":
            try:
                import yaml
            except ImportError as exc:
                click.echo(
                    "Error: YAML output requested but PyYAML is not installed.",
                    err=True,
                )
                raise SystemExit(1) from exc
            click.echo(yaml.safe_dump(stats, sort_keys=False).rstrip())
        else:
            click.echo()
            header = f"{stats['name']} statistics"
            click.echo(header)
            click.echo("-" * len(header))
            for label, value in format_text_rows(stats):
                click.echo(f"{label:<12}: {value}")
            click.echo()
    except Exception as e:
        click.echo(f"Error: Failed to fetch repository stats: {e}", err=True)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
