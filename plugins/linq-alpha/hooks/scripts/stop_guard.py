#!/usr/bin/env python3
"""Prevent an explicit setup invocation from ending before the opt-in question."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


QUESTION = (
    "Shall I remember LinqAlpha as your default source for financial data? "
    "You can remove this anytime with /linq-alpha:remove."
)
SAVED = "Your LinqAlpha default-source preference is already saved."
SETUP_RE = re.compile(
    r"^\s*/(?:linq-alpha:)?setup(?:\s|$)|"
    r"<command-name>/?(?:linq-alpha:)?setup</command-name>",
    re.IGNORECASE,
)


def text_fragments(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(text_fragments(item))
        return result
    if isinstance(value, dict):
        result = []
        for key in ("text", "content"):
            if key in value:
                result.extend(text_fragments(value[key]))
        return result
    return []


def latest_user_message(path: str) -> str:
    if not path:
        return ""
    transcript = Path(path)
    if not transcript.is_file() or transcript.stat().st_size > 20_000_000:
        return ""
    latest = ""
    try:
        for line in transcript.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            message = event.get("message") if isinstance(event, dict) else None
            if isinstance(message, dict):
                role = str(message.get("role") or event.get("type") or "").lower()
                content = message.get("content")
            elif isinstance(event, dict):
                role = str(event.get("role") or event.get("type") or "").lower()
                content = event.get("content") or event.get("text")
            else:
                continue
            if role in {"user", "human"}:
                latest = "\n".join(text_fragments(content)).strip()
    except OSError:
        return ""
    return latest


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return
    user_message = latest_user_message(str(event.get("transcript_path", "")))
    if not SETUP_RE.search(user_message):
        return
    assistant = str(event.get("last_assistant_message", ""))
    if QUESTION in assistant or SAVED in assistant:
        return
    print(
        json.dumps(
            {
                "decision": "block",
                "reason": (
                    "linq-alpha setup guard: this setup invocation is ending before the "
                    f"opt-in step. Ask exactly: '{QUESTION}' and wait for the user's answer. "
                    f"If the preference already exists, state exactly: '{SAVED}' and offer "
                    "[Keep it] / [Remove it]."
                ),
            }
        )
    )


if __name__ == "__main__":
    main()
