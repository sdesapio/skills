"""Integration tests use disposable Git repositories and home directories."""

import importlib.machinery
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/install-thoughts"
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
        (self.repo / "thoughts").mkdir()
        self.home.mkdir()
        shutil.copyfile(SCRIPT, self.repo / "scripts/install-thoughts")
        (self.repo / "thoughts/SKILL.md").write_text("---\nname: thoughts\n---\nVersion one\n")
        (self.repo / "thoughts/thoughts-skill.mdc").write_text("Version one rule\n")
        self.git("init", "-q")
        self.git("config", "user.email", "installer-test@example.invalid")
        self.git("config", "user.name", "Installer Test")
        self.git("config", "commit.gpgsign", "false")
        self.commit()
        self.installer = installer_module.Installer(self.home)

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], stderr=subprocess.PIPE).decode().strip()

    def commit(self):
        self.git("add", ".")
        self.git("commit", "-qm", "fixture version")
        return self.git("rev-parse", "HEAD")

    def run_cli(self, *args, ok=True):
        result = subprocess.run(
            [sys.executable, str(self.repo / "scripts/install-thoughts"), "--home", str(self.home), *args],
            capture_output=True, text=True,
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
        (self.repo / "thoughts/SKILL.md").write_text("Version two\n")
        (self.repo / "thoughts/thoughts-skill.mdc").write_text("Version two rule\n")
        return self.commit()

    def test_dry_run_writes_nothing_then_install_check_and_noop(self):
        before = self.tree()
        self.run_cli("--dry-run")
        self.assertEqual(before, self.tree())
        self.assertFalse(self.installer.root.exists())
        self.run_cli()
        state = self.installer.state()
        self.assertEqual(state["revision"], self.git("rev-parse", "HEAD"))
        for target, source in installer_module.SOURCES.items():
            self.assertEqual((self.home / target).read_bytes(), (self.repo / source).read_bytes())
        self.run_cli("--check")
        before = self.tree()
        self.assertIn("Already installed", self.run_cli())
        self.assertEqual(before, self.tree())

    def test_adopts_matching_files_and_first_rollback_restores_original(self):
        self.target().parent.mkdir(parents=True)
        shutil.copyfile(self.repo / "thoughts/SKILL.md", self.target())
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

    def test_dirty_or_staged_source_blocks_install(self):
        source = self.repo / "thoughts/SKILL.md"
        original = source.read_bytes()
        source.write_text("Uncommitted\n")
        self.assertIn("Commit or discard", self.run_cli(ok=False))
        self.git("add", "thoughts/SKILL.md")
        source.write_bytes(original)
        self.assertIn("Commit or discard", self.run_cli(ok=False))
        self.assertFalse(self.target().exists())

    def test_update_rollback_and_recorded_check_with_newer_source(self):
        self.run_cli()
        original_files, original_state = self.installer.snapshot(), self.installer.state()
        revision = self.new_version()
        self.assertIn("Repository source differs", self.run_cli("--check"))
        self.run_cli()
        self.assertEqual(self.installer.state()["revision"], revision)
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

        with patch.object(installer_module, "REPO", self.repo), patch.object(self.installer, "write", fail_once):
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

        with patch.object(installer_module, "REPO", self.repo), patch.object(self.installer, "apply", interrupted_apply):
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

        with patch.object(installer_module, "REPO", self.repo), patch.object(self.installer, "write", fail_record_once):
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


if __name__ == "__main__":
    unittest.main()
