"""Exercise the downloads as a recipient without a checkout or Git executable."""

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile


SOURCE = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_download_contents_reproducibility_and_standalone_lifecycle(self):
        with tempfile.TemporaryDirectory(prefix="thoughts-download-") as directory:
            root = Path(directory)
            source = root / "isolated-source" / "thoughts"
            shutil.copytree(SOURCE, source, ignore=shutil.ignore_patterns("__pycache__"))
            (source / "personal-notes.txt").write_text("Do not distribute this file.\n")
            env = {**os.environ, "PATH": str(root / "no-executables")}

            def run(*args):
                result = subprocess.run([sys.executable, *map(str, args)], env=env,
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                return result.stdout

            output = root / "downloads"
            second = root / "second-build"
            run(source / "scripts/build_packages.py", "--output", output)
            run(source / "scripts/build_packages.py", "--output", second)
            for name in ("thoughts.zip", "thoughts-managed.zip", "SHA256SUMS.txt"):
                self.assertEqual((output / name).read_bytes(), (second / name).read_bytes())
            for line in (output / "SHA256SUMS.txt").read_text().splitlines():
                checksum, name = line.split()
                self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), checksum)

            basic = {"thoughts/SKILL.md", "thoughts/README.md", "thoughts/LICENSE",
                     "thoughts/thoughts-skill.mdc"}
            for name, expected in (("thoughts.zip", basic),
                                   ("thoughts-managed.zip", basic | {"thoughts/scripts/install.py"})):
                with zipfile.ZipFile(output / name) as bundle:
                    self.assertEqual(set(bundle.namelist()), expected)
                    for member in expected:
                        self.assertEqual(bundle.read(member), (source / member.removeprefix("thoughts/")).read_bytes())
                    bundle.extractall(root / name.removesuffix(".zip"))

            # Discard the source to prove the extracted package has no dependency on it.
            shutil.rmtree(source.parent)
            package = root / "thoughts-managed" / "thoughts"
            installer = package / "scripts/install.py"
            home = root / "recipient-home"
            original = (package / "SKILL.md").read_bytes()
            run(installer, "--home", home, "--target", "both", "--dry-run")
            self.assertFalse(home.exists())
            run(installer, "--home", home, "--target", "both")
            run(installer, "--home", home, "--check")
            self.assertEqual((home / ".agents/skills/thoughts/SKILL.md").read_bytes(), original)
            self.assertEqual((home / ".cursor/skills/thoughts/SKILL.md").read_bytes(), original)
            (package / "SKILL.md").write_bytes(original + b"\nTest update.\n")
            run(installer, "--home", home)
            self.assertEqual((home / ".agents/skills/thoughts/SKILL.md").read_bytes(), original + b"\nTest update.\n")
            run(installer, "--home", home, "--rollback")
            self.assertEqual((home / ".agents/skills/thoughts/SKILL.md").read_bytes(), original)
            run(installer, "--home", home, "--check")
            run(installer, "--home", home, "--rollback")
            self.assertFalse((home / ".agents/skills/thoughts/SKILL.md").exists())
            self.assertFalse((home / ".cursor/rules/thoughts-skill.mdc").exists())
            self.assertFalse((home / ".local/state/thoughts-installer/state.json").exists())


if __name__ == "__main__":
    unittest.main()
