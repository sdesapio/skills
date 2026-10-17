# Thoughts

Examine ideas with integrity, evidence, and valid reasoning. Conclusions must
follow from evidence and valid inference.

The skill rests on Aristotle's three laws of thought: identity,
noncontradiction, and excluded middle.

## Install

Installation is two files: [`SKILL.md`](SKILL.md) and the companion Cursor rule
[`thoughts-skill.mdc`](thoughts-skill.mdc). No Git, Python, or installer is
needed.

For **Codex**, create `~/.agents/skills/thoughts/` and copy `SKILL.md` into it.

For **Cursor**, create `~/.cursor/skills/thoughts/` and copy `SKILL.md` into it.
Also copy `thoughts-skill.mdc` into `~/.cursor/rules/`, creating that directory if
needed. The rule points to the installed Cursor skill at the path above.

Or download them directly:

```bash
# Codex
mkdir -p ~/.agents/skills/thoughts
curl -fsSL -o ~/.agents/skills/thoughts/SKILL.md \
  https://raw.githubusercontent.com/sdesapio/skills/master/thoughts/SKILL.md

# Cursor
mkdir -p ~/.cursor/skills/thoughts ~/.cursor/rules
curl -fsSL -o ~/.cursor/skills/thoughts/SKILL.md \
  https://raw.githubusercontent.com/sdesapio/skills/master/thoughts/SKILL.md
curl -fsSL -o ~/.cursor/rules/thoughts-skill.mdc \
  https://raw.githubusercontent.com/sdesapio/skills/master/thoughts/thoughts-skill.mdc
```

These commands overwrite existing files. Preserve local edits before running
them. If you already use the managed installer, use it for updates as well so
its checksums and backups remain consistent. Start a fresh chat after
installation so the host can load the skill. Keep the [MIT license](LICENSE) with
any copy you redistribute.

## Use

**"Thoughts?"**, a direct skill invocation, opinions, and reasoning challenges
use the full Method in the current conversation by default. Integrity, evidence,
and the foundational logical laws apply in every mode.

Say **"Thoughts? Full council"** or **"Run a council review"** to opt into
independent council review and its compact substance receipt. Council applies to
that request and the follow-up work needed to complete it. A new assessment
returns to Method unless you explicitly keep council enabled for a longer scope.
**"No council"** and **"quick take"** still select Method; they are unnecessary
under the default. Asking for a thorough assessment or a receipt alone does not
activate a council.

The agent may suggest council review when independent scrutiny could help resolve
a material uncertainty, but waits for your instruction before starting it.
Quoting triggers or discussing this skill does not invoke a council.

Council participants form independent positions, cross-review them, and verify
the chair's synthesis. The skill uses the host's available delegation tools and
reasoning models. It reports limited model diversity, partial review, or a
single-model fallback when applicable. Installing the skill does not add models,
enable tools, or change application settings.

## Optional managed installation

Use `scripts/install.py` if you want checksum checks, backups, rollback, and
interrupted-update recovery. Clone this repository, or download it with GitHub's
**Code > Download ZIP**. The installer needs Python 3.9+ on macOS or Linux and
uses only the standard library.

From inside the `thoughts/` folder, select `codex`, `cursor`, or `both`:

```bash
python3 scripts/install.py --target both --dry-run
python3 scripts/install.py --target both
python3 scripts/install.py --check
```

The installer manages only `SKILL.md` at the selected app destinations above,
plus the companion rule for Cursor. It does not install documentation or tests
into the app. Codex-only installation does not create or inspect an unmanaged
Cursor installation, and vice versa.

For updates, pull or download the repository again, then run the installer.
Without `--target`, an update uses the previously recorded destinations; a first
installation defaults to both apps. An explicit target adds or updates that app
without removing or updating the other app's existing installation. All already
managed files are checked for local changes before any update.

```bash
python3 scripts/install.py --dry-run
python3 scripts/install.py
```

Available maintenance actions:

- `--check`: verify every managed file against its recorded checksum. Differences
  between the current package and the installed version are reported separately.
- `--rollback`: undo the last installation operation, restoring prior content,
  file permissions, and the record. Repeat to walk back through earlier backups.
  The first rollback restores any original files or their absence.
- `--recover`: undo an interrupted install or rollback. Files edited after the
  interruption block recovery until those edits are reconciled.
- `--home /path/to/test-home`: use a separate home directory for testing.

Check, rollback, and recovery cover the recorded installation or transaction;
`--target` applies only to installation and dry runs.

On first installation, missing files are created and exact existing matches are
adopted. Divergent files are refused. Later updates and rollbacks refuse to
replace modified or deleted managed files. There is no force-overwrite option.
Symlinked managed destinations and parent directories are refused.

Records and backups remain in `~/.local/state/thoughts-installer/`. Keep this
folder for rollback. The installer reads the former Git-based record format and
preserves its backup chain when migrating to the new format. New records store
per-file SHA-256 checksums and the runtime-content fingerprint of the last source
package; that fingerprint is not a Git commit or an authenticity signature. Use
this new installer for subsequent maintenance, including rollback to older files.

Files are replaced atomically one at a time, then verified. A write failure
triggers restoration; interruption leaves a recovery journal. These destinations
are not a single filesystem transaction, so avoid editing or using the skill
while an install or rollback is underway. Concurrent installer writes are locked
out.

## For maintainers

This folder is the source of truth. All Thoughts-specific source, tools, and
tests live here; sibling skill folders are not dependencies. The install
instructions above read from `master`, so a push to `master` publishes the change.
Review and test before pushing.

From this source folder, run:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/build_packages.py --output /tmp/thoughts-release
```

Versioned release packages are optional. The basic package contains only
`SKILL.md`, `README.md`, `LICENSE`, and `thoughts-skill.mdc`; the managed package
adds only `scripts/install.py`. The builder uses an explicit file list, produces
both ZIPs and `SHA256SUMS.txt`, and uses fixed ZIP timestamps and permissions. To
publish one, build from the reviewed commit, tag it with a skill-specific version
such as `thoughts-v1.1.0`, and attach all three artifacts to that GitHub release.
Generated artifacts are not committed to the repository.

The installer reads the files in its own folder, including uncommitted edits.
If the skill gains runtime resources, update the installer and package file lists
together.

[Behavioral fixtures](https://github.com/sdesapio/skills/blob/master/thoughts/tests/evaluation.md)
and [recorded validation](https://github.com/sdesapio/skills/blob/master/thoughts/tests/validation.md)
are maintainer material. Behavioral smoke tests do not establish a measured
improvement over the previous skill.

[MIT license](LICENSE).
