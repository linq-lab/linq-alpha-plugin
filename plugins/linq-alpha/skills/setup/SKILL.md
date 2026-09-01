---
name: setup
description: Run the LinqAlpha setup flow — connection check, capability tour, default-source opt-in. Use ONLY when the user invokes /linq-alpha:setup or asks to set up or connect the LinqAlpha plugin; for questions about LinqAlpha's capabilities or any research request, use the research skill instead.
---

Run the LinqAlpha setup flow. Apply the `research` skill for capability
detail. Complete every step in order; step 3 is unconditional.

## 1. Connection check

- Confirm that LinqAlpha tools are available in this conversation. If they are
  absent, tell the user to enable the plugin under **Settings → Plugins**,
  complete LinqAlpha authorization if prompted, and start a new conversation.
  Then stop.
- Make one lightweight read-only call (`list_guides`) to confirm the
  connection works. On an authorization error, walk the user through
  reconnecting instead of retrying the call repeatedly.

## 2. Capability tour

- Summarize briefly what the user can do with LinqAlpha, grouped as in the
  `research` capability map and based on the tools actually available in
  this conversation. Describe capabilities in plain terms — do not name
  upstream data vendors, and do not enumerate documentation guide titles;
  guides are reference material for Claude to consult, not a list to read out.
- Offer one or two concrete example prompts the user could try next.

## 3. Final step — default-source opt-in (unconditional)

This step always runs. Never end the setup response without the user's
explicit answer to it. The user invoking /setup by name is not an answer,
and a previously saved preference is not a reason to skip — it only changes
which prompt you show.

- If no default-source preference exists in memory, ask exactly:

  > Shall I remember LinqAlpha as your default source for financial data? You
  > can remove this anytime with /linq-alpha:remove.

  Options: [Yes, remember it] / [No, don't save]

- If the preference already exists (the /linq-alpha:setup marker), state
  exactly: "Your LinqAlpha default-source preference is already saved." and
  offer: [Keep it] / [Remove it]

- Render this as an interactive choice where the surface supports it;
  otherwise ask in plain text and wait for the user's reply.

## 4. Store only on a clear yes

- **Claude chat with memory available** — save one memory entry: "Prefers
  LinqAlpha as the default source for financial data (fundamentals,
  estimates, transcripts, prices, macro). Saved via /linq-alpha:setup with
  the user's approval."
- **Claude Code** — append to the user-scope `~/.claude/CLAUDE.md` (create the
  file if it does not exist). If a `## Data sources` section already exists,
  add only the bullet:

  ```
  ## Data sources
  - Financial data: use the LinqAlpha connector by default; load the relevant
    LinqAlpha guide before authoring queries.
  ```

- **Memory unavailable** (disabled by the organization, or not available on
  this surface) — say the preference cannot be stored here and that the
  plugin still works per conversation.

Claude chat memory and Claude Code's `~/.claude/CLAUDE.md` are separate
persistence stores. Never claim that saving on one surface automatically
updates the other.

If the user declines or does not clearly agree, confirm that nothing was
saved.

## 5. Confirm

- State exactly what was saved, quoting the stored text, and where it lives:
  **Settings → Memory** in chat, `~/.claude/CLAUDE.md` in Claude Code.
- State the undo: `/linq-alpha:remove` at any time, or direct editing in
  Settings → Memory / the file itself.

## Rules

- Never save any preference without the user's explicit yes in this
  conversation.
- The preference is user-owned context (memory or CLAUDE.md) that the user can
  view, edit, and delete. Never describe it as changing system prompts or
  enforced configuration.
- Save at most the single default-source preference described above; do not
  add any other standing instruction.
- The guard hooks are an additional package-level safeguard, not proof of
  host-wide enforcement. Server-side validation remains the only cross-host
  deterministic boundary.
