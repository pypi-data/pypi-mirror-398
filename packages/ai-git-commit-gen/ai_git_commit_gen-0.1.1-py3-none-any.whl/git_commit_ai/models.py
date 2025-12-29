"""Pydantic models for git-commit-ai."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class CommitStyle(str, Enum):
    """Supported commit message styles."""

    CONVENTIONAL = "conventional"
    GITMOJI = "gitmoji"
    SIMPLE = "simple"


class FileChange(BaseModel):
    """Represents a file change in git."""

    path: str
    status: str  # added, modified, deleted, renamed
    additions: int = 0
    deletions: int = 0


class CommitOptions(BaseModel):
    """Options for generating commit messages."""

    num_suggestions: int = Field(default=3, ge=1, le=10)
    style: CommitStyle = CommitStyle.CONVENTIONAL
    auto_commit: bool = False
    dry_run: bool = False
    include_body: bool = False


class CommitMessage(BaseModel):
    """Represents a generated commit message."""

    subject: str
    body: Optional[str] = None
    style: CommitStyle = CommitStyle.CONVENTIONAL


class GenerationResult(BaseModel):
    """Result of commit message generation."""

    messages: list[CommitMessage]
    diff_summary: str
    files_changed: list[FileChange]