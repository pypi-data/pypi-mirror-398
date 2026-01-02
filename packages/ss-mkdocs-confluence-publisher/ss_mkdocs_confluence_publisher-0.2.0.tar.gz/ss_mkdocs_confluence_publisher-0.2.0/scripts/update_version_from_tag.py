#!/usr/bin/env python3
import os
import re
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETUP_PATH = ROOT / "setup.py"
MARKER_PATH = ROOT / ".version_changed"

def normalize_tag(tag: str) -> str:
    """
    Normalize a release tag to a plain version string.
    Accepts tags like 'v1.2.3' or '1.2.3' and returns '1.2.3'.
    """
    tag = tag.strip()
    if tag.startswith("refs/tags/"):
        tag = tag[len("refs/tags/"):]
    if tag.lower().startswith("v"):
        tag = tag[1:]
    return tag

def get_current_version(setup_text: str) -> str:
    """
    Extract the version string from setup.py.
    Assumes a line like: version='0.1.2',
    """
    m = re.search(r"version\s*=\s*['\"]([^'\"]+)['\"]\s*,", setup_text)
    if not m:
        raise RuntimeError("Could not find version=... in setup.py")
    return m.group(1)

def replace_version(setup_text: str, new_version: str) -> str:
    return re.sub(
        r"(version\s*=\s*['\"])([^'\"]+)(['\"]\s*,)",
        rf"\g<1>{new_version}\g<3>",
        setup_text,
        count=1,
    )

def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)

def main():
    if len(sys.argv) < 2:
        tag = os.environ.get("RELEASE_TAG") or os.environ.get("GITHUB_REF") or ""
    else:
        tag = sys.argv[1]
    if not tag:
        print("No release tag provided via argv or env", file=sys.stderr)
        sys.exit(1)

    version = normalize_tag(tag)

    setup_text = SETUP_PATH.read_text(encoding="utf-8")
    current_version = get_current_version(setup_text)

    if current_version == version:
        # No changes needed
        print(f"Version already matches tag: {version}")
        # ensure marker does not exist
        if MARKER_PATH.exists():
            MARKER_PATH.unlink()
        return

    new_text = replace_version(setup_text, version)
    SETUP_PATH.write_text(new_text, encoding="utf-8")

    # Stage and commit
    run(["git", "add", str(SETUP_PATH)])
    run(["git", "commit", "-m", f"chore: bump version to {version}"])

    # Create a marker file so the workflow can decide to push and retag
    MARKER_PATH.write_text(version, encoding="utf-8")
    print(f"Updated setup.py version to {version} and committed.")

if __name__ == "__main__":
    main()
