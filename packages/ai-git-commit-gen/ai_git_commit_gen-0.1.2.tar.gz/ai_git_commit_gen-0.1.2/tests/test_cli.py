"""Tests for CLI commands."""

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from git_commit_ai.cli import app

runner = CliRunner()


def test_version():
    """Test version command."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "git-commit-ai version" in result.stdout


def test_check_not_git_repo():
    """Test check command when not in a git repo."""
    with patch("git_commit_ai.cli.is_git_repo", return_value=False):
        result = runner.invoke(app, ["check"])
        assert result.exit_code == 1
        assert "Not a git repository" in result.stdout


def test_check_no_staged_changes():
    """Test check command with no staged changes."""
    with patch("git_commit_ai.cli.is_git_repo", return_value=True):
        with patch("git_commit_ai.cli.get_current_branch", return_value="main"):
            with patch("git_commit_ai.cli.has_staged_changes", return_value=False):
                result = runner.invoke(app, ["check"])
                assert result.exit_code == 1
                assert "No staged changes" in result.stdout


def test_check_success():
    """Test check command with staged changes."""
    mock_files = [
        MagicMock(path="file1.py", status="modified"),
        MagicMock(path="file2.py", status="added"),
    ]

    with patch("git_commit_ai.cli.is_git_repo", return_value=True):
        with patch("git_commit_ai.cli.get_current_branch", return_value="main"):
            with patch("git_commit_ai.cli.has_staged_changes", return_value=True):
                with patch("git_commit_ai.cli.get_changed_files", return_value=mock_files):
                    result = runner.invoke(app, ["check"])
                    assert result.exit_code == 0
                    assert "Ready to generate commit messages" in result.stdout


def test_generate_not_git_repo():
    """Test generate command when not in a git repo."""
    with patch("git_commit_ai.cli.is_git_repo", return_value=False):
        result = runner.invoke(app, ["generate"])
        assert result.exit_code == 1
        assert "Not a git repository" in result.stdout


def test_generate_no_staged_changes():
    """Test generate command with no staged changes."""
    with patch("git_commit_ai.cli.is_git_repo", return_value=True):
        with patch("git_commit_ai.cli.has_staged_changes", return_value=False):
            result = runner.invoke(app, ["generate"])
            assert result.exit_code == 1
            assert "No staged changes found" in result.stdout


@pytest.mark.asyncio
async def test_generate_dry_run():
    """Test generate command with dry run."""
    mock_files = [MagicMock(path="file1.py", status="modified")]
    mock_messages = [
        MagicMock(subject="fix: update file1", body=None),
        MagicMock(subject="chore: modify file1", body=None),
    ]

    with patch("git_commit_ai.cli.is_git_repo", return_value=True):
        with patch("git_commit_ai.cli.has_staged_changes", return_value=True):
            with patch("git_commit_ai.cli.get_staged_diff", return_value="diff content"):
                with patch(
                    "git_commit_ai.cli.get_changed_files", return_value=mock_files
                ):
                    with patch(
                        "git_commit_ai.cli.asyncio.run", return_value=mock_messages
                    ):
                        result = runner.invoke(
                            app, ["generate", "--dry-run", "--auto"]
                        )
                        assert result.exit_code == 0
                        assert "Dry run - would commit" in result.stdout


@pytest.mark.asyncio
async def test_generate_auto_commit():
    """Test generate command with auto commit."""
    mock_files = [MagicMock(path="file1.py", status="modified")]
    mock_messages = [
        MagicMock(subject="fix: update file1", body=None),
    ]

    with patch("git_commit_ai.cli.is_git_repo", return_value=True):
        with patch("git_commit_ai.cli.has_staged_changes", return_value=True):
            with patch("git_commit_ai.cli.get_staged_diff", return_value="diff content"):
                with patch(
                    "git_commit_ai.cli.get_changed_files", return_value=mock_files
                ):
                    with patch(
                        "git_commit_ai.cli.asyncio.run", return_value=mock_messages
                    ):
                        with patch(
                            "git_commit_ai.cli.create_commit", return_value=True
                        ):
                            result = runner.invoke(app, ["generate", "--auto"])
                            assert result.exit_code == 0
                            assert "Committed" in result.stdout


def test_generate_quit_interactive():
    """Test generate command with quit in interactive mode."""
    mock_files = [MagicMock(path="file1.py", status="modified")]
    mock_messages = [
        MagicMock(subject="fix: update file1", body=None),
    ]

    with patch("git_commit_ai.cli.is_git_repo", return_value=True):
        with patch("git_commit_ai.cli.has_staged_changes", return_value=True):
            with patch("git_commit_ai.cli.get_staged_diff", return_value="diff content"):
                with patch(
                    "git_commit_ai.cli.get_changed_files", return_value=mock_files
                ):
                    with patch(
                        "git_commit_ai.cli.asyncio.run", return_value=mock_messages
                    ):
                        with patch("git_commit_ai.cli.Prompt.ask", return_value="q"):
                            result = runner.invoke(app, ["generate"])
                            assert result.exit_code == 0
                            assert "Commit cancelled" in result.stdout