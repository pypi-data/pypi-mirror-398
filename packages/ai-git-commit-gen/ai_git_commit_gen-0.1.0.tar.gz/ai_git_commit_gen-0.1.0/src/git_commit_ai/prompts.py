"""Prompt templates for different commit message styles."""

CONVENTIONAL_PROMPT = """You are a Git commit message generator. Analyze the following git diff and generate {num} commit message suggestions.

Follow Conventional Commits format: type(scope): description

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- style: Code style changes (formatting, semicolons, etc.)
- refactor: Code refactoring
- test: Adding or updating tests
- chore: Maintenance tasks
- perf: Performance improvements
- ci: CI/CD changes
- build: Build system changes

Rules:
1. Subject line must be max 72 characters
2. Use imperative mood ("add" not "added" or "adds")
3. Be specific about what changed
4. Focus on WHAT and WHY, not HOW
5. Scope is optional but helpful (e.g., auth, api, ui)
6. No period at the end of the subject line

Changed files:
{files}

Git diff:
```diff
{diff}
```

Generate exactly {num} commit messages, one per line, numbered 1-{num}. Only output the commit messages, nothing else:"""

GITMOJI_PROMPT = """You are a Git commit message generator. Analyze the following git diff and generate {num} commit message suggestions using Gitmoji format.

Format: <emoji> <type>(<scope>): <description>

Common emojis:
- ✨ :sparkles: New feature
- 🐛 :bug: Bug fix
- 📝 :memo: Documentation
- 💄 :lipstick: UI/style updates
- ♻️ :recycle: Refactoring
- ✅ :white_check_mark: Tests
- 🔧 :wrench: Configuration
- ⚡️ :zap: Performance
- 🔥 :fire: Remove code/files
- 🚀 :rocket: Deploy/release
- 🎨 :art: Improve structure
- 🔒 :lock: Security
- ⬆️ :arrow_up: Upgrade dependencies
- ⬇️ :arrow_down: Downgrade dependencies
- 🏗️ :building_construction: Architectural changes

Rules:
1. Start with appropriate emoji
2. Use imperative mood
3. Be concise and specific
4. Max 72 characters total
5. Include scope when relevant

Changed files:
{files}

Git diff:
```diff
{diff}
```

Generate exactly {num} commit messages, one per line, numbered 1-{num}. Only output the commit messages, nothing else:"""

SIMPLE_PROMPT = """You are a Git commit message generator. Analyze the following git diff and generate {num} simple, clear commit message suggestions.

Rules:
1. Use imperative mood ("add" not "added")
2. Be specific and concise
3. Max 72 characters
4. Focus on the main change
5. No unnecessary punctuation

Changed files:
{files}

Git diff:
```diff
{diff}
```

Generate exactly {num} commit messages, one per line, numbered 1-{num}. Only output the commit messages, nothing else:"""

BODY_PROMPT_ADDON = """

Also generate a commit body that:
1. Explains WHY the change was made
2. Lists key modifications if multiple
3. Notes any breaking changes
4. Keeps lines under 72 characters
5. Separates body from subject with blank line

Format each suggestion as:
<number>. <subject line>

<body>
---"""


def get_prompt(style: str, include_body: bool = False) -> str:
    """Get the appropriate prompt template for the given style."""
    prompts = {
        "conventional": CONVENTIONAL_PROMPT,
        "gitmoji": GITMOJI_PROMPT,
        "simple": SIMPLE_PROMPT,
    }

    prompt = prompts.get(style, CONVENTIONAL_PROMPT)

    if include_body:
        prompt += BODY_PROMPT_ADDON

    return prompt