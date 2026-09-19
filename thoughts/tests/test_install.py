"""Integration tests use standalone packages and disposable home directories; no Git."""

import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/install.py"
loader = importlib.machinery.SourceFileLoader("thoughts_installer", str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
installer_module = importlib.util.module_from_spec(spec)
loader.exec_module(installer_module)


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="thoughts-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root / "repo"
        self.home = self.root / "home"
        (self.repo / "scripts").mkdir(parents=True)
        self.home.mkdir()
        shutil.copyfile(SCRIPT, self.repo / "scripts/install.py")
        (self.repo / "SKILL.md").write_text("---\nname: thoughts\n---\nVersion one\n")
        (self.repo / "thoughts-skill.mdc").write_text("Version one rule\n")
        self.installer = installer_module.Installer(self.home)

    def run_cli(self, *args, ok=True):
        result = subprocess.run(
            [sys.executable, str(self.repo / "scripts/install.py"), "--home", str(self.home), *args],
            capture_output=True, text=True,
            env={**os.environ, "PATH": str(self.root / "no-executables")},
        )
        if ok:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def tree(self):
        return {str(path.relative_to(self.home)): path.read_bytes()
                for path in self.home.rglob("*") if path.is_file() and path.name != "lock"}

    def target(self):
        return self.home / ".agents/skills/thoughts/SKILL.md"

    def new_version(self):
        (self.repo / "SKILL.md").write_text("Version two\n")
        (self.repo / "thoughts-skill.mdc").write_text("Version two rule\n")
        return "Version two\n"

    def test_dry_run_writes_nothing_then_install_check_and_noop(self):
        before = self.tree()
        self.run_cli("--dry-run")
        self.assertEqual(before, self.tree())
        self.assertFalse(self.installer.root.exists())
        self.run_cli()
        state = self.installer.state()
        self.assertEqual(state["schema"], 2)
        self.assertEqual(len(state["revision"]), 64)
        for target, source in installer_module.SOURCES.items():
            self.assertEqual((self.home / target).read_bytes(), (self.repo / source).read_bytes())
        self.run_cli("--check")
        before = self.tree()
        self.assertIn("Already installed", self.run_cli())
        self.assertEqual(before, self.tree())

    def test_adopts_matching_files_and_first_rollback_restores_original(self):
        self.target().parent.mkdir(parents=True)
        shutil.copyfile(self.repo / "SKILL.md", self.target())
        self.target().chmod(0o640)
        original = self.installer.snapshot()
        self.run_cli()
        self.run_cli("--rollback")
        self.assertEqual(original, self.installer.snapshot())
        self.assertIsNone(self.installer.state())
        self.run_cli("--check", ok=False)

    def test_divergent_unmanaged_file_is_never_overwritten(self):
        self.target().parent.mkdir(parents=True)
        self.target().write_text("Unpublished local changes\n")
        before = self.tree()
        output = self.run_cli(ok=False)
        self.assertIn("Unexpected local changes", output)
        self.assertIn("+Unpublished local changes", output)
        self.assertEqual(before, self.tree())
        self.assertFalse(self.installer.record.exists())

    def test_managed_drift_blocks_update_rollback_and_check(self):
        self.run_cli()
        self.new_version()
        self.target().write_text("Local edit\n")
        before = self.tree()
        for args in ((), ("--dry-run",), ("--rollback",), ("--check",)):
            self.run_cli(*args, ok=False)
            self.assertEqual(before, self.tree())

    def test_deleted_managed_file_blocks_update(self):
        self.run_cli()
        self.target().unlink()
        self.run_cli(ok=False)
        self.assertFalse(self.target().exists())

    def test_missing_or_symlinked_source_blocks_install(self):
        source = self.repo / "SKILL.md"
        source.unlink()
        self.assertIn("regular source file", self.run_cli(ok=False))
        source.symlink_to(self.repo / "thoughts-skill.mdc")
        self.assertIn("regular source file", self.run_cli(ok=False))
        self.assertFalse(self.target().exists())

    def test_update_rollback_and_recorded_check_with_newer_source(self):
        self.run_cli()
        original_files, original_state = self.installer.snapshot(), self.installer.state()
        self.new_version()
        self.assertIn("Package source differs", self.run_cli("--check"))
        self.run_cli()
        self.assertNotEqual(self.installer.state()["revision"], original_state["revision"])
        self.assertEqual(self.target().read_text(), "Version two\n")
        self.run_cli("--rollback")
        self.assertEqual(self.installer.snapshot(), original_files)
        self.assertEqual(self.installer.state(), original_state)
        self.run_cli("--check")

    def test_symlink_file_or_parent_is_refused(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.home / ".agents").symlink_to(outside, target_is_directory=True)
        self.assertIn("symlink", self.run_cli(ok=False))
        self.assertEqual(list(outside.iterdir()), [])

    def test_damaged_backup_refused_before_writes(self):
        self.run_cli()
        backup_path = self.installer.backups / (self.installer.state()["backup"] + ".json")
        backup = json.loads(backup_path.read_text())
        backup["files"][next(iter(installer_module.SOURCES))] = {
            "data": "YWJj", "sha256": "wrong", "mode": 0o644,
        }
        backup_path.write_text(json.dumps(backup))
        before = self.tree()
        self.run_cli("--rollback", ok=False)
        self.assertEqual(before, self.tree())

    def test_partial_write_failure_restores_files_and_record(self):
        self.run_cli()
        before, old_state = self.installer.snapshot(), self.installer.state()
        self.new_version()
        original_write = self.installer.write
        failed = False

        def fail_once(path, *args, **kwargs):
            nonlocal failed
            if path == self.home / ".cursor/skills/thoughts/SKILL.md" and not failed:
                failed = True
                raise OSError("simulated disk error")
            return original_write(path, *args, **kwargs)

        with patch.object(installer_module, "SKILL_ROOT", self.repo), patch.object(self.installer, "write", fail_once):
            with self.assertRaisesRegex(installer_module.InstallError, "previous files were restored"):
                self.installer.install()
        self.assertEqual(self.installer.snapshot(), before)
        self.assertEqual(self.installer.state(), old_state)
        self.assertFalse(self.installer.pending.exists())

    def test_interruption_recovery_and_post_interruption_edits(self):
        self.run_cli()
        before, old_state = self.installer.snapshot(), self.installer.state()
        self.new_version()

        def interrupted_apply(files):
            item = files[".agents/skills/thoughts/SKILL.md"]
            self.installer.write(self.target(), installer_module.unpack(item), item["mode"])
            raise KeyboardInterrupt()

        with patch.object(installer_module, "SKILL_ROOT", self.repo), patch.object(self.installer, "apply", interrupted_apply):
            with self.assertRaises(KeyboardInterrupt):
                self.installer.install()
        self.assertTrue(self.installer.pending.exists())
        self.assertIn("--recover", self.run_cli("--check", ok=False))
        interrupted_data = self.target().read_bytes()
        self.target().write_text("Edit after interruption\n")
        self.assertIn("refusing to overwrite", self.run_cli("--recover", ok=False))
        self.assertEqual(self.target().read_text(), "Edit after interruption\n")
        self.target().write_bytes(interrupted_data)
        self.run_cli("--recover")
        self.assertEqual(self.installer.snapshot(), before)
        self.assertEqual(self.installer.state(), old_state)
        self.assertFalse(self.installer.pending.exists())

    def test_concurrent_installer_is_refused(self):
        with self.installer.lock():
            self.assertIn("Another Thoughts installer", self.run_cli(ok=False))

    def test_record_write_failure_restores_previous_release(self):
        self.run_cli()
        before, old_state = self.installer.snapshot(), self.installer.state()
        self.new_version()
        original_write = self.installer.write
        failed = False

        def fail_record_once(path, *args, **kwargs):
            nonlocal failed
            if path == self.installer.record and not failed:
                failed = True
                raise OSError("simulated record write error")
            return original_write(path, *args, **kwargs)

        with patch.object(installer_module, "SKILL_ROOT", self.repo), patch.object(self.installer, "write", fail_record_once):
            with self.assertRaisesRegex(installer_module.InstallError, "previous files were restored"):
                self.installer.install()
        self.assertEqual(self.installer.snapshot(), before)
        self.assertEqual(self.installer.state(), old_state)

    def test_failed_rollback_preserves_current_release(self):
        self.run_cli()
        self.new_version()
        self.run_cli()
        before, old_state = self.installer.snapshot(), self.installer.state()
        original_write = self.installer.write
        failed = False

        def fail_once(path, *args, **kwargs):
            nonlocal failed
            if path == self.home / ".cursor/skills/thoughts/SKILL.md" and not failed:
                failed = True
                raise OSError("simulated rollback write error")
            return original_write(path, *args, **kwargs)

        with patch.object(self.installer, "write", fail_once):
            with self.assertRaisesRegex(installer_module.InstallError, "previous files were restored"):
                self.installer.rollback()
        self.assertEqual(self.installer.snapshot(), before)
        self.assertEqual(self.installer.state(), old_state)

    def test_codex_install_does_not_touch_cursor_symlink(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.home / ".cursor").symlink_to(outside, target_is_directory=True)
        self.run_cli("--target", "codex")
        self.assertTrue(self.target().exists())
        self.assertEqual(list(outside.iterdir()), [])
        self.assertEqual(set(self.installer.state()["files"]), {".agents/skills/thoughts/SKILL.md"})
        self.new_version()
        self.run_cli()  # Default update retains Codex-only scope.
        self.assertEqual(self.target().read_text(), "Version two\n")
        self.run_cli("--check")
        self.run_cli("--rollback")
        self.run_cli("--rollback")
        self.assertFalse(self.target().exists())
        self.assertIsNone(self.installer.state())

    def test_cursor_install_leaves_unmanaged_codex_edit_alone(self):
        self.target().parent.mkdir(parents=True)
        self.target().write_text("Personal Codex copy\n")
        self.run_cli("--target", "cursor")
        self.assertEqual(len(self.installer.state()["files"]), 2)
        self.run_cli("--check")
        self.assertIn("Personal Codex", self.target().read_text())
        before = self.tree()
        self.run_cli("--target", "both", ok=False)
        self.assertEqual(before, self.tree())
        self.run_cli("--rollback")
        self.assertEqual(self.target().read_text(), "Personal Codex copy\n")
        self.assertFalse((self.home / ".cursor/rules/thoughts-skill.mdc").exists())

    def test_adding_a_target_and_rollback_preserves_previous_scope(self):
        self.run_cli("--target", "codex")
        state = self.installer.state()
        self.new_version()
        self.run_cli("--target", "cursor")
        self.assertNotEqual(self.target().read_text(), "Version two\n")
        self.assertEqual((self.home / ".cursor/skills/thoughts/SKILL.md").read_text(), "Version two\n")
        self.run_cli("--check")
        self.run_cli("--rollback")
        self.assertEqual(self.installer.state(), state)
        self.assertFalse((self.home / ".cursor/skills/thoughts/SKILL.md").exists())
        self.run_cli("--rollback")
        self.assertFalse(self.target().exists())

    def test_updating_one_managed_target_preserves_the_other(self):
        self.run_cli()
        before = self.installer.snapshot()
        self.new_version()
        self.run_cli("--target", "codex")
        self.assertEqual(self.target().read_text(), "Version two\n")
        cursor = ".cursor/skills/thoughts/SKILL.md"
        self.assertEqual(self.installer.snapshot()[cursor], before[cursor])
        self.run_cli("--check")
        self.run_cli("--rollback")
        self.assertEqual(self.installer.snapshot(), before)

    def test_old_git_state_migrates_and_rolls_back_through_old_backups(self):
        self.run_cli()
        old = self.installer.state()
        old.update(schema=1, revision="a" * 40)
        self.installer.write_json(self.installer.record, old)
        old_backup = (self.installer.backups / (old["backup"] + ".json")).read_bytes()
        self.run_cli("--check")
        self.run_cli()  # Same runtime files still migrate the record once.
        self.assertEqual(self.installer.state()["schema"], 2)
        self.assertEqual((self.installer.backups / (old["backup"] + ".json")).read_bytes(), old_backup)
        self.run_cli("--rollback")
        self.assertEqual(self.installer.state(), old)
        self.run_cli("--rollback")
        self.assertIsNone(self.installer.state())
        self.assertFalse(self.target().exists())

    def test_legacy_interrupted_transaction_recovers(self):
        self.run_cli()
        old = self.installer.state()
        old.update(schema=1, revision="b" * 40)
        self.installer.write_json(self.installer.record, old)
        before = self.installer.snapshot()
        after = dict(before)
        after[".agents/skills/thoughts/SKILL.md"] = installer_module.pack(b"Interrupted update\n", 0o644)
        new = dict(old, revision="c" * 40, files=installer_module.hashes(after))
        self.installer.write_json(self.installer.pending, {
            "schema": 1, "before": before, "after": after, "old_state": old, "new_state": new,
        })
        self.target().write_bytes(b"Interrupted update\n")
        self.run_cli("--recover")
        self.assertEqual(self.installer.state(), old)
        self.assertEqual(self.installer.snapshot(), before)

    def test_scope_flags_are_rejected_for_rollback(self):
        self.run_cli("--target", "codex")
        before = self.tree()
        self.run_cli("--target", "cursor", "--rollback", ok=False)
        self.assertEqual(self.tree(), before)


if __name__ == "__main__":
    unittest.main()
