# Thoughts

Examine ideas with integrity, evidence, and valid reasoning. Identity and
noncontradiction are foundational; conclusions must follow from evidence and
valid inference.

## Download and install

[Download thoughts.zip](https://github.com/sdesapio/skills/releases/download/thoughts-v1.1.0/thoughts.zip)
and extract it. It contains one `thoughts/` folder with the skill, these
instructions, the MIT license, and the companion Cursor rule. No Git, Python,
or installer is needed for manual installation.

For **Codex**, create `~/.agents/skills/thoughts/` and copy `SKILL.md` into it.

For **Cursor**, create `~/.cursor/skills/thoughts/` and copy `SKILL.md` into it.
Also copy `thoughts-skill.mdc` into `~/.cursor/rules/`, creating that directory if
needed. The rule points to the installed Cursor skill at the path above.

Keep `LICENSE` with any copy you redistribute. Preserve existing local edits
before replacing an installed file. If you already use the managed installer,
use it for updates as well so its checksums and backups remain consistent.
Start a fresh chat after installation so the host can load the skill.

Downloads from this private repository require access. A recipient of a shared
ZIP can install it without GitHub access. Release assets also include
`SHA256SUMS.txt` for checking the downloaded archives.

## Use

**"Thoughts?"**, a direct skill invocation, opinions, and reasoning challenges
use the full Method in the current conversation by default. Integrity, evidence,
identity, and noncontradiction apply in every mode.

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

[Download thoughts-managed.zip](https://github.com/sdesapio/skills/releases/download/thoughts-v1.1.0/thoughts-managed.zip)
if you want checksum checks, backups, rollback, and interrupted-update recovery.
This package adds `scripts/install.py`. It needs Python 3.9+ on macOS or Linux,
uses only the standard library, and requires neither Git nor network access.

From inside the extracted `thoughts/` folder, select `codex`, `cursor`, or `both`:

```bash
python3 scripts/install.py --target both --dry-run
python3 scripts/install.py --target both
python3 scripts/install.py --check
```

The installer manages only `SKILL.md` at the selected app destinations above,
plus the companion rule for Cursor. It does not install documentation or tests
into the app. Codex-only installation does not create or inspect an unmanaged
Cursor installation, and vice versa.

For updates, download and extract a new managed package, then run its installer.
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
tests live here; sibling skill folders are not dependencies. The basic download
contains only `SKILL.md`, `README.md`, `LICENSE`, and `thoughts-skill.mdc`. The
managed download adds only `scripts/install.py`. Tests and the package builder
remain in the repository.

From this source folder, run:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/build_packages.py --output /tmp/thoughts-release
```

The builder uses an explicit file list, produces both ZIPs and `SHA256SUMS.txt`,
and uses fixed ZIP timestamps and permissions. Build from the reviewed release
commit, tag it with a skill-specific version such as `thoughts-v1.1.0`, and attach
all three artifacts to that GitHub release. Update the versioned download links
in this README and the repository catalog for each release. Generated artifacts
are not committed to the repository.

The installer reads the files in its own folder, including uncommitted edits.
Review and commit source changes before deploying a release. If the skill gains
runtime resources, update the installer and package file lists together.

[Behavioral fixtures](https://github.com/sdesapio/skills/blob/master/thoughts/tests/evaluation.md)
and [recorded validation](https://github.com/sdesapio/skills/blob/master/thoughts/tests/validation.md)
are maintainer material. Behavioral smoke tests do not establish a measured
improvement over the previous skill.

[MIT license](LICENSE).
