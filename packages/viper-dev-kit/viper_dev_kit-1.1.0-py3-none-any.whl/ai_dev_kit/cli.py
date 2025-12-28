import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from ai_dev_kit import __version__

DEFAULT_ASSET_DIRS = (
    "agents",
    "commands",
    "skills",
    "protocols",
    "templates",
    "scripts",
    "dev-tools",
    "output-styles",
)


def _version_key(name: str) -> tuple:
    cleaned = name.lstrip("v")
    parts = cleaned.split(".")
    key = []
    for part in parts:
        try:
            key.append(int(part))
        except ValueError:
            key.append(-1)
    return tuple(key)


def resolve_source(explicit: str | None) -> Path | None:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))

    env_source = os.getenv("AI_DEV_KIT_SOURCE")
    if env_source:
        candidates.append(Path(env_source))

    candidates.append(Path.cwd() / "plugins/ai-dev-kit")
    candidates.append(Path.home() / ".claude/plugins/ai-dev-kit")

    cache_root = Path.home() / ".claude/plugins/cache/ai-dev-kit/ai-dev-kit"
    if cache_root.is_dir():
        versions = sorted(
            (path for path in cache_root.iterdir() if path.is_dir()),
            key=lambda path: _version_key(path.name),
        )
        if versions:
            candidates.append(versions[-1])

    for candidate in candidates:
        if (candidate / ".claude-plugin/plugin.json").is_file():
            return candidate

    for candidate in candidates:
        if candidate.is_dir():
            return candidate

    return None


def read_plugin_version(source: Path) -> str | None:
    manifest_path = source / ".claude-plugin/plugin.json"
    if not manifest_path.is_file():
        return None
    try:
        data = json.loads(manifest_path.read_text())
    except json.JSONDecodeError:
        return None
    return data.get("version")


def write_manifest(target: Path, source: Path, source_version: str | None) -> None:
    manifest = {
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "source_path": str(source),
        "source_version": source_version or "unknown",
        "cli_version": __version__,
    }
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def sync_assets(source: Path, target: Path, verbose: bool) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for dir_name in DEFAULT_ASSET_DIRS:
        src_dir = source / dir_name
        if not src_dir.is_dir():
            if verbose:
                print(f"skip: {dir_name} (missing)")
            continue
        dest_dir = target / dir_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_dir, dest_dir, dirs_exist_ok=True)
        if verbose:
            print(f"sync: {dir_name}")


def cmd_sync(args: argparse.Namespace) -> int:
    source = resolve_source(args.source)
    if not source:
        print("ai-dev-kit sync: unable to locate plugin assets.", file=sys.stderr)
        print("Install the plugin or set AI_DEV_KIT_SOURCE.", file=sys.stderr)
        return 2

    target = Path(args.target)
    if args.dry_run:
        print(f"source: {source}")
        print(f"target: {target}")
        print("dry-run: no files copied")
        return 0

    sync_assets(source, target, args.verbose)
    write_manifest(target, source, read_plugin_version(source))

    print(f"synced assets to {target}")
    return 0


def cmd_where(args: argparse.Namespace) -> int:
    source = resolve_source(args.source)
    if not source:
        print("ai-dev-kit where: no source found", file=sys.stderr)
        return 2
    print(source)
    return 0


def cmd_version(_: argparse.Namespace) -> int:
    print(__version__)
    return 0


SETTINGS_TEMPLATE = {
    "$schema": "https://json.schemastore.org/claude-code-settings.json",
    "enabledPlugins": {"ai-dev-kit@ai-dev-kit": True},
    "permissions": {
        "allow": [
            "Bash(python:*)",
            "Bash(uv:*)",
            "Bash(git:*)",
            "Bash(pytest:*)",
            "Read(*)",
            "Write(*)",
            "Edit(*)",
            "Glob(*)",
            "Grep(*)",
            "TodoWrite(*)",
            "Task(*)",
        ],
        "deny": [],
    },
}


