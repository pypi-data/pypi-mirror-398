"""Git operations for git-commit-ai."""

from pathlib import Path
from typing import Optional

import git
from git import Repo
from rich.console import Console

from .models import FileChange

console = Console()

MAX_DIFF_SIZE = 10000  # Maximum diff size to process


def get_repo(path: Path = Path.cwd()) -> Optional[Repo]:
    """Get the git repository from the current or parent directories."""
    try:
        return Repo(path, search_parent_directories=True)
    except git.InvalidGitRepositoryError:
        return None


def is_git_repo(path: Path = Path.cwd()) -> bool:
    """Check if the current directory is a git repository."""
    return get_repo(path) is not None


def has_staged_changes(path: Path = Path.cwd()) -> bool:
    """Check if there are staged changes in the repository."""
    repo = get_repo(path)
    if not repo:
        return False

    # Check if there are staged files
    if len(repo.index.entries) > 0:
        return True

    try:
        return len(repo.index.diff("HEAD")) > 0 or len(repo.index.diff(None)) > 0
    except git.BadName:
        # No HEAD yet (initial commit)
        return len(repo.index.entries) > 0


def get_staged_diff(path: Path = Path.cwd()) -> str:
    """Get the staged diff from the current repository."""
    repo = get_repo(path)
    if not repo:
        raise ValueError("Not a git repository")

    # Get staged changes
    try:
        staged_diff = repo.git.diff("--cached", "--no-color")
    except git.GitCommandError:
        # For initial commit, generate a pseudo-diff
        staged_files = []
        for (path_str, stage), entry in repo.index.entries.items():
            if stage == 0:  # Normal stage
                try:
                    content = Path(repo.working_dir) / path_str
                    if content.exists():
                        with open(content, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            staged_files.append(f"diff --git a/{path_str} b/{path_str}")
                            staged_files.append(f"new file mode {oct(entry.mode)}")
                            staged_files.append(f"--- /dev/null")
                            staged_files.append(f"+++ b/{path_str}")
                            for line in lines[:50]:  # Limit lines for large files
                                staged_files.append(f"+{line.rstrip()}")
                            if len(lines) > 50:
                                staged_files.append(f"+... ({len(lines)-50} more lines)")
                except Exception:
                    continue
        staged_diff = "\n".join(staged_files) if staged_files else ""

    if not staged_diff:
        # Check for changes in a new repo (no HEAD yet)
        try:
            staged_diff = repo.git.diff("--cached", "--no-color", "--", ".")
        except git.GitCommandError:
            # If still no diff, return empty
            return ""

    # Truncate if too large
    if len(staged_diff) > MAX_DIFF_SIZE:
        console.print(
            f"[yellow]⚠️ Diff is large ({len(staged_diff)} chars), "
            f"truncating to {MAX_DIFF_SIZE} chars for analysis...[/yellow]"
        )
        # Try to truncate intelligently at file boundaries
        lines = staged_diff[:MAX_DIFF_SIZE].split("\n")
        # Find the last complete diff header
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].startswith("diff --git"):
                staged_diff = "\n".join(lines[:i])
                break
        else:
            staged_diff = staged_diff[:MAX_DIFF_SIZE]

    return staged_diff


def get_changed_files(path: Path = Path.cwd()) -> list[FileChange]:
    """Get list of staged files with their status."""
    repo = get_repo(path)
    if not repo:
        raise ValueError("Not a git repository")

    changes = []

    # Get staged files
    try:
        # For existing commits
        diff = repo.index.diff("HEAD")
        for item in diff:
            status = "modified"
            if item.new_file:
                status = "added"
            elif item.deleted_file:
                status = "deleted"
            elif item.renamed:
                status = "renamed"

            changes.append(
                FileChange(
                    path=item.a_path if item.a_path else item.b_path,
                    status=status,
                    additions=item.diff.count(b"\n+") if item.diff else 0,
                    deletions=item.diff.count(b"\n-") if item.diff else 0,
                )
            )
    except git.BadName:
        # For initial commit (no HEAD)
        for item in repo.index.entries.keys():
            changes.append(
                FileChange(
                    path=item[0],
                    status="added",
                    additions=0,
                    deletions=0,
                )
            )

    # Also check untracked files that are staged
    for item in repo.index.diff(None):
        if item.new_file:
            changes.append(
                FileChange(
                    path=item.a_path if item.a_path else item.b_path,
                    status="added",
                    additions=item.diff.count(b"\n+") if item.diff else 0,
                    deletions=0,
                )
            )

    return changes


def create_commit(message: str, path: Path = Path.cwd()) -> bool:
    """Create a commit with the given message."""
    repo = get_repo(path)
    if not repo:
        raise ValueError("Not a git repository")

    try:
        repo.index.commit(message)
        return True
    except git.GitCommandError as e:
        console.print(f"[red]❌ Failed to create commit: {e}[/red]")
        return False


def get_current_branch(path: Path = Path.cwd()) -> str:
    """Get the current branch name."""
    repo = get_repo(path)
    if not repo:
        raise ValueError("Not a git repository")

    try:
        return repo.active_branch.name
    except TypeError:
        # Detached HEAD state
        return "HEAD (detached)"