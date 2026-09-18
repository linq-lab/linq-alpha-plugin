#!/usr/bin/env python3
"""Guard LinqAlpha default-source preference writes with transcript evidence."""

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
PREFERENCE_RE = re.compile(
    r"linqalpha as (?:your|the) default source|"
    r"linqalpha connector by default|"
    r"saved via /linq-alpha:setup",
    re.IGNORECASE,
)
CLAUDE_MD_RE = re.compile(r"(?:^|[/\\])\.claude[/\\]CLAUDE\.md$", re.IGNORECASE)
NEGATIVE_RE = re.compile(r"\b(no|nope|don't|do not|not now|decline)\b", re.IGNORECASE)
POSITIVE_RE = re.compile(
    r"^(?:yes|y|yes[,.]? remember it|remember it|please (?:do )?remember it|"
    r"sure[,.]? remember it|ok(?:ay)?[,.]? remember it|네|예|응|저장해|기억해)(?:[.!\s]*)$",
    re.IGNORECASE,
)


def emit_deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
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


def transcript_messages(path: str) -> list[tuple[str, str]]:
    if not path:
        return []
    transcript = Path(path)
    if not transcript.is_file() or transcript.stat().st_size > 20_000_000:
        return []
    messages: list[tuple[str, str]] = []
    try:
        for line in transcript.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            message = event.get("message") if isinstance(event, dict) else None
            if isinstance(message, dict):
                role = str(message.get("role") or event.get("type") or "").lower()
                text = "\n".join(text_fragments(message.get("content")))
            elif isinstance(event, dict):
                role = str(event.get("role") or event.get("type") or "").lower()
                text = "\n".join(text_fragments(event.get("content") or event.get("text")))
            else:
                continue
            if role in {"user", "human"}:
                messages.append(("user", text.strip()))
            elif role in {"assistant", "agent"}:
                messages.append(("assistant", text.strip()))
    except OSError:
        return []
    return messages


def clear_opt_in(messages: list[tuple[str, str]]) -> bool:
    for index in range(len(messages) - 1, -1, -1):
        role, text = messages[index]
        if role != "assistant" or QUESTION not in text:
            continue
        following_users = [body for role, body in messages[index + 1 :] if role == "user" and body]
        if not following_users:
            return False
        answer = following_users[0].strip()
        return not NEGATIVE_RE.search(answer) and bool(POSITIVE_RE.fullmatch(answer))
    return False


def written_payload(tool_name: str, tool_input: dict[str, Any]) -> tuple[str, bool]:
    lower_name = tool_name.lower()
    if "memory_" in lower_name:
        return json.dumps(tool_input, ensure_ascii=False), True
    if tool_name == "Write":
        path = str(tool_input.get("file_path", ""))
        return str(tool_input.get("content", "")), bool(CLAUDE_MD_RE.search(path))
    if tool_name == "Edit":
        path = str(tool_input.get("file_path", ""))
        return str(tool_input.get("new_string", "")), bool(CLAUDE_MD_RE.search(path))
    if tool_name == "MultiEdit":
        path = str(tool_input.get("file_path", ""))
        edits = tool_input.get("edits")
        if not isinstance(edits, list):
            return "", False
        written = "\n".join(
            str(edit.get("new_string", "")) for edit in edits if isinstance(edit, dict)
        )
        return written, bool(CLAUDE_MD_RE.search(path))
    if tool_name == "Bash":
        command = str(tool_input.get("command", ""))
        targets_claude_md = bool(re.search(r"\.claude[/\\]CLAUDE\.md", command, re.I))
        return command, targets_claude_md
    return "", False


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        # The hook runs on every Edit, Write, MultiEdit and Bash call. Unparsable
        # input tells us nothing about a preference write, so allow and let the
        # unrelated call through.
        return
    tool_name = str(event.get("tool_name", ""))
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return
    written, relevant_target = written_payload(tool_name, tool_input)
    if not relevant_target or not PREFERENCE_RE.search(written):
        return
    messages = transcript_messages(str(event.get("transcript_path", "")))
    if clear_opt_in(messages):
        return
    emit_deny(
        "linq-alpha opt-in guard: this preference write is not backed by the setup "
        f"question and a clear user opt-in in the current transcript. Ask exactly: '{QUESTION}' "
        "and wait for an explicit yes before retrying. If the user declines, do not save."
    )


if __name__ == "__main__":
    main()
