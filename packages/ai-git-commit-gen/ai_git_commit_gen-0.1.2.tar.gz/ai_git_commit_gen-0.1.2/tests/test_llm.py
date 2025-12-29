"""Tests for LLM integration."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from git_commit_ai.llm import (
    call_huggingface_api,
    generate_commit_messages,
    generate_fallback_messages,
    get_cache_key,
    get_cached_result,
    parse_commit_messages,
    save_to_cache,
)
from git_commit_ai.models import CommitStyle, FileChange


def test_get_cache_key():
    """Test cache key generation."""
    files = [FileChange(path="file.py", status="modified")]
    key1 = get_cache_key("diff1", files, "conventional", 3)
    key2 = get_cache_key("diff2", files, "conventional", 3)
    key3 = get_cache_key("diff1", files, "gitmoji", 3)

    # Different inputs should produce different keys
    assert key1 != key2
    assert key1 != key3
    assert key2 != key3

    # Same inputs should produce same key
    key4 = get_cache_key("diff1", files, "conventional", 3)
    assert key1 == key4


def test_get_cached_result_not_exists():
    """Test get_cached_result when cache doesn't exist."""
    with patch("git_commit_ai.llm.Path.exists", return_value=False):
        result = get_cached_result("test_key")
        assert result is None


def test_get_cached_result_expired():
    """Test get_cached_result when cache is expired."""
    import time

    mock_path = MagicMock()
    mock_path.exists.return_value = True
    mock_path.stat.return_value.st_mtime = time.time() - 7200  # 2 hours old

    with patch("git_commit_ai.llm.CACHE_DIR") as mock_cache_dir:
        mock_cache_dir.__truediv__.return_value = mock_path
        result = get_cached_result("test_key")
        assert result is None
        mock_path.unlink.assert_called_once()


def test_get_cached_result_valid():
    """Test get_cached_result returns cached messages."""
    import time

    mock_path = MagicMock()
    mock_path.exists.return_value = True
    mock_path.stat.return_value.st_mtime = time.time() - 600  # 10 minutes old

    cache_data = json.dumps({"messages": ["fix: update file", "chore: refactor"]})

    with patch("git_commit_ai.llm.CACHE_DIR") as mock_cache_dir:
        mock_cache_dir.__truediv__.return_value = mock_path
        with patch("builtins.open", mock_open(read_data=cache_data)):
            result = get_cached_result("test_key")
            assert result == ["fix: update file", "chore: refactor"]


def test_save_to_cache():
    """Test save_to_cache saves messages correctly."""
    messages = ["fix: update file", "chore: refactor"]

    with patch("git_commit_ai.llm.CACHE_DIR") as mock_cache_dir:
        mock_cache_dir.mkdir = MagicMock()
        mock_file = MagicMock()
        mock_cache_dir.__truediv__.return_value = mock_file

        with patch("builtins.open", mock_open()) as mock_file_open:
            save_to_cache("test_key", messages)
            mock_cache_dir.mkdir.assert_called_once_with(
                parents=True, exist_ok=True
            )
            # Check that json.dump was called with correct data
            handle = mock_file_open()
            written_content = "".join(
                str(call.args[0]) for call in handle.write.call_args_list
            )
            assert "messages" in written_content


def test_parse_commit_messages():
    """Test parse_commit_messages extracts messages correctly."""
    response = """
1. fix: update authentication logic
2. chore: refactor auth module
3. feat: add token validation
4. Some extra text
"""
    messages = parse_commit_messages(response, 3)
    assert len(messages) == 3
    assert messages[0] == "fix: update authentication logic"
    assert messages[1] == "chore: refactor auth module"
    assert messages[2] == "feat: add token validation"


def test_parse_commit_messages_with_prefixes():
    """Test parse_commit_messages removes various prefixes."""
    response = """
1) fix: update file
- chore: refactor code
* feat: add feature
"""
    messages = parse_commit_messages(response, 3)
    assert len(messages) == 3
    assert messages[0] == "fix: update file"
    assert messages[1] == "chore: refactor code"
    assert messages[2] == "feat: add feature"


