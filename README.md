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

### Thoughts: managed installation (recommended)

The Git repository is the editable source of truth. The copies in `~/.agents/skills/`
and `~/.cursor/skills/`, and the Cursor companion rule, are installed releases.
Edit the repository files, review and commit them, then deploy with:

```bash
./scripts/install-thoughts --dry-run
./scripts/install-thoughts
./scripts/install-thoughts --check
```

Run these from a local checkout of this repository. Requires Git and Python 3.9+
on macOS or Linux; no Python packages or network access are required. Installation
uses the local HEAD commit and never fetches, pulls, commits, or pushes.
Both Thoughts source files must match HEAD and have no staged changes. Unrelated
working-tree changes do not prevent installation.

The installer deploys:

- `thoughts/SKILL.md` to `~/.agents/skills/thoughts/SKILL.md` and
  `~/.cursor/skills/thoughts/SKILL.md`.
- `thoughts/thoughts-skill.mdc` to `~/.cursor/rules/thoughts-skill.mdc`.

The companion rule already references the installed Cursor skill path. The
installer manages only these three files, leaving other skills and rules alone.
If Thoughts gains additional resource files, extend the installer's source map
and tests before releasing that version.

On first installation, missing files are created and existing exact matches are
adopted. Divergent existing files are refused: reconcile their changes into the
repository before retrying. Later installations check existing files against
the recorded checksums before updating; modified or deleted files block the
update. There is no force-overwrite option. Symlinked destinations or parent
directories are refused to avoid modifying a different installation indirectly.

Backups, SHA-256 checksums, and the installed Git revision are kept in
`~/.local/state/thoughts-installer/`. Keep this directory for rollback. Backups are
retained; they contain only the managed files and installation records.

Available commands:

- `./scripts/install-thoughts --dry-run`: preflight the source and destinations,
  list intended changes, and write nothing.
- `./scripts/install-thoughts --check`: verify all three files against the recorded
  installation. A newer/different repository source is reported separately and
  does not fail verification of an intact installed release. No record or changed
  installed content exits with an error.
- `./scripts/install-thoughts --rollback`: restore the previous file contents,
  permissions, and installation record. Subsequent local edits block rollback.
  Repeating rollback walks back through recorded installations. Rolling back the
  first installation restores the original files (or their absence) and removes
  the managed record; `--check` then reports no recorded installation.
- `./scripts/install-thoughts --recover`: restore the state before an interrupted
  install or rollback. Further edits after interruption are preserved by refusing
  recovery until those changes are reconciled.
- `./scripts/install-thoughts --home /path/to/test-home`: use an alternate home
  directory, including its installation records, for testing.

Writes replace each file atomically and verify all files before reporting success.
An ordinary write failure triggers restoration; a process interruption leaves a
recovery journal and blocks further updates until recovery. The three destinations
are not a single filesystem transaction: avoid running the skill or manually
editing its files during installation. Concurrent installer writes are locked out.

Run the isolated integration tests with:

```bash
python3 -m unittest discover -s tests -v
```

The tests use temporary repositories and home directories, never your installed
skills. To publish an update, commit and push through the normal Git workflow;
on another machine, update its checkout explicitly before running the installer.

### Manual installation alternatives

The following copy-based instructions are retained for existing Cursor setups.
For Thoughts, prefer the managed installer above and do not alternate between
manual copying and managed updates. Reconcile any previous manual installation
with repository source before adopting it.

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

For managed Thoughts installations, update your local checkout and run
`./scripts/install-thoughts`. The manual steps below apply only to manual installs.

If you used Option A:

```bash
cd ~/.cursor/skills/sdesapio-skills && git pull
cp thoughts/thoughts-skill.mdc ~/.cursor/rules/
```

If you used Option B, repeat the copy steps (skill directory and, for thoughts, the rule into `~/.cursor/rules/`).

## Usage

Once installed, skills activate automatically when you describe the relevant task to the agent. For example:

- "Build the screen capture mechanism" or "add marketing screenshots" triggers the **marketing-capture** skill.
- A substantive **"Thoughts?"** request triggers the **thoughts** skill's council workflow and compact substance receipt. Three participants form independent positions, cross-review them, and verify the chair's final synthesis. The chair selects distinct available reasoning models when the host supports it.
- Ordinary opinion requests and challenges use the lighter Method. "Quick take, no council" overrides full review. Quoting the trigger or discussing the skill does not automatically launch a council.
- The workflow uses the host's native subagent tools. With limited model diversity it reports the actual diversity; with missing participants it reports partial review; with delegation unavailable it discloses a single-model fallback. Installing this skill does not add models, enable tools, or change application settings.

Each skill's `SKILL.md` contains the full instructions the agent follows. The `examples.md` (when present) provides concrete implementation patterns from real projects. Thoughts also ships `thoughts-skill.mdc`, a small Cursor routing rule that delegates to the skill instead of duplicating the review procedure. The managed installer deploys both together.

The Thoughts behavioral fixtures and human-review criteria are in
[`tests/thoughts-evaluation.md`](tests/thoughts-evaluation.md). They cover the council
workflow, trigger intent, lightweight overrides, unsupported claims, contradictions,
equal evidentiary standards, and truthful fallback reporting. Recorded validation
is in [`tests/thoughts-validation.md`](tests/thoughts-validation.md); smoke tests do
not establish a measured improvement over the previous skill.

## License

MIT