def check_permissions(target_root: Path, verbose: bool = False) -> tuple[bool, list[str]]:
    """Check write permissions on target directory and key paths.

    Returns (success, list of issues).
    """
    issues = []

    # Check if target root exists and is writable
    if target_root.exists():
        if not os.access(target_root, os.W_OK):
            issues.append(f"No write permission on {target_root}")
            # Check if it's a permission issue we can diagnose
            stat_info = target_root.stat()
            mode = oct(stat_info.st_mode)[-3:]
            issues.append(f"  Current mode: {mode}")
            issues.append(f"  Fix with: chmod u+w {target_root}")
    else:
        # Check parent directory
        parent = target_root.parent
        if parent.exists() and not os.access(parent, os.W_OK):
            issues.append(f"No write permission on parent {parent}")

    # Check .claude directory if it exists
    claude_dir = target_root / ".claude"
    if claude_dir.exists() and not os.access(claude_dir, os.W_OK):
        issues.append(f"No write permission on {claude_dir}")
        issues.append(f"  Fix with: chmod -R u+w {claude_dir}")

    # Check for common read-only patterns
    test_paths = [
        target_root / "architecture",
        target_root / "specs",
    ]
    for path in test_paths:
        if path.exists() and not os.access(path, os.W_OK):
            issues.append(f"No write permission on {path}")

    if verbose and not issues:
        print(f"permissions: OK ({target_root})")

    return len(issues) == 0, issues


def cmd_setup(args: argparse.Namespace) -> int:
    """Bootstrap ai-dev-kit in the current repository."""
    target_root = Path(args.target) if args.target else Path.cwd()
    claude_dir = target_root / ".claude"
    settings_file = claude_dir / "settings.json"

    # Check permissions first
    ok, issues = check_permissions(target_root, args.verbose)
    if not ok:
        print("Permission check failed:", file=sys.stderr)
        for issue in issues:
            print(f"  {issue}", file=sys.stderr)
        print("\nTo fix read-only permissions, run:", file=sys.stderr)
        print(f"  chmod -R u+w {target_root}", file=sys.stderr)
        return 1

    # Check if already configured
    if settings_file.exists() and not args.force:
        try:
            existing = json.loads(settings_file.read_text())
            if existing.get("enabledPlugins", {}).get("ai-dev-kit@ai-dev-kit"):
                print(f"ai-dev-kit already enabled in {settings_file}")
                if not args.sync_only:
                    print("Use --force to overwrite settings.")
                    return 0
        except json.JSONDecodeError:
            pass

    # Create directories
    dirs_to_create = [
        claude_dir,
        claude_dir / "run-logs",
        claude_dir / "run-reports",
        claude_dir / "ai-dev-kit",
        target_root / "architecture" / "c4",
        target_root / "specs" / "phases",
        target_root / "specs" / "external-requests",
    ]

    for d in dirs_to_create:
        try:
            d.mkdir(parents=True, exist_ok=True)
            if args.verbose:
                print(f"mkdir: {d}")
        except PermissionError as e:
            print(f"Permission denied creating {d}: {e}", file=sys.stderr)
            print(f"Fix with: chmod -R u+w {d.parent}", file=sys.stderr)
            return 1

    # Create or update settings.json
    if not args.sync_only:
        if settings_file.exists():
            try:
                existing = json.loads(settings_file.read_text())
                # Merge: keep existing permissions, enable plugin
                existing.setdefault("enabledPlugins", {})
                existing["enabledPlugins"]["ai-dev-kit@ai-dev-kit"] = True
                settings_file.write_text(json.dumps(existing, indent=2) + "\n")
            except json.JSONDecodeError:
                settings_file.write_text(json.dumps(SETTINGS_TEMPLATE, indent=2) + "\n")
        else:
            settings_file.write_text(json.dumps(SETTINGS_TEMPLATE, indent=2) + "\n")
        print(f"configured: {settings_file}")

    # Sync assets
    source = resolve_source(args.source)
    if source:
        asset_target = claude_dir / "ai-dev-kit"
        sync_assets(source, asset_target, args.verbose)
        write_manifest(asset_target, source, read_plugin_version(source))
        print(f"synced assets to {asset_target}")
    else:
        print("warning: could not locate plugin source for asset sync")
        print("set AI_DEV_KIT_SOURCE or run 'ai-dev-kit sync' later")

    print(f"\nai-dev-kit setup complete in {target_root}")
    print("\nNext steps:")
    print("  1. Run /ai-dev-kit:validate to verify installation")
    print("  2. Run /ai-dev-kit:explore-architecture to analyze codebase")
    print("  3. Run /ai-dev-kit:plan-phase to plan your first phase")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-dev-kit",
        description="AI Dev Kit helper CLI for syncing plugin assets.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="Sync plugin assets locally.")
    sync_parser.add_argument(
        "--target",
        default=".claude/ai-dev-kit",
        help="Target directory for synced assets.",
    )
    sync_parser.add_argument(
        "--source",
        default=None,
        help="Explicit plugin source directory.",
    )
    sync_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print resolved paths without copying files.",
    )
    sync_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-directory sync status.",
    )
    sync_parser.set_defaults(func=cmd_sync)

    where_parser = subparsers.add_parser("where", help="Print resolved asset source.")
    where_parser.add_argument(
        "--source",
        default=None,
        help="Explicit plugin source directory.",
    )
    where_parser.set_defaults(func=cmd_where)

    version_parser = subparsers.add_parser("version", help="Print CLI version.")
    version_parser.set_defaults(func=cmd_version)

    setup_parser = subparsers.add_parser(
        "setup", help="Bootstrap ai-dev-kit in a repository."
    )
    setup_parser.add_argument(
        "--target",
        default=None,
        help="Target repository root (default: current directory).",
    )
    setup_parser.add_argument(
        "--source",
        default=None,
        help="Explicit plugin source directory for asset sync.",
    )
    setup_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing settings.",
    )
    setup_parser.add_argument(
        "--sync-only",
        action="store_true",
        help="Only sync assets, don't modify settings.",
    )
    setup_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed progress.",
    )
    setup_parser.set_defaults(func=cmd_setup)

    check_parser = subparsers.add_parser(
        "check", help="Check if a repository is ready for ai-dev-kit setup."
    )
    check_parser.add_argument(
        "--target",
        default=None,
        help="Target repository root (default: current directory).",
    )
    check_parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to fix permission issues.",
    )
    check_parser.set_defaults(func=cmd_check)

    return parser


