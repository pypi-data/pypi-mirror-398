import json
import sys
from typing import Dict, List, Tuple, Union

import click

from github import GitHubClient


def format_text_rows(stats: Dict[str, Union[str, int]]) -> Tuple[Tuple[str, str], ...]:
    """Produce label/value rows for text output."""
    rows = [
        ("Stars", f"{stats['stars']:,}"),
        ("Forks", f"{stats['forks']:,}"),
        ("Open issues", f"{stats['open_issues']:,}"),
        ("Watchers", f"{stats['watchers']:,}"),
        ("Language", str(stats.get("language") or "Unknown")),
    ]

    # Add license if available
    if stats.get("license") and stats["license"] != "Unknown":
        rows.append(("License", str(stats["license"])))

    # Add size (convert KB to MB if > 1024 KB)
    size_kb = stats.get("size", 0)
    if isinstance(size_kb, int):
        if size_kb >= 1024:
            rows.append(("Size", f"{size_kb / 1024:.1f} MB"))
        elif size_kb > 0:
            rows.append(("Size", f"{size_kb} KB"))

    # Add default branch
    if stats.get("default_branch"):
        rows.append(("Default branch", str(stats["default_branch"])))

    # Add open PRs (approximation)
    open_prs = stats.get("open_pull_requests", 0)
    if isinstance(open_prs, int) and open_prs > 0:
        rows.append(("Open PRs", f"{open_prs:,}"))

    # Add latest release
    if stats.get("latest_release"):
        rows.append(("Latest release", str(stats["latest_release"])))

    # Add timestamps
    rows.extend(
        [
            ("Created", str(stats["created_at"])),
            ("Updated", str(stats["updated_at"])),
        ]
    )

    return tuple(rows)


def format_output(stats: Dict[str, Union[str, int]], output_format: str) -> str:
    """Format repository statistics based on output format."""
    normalized_format = output_format.lower()

    if normalized_format == "json":
        return json.dumps(stats, indent=2, sort_keys=False)
    elif normalized_format == "yaml":
        try:
            import yaml

            return str(yaml.safe_dump(stats, sort_keys=False).rstrip())
        except ImportError:
            raise RuntimeError(
                "YAML output requested but PyYAML is not installed. "
                "Install it with: pip install PyYAML"
            )
    else:  # text
        lines = []
        header = f"{stats['name']} statistics"
        lines.append(header)
        lines.append("-" * len(header))
        for label, value in format_text_rows(stats):
            lines.append(f"{label:<12}: {value}")
        return "\n".join(lines)


@click.command()
@click.argument("repos", nargs=-1, required=True)
@click.option("--token", help="GitHub API token", envvar="GITHUB_TOKEN")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "yaml"], case_sensitive=False),
    default="text",
    show_default=True,
    help="Output format",
)
@click.option(
    "--output",
    "-o",
    "output_file",
    type=click.Path(),
    help="Output file (default: stdout)",
)
def main(
    repos: Tuple[str, ...],
    token: Union[str, None] = None,
    output_format: str = "text",
    output_file: Union[str, None] = None,
):
    """Fetch statistics for one or more GitHub repositories.

    REPOS should be in the format 'owner/repo', e.g., 'python/cpython'

    Examples:

        repostats python/cpython

        repostats python/cpython golang/go rust-lang/rust

        repostats python/cpython --format json --output stats.json
    """
    client = GitHubClient(token)
    results: List[Dict[str, Union[str, int]]] = []
    errors: List[str] = []

    for repo in repos:
        try:
            owner, repo_name = repo.split("/", 1)
        except ValueError:
            errors.append(
                f"Error: Repository '{repo}' should be in the format 'owner/repo'"
            )
            continue

        try:
            stats = client.get_repo_stats(owner, repo_name)
            results.append(stats)
        except Exception as e:
            errors.append(f"Error fetching {repo}: {e}")

    # Handle output
    output_lines = []

    if output_format.lower() in ["json", "yaml"]:
        # For structured formats, output all repos as array/list
        if len(results) == 1:
            formatted = format_output(results[0], output_format)
        else:
            if output_format.lower() == "json":
                formatted = json.dumps(results, indent=2, sort_keys=False)
            else:  # yaml
                try:
                    import yaml
                except ImportError:
                    click.echo(
                        "Error: YAML output requested but PyYAML is not installed.",
                        err=True,
                    )
                    raise SystemExit(1)
                formatted = yaml.safe_dump(results, sort_keys=False).rstrip()
        output_lines.append(formatted)
    else:
        # For text format, separate each repo with blank lines
        for i, stats in enumerate(results):
            if i > 0:
                output_lines.append("")  # Blank line between repos
            output_lines.append(format_output(stats, output_format))

    # Write output
    output_content = "\n".join(output_lines)
    if output_content:
        if output_file:
            try:
                with open(output_file, "w") as f:
                    f.write(output_content)
                    if not output_content.endswith("\n"):
                        f.write("\n")
                click.echo(f"Output written to {output_file}")
            except IOError as e:
                click.echo(f"Error writing to file: {e}", err=True)
                raise SystemExit(1)
        else:
            click.echo()
            click.echo(output_content)
            click.echo()

    # Print errors to stderr
    if errors:
        click.echo("", err=True)
        for error in errors:
            click.echo(error, err=True)
        raise SystemExit(1)

    # Exit with error if no successful results
    if not results:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
