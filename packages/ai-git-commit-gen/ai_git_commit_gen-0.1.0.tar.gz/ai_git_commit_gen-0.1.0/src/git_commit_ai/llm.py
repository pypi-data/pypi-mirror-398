"""LLM integration for git-commit-ai using free APIs."""

import asyncio
import hashlib
import json
import re
from pathlib import Path
from typing import Optional

import httpx
from rich.console import Console

from .models import CommitMessage, CommitStyle, FileChange
from .prompts import get_prompt

console = Console()

# Free LLM APIs that don't require API keys
# Primary: LLM7.io - OpenAI compatible, reliable
LLM7_API_URL = "https://api.llm7.io/v1/chat/completions"
# Fallback: ApiFreeLLM - Simple and fast
APIFREELLM_URL = "https://apifreellm.com/api/generate"

# Cache configuration
CACHE_DIR = Path.home() / ".cache" / "git-commit-ai"
CACHE_TTL_SECONDS = 3600  # 1 hour


def get_cache_key(diff: str, files: list[FileChange], style: str, num: int) -> str:
    """Generate a cache key for the given input."""
    content = f"{diff}{files}{style}{num}"
    return hashlib.sha256(content.encode()).hexdigest()


def get_cached_result(cache_key: str) -> Optional[list[str]]:
    """Get cached result if it exists and is not expired."""
    cache_file = CACHE_DIR / f"{cache_key}.json"

    if not cache_file.exists():
        return None

    try:
        # Check if cache is expired
        import time

        if time.time() - cache_file.stat().st_mtime > CACHE_TTL_SECONDS:
            cache_file.unlink()  # Delete expired cache
            return None

        with open(cache_file, "r") as f:
            data = json.load(f)
            return data.get("messages", [])
    except (json.JSONDecodeError, IOError):
        return None