def cmd_check(args: argparse.Namespace) -> int:
    """Check if a repository is ready for ai-dev-kit setup."""
    import subprocess

    target_root = Path(args.target) if args.target else Path.cwd()

    print(f"Checking {target_root}...")
    print()

    # Check if it's a git repo
    git_dir = target_root / ".git"
    if git_dir.exists():
        print("✓ Git repository detected")
    else:
        print("✗ Not a git repository")
        print("  Run: git init")

    # Check permissions
    ok, issues = check_permissions(target_root, verbose=True)
    if ok:
        print("✓ Write permissions OK")
    else:
        print("✗ Permission issues found:")
        for issue in issues:
            print(f"  {issue}")

        if args.fix:
            print("\nAttempting to fix permissions...")
            try:
                subprocess.run(
                    ["chmod", "-R", "u+w", str(target_root)],
                    check=True,
                    capture_output=True,
                )
                print("✓ Permissions fixed")
            except subprocess.CalledProcessError as e:
                print(f"✗ Failed to fix permissions: {e}")
                return 1
        else:
            print("\nRun with --fix to attempt automatic repair, or manually:")
            print(f"  chmod -R u+w {target_root}")

    # Check for existing settings
    settings_file = target_root / ".claude" / "settings.json"
    if settings_file.exists():
        try:
            existing = json.loads(settings_file.read_text())
            if existing.get("enabledPlugins", {}).get("ai-dev-kit@ai-dev-kit"):
                print("✓ ai-dev-kit already enabled")
            else:
                print("○ .claude/settings.json exists (will be merged)")
        except json.JSONDecodeError:
            print("✗ .claude/settings.json is invalid JSON")
    else:
        print("○ No existing settings (will be created)")

    # Check for plugin source
    source = resolve_source(None)
    if source:
        version = read_plugin_version(source)
        print(f"✓ Plugin source found: {source}")
        if version:
            print(f"  Version: {version}")
    else:
        print("○ No plugin source found")
        print("  Set AI_DEV_KIT_SOURCE or install plugin")

    print()
    if ok:
        print("Ready for setup. Run: ai-dev-kit setup")
        return 0
    else:
        print("Fix issues above before running setup.")
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
