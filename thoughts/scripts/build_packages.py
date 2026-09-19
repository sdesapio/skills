#!/usr/bin/env python3
"""Build the basic and managed Thoughts downloads from this self-contained folder."""

import argparse
import hashlib
from pathlib import Path
import zipfile


SKILL_ROOT = Path(__file__).resolve().parent.parent
BASIC = ("SKILL.md", "README.md", "LICENSE", "thoughts-skill.mdc")
PACKAGES = {"thoughts.zip": BASIC, "thoughts-managed.zip": (*BASIC, "scripts/install.py")}


def build(output):
    # Read and validate the complete payload before producing any archive.
    payload = {}
    for name in dict.fromkeys(name for files in PACKAGES.values() for name in files):
        path = SKILL_ROOT / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Expected a regular package file: {path}")
        payload[name] = path.read_bytes()
    output.mkdir(parents=True, exist_ok=True)
    checksums = []
    for archive, files in PACKAGES.items():
        destination = output / archive
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for name in sorted(files):
                info = zipfile.ZipInfo("thoughts/" + name, date_time=(2020, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                bundle.writestr(info, payload[name])
        checksums.append(f"{hashlib.sha256(destination.read_bytes()).hexdigest()}  {archive}\n")
    (output / "SHA256SUMS.txt").write_text("".join(checksums), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="directory for both ZIPs and SHA256SUMS.txt")
    args = parser.parse_args()
    build(args.output)
    print(f"Built both Thoughts downloads and checksums in {args.output.resolve()}")


if __name__ == "__main__":
    main()