def save_to_cache(cache_key: str, messages: list[str]) -> None:
    """Save messages to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{cache_key}.json"

    try:
        with open(cache_file, "w") as f:
            json.dump({"messages": messages}, f)
    except IOError:
        pass  # Ignore cache write errors


async def call_llm7_api(prompt: str, max_retries: int = 2) -> Optional[str]:
    """Call LLM7.io free API (OpenAI compatible, no API key needed)."""
    headers = {"Content-Type": "application/json"}

    # Format as chat completion request
    data = {
        "model": "gpt-3.5-turbo",  # LLM7 supports various models
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that generates git commit messages."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 150
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
        for attempt in range(max_retries):
            try:
                response = await client.post(LLM7_API_URL, headers=headers, json=data)

                if response.status_code == 200:
                    result = response.json()
                    if "choices" in result and len(result["choices"]) > 0:
                        return result["choices"][0]["message"]["content"]
                    return None

                elif response.status_code == 429:
                    # Rate limited (40 req/min)
                    wait_time = 2 + attempt
                    console.print(f"[yellow]Rate limited, waiting {wait_time}s...[/yellow]")
                    await asyncio.sleep(wait_time)
                    continue

                else:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)
                        continue
                    return None

            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                return None

    return None


async def call_apifreellm(prompt: str) -> Optional[str]:
    """Call ApiFreeLLM.com (no API key, simple fetch)."""
    headers = {"Content-Type": "application/json"}

    data = {
        "prompt": prompt,
        "max_tokens": 150
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(20.0)) as client:
            response = await client.post(APIFREELLM_URL, headers=headers, json=data)

            if response.status_code == 200:
                result = response.json()
                if isinstance(result, dict) and "text" in result:
                    return result["text"]
                elif isinstance(result, str):
                    return result
            return None

    except Exception:
        return None


def analyze_and_generate_messages(
    diff: str,
    changed_files: list[FileChange],
    num: int,
    style: str
) -> list[str]:
    """Analyze diff and generate intelligent commit messages locally."""
    messages = []

    # Analyze the diff content for patterns
    diff_lower = diff.lower()

    # Detect what kind of changes were made
    has_tests = any("test" in f.path.lower() for f in changed_files)
    has_docs = any(f.path.endswith((".md", ".rst", ".txt")) for f in changed_files)
    has_config = any(f.path.endswith((".json", ".yml", ".yaml", ".toml", ".ini")) for f in changed_files)

    # Look for specific patterns in the diff
    is_bugfix = "fix" in diff_lower or "bug" in diff_lower or "error" in diff_lower
    is_feature = "def " in diff or "class " in diff or "function " in diff or "feat" in diff_lower
    is_refactor = "refactor" in diff_lower or "rename" in diff_lower
    is_security = "security" in diff_lower or "auth" in diff_lower or "token" in diff_lower
    is_performance = "performance" in diff_lower or "optimize" in diff_lower or "cache" in diff_lower

    # Count lines changed
    additions = diff.count("\n+")
    deletions = diff.count("\n-")

    # Get primary file info
    if changed_files:
        primary_file = changed_files[0]
        file_name = Path(primary_file.path).stem
        file_ext = Path(primary_file.path).suffix

        # Generate contextual messages based on analysis
        if style == "conventional":
            if is_bugfix:
                messages.append(f"fix: resolve issue in {file_name}")
                messages.append(f"fix({file_name}): correct error handling")
            elif is_feature:
                messages.append(f"feat: implement {file_name} functionality")
                messages.append(f"feat({file_name}): add new capabilities")
            elif is_refactor:
                messages.append(f"refactor: improve {file_name} structure")
                messages.append(f"refactor({file_name}): optimize code organization")
            elif has_tests:
                messages.append(f"test: add tests for {file_name}")
                messages.append(f"test({file_name}): improve test coverage")
            elif has_docs:
                messages.append(f"docs: update {file_name} documentation")
                messages.append(f"docs({file_name}): improve documentation")
            elif has_config:
                messages.append(f"chore: update {file_name} configuration")
                messages.append(f"config: modify {file_name} settings")
            elif is_security:
                messages.append(f"security: enhance {file_name} security")
                messages.append(f"fix(security): address vulnerabilities in {file_name}")
            elif is_performance:
                messages.append(f"perf: optimize {file_name} performance")
                messages.append(f"perf({file_name}): improve efficiency")
            else:
                # Default messages based on file operations
                if primary_file.status == "added":
                    messages.append(f"feat: add {file_name} module")
                elif primary_file.status == "deleted":
                    messages.append(f"chore: remove {file_name}")
                else:
                    messages.append(f"update: modify {file_name}")

            # Add a comprehensive message
            if len(changed_files) > 1:
                messages.append(f"feat: update {len(changed_files)} files with improvements")

        elif style == "gitmoji":
            emoji_map = {
                "feat": "✨",
                "fix": "🐛",
                "docs": "📝",
                "style": "💄",
                "refactor": "♻️",
                "test": "✅",
                "chore": "🔧",
                "perf": "⚡️",
                "security": "🔒"
            }

            if is_bugfix:
                messages.append(f"🐛 fix: resolve issue in {file_name}")
            elif is_feature:
                messages.append(f"✨ feat: add {file_name} functionality")
            elif has_tests:
                messages.append(f"✅ test: add {file_name} tests")
            elif has_docs:
                messages.append(f"📝 docs: update {file_name}")
            else:
                messages.append(f"🔧 chore: update {file_name}")

        else:  # simple style
            if is_bugfix:
                messages.append(f"Fix issue in {file_name}")
            elif is_feature:
                messages.append(f"Add {file_name} functionality")
            elif is_refactor:
                messages.append(f"Refactor {file_name}")
            else:
                messages.append(f"Update {file_name}")

            if additions > deletions:
                messages.append(f"Add new code to {file_name}")
            elif deletions > additions:
                messages.append(f"Clean up {file_name}")

    # Ensure we have enough unique messages
    messages = list(dict.fromkeys(messages))  # Remove duplicates while preserving order

    # Add more generic messages if needed
    while len(messages) < num:
        if style == "conventional":
            generic = [
                "chore: update project files",
                "feat: enhance functionality",
                "fix: resolve issues",
                "refactor: improve code quality"
            ]
        elif style == "gitmoji":
            generic = [
                "🔧 chore: update project",
                "✨ feat: add improvements",
                "🐛 fix: resolve issues"
            ]
        else:
            generic = [
                "Update project files",
                "Make improvements",
                "Fix issues"
            ]

        for msg in generic:
            if msg not in messages:
                messages.append(msg)
                if len(messages) >= num:
                    break

    return messages[:num]


def parse_commit_messages(response: str, num_suggestions: int) -> list[str]:
    """Parse commit messages from LLM response."""
    lines = response.strip().split("\n")
    messages = []

    for line in lines:
        # Remove numbering (1. 2. etc) and clean up
        line = line.strip()
        if line and len(line) > 5:
            # Remove common prefixes like "1.", "1)", "- ", etc
            import re

            cleaned = re.sub(r"^[\d]+[\.\)]\s*", "", line)
            cleaned = re.sub(r"^[-\*]\s*", "", cleaned)
            cleaned = cleaned.strip()

            if cleaned and len(cleaned) > 5:
                messages.append(cleaned)

                if len(messages) >= num_suggestions:
                    break

    return messages


async def generate_commit_messages(
    diff: str,
    changed_files: list[FileChange],
    num_suggestions: int = 3,
    style: str = "conventional",
    include_body: bool = False,
) -> list[CommitMessage]:
    """Generate commit message suggestions using free LLM APIs."""
    # Check cache first
    cache_key = get_cache_key(diff, changed_files, style, num_suggestions)
    cached = get_cached_result(cache_key)

    if cached:
        console.print("[dim]Using cached suggestions...[/dim]")
        return [
            CommitMessage(subject=msg, style=CommitStyle(style)) for msg in cached
        ]

    # Prepare the prompt
    prompt_template = get_prompt(style, include_body)

    # Format file list
    files_str = "\n".join(
        [f"- {fc.path} ({fc.status})" for fc in changed_files[:20]]
    )

    # Truncate diff if needed
    if len(diff) > 5000:
        diff = diff[:5000] + "\n... (truncated)"

    prompt = prompt_template.format(num=num_suggestions, files=files_str, diff=diff)

    # Try LLM7.io first (most reliable)
    console.print("[green]Generating commit messages...[/green]")
    response = await call_llm7_api(prompt)

    # If LLM7 fails, try ApiFreeLLM
    if not response:
        console.print("[yellow]Trying alternative service...[/yellow]")
        response = await call_apifreellm(prompt)

    # Parse response if we got one
    messages = []
    if response:
        messages = parse_commit_messages(response, num_suggestions)

    # If we still don't have enough messages, use intelligent local generation
    if len(messages) < num_suggestions:
        console.print("[yellow]Using intelligent analysis...[/yellow]")
        local_messages = analyze_and_generate_messages(
            diff, changed_files, num_suggestions - len(messages), style
        )
        messages.extend(local_messages)

    # Ensure we have enough messages
    if not messages:
        messages = analyze_and_generate_messages(
            diff, changed_files, num_suggestions, style
        )

    # Save to cache
    save_to_cache(cache_key, messages[:num_suggestions])

    return [
        CommitMessage(subject=msg, style=CommitStyle(style))
        for msg in messages[:num_suggestions]
    ]


def generate_fallback_messages(
    changed_files: list[FileChange], num: int, style: str
) -> list[CommitMessage]:
    """Generate basic commit messages when API is unavailable."""
    messages = []

    if not changed_files:
        messages.append("update code")
    else:
        # Analyze file changes
        added = [f for f in changed_files if f.status == "added"]
        modified = [f for f in changed_files if f.status == "modified"]
        deleted = [f for f in changed_files if f.status == "deleted"]

        # Generate messages based on changes
        if len(changed_files) == 1:
            file = changed_files[0]
            base_name = Path(file.path).stem

            if style == "conventional":
                if file.status == "added":
                    messages.append(f"feat: add {base_name}")
                elif file.status == "deleted":
                    messages.append(f"chore: remove {base_name}")
                else:
                    messages.append(f"fix: update {base_name}")
            else:
                if file.status == "added":
                    messages.append(f"add {base_name}")
                elif file.status == "deleted":
                    messages.append(f"remove {base_name}")
                else:
                    messages.append(f"update {base_name}")

        else:
            # Multiple files
            if added and not modified and not deleted:
                if style == "conventional":
                    messages.append(f"feat: add {len(added)} new files")
                else:
                    messages.append(f"add {len(added)} new files")

            if modified and not added and not deleted:
                if style == "conventional":
                    messages.append(f"fix: update {len(modified)} files")
                else:
                    messages.append(f"update {len(modified)} files")

            if style == "conventional":
                messages.append(
                    f"chore: update {len(changed_files)} files"
                )
            else:
                messages.append(f"update {len(changed_files)} files")

    # Ensure we have enough messages
    while len(messages) < num:
        if style == "conventional":
            messages.append(f"chore: update project files")
        else:
            messages.append(f"update project files")

    return [
        CommitMessage(subject=msg, style=CommitStyle(style))
        for msg in messages[:num]
    ]