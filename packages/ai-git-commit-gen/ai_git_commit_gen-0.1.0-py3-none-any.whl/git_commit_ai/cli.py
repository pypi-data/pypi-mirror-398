"""CLI commands for git-commit-ai."""

import asyncio
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from typing_extensions import Annotated

from . import __version__
from .git_utils import (
    create_commit,
    get_changed_files,
    get_current_branch,
    get_staged_diff,
    has_staged_changes,
    is_git_repo,
)
from .llm import generate_commit_messages
from .models import CommitOptions, CommitStyle

app = typer.Typer(
    name="gcai",
    help="AI-powered git commit message generator",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"git-commit-ai version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """git-commit-ai - Generate meaningful commit messages using AI."""
    pass


@app.command(name="generate", help="Generate commit message suggestions")
@app.command(name="g", help="Generate commit message suggestions (alias)", hidden=True)
def generate(
    auto: Annotated[
        bool,
        typer.Option(
            "--auto",
            "-a",
            help="Auto-commit with first suggestion",
        ),
    ] = False,
    num: Annotated[
        int,
        typer.Option(
            "--num",
            "-n",
            help="Number of suggestions to generate",
            min=1,
            max=10,
        ),
    ] = 3,
    style: Annotated[
        CommitStyle,
        typer.Option(
            "--style",
            "-s",
            help="Commit message style",
        ),
    ] = CommitStyle.CONVENTIONAL,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-d",
            help="Show message without committing",
        ),
    ] = False,
    body: Annotated[
        bool,
        typer.Option(
            "--body",
            "-b",
            help="Include commit body",
        ),
    ] = False,
) -> None:
    """Generate commit message suggestions for staged changes."""
    # Check if in git repo
    if not is_git_repo():
        console.print("[red]❌ Error: Not a git repository[/red]")
        console.print("[yellow]💡 Run this command inside a git repository[/yellow]")
        raise typer.Exit(1)

    # Check for staged changes
    if not has_staged_changes():
        console.print("[red]❌ No staged changes found[/red]")
        console.print("[yellow]💡 Stage your changes first: [bold]git add <files>[/bold][/yellow]")
        raise typer.Exit(1)

    # Show analyzing message
    with console.status("[bold green]🔍 Analyzing staged changes..."):
        # Get diff and changed files
        try:
            diff = get_staged_diff()
            changed_files = get_changed_files()
        except Exception as e:
            console.print(f"[red]❌ Error getting git diff: {e}[/red]")
            raise typer.Exit(1)

    # Display changed files
    if changed_files:
        console.print("\n[bold]📁 Files changed:[/bold]")
        for file in changed_files[:10]:  # Limit display
            status_emoji = {
                "added": "✨",
                "modified": "📝",
                "deleted": "🗑️",
                "renamed": "📝",
            }.get(file.status, "📄")
            console.print(f"   {status_emoji} [cyan]{file.path}[/cyan] ({file.status})")

        if len(changed_files) > 10:
            console.print(f"   [dim]... and {len(changed_files) - 10} more files[/dim]")

    # Generate commit messages
    with console.status("[bold green]✨ Generating commit messages..."):
        try:
            messages = asyncio.run(
                generate_commit_messages(
                    diff=diff,
                    changed_files=changed_files,
                    num_suggestions=num,
                    style=style.value,
                    include_body=body,
                )
            )
        except Exception as e:
            console.print(f"[red]❌ Error generating messages: {e}[/red]")
            raise typer.Exit(1)

    if not messages:
        console.print("[red]❌ Failed to generate commit messages[/red]")
        raise typer.Exit(1)

    # Display suggestions
    console.print("\n[bold]✨ Suggested commit messages:[/bold]\n")

    for i, msg in enumerate(messages, 1):
        console.print(f"  [[bold cyan]{i}[/bold cyan]] {msg.subject}")
        if msg.body:
            console.print(f"\n{msg.body}\n")

    # Handle auto-commit
    if auto:
        selected_msg = messages[0].subject
        if not dry_run:
            if create_commit(selected_msg):
                console.print(f"\n[green]✅ Committed: {selected_msg}[/green]")
            else:
                console.print("[red]❌ Failed to create commit[/red]")
                raise typer.Exit(1)
        else:
            console.print(f"\n[yellow]🔍 Dry run - would commit: {selected_msg}[/yellow]")
        return

    # Interactive selection
    while True:
        console.print()
        choice = Prompt.ask(
            "Select [[cyan]1-{}[/cyan]], [[cyan]r[/cyan]]egenerate, [[cyan]e[/cyan]]dit, or [[cyan]q[/cyan]]uit".format(
                len(messages)
            ),
            default="1",
        )

        if choice.lower() == "q":
            console.print("[yellow]👋 Commit cancelled[/yellow]")
            raise typer.Exit(0)

        elif choice.lower() == "r":
            # Regenerate
            with console.status("[bold green]✨ Regenerating messages..."):
                messages = asyncio.run(
                    generate_commit_messages(
                        diff=diff,
                        changed_files=changed_files,
                        num_suggestions=num,
                        style=style.value,
                        include_body=body,
                    )
                )
            console.print("\n[bold]✨ New suggestions:[/bold]\n")
            for i, msg in enumerate(messages, 1):
                console.print(f"  [[bold cyan]{i}[/bold cyan]] {msg.subject}")
            continue

        elif choice.lower() == "e":
            # Edit mode
            if len(messages) == 1:
                selected_msg = messages[0].subject
            else:
                edit_choice = Prompt.ask(
                    f"Which message to edit? [1-{len(messages)}]", default="1"
                )
                try:
                    idx = int(edit_choice) - 1
                    if 0 <= idx < len(messages):
                        selected_msg = messages[idx].subject
                    else:
                        console.print("[red]Invalid selection[/red]")
                        continue
                except ValueError:
                    console.print("[red]Invalid selection[/red]")
                    continue

            # Try to use editor
            import os
            import tempfile

            editor = os.environ.get("EDITOR", "nano")

            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                f.write(selected_msg)
                temp_path = f.name

            try:
                subprocess.call([editor, temp_path])
                with open(temp_path, "r") as f:
                    edited_msg = f.read().strip()
                os.unlink(temp_path)

                if edited_msg:
                    selected_msg = edited_msg
                else:
                    console.print("[yellow]Empty message, using original[/yellow]")

            except Exception:
                # Fallback to inline editing
                edited = Prompt.ask("Edit message", default=selected_msg)
                if edited:
                    selected_msg = edited

            # Commit with edited message
            if not dry_run:
                if create_commit(selected_msg):
                    console.print(f"\n[green]✅ Committed: {selected_msg}[/green]")
                else:
                    console.print("[red]❌ Failed to create commit[/red]")
                    raise typer.Exit(1)
            else:
                console.print(
                    f"\n[yellow]🔍 Dry run - would commit: {selected_msg}[/yellow]"
                )
            break

        else:
            # Numeric selection
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(messages):
                    selected_msg = messages[idx].subject

                    if not dry_run:
                        if create_commit(selected_msg):
                            console.print(
                                f"\n[green]✅ Committed: {selected_msg}[/green]"
                            )
                        else:
                            console.print("[red]❌ Failed to create commit[/red]")
                            raise typer.Exit(1)
                    else:
                        console.print(
                            f"\n[yellow]🔍 Dry run - would commit: {selected_msg}[/yellow]"
                        )
                    break
                else:
                    console.print("[red]Invalid selection, please try again[/red]")
            except ValueError:
                console.print("[red]Invalid input, please try again[/red]")


@app.command(help="Check if ready to generate commit messages")
def check() -> None:
    """Check if the current directory is ready for commit message generation."""
    # Check git repo
    if not is_git_repo():
        console.print("[red]❌ Not a git repository[/red]")
        raise typer.Exit(1)

    console.print("[green]✅ Git repository found[/green]")

    # Check branch
    branch = get_current_branch()
    console.print(f"[cyan]🌿 Current branch: {branch}[/cyan]")

    # Check staged changes
    if not has_staged_changes():
        console.print("[yellow]⚠️ No staged changes[/yellow]")
        console.print("[dim]Run 'git add <files>' to stage changes[/dim]")
        raise typer.Exit(1)

    console.print("[green]✅ Staged changes found[/green]")

    # Show changed files
    changed_files = get_changed_files()
    if changed_files:
        table = Table(title="Staged Files", show_header=True)
        table.add_column("Status", style="cyan")
        table.add_column("File", style="white")

        for file in changed_files[:15]:
            table.add_row(file.status.upper(), file.path)

        if len(changed_files) > 15:
            table.add_row("...", f"and {len(changed_files) - 15} more files")

        console.print(table)

    console.print("\n[green]✅ Ready to generate commit messages![/green]")
    console.print("[dim]Run 'gcai generate' to generate commit messages[/dim]")


if __name__ == "__main__":
    app()