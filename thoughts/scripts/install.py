#!/usr/bin/env python3
"""Install Thoughts from this folder; Python 3.9+, macOS/Linux, no Git required."""

import argparse
import base64
import binascii
import contextlib
import difflib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import uuid


SOURCES = {
    ".agents/skills/thoughts/SKILL.md": "SKILL.md",
    ".cursor/skills/thoughts/SKILL.md": "SKILL.md",
    ".cursor/rules/thoughts-skill.mdc": "thoughts-skill.mdc",
}
SKILL_ROOT = Path(__file__).resolve().parent.parent
TARGETS = {
    "codex": (".agents/skills/thoughts/SKILL.md",),
    "cursor": (".cursor/skills/thoughts/SKILL.md", ".cursor/rules/thoughts-skill.mdc"),
    "both": tuple(SOURCES),
}


class InstallError(Exception):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source_files():
    files = {}
    for target, source in SOURCES.items():
        path = SKILL_ROOT / source
        if path.is_symlink() or not path.is_file():
            raise InstallError(f"Expected a regular source file: {path}")
        files[target] = pack(path.read_bytes(), 0o644)
    # A reproducible identity for the runtime files, independent of Git or location.
    identity = json.dumps(hashes(files), sort_keys=True, separators=(",", ":")).encode()
    return digest(identity), files


def pack(data, mode):
    return {"data": base64.b64encode(data).decode(), "sha256": digest(data), "mode": mode}


def unpack(item):
    if item is None:
        return None
    try:
        data = base64.b64decode(item["data"], validate=True)
        mode = item["mode"]
        if digest(data) != item["sha256"] or type(mode) is not int or not 0 <= mode <= 0o777:
            raise ValueError("Invalid hash or file mode")
        return data
    except (KeyError, TypeError, ValueError, binascii.Error) as exc:
        raise InstallError("Invalid or damaged snapshot; nothing was restored.") from exc


def validate_files(files):
    if not isinstance(files, dict) or (not files or not set(files) <= set(SOURCES)):
        raise InstallError("Snapshot has an unexpected file list.")
    for item in files.values():
        unpack(item)


def hashes(files):
    return {name: item["sha256"] if item else None for name, item in files.items()}


def validate_state(value):
    if value is None:
        return
    if (not isinstance(value, dict) or value.get("schema") not in (1, 2)
            or not isinstance(value.get("revision"), str)
            or len(value["revision"]) not in (40, 64)
            or any(c not in "0123456789abcdef" for c in value["revision"])
            or not isinstance(value.get("files"), dict)
            or not value["files"] or not set(value["files"]) <= set(SOURCES)
            or (value.get("schema") == 1 and set(value["files"]) != set(SOURCES))
            or not isinstance(value.get("backup"), str)
            or len(value["backup"]) != 32
            or any(c not in "0123456789abcdef" for c in value["backup"])):
        raise InstallError("Invalid installation record.")
    for value_hash in value["files"].values():
        if (not isinstance(value_hash, str) or len(value_hash) != 64
                or any(c not in "0123456789abcdef" for c in value_hash)):
            raise InstallError("Invalid recorded checksum.")