def test_generate_fallback_messages_single_file():
    """Test fallback messages for single file changes."""
    files = [FileChange(path="auth/login.py", status="added")]

    messages = generate_fallback_messages(files, 3, "conventional")
    assert len(messages) == 3
    assert "feat: add login" in messages[0].subject


def test_generate_fallback_messages_multiple_files():
    """Test fallback messages for multiple file changes."""
    files = [
        FileChange(path="file1.py", status="modified"),
        FileChange(path="file2.py", status="modified"),
        FileChange(path="file3.py", status="added"),
    ]

    messages = generate_fallback_messages(files, 2, "simple")
    assert len(messages) == 2
    assert "update" in messages[0].subject.lower()


def test_generate_fallback_messages_empty_files():
    """Test fallback messages with no files."""
    messages = generate_fallback_messages([], 2, "conventional")
    assert len(messages) == 2
    assert messages[0].subject == "update code"


@pytest.mark.asyncio
async def test_call_huggingface_api_success():
    """Test successful API call."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"generated_text": "fix: update authentication"}
    ]

    with patch("git_commit_ai.llm.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )
        result = await call_huggingface_api("test prompt")
        assert result == "fix: update authentication"


@pytest.mark.asyncio
async def test_call_huggingface_api_rate_limit():
    """Test API call with rate limiting."""
    mock_response_429 = MagicMock()
    mock_response_429.status_code = 429

    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = [{"generated_text": "fix: update file"}]

    with patch("git_commit_ai.llm.httpx.AsyncClient") as mock_client:
        mock_post = AsyncMock()
        mock_post.side_effect = [mock_response_429, mock_response_200]
        mock_client.return_value.__aenter__.return_value.post = mock_post

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await call_huggingface_api("test prompt")
            assert result == "fix: update file"


@pytest.mark.asyncio
async def test_call_huggingface_api_model_loading():
    """Test API call when model is loading."""
    mock_response_503 = MagicMock()
    mock_response_503.status_code = 503

    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = [{"generated_text": "fix: update file"}]

    with patch("git_commit_ai.llm.httpx.AsyncClient") as mock_client:
        mock_post = AsyncMock()
        mock_post.side_effect = [mock_response_503, mock_response_200]
        mock_client.return_value.__aenter__.return_value.post = mock_post

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await call_huggingface_api("test prompt")
            assert result == "fix: update file"


@pytest.mark.asyncio
async def test_generate_commit_messages_with_cache():
    """Test generate_commit_messages uses cache when available."""
    files = [FileChange(path="file.py", status="modified")]
    cached_messages = ["fix: cached message 1", "fix: cached message 2"]

    with patch("git_commit_ai.llm.get_cached_result", return_value=cached_messages):
        messages = await generate_commit_messages("diff", files, 2, "conventional")
        assert len(messages) == 2
        assert messages[0].subject == "fix: cached message 1"
        assert messages[1].subject == "fix: cached message 2"


@pytest.mark.asyncio
async def test_generate_commit_messages_api_call():
    """Test generate_commit_messages makes API call when no cache."""
    files = [FileChange(path="file.py", status="modified")]

    with patch("git_commit_ai.llm.get_cached_result", return_value=None):
        with patch(
            "git_commit_ai.llm.call_huggingface_api",
            new_callable=AsyncMock,
            return_value="1. fix: update file\n2. chore: refactor",
        ):
            with patch("git_commit_ai.llm.save_to_cache"):
                messages = await generate_commit_messages(
                    "diff", files, 2, "conventional"
                )
                assert len(messages) == 2
                assert messages[0].subject == "fix: update file"
                assert messages[1].subject == "chore: refactor"


@pytest.mark.asyncio
async def test_generate_commit_messages_fallback():
    """Test generate_commit_messages uses fallback when API fails."""
    files = [FileChange(path="file.py", status="modified")]

    with patch("git_commit_ai.llm.get_cached_result", return_value=None):
        with patch(
            "git_commit_ai.llm.call_huggingface_api",
            new_callable=AsyncMock,
            return_value=None,
        ):
            messages = await generate_commit_messages(
                "diff", files, 2, "conventional"
            )
            assert len(messages) == 2
            # Should have fallback messages
            assert "update" in messages[0].subject.lower() or "fix" in messages[0].subject.lower()