"""Terminal User Interface for repostats using Textual."""

import os
import sys
from typing import Any, Dict, Union

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Input, Label, Static

from github import GitHubClient


class RepoStats(Static):
    """A widget to display repository statistics."""

    def __init__(self, repo_name: str) -> None:
        super().__init__()
        self.repo_name = repo_name
        self.stats_data: Union[Dict[str, Any], None] = None

    def compose(self) -> ComposeResult:
        yield Label(f"Repository: {self.repo_name}", classes="repo-title")
        yield Static("Loading...", id="stats-content")

    async def fetch_and_display_stats(self, token: Union[str, None] = None) -> None:
        """Fetch stats from GitHub and update display."""
        try:
            parts = self.repo_name.split("/")
            if len(parts) != 2:
                self.query_one("#stats-content", Static).update(
                    "[red]Invalid format. Use 'owner/repo'[/red]"
                )
                return

            owner, repo = parts

            # Create client and fetch stats synchronously in a worker thread
            def fetch_stats() -> Dict[str, Any]:
                client = GitHubClient(token=token)
                return client.get_repo_stats(owner, repo)  # type: ignore[no-any-return]

            worker = self.run_worker(fetch_stats, thread=True)
            stats = await worker.wait()
            self.stats_data = stats

            # Format the stats nicely
            content = f"""
[bold cyan]Repository Information[/bold cyan]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[yellow]⭐ Stars:[/yellow]           {stats['stars']:,}
[yellow]🔱 Forks:[/yellow]           {stats['forks']:,}
[yellow]📝 Open Issues:[/yellow]     {stats['open_issues']:,}
[yellow]👀 Watchers:[/yellow]        {stats['watchers']:,}
[yellow]🔀 Open PRs:[/yellow]        {stats['open_pull_requests']:,}

[bold cyan]Repository Details[/bold cyan]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[yellow]Language:[/yellow]          {stats['language']}
[yellow]License:[/yellow]           {stats['license']}
[yellow]Default Branch:[/yellow]    {stats['default_branch']}
[yellow]Size:[/yellow]              {stats['size'] / 1024:.2f} MB
[yellow]Latest Release:[/yellow]    {stats['latest_release'] or 'None'}

[bold cyan]Timestamps[/bold cyan]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[yellow]Created:[/yellow]           {stats['created_at']}
[yellow]Last Updated:[/yellow]      {stats['updated_at']}
"""
            self.query_one("#stats-content", Static).update(content)

        except RuntimeError as e:
            self.query_one("#stats-content", Static).update(f"[red]Error: {e}[/red]")
        except Exception as e:
            self.query_one("#stats-content", Static).update(
                f"[red]Unexpected error: {e}[/red]"
            )


class RepoStatsApp(App):
    """A Textual app to display GitHub repository statistics."""

    CSS = """
    Screen {
        background: $surface;
    }

    #input-container {
        height: auto;
        padding: 1 2;
        background: $panel;
    }

    Input {
        margin: 1 0;
    }

    Button {
        margin: 1 2;
    }

    .repo-title {
        text-style: bold;
        color: $accent;
        padding: 1 2;
    }

    #stats-content {
        padding: 0 2;
    }

    #help-text {
        color: $text-muted;
        padding: 0 2 1 2;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
    ]

    def __init__(self, initial_repo: Union[str, None] = None):
        super().__init__()
        self.initial_repo = initial_repo
        self.token = os.environ.get("GITHUB_TOKEN")

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Container(
            Static(
                "Enter a repository in the format 'owner/repo':",
                id="help-text",
            ),
            Input(
                placeholder="owner/repo",
                id="repo-input",
                value=self.initial_repo or "",
            ),
            Horizontal(
                Button("Fetch Stats", variant="primary", id="fetch-btn"),
                Button("Clear", variant="default", id="clear-btn"),
            ),
            id="input-container",
        )
        yield Vertical(id="results-container")
        yield Footer()

    async def on_mount(self) -> None:
        """Handle app mount."""
        # If initial repo provided, fetch stats immediately
        if self.initial_repo:
            await self.fetch_stats()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "fetch-btn":
            await self.fetch_stats()
        elif event.button.id == "clear-btn":
            self.query_one("#repo-input", Input).value = ""
            container = self.query_one("#results-container", Vertical)
            await container.remove_children()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission (Enter key)."""
        if event.input.id == "repo-input":
            await self.fetch_stats()

    async def fetch_stats(self) -> None:
        """Fetch and display repository statistics."""
        repo_input = self.query_one("#repo-input", Input)
        repo_name = repo_input.value.strip()

        if not repo_name:
            return

        # Clear previous results
        container = self.query_one("#results-container", Vertical)
        await container.remove_children()

        # Create and mount new stats widget
        stats_widget = RepoStats(repo_name)
        await container.mount(stats_widget)
        await stats_widget.fetch_and_display_stats(token=self.token)

    def action_refresh(self) -> None:
        """Refresh the current stats."""
        repo_input = self.query_one("#repo-input", Input)
        if repo_input.value.strip():
            self.run_worker(self.fetch_stats())


def main() -> None:
    """Run the TUI application."""
    initial_repo = sys.argv[1] if len(sys.argv) > 1 else None
    app = RepoStatsApp(initial_repo=initial_repo)
    app.run()


if __name__ == "__main__":
    main()
