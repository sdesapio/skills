# Handoff

Maintain concise project state and produce a ready-to-paste continuation prompt
for a fresh chat. Works across project types, including projects without Git or
an existing `state.md`.

## Install in Codex

Copy this entire `handoff/` directory, including `agents/openai.yaml`, into
`~/.codex/skills/handoff/` (or `$CODEX_HOME/skills/handoff/` when using a custom
Codex home). Preserve and reconcile any existing local edits before replacing an
installed copy. Start a fresh chat, then say **"Prepare handoff"** or invoke
**`$handoff`**.

The skill updates the project's existing state document, keeps active context
concise, links or archives useful history, and returns a continuation prompt.
The 100–150 line guideline never justifies losing binding decisions, open issues,
or verification limitations. Invoking it does not authorize implementation,
committing, pushing, deployment, or creating another chat.

The editable instructions are in [SKILL.md](SKILL.md). Update this source first,
then copy the updated folder into your installation.