class Installer:
    def __init__(self, home):
        self.home = home.expanduser().resolve()
        self.root = self.home / ".local/state/thoughts-installer"
        self.record = self.root / "state.json"
        self.pending = self.root / "pending.json"
        self.backups = self.root / "backups"
        self.safe(self.backups)

    def safe(self, path):
        # Check managed paths only; resolving --home permits macOS /tmp aliases.
        for part in (path, *path.parents):
            if part == self.home:
                break
            if part.is_symlink():
                raise InstallError(f"Refusing to replace or follow a symlink: {part}")
            if part != path and part.exists() and not part.is_dir():
                raise InstallError(f"Expected a directory: {part}")
        return path

    def read_json(self, path):
        self.safe(path)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except (ValueError, UnicodeError) as exc:
            raise InstallError(f"Cannot read valid JSON: {path}") from exc

    def state(self):
        value = self.read_json(self.record)
        if value is None and self.record.exists():
            raise InstallError("Empty installation record.")
        validate_state(value)
        return value

    def snapshot(self, names=None):
        files = {}
        for relative in (SOURCES if names is None else names):
            path = self.safe(self.home / relative)
            if not path.exists():
                files[relative] = None
            elif not path.is_file():
                raise InstallError(f"Expected a regular installed file: {path}")
            else:
                files[relative] = pack(path.read_bytes(), stat.S_IMODE(path.stat().st_mode) & 0o777)
        return files

    def write(self, path, data, mode=0o600):
        self.safe(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=".thoughts-", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fchmod(stream.fileno(), mode)
                os.fsync(stream.fileno())
            os.replace(temp_name, path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def write_json(self, path, value):
        self.write(path, (json.dumps(value, indent=2, sort_keys=True) + "\n").encode())

    def set_state(self, value):
        if value is None:
            self.safe(self.record).unlink(missing_ok=True)
        else:
            self.write_json(self.record, value)

    def apply(self, files):
        validate_files(files)
        current = self.snapshot(files)
        for relative, item in files.items():
            if current[relative] == item:
                continue
            path = self.safe(self.home / relative)
            if item is None:
                path.unlink(missing_ok=True)
            else:
                self.write(path, unpack(item), item["mode"])
        if self.snapshot(files) != files:
            raise InstallError("Installed files failed verification.")

    @contextlib.contextmanager
    def lock(self):
        self.root.mkdir(parents=True, exist_ok=True)
        lock_path = self.safe(self.root / "lock")
        with lock_path.open("a") as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise InstallError("Another Thoughts installer is running.") from exc
            yield

    def require_no_pending(self):
        if self.pending.exists() or self.pending.is_symlink():
            raise InstallError("An interrupted transaction exists. Run --recover first.")

    def ensure_expected(self, files, expected):
        actual = hashes(files)
        changed = [name for name in expected if actual.get(name) != expected[name]]
        if changed:
            details = []
            for name in changed:
                details.append(f"  {self.home / name}\n    expected: {expected[name]}\n    found:    {actual[name]}")
                source = SKILL_ROOT / SOURCES[name]
                if source.is_file() and files[name]:
                    diff = list(difflib.unified_diff(
                        source.read_text(errors="replace").splitlines(keepends=True),
                        unpack(files[name]).decode(errors="replace").splitlines(keepends=True),
                        fromfile=f"current package: {SOURCES[name]}",
                        tofile=f"installed: {name}",
                    ))
                    details.append("".join(diff[:120]))
                    if len(diff) > 120:
                        details.append("  (Diff truncated; compare the files for the full changes.)")
            raise InstallError(
                "Unexpected local changes (including missing files); nothing was overwritten:\n"
                + "\n".join(details) + "\nCompare these with the package or saved backup and reconcile first."
            )

    def transaction(self, before, old_state, after, new_state):
        journal = {"schema": 1, "before": before, "old_state": old_state,
                   "after": after, "new_state": new_state}
        # Recheck after planning, immediately before the journal and writes.
        if self.snapshot(before) != before or self.state() != old_state:
            raise InstallError("Installation changed during preflight; run again.")
        self.write_json(self.pending, journal)
        try:
            self.apply(after)
            self.set_state(new_state)
            self.pending.unlink()
        except Exception as exc:
            try:
                self.recover(announce=False)
            except Exception as recovery_error:
                raise InstallError(
                    f"Installation interrupted: {exc}. Recovery incomplete: {recovery_error}. "
                    "Keep the saved backups and run --recover after resolving the problem."
                ) from exc
            raise InstallError(f"Installation failed; previous files were restored: {exc}") from exc

    def install(self, dry_run=False, target=None):
        self.require_no_pending()
        revision, source = source_files()
        old_state = self.state()
        # Without --target, update the recorded scope; first install defaults to both.
        selected = TARGETS[target] if target else (old_state["files"] if old_state else SOURCES)
        scope = dict.fromkeys([*(old_state["files"] if old_state else ()), *selected])
        before = self.snapshot(scope)
        if old_state:
            self.ensure_expected(before, old_state["files"])
        unmanaged = {name: source[name]["sha256"] if before[name] else None
                     for name in selected if not old_state or name not in old_state["files"]}
        self.ensure_expected(before, unmanaged)
        after = dict(before)
        after.update({name: source[name] for name in selected})
        if (old_state and old_state["schema"] == 2 and before == after
                and old_state["files"] == hashes(after)):
            print("Already installed and verified.")
            return
        for relative in selected:
            action = "keep" if before[relative] == after[relative] else "install"
            print(f"{action}: {self.home / relative}")
        print(f"Runtime package SHA-256: {revision}")
        if dry_run:
            print("Dry run: no files or installation records changed.")
            return
        backup_id = uuid.uuid4().hex
        self.write_json(self.backups / f"{backup_id}.json", {
            "schema": 1, "files": before, "state": old_state,
        })
        # revision identifies the last source package; files are authoritative when
        # a user updates one app while retaining an older installation in the other.
        new_state = {"schema": 2, "revision": revision, "files": hashes(after), "backup": backup_id}
        self.transaction(before, old_state, after, new_state)
        print(f"Installed and verified. Backup: {self.backups / (backup_id + '.json')}")

    def check(self):
        self.require_no_pending()
        state = self.state()
        if not state:
            raise InstallError("No recorded installation. Run --dry-run, then install to adopt matching files.")
        self.ensure_expected(self.snapshot(state["files"]), state["files"])
        print(f"All {len(state['files'])} managed files match the installation record.")
        differences = [SOURCES[target] for target in state["files"]
                       if not (SKILL_ROOT / SOURCES[target]).is_file()
                       or digest((SKILL_ROOT / SOURCES[target]).read_bytes()) != state["files"][target]]
        if differences:
            print("Package source differs from this installation: " + ", ".join(sorted(set(differences))))

    def rollback(self):
        self.require_no_pending()
        old_state = self.state()
        if not old_state:
            raise InstallError("No recorded installation to roll back.")
        before = self.snapshot(old_state["files"])
        self.ensure_expected(before, old_state["files"])
        backup = self.read_json(self.backups / f"{old_state['backup']}.json")
        if not isinstance(backup, dict) or backup.get("schema") != 1:
            raise InstallError("Missing or invalid rollback backup.")
        after, new_state = backup.get("files"), backup.get("state")
        validate_files(after)
        validate_state(new_state)
        if set(after) != set(before):
            raise InstallError("Backup scope does not match the installation record.")
        if new_state and (not set(new_state["files"]) <= set(after)
                          or any(hashes(after)[name] != value for name, value in new_state["files"].items())):
            raise InstallError("Backup does not match its installation record.")
        self.transaction(before, old_state, after, new_state)
        label = new_state["revision"] if new_state else "the original, unmanaged installation"
        print(f"Restored {label}. Backups retained in {self.backups}.")

    def recover(self, announce=True):
        journal = self.read_json(self.pending)
        if not isinstance(journal, dict) or journal.get("schema") != 1:
            raise InstallError("No valid interrupted transaction to recover.")
        for key in ("before", "after"):
            validate_files(journal.get(key))
        for key in ("old_state", "new_state"):
            validate_state(journal.get(key))
        if set(journal["before"]) != set(journal["after"]):
            raise InstallError("Interrupted transaction has inconsistent file lists.")
        current = self.snapshot(journal["before"])
        for relative in current:
            if current[relative] not in (journal["before"][relative], journal["after"][relative]):
                raise InstallError(f"File changed after interruption; refusing to overwrite: {self.home / relative}")
        if self.state() not in (journal["old_state"], journal["new_state"]):
            raise InstallError("Installation record changed after interruption; refusing to overwrite it.")
        self.apply(journal["before"])
        self.set_state(journal["old_state"])
        self.pending.unlink()
        if announce:
            print("Recovered the files and record from before the interrupted operation.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true", help="verify files against the recorded installation")
    action.add_argument("--dry-run", action="store_true", help="show installation changes without writing")
    action.add_argument("--rollback", action="store_true", help="restore the previous installation")
    action.add_argument("--recover", action="store_true", help="undo an interrupted install or rollback")
    parser.add_argument("--target", choices=tuple(TARGETS),
                        help="install/update Codex, Cursor, or both (default: recorded scope, initially both)")
    parser.add_argument("--home", type=Path, default=Path.home(), help="alternate home directory for testing")
    args = parser.parse_args()
    if args.target and (args.check or args.rollback or args.recover):
        parser.error("--target applies only to installation or --dry-run; other actions cover the recorded transaction")
    try:
        installer = Installer(args.home)
        if args.check:
            installer.check()
        elif args.dry_run:
            installer.install(dry_run=True, target=args.target)
        else:
            with installer.lock():
                if args.rollback:
                    installer.rollback()
                elif args.recover:
                    installer.recover()
                else:
                    installer.install(target=args.target)
        return 0
    except (InstallError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
