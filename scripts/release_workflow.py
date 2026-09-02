#!/usr/bin/env python3
"""Release and PR version helpers for Fitness Ledger."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / ".codex-plugin" / "plugin.json"
PYPROJECT = ROOT / "pyproject.toml"
CHANGELOG = ROOT / "CHANGELOG.md"
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def run_git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def parse_version(version: str) -> tuple[int, int, int]:
    match = SEMVER_RE.match(version)
    if not match:
        raise ValueError(f"version must be semantic X.Y.Z, got {version!r}")
    return tuple(int(part) for part in match.groups())


def format_version(parts: tuple[int, int, int]) -> str:
    return ".".join(str(part) for part in parts)


def bump_version(version: str, kind: str) -> str:
    major, minor, patch = parse_version(version)
    if kind == "major":
        return format_version((major + 1, 0, 0))
    if kind == "minor":
        return format_version((major, minor + 1, 0))
    if kind == "patch":
        return format_version((major, minor, patch + 1))
    raise ValueError("bump kind must be major, minor, or patch")


def manifest_version(path: Path = MANIFEST) -> str:
    return json.loads(path.read_text(encoding="utf-8"))["version"]


def pyproject_version(path: Path = PYPROJECT) -> str:
    match = re.search(r'^version = "([^"]+)"$', path.read_text(encoding="utf-8"), flags=re.MULTILINE)
    if not match:
        raise ValueError("pyproject.toml is missing a [project] version")
    return match.group(1)


def base_manifest_version(base_ref: str) -> str:
    raw = run_git("show", f"{base_ref}:.codex-plugin/plugin.json")
    return json.loads(raw)["version"]


def ensure_versions_match(version: str | None = None) -> str:
    manifest = manifest_version()
    project = pyproject_version()
    if manifest != project:
        raise ValueError(f"plugin.json version {manifest} does not match pyproject.toml version {project}")
    if version is not None and manifest != version:
        raise ValueError(f"requested version {version} does not match checked-out version {manifest}")
    parse_version(manifest)
    return manifest


def changelog_has_version(version: str) -> bool:
    return re.search(rf"^## {re.escape(version)}(?:\s|$)", CHANGELOG.read_text(encoding="utf-8"), flags=re.MULTILINE) is not None


def check_pr_version(base_ref: str) -> None:
    current = ensure_versions_match()
    base = base_manifest_version(base_ref)
    if parse_version(current) <= parse_version(base):
        raise ValueError(f"PR version must increase from base {base}; current is {current}")
    if not changelog_has_version(current):
        raise ValueError(f"CHANGELOG.md must include a section for {current}")


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def replace_pyproject_version(version: str) -> None:
    text = PYPROJECT.read_text(encoding="utf-8")
    updated, count = re.subn(r'^version = "[^"]+"$', f'version = "{version}"', text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise ValueError("pyproject.toml version replacement failed")
    PYPROJECT.write_text(updated, encoding="utf-8")


def add_changelog_entry(version: str, message: str, today: str | None = None) -> None:
    text = CHANGELOG.read_text(encoding="utf-8")
    if changelog_has_version(version):
        return
    date_text = today or dt.date.today().isoformat()
    entry = f"## {version} - {date_text}\n\n- {message}\n\n"
    if not text.startswith("# Changelog\n\n"):
        raise ValueError("CHANGELOG.md must start with '# Changelog' followed by a blank line")
    CHANGELOG.write_text("# Changelog\n\n" + entry + text[len("# Changelog\n\n"):], encoding="utf-8")


def apply_bump(kind: str, message: str) -> str:
    current = ensure_versions_match()
    version = bump_version(current, kind)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["version"] = version
    write_json(MANIFEST, manifest)
    replace_pyproject_version(version)
    add_changelog_entry(version, message)
    return version


def ensure_clean_worktree() -> None:
    if run_git("status", "--porcelain"):
        raise ValueError("working tree must be clean before tagging a release")


def create_tag(version: str, push: bool) -> str:
    ensure_versions_match(version)
    ensure_clean_worktree()
    tag = f"v{version}"
    existing = run_git("tag", "--list", tag)
    if existing and run_git("rev-list", "-n", "1", tag) != run_git("rev-parse", "HEAD"):
        raise ValueError(f"tag {tag} already exists on a different commit")
    if not existing:
        run_git("tag", "-a", tag, "-m", f"Release {tag}")
    if push:
        run_git("push", "origin", tag)
    return tag


def ensure_release(tag: str) -> None:
    try:
        subprocess.run(["gh", "release", "view", tag], cwd=ROOT, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError):
        subprocess.run(["gh", "release", "create", tag, "--verify-tag", "--generate-notes"], cwd=ROOT, check=True)


def wait_for_copilot_review(pr: str, wait_minutes: float = 5.0, poll_seconds: float = 15.0) -> None:
    """Wait for a current-head Copilot review and fail on recommended changes."""
    if wait_minutes < 0:
        raise ValueError("wait_minutes must be non-negative")
    poll_interval = max(1.0, poll_seconds)
    deadline = time.monotonic() + wait_minutes * 60
    while True:
        result = subprocess.run(["gh", "pr", "view", pr, "--json", "headRefOid,reviews"], cwd=ROOT, check=True, capture_output=True, text=True)
        data = json.loads(result.stdout)
        head = data.get("headRefOid")
        current = [r for r in data.get("reviews", []) if r.get("author", {}).get("login") == "copilot-pull-request-reviewer" and r.get("commit", {}).get("oid") == head]
        if current:
            latest = max(current, key=lambda r: r.get("submittedAt") or "")
            body = latest.get("body") or ""
            if "Changes recommended" in body or "Changes requested" in body:
                raise ValueError("Copilot review recommends changes; do not merge or tag")
            if time.monotonic() >= deadline:
                return
        if time.monotonic() >= deadline:
            raise TimeoutError("Copilot review did not complete within the configured wait")
        time.sleep(min(poll_interval, max(0.0, deadline - time.monotonic())))


def validate_tag_release_options(push: bool, create_release: bool) -> None:
    if create_release and not push:
        raise ValueError("--create-release requires --push so the verified tag exists on GitHub")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check-pr-version")
    check.add_argument("--base-ref", required=True)
    bump = sub.add_parser("bump")
    bump.add_argument("kind", choices=("major", "minor", "patch"))
    bump.add_argument("--message", required=True)
    tag = sub.add_parser("tag-release")
    tag.add_argument("--version")
    tag.add_argument("--push", action="store_true")
    tag.add_argument("--create-release", action="store_true")
    review = sub.add_parser("wait-pr-review")
    review.add_argument("--pr", required=True)
    review.add_argument("--wait-minutes", type=float, default=5.0)
    review.add_argument("--poll-seconds", type=float, default=15.0)
    args = parser.parse_args(argv)
    try:
        if args.command == "check-pr-version":
            check_pr_version(args.base_ref)
            print("PR version bump is valid.")
        elif args.command == "bump":
            print(apply_bump(args.kind, args.message))
        elif args.command == "tag-release":
            validate_tag_release_options(args.push, args.create_release)
            version = args.version or ensure_versions_match()
            created = create_tag(version, args.push)
            if args.create_release:
                ensure_release(created)
            print(created)
        elif args.command == "wait-pr-review":
            wait_for_copilot_review(args.pr, args.wait_minutes, args.poll_seconds)
            print("Copilot review gate passed.")
    except Exception as exc:
        print(f"release workflow error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
