# Skills

Agent skills for Codex and Cursor. Each top-level skill folder is self-contained.
Open a skill's instructions below or copy its folder from this repository; you do
not need the other skills.

## Thoughts

Thoughts instructs an AI agent to examine ideas with integrity, evidence, and
valid reasoning. It targets the failures that make agent answers hard to trust:
agreeing to please, hedging to avoid a conclusion, and stating unsupported claims
as fact.

Ask for an opinion, challenge the agent's reasoning, or end a message with
**"Thoughts?"**. The agent separates facts, inferences, and value judgments,
examines the premises, and commits to a conclusion at the confidence the evidence
supports. Say **"Thoughts? Full council"** to have independent agents assess the
question, review each other's work, and verify one integrated answer.

Installation is two files: [`SKILL.md`](thoughts/SKILL.md) and, for Cursor, the
companion rule [`thoughts-skill.mdc`](thoughts/thoughts-skill.mdc). The
[Thoughts README](thoughts/README.md#install) says where to copy each one, and
has commands to download them directly. The
[recorded validation](thoughts/tests/validation.md) states what has been tested
and what has not.

## Other skills

- **[Handoff](handoff/README.md)** - Preserve concise project state and prepare
  a continuation prompt for a fresh chat.
- **[Project Docs](project-docs/SKILL.md)** - Maintain project architecture,
  current state, and on-demand history, with Codex and Cursor context loaders.
- **[Marketing Capture](marketing-capture/SKILL.md)** - Set up automated App Store
  screenshot capture for iOS and watchOS. Copy the complete `marketing-capture/`
  folder into your agent's skills directory, including its templates and examples.

Each skill contains its own supporting resources and maintainer tooling, where
needed. Generated download packages exclude tests and development tools unless
explicitly offered as an optional installer.

## Maintaining a local installation

For personal development, keep this checkout as the source of truth and symlink
individual skill folders into your user skills directory. Codex supports skill
folder symlinks. For example, if this checkout is at `~/_Projects/skills`,
the Project Docs installation is:

```bash
mkdir -p "$HOME/.agents/skills"
ln -s "$HOME/_Projects/skills/project-docs" "$HOME/.agents/skills/project-docs"
```

Run this only when the destination is absent. If a copy already exists, compare
and preserve any unique changes before replacing it with the link. Edit the
repository files, then commit and push those changes; there is no second installed
copy to synchronize. Keep this checkout at a stable path and on the revision you
want to use. If changes do not appear in Codex, restart it.

Avoid another installation of the same skill under a second discovery directory.
For project collaborators, install from this repository separately. If a project
must vendor a copy, record its upstream revision and treat it as a versioned
dependency, with changes maintained here rather than independently in both repos.

[MIT license](LICENSE).
