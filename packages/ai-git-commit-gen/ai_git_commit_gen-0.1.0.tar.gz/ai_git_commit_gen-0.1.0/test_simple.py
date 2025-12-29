#!/usr/bin/env python3
"""Simple test script for git-commit-ai."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from git_commit_ai.models import FileChange
from git_commit_ai.llm import generate_fallback_messages

# Test fallback message generation
files = [
    FileChange(path="hello.py", status="added"),
    FileChange(path="README.md", status="added")
]

print("Testing fallback message generation...\n")

# Test different styles
for style in ["conventional", "gitmoji", "simple"]:
    print(f"Style: {style}")
    messages = generate_fallback_messages(files, 3, style)
    for i, msg in enumerate(messages, 1):
        print(f"  {i}. {msg.subject}")
    print()

print("✅ Test complete!")