"""Tests for git utilities."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from git_commit_ai.git_utils import (
    create_commit,
    get_changed_files,
    get_current_branch,
    get_repo,
    get_staged_diff,
    has_staged_changes,
    is_git_repo,
)


def test_is_git_repo_true():
    """Test is_git_repo returns True for valid repo."""
    with patch("git_commit_ai.git_utils.Repo") as mock_repo_class:
        mock_repo_class.return_value = MagicMock()
        assert is_git_repo() is True


def test_is_git_repo_false():
    """Test is_git_repo returns False for non-repo."""
    with patch("git_commit_ai.git_utils.Repo") as mock_repo_class:
        import git

        mock_repo_class.side_effect = git.InvalidGitRepositoryError
        assert is_git_repo() is False


def test_get_repo_valid():
    """Test get_repo returns repo object."""
    with patch("git_commit_ai.git_utils.Repo") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        result = get_repo()
        assert result == mock_repo


def test_get_repo_invalid():
    """Test get_repo returns None for non-repo."""
    with patch("git_commit_ai.git_utils.Repo") as mock_repo_class:
        import git

        mock_repo_class.side_effect = git.InvalidGitRepositoryError
        result = get_repo()
        assert result is None


def test_has_staged_changes_true():
    """Test has_staged_changes returns True when changes exist."""
    mock_repo = MagicMock()
    mock_repo.index.diff.return_value = [MagicMock()]  # Has changes

    with patch("git_commit_ai.git_utils.get_repo", return_value=mock_repo):
        assert has_staged_changes() is True


def test_has_staged_changes_false():
    """Test has_staged_changes returns False when no changes."""
    mock_repo = MagicMock()
    mock_repo.index.diff.return_value = []  # No changes

    with patch("git_commit_ai.git_utils.get_repo", return_value=mock_repo):
        assert has_staged_changes() is False


def test_has_staged_changes_no_repo():
    """Test has_staged_changes returns False when not in repo."""
    with patch("git_commit_ai.git_utils.get_repo", return_value=None):
        assert has_staged_changes() is False


def test_get_staged_diff_success():
    """Test get_staged_diff returns diff string."""
    mock_repo = MagicMock()
    mock_repo.git.diff.return_value = "diff --git a/file.py b/file.py\n+added line"

    with patch("git_commit_ai.git_utils.get_repo", return_value=mock_repo):
        result = get_staged_diff()
        assert "diff --git" in result
        assert "+added line" in result


def test_get_staged_diff_no_repo():
    """Test get_staged_diff raises error when not in repo."""
    with patch("git_commit_ai.git_utils.get_repo", return_value=None):
        with pytest.raises(ValueError, match="Not a git repository"):
            get_staged_diff()


def test_get_staged_diff_truncate():
    """Test get_staged_diff truncates large diffs."""
    mock_repo = MagicMock()
    # Create a diff larger than MAX_DIFF_SIZE
    large_diff = "x" * 11000
    mock_repo.git.diff.return_value = large_diff

    with patch("git_commit_ai.git_utils.get_repo", return_value=mock_repo):
        result = get_staged_diff()
        assert len(result) <= 10000


def test_get_changed_files():
    """Test get_changed_files returns list of FileChange objects."""
    mock_repo = MagicMock()

    # Create mock diff items
    mock_item1 = MagicMock()
    mock_item1.a_path = "file1.py"
    mock_item1.new_file = True
    mock_item1.deleted_file = False
    mock_item1.renamed = False
    mock_item1.diff = b"+line1\n+line2\n-line3"

    mock_item2 = MagicMock()
    mock_item2.a_path = "file2.py"
    mock_item2.new_file = False
    mock_item2.deleted_file = True
    mock_item2.renamed = False
    mock_item2.diff = b"-line1\n-line2"

    mock_repo.index.diff.return_value = [mock_item1, mock_item2]

    with patch("git_commit_ai.git_utils.get_repo", return_value=mock_repo):
        result = get_changed_files()
        assert len(result) == 2
        assert result[0].path == "file1.py"
        assert result[0].status == "added"
        assert result[1].path == "file2.py"
        assert result[1].status == "deleted"


def test_get_changed_files_no_repo():
    """Test get_changed_files raises error when not in repo."""
    with patch("git_commit_ai.git_utils.get_repo", return_value=None):
        with pytest.raises(ValueError, match="Not a git repository"):
            get_changed_files()


def test_create_commit_success():
    """Test create_commit successfully creates commit."""
    mock_repo = MagicMock()
    mock_repo.index.commit.return_value = MagicMock()

    with patch("git_commit_ai.git_utils.get_repo", return_value=mock_repo):
        result = create_commit("test: add test commit")
        assert result is True
        mock_repo.index.commit.assert_called_once_with("test: add test commit")


def test_create_commit_failure():
    """Test create_commit handles git errors."""
    import git

    mock_repo = MagicMock()
    mock_repo.index.commit.side_effect = git.GitCommandError("commit", 1)

    with patch("git_commit_ai.git_utils.get_repo", return_value=mock_repo):
        result = create_commit("test: add test commit")
        assert result is False


def test_create_commit_no_repo():
    """Test create_commit raises error when not in repo."""
    with patch("git_commit_ai.git_utils.get_repo", return_value=None):
        with pytest.raises(ValueError, match="Not a git repository"):
            create_commit("test: add test commit")


def test_get_current_branch():
    """Test get_current_branch returns branch name."""
    mock_repo = MagicMock()
    mock_branch = MagicMock()
    mock_branch.name = "feature/test"
    mock_repo.active_branch = mock_branch

    with patch("git_commit_ai.git_utils.get_repo", return_value=mock_repo):
        result = get_current_branch()
        assert result == "feature/test"


def test_get_current_branch_detached():
    """Test get_current_branch handles detached HEAD."""
    mock_repo = MagicMock()
    mock_repo.active_branch = MagicMock(side_effect=TypeError)

    with patch("git_commit_ai.git_utils.get_repo", return_value=mock_repo):
        result = get_current_branch()
        assert result == "HEAD (detached)"


def test_get_current_branch_no_repo():
    """Test get_current_branch raises error when not in repo."""
    with patch("git_commit_ai.git_utils.get_repo", return_value=None):
        with pytest.raises(ValueError, match="Not a git repository"):
            get_current_branch()