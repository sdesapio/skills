# Cursor Agent Skills

Reusable [Cursor](https://cursor.com) agent skills for iOS and macOS development. Each subdirectory is a self-contained skill that can be installed independently. The handoff skill also works across project types in Codex.

## Available Skills

| Skill | Description |
|---|---|
| [handoff](handoff/) | "Prepare handoff": maintain concise project state and produce a fresh-chat continuation prompt |
| [marketing-capture](marketing-capture/) | Automated App Store screenshot capture for iOS and watchOS apps |
| [thoughts](thoughts/) | Epistemological framework for reasoning with integrity, objectivity, and honesty. Requires the companion always-apply rule (`thoughts/thoughts-skill.mdc`). |

## Installation

### Handoff: personal Codex installation

The repository copy in `handoff/` is the editable source. To make it available
across your Codex projects, copy that directory into `~/.codex/skills/handoff/`
(or `$CODEX_HOME/skills/handoff/` when using a custom Codex home). Preserve and
reconcile any existing local edits before replacing an installed copy.
Start a fresh chat to load the newly installed skill, then say **"Prepare handoff"**
or invoke **`$handoff`**.

The skill updates the project's existing state document, keeps active context
concise, links or archives useful history, and returns a ready-to-paste prompt.
It adapts to projects without `state.md` or Git. The 100–150 line guideline never
justifies losing binding decisions, open issues, or verification limitations.
It does not authorize implementation, committing, pushing, deployment, or
creating another chat.


### Option A: Install all skills

Clone the repo into your Cursor skills directory:

```bash
git clone https://github.com/sdesapio/skills ~/.cursor/skills/sdesapio-skills
```

Every subdirectory becomes an available skill automatically.

**Thoughts also needs its compliance rule** (skills are not always-apply; the rule is):

```bash
cp ~/.cursor/skills/sdesapio-skills/thoughts/thoughts-skill.mdc ~/.cursor/rules/
```

If you install Thoughts under Option A, update the path inside `~/.cursor/rules/thoughts-skill.mdc` so it points at `~/.cursor/skills/sdesapio-skills/thoughts/SKILL.md` (the shipped rule assumes Option B's `~/.cursor/skills/thoughts/SKILL.md`).

### Option B: Install a single skill

Clone the repo somewhere and copy the skill you want:

```bash
git clone https://github.com/sdesapio/skills /tmp/cursor-skills
cp -r /tmp/cursor-skills/marketing-capture ~/.cursor/skills/
```

For **thoughts**, install both the skill and the always-apply compliance rule:

```bash
cp -r /tmp/cursor-skills/thoughts ~/.cursor/skills/
cp /tmp/cursor-skills/thoughts/thoughts-skill.mdc ~/.cursor/rules/
```

### Updating

If you used Option A:

```bash
cd ~/.cursor/skills/sdesapio-skills && git pull
cp thoughts/thoughts-skill.mdc ~/.cursor/rules/
```

If you used Option B, repeat the copy steps (skill directory and, for thoughts, the rule into `~/.cursor/rules/`).

## Usage

Once installed, skills activate automatically when you describe the relevant task to the agent. For example:

- "Build the screen capture mechanism" or "add marketing screenshots" triggers the **marketing-capture** skill.
- Ending a message with **"Thoughts?"** triggers the **thoughts** skill (full Loop + substance receipt), gated by the always-apply compliance rule.

Each skill's `SKILL.md` contains the full instructions the agent follows. The `examples.md` (when present) provides concrete implementation patterns from real projects. Thoughts also ships `thoughts-skill.mdc` — install it into `~/.cursor/rules/` so `"Thoughts?"` is enforced every turn.

## License

MIT
