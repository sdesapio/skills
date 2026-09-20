# Skills

Each top-level skill folder is self-contained. Open a skill's instructions below
or copy its folder from this repository; you do not need the other skills.

- **[Thoughts](thoughts/README.md)** — Examine ideas with integrity, evidence,
  and valid reasoning. [Download the skill](https://github.com/sdesapio/skills/releases/download/thoughts-v1.1.0/thoughts.zip)
  or [download with the optional installer](https://github.com/sdesapio/skills/releases/download/thoughts-v1.1.0/thoughts-managed.zip).
- **[Handoff](handoff/README.md)** — Preserve concise project state and prepare
  a continuation prompt for a fresh chat.
- **[Project Docs](project-docs/SKILL.md)** — Maintain project architecture,
  current state, and on-demand history, with Codex and Cursor context loaders.
- **[Marketing Capture](marketing-capture/SKILL.md)** — Set up automated App Store
  screenshot capture for iOS and watchOS. Copy the complete `marketing-capture/`
  folder into your agent's skills directory, including its templates and examples.

This repository is private; repository and release downloads require access.
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
