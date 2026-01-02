#!/usr/bin/env python3
import re
import sys
import subprocess
from pathlib import Path

SETUP_PATH = Path("setup.py")

def run(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result

def abort(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)

def warn(msg):
    print(f"WARNING: {msg}", file=sys.stderr)

def validate_version_arg(arg: str) -> str:
    # Must be like v0.2.0
    if not re.fullmatch(r"v\d+\.\d+\.\d+", arg):
        abort('Version must be in format vX.Y.Z, e.g., v0.2.0')
    return arg

def git_tag_exists(tag: str) -> bool:
    res = run(["git", "tag", "--list", tag])
    return tag in res.stdout.splitlines()

def get_current_setup_version(text: str) -> str:
    # Match version='0.1.2' or version="0.1.2"
    m = re.search(r"version\s*=\s*['\"](\d+\.\d+\.\d+)['\"]", text)
    if not m:
        abort("Could not find version in setup.py")
    return m.group(1)

def update_setup_version(text: str, new_version: str) -> str:
    pattern = r"(version\s*=\s*['\"])(\d+\.\d+\.\d+)(['\"])"
    return re.sub(
        pattern,
        lambda m: f"{m.group(1)}{new_version}{m.group(3)}",
        text,
        count=1
    )

def main():
    if len(sys.argv) != 2:
        abort("Usage: scripts/bump_version_and_tag.py vX.Y.Z")

    tag = validate_version_arg(sys.argv[1])
    new_version_no_v = tag[1:]  # strip leading 'v'

    # Abort if tag already exists
    if git_tag_exists(tag):
        abort(f"Tag {tag} already exists")

    setup_text = SETUP_PATH.read_text(encoding="utf-8")
    current_version = get_current_setup_version(setup_text)

    if current_version == new_version_no_v:
        warn(f"setup.py already has version {current_version}; will create tag {tag} anyway")
        # Still create a tag without changing files/committing
        res = run(["git", "tag", tag])
        if res.returncode != 0:
            abort(f"Failed to create tag: {res.stderr.strip()}")
        print(f"Created tag {tag}")
        sys.exit(0)

    # Update setup.py
    updated_text = update_setup_version(setup_text, new_version_no_v)
    if updated_text == setup_text:
        abort("Failed to update version in setup.py")

    SETUP_PATH.write_text(updated_text, encoding="utf-8")

    # Stage and commit
    res = run(["git", "add", str(SETUP_PATH)])
    if res.returncode != 0:
        abort(f"Failed to stage setup.py: {res.stderr.strip()}")

    res = run(["git", "commit", "-m", f"Release {tag}"])
    if res.returncode != 0:
        abort(f"Failed to commit version bump: {res.stderr.strip()}")

    # Create tag
    res = run(["git", "tag", tag])
    if res.returncode != 0:
        abort(f"Failed to create tag: {res.stderr.strip()}")

    print(f"Bumped version to {new_version_no_v}, committed, and created tag {tag}")

if __name__ == "__main__":
    main()
