# Cursor Agent Skills

Reusable [Cursor](https://cursor.com) agent skills for iOS and macOS development. Each subdirectory is a self-contained skill that can be installed independently.

## Available Skills

| Skill | Description |
|---|---|
| [marketing-capture](marketing-capture/) | Automated App Store screenshot capture for iOS and watchOS apps |
| [thoughts](thoughts/) | Epistemological framework for reasoning with integrity, objectivity, and honesty |

## Installation

### Option A: Install all skills

Clone the repo into your Cursor skills directory:

```bash
git clone https://github.com/sdesapio/skills ~/.cursor/skills/sdesapio-skills
```

Every subdirectory becomes an available skill automatically.

### Option B: Install a single skill

Clone the repo somewhere and copy the skill you want:

```bash
git clone https://github.com/sdesapio/skills /tmp/cursor-skills
cp -r /tmp/cursor-skills/marketing-capture ~/.cursor/skills/
```

### Updating

If you used Option A:

```bash
cd ~/.cursor/skills/sdesapio-skills && git pull
```

If you used Option B, repeat the copy step.

## Usage

Once installed, skills activate automatically when you describe the relevant task to the agent. For example:

- "Build the screen capture mechanism" or "add marketing screenshots" triggers the **marketing-capture** skill.

Each skill's `SKILL.md` contains the full instructions the agent follows. The `examples.md` (when present) provides concrete implementation patterns from real projects.

## License

MIT
