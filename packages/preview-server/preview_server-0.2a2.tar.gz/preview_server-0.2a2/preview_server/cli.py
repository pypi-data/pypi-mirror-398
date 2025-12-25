"""CLI interface for preview server."""

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from preview_server import __version__
from preview_server.config import load_config


# Cache directory location
CACHE_DIR = Path.home() / ".cache" / "preview-server"
REPOS_DIR = CACHE_DIR / "repos"
WORKTREES_DIR = CACHE_DIR / "worktrees"


@dataclass
class CLIConfig:
    """Configuration from CLI arguments."""

    repo: Optional[str] = None
    repos: Optional[dict[str, str]] = None
    port: int = 8000
    host: str = "127.0.0.1"
    idle_ttl: str = "5m"
    auto_pull: Optional[str] = None
    basic_auth: Optional[str] = None
    log_file: Optional[str] = None
    secret: Optional[str] = None
    cleanup: bool = False
    cleanup_yes: bool = False  # Skip confirmation for --cleanup
    sign: Optional[str] = None  # Hostname to sign (for --sign command)
    admin_secret: Optional[str] = None  # Secret for admin API access
    persist_repos: Optional[str] = None  # Path to JSON file for repo persistence
    base_domain: str = "localhost"  # Base domain for hostname parsing


def _is_bare_url_or_special(arg: str) -> bool:
    r"""Check if argument is a bare URL or special path (not label:path).

    Returns True for:
    - HTTP/HTTPS URLs: https://github.com/...
    - SSH URLs: git@github.com:user/repo.git
    - Windows paths: C:\path\to\repo

    Returns False for labeled paths/URLs like:
    - myapp:/path/to/repo
    - api:https://github.com/...
    """
    # Check for URL scheme at the start (bare URL)
    # e.g., https://github.com/... or git://host/...
    if "://" in arg:
        scheme_end = arg.index("://")
        # If :// comes early and before any other colons, it's a bare URL
        if ":" not in arg[:scheme_end]:
            return True
        # Otherwise it might be label:https://... which is NOT a bare URL
        return False

    # Windows paths (single letter drive): C:\path
    if len(arg) >= 2 and arg[1] == ":" and arg[0].isalpha():
        return True

    # SSH URLs: user@host:path pattern (has @ before first :)
    if ":" in arg and "@" in arg:
        at_idx = arg.index("@")
        colon_idx = arg.index(":")
        if at_idx < colon_idx:
            return True

    return False


def _parse_labeled_arg(arg: str) -> tuple[str, str]:
    """Parse a label:path argument, handling URLs after the label.

    Args:
        arg: The argument string (e.g., "myapp:/path" or "myapp:https://...")

    Returns:
        Tuple of (label, path)

    Raises:
        ValueError: If format is invalid
    """
    colon_idx = arg.index(":")
    label = arg[:colon_idx]
    path = arg[colon_idx + 1 :]

    if not label or not path:
        raise ValueError(f"Invalid repo format '{arg}': expected 'label:path'")

    return label, path


def parse_repo_args(
    repo_args: list[str],
) -> tuple[Optional[str], Optional[dict[str, str]]]:
    r"""Parse repository positional arguments.

    Supports two formats:
    - Single arg without colon: single repo mode (path only)
    - One or more args with label:path format: multi-repo mode

    Special cases handled as single repo (not label:path):
    - HTTP/HTTPS URLs: https://github.com/user/repo
    - SSH URLs: git@github.com:user/repo.git
    - Windows paths: C:\path\to\repo

    Args:
        repo_args: List of repository arguments

    Returns:
        Tuple of (repo, repos) where one will be None

    Raises:
        ValueError: If format is invalid
    """
    if not repo_args:
        return None, None

    if len(repo_args) == 1:
        arg = repo_args[0]

        # Check for bare URLs/special paths that shouldn't be parsed as label:path
        if _is_bare_url_or_special(arg):
            return arg, None

        # Check if it has a colon (potential label:path)
        if ":" in arg:
            label, path = _parse_labeled_arg(arg)
            return None, {label: path}
        else:
            # Single path without label
            return arg, None

    # Multiple arguments - all must be label:path format
    repos = {}
    for arg in repo_args:
        # For multiple args, bare URLs/special paths are not allowed
        if _is_bare_url_or_special(arg):
            raise ValueError(
                f"Multiple repos require label:path format. "
                f"Use 'name:{arg}' instead of just '{arg}'"
            )
        if ":" not in arg:
            raise ValueError(
                f"Multiple repos require label:path format. "
                f"Use 'name:{arg}' instead of just '{arg}'"
            )

        label, path = _parse_labeled_arg(arg)
        if label in repos:
            raise ValueError(f"Duplicate repo label: {label}")
        repos[label] = path

    return None, repos


def run_cleanup(dry_run: bool = False) -> dict:
    """Clean up stale worktrees and cached repos.

    Removes:
    - All worktrees in ~/.cache/preview-server/worktrees/
    - All cloned repos in ~/.cache/preview-server/repos/
    - Prunes git worktrees for any repos that have them

    Args:
        dry_run: If True, only report what would be deleted

    Returns:
        Dict with cleanup results: {worktrees: [...], repos: [...], total_bytes: int}
    """
    results = {
        "worktrees": [],
        "repos": [],
        "total_bytes": 0,
    }

    def get_dir_size(path: Path) -> int:
        """Calculate total size of a directory."""
        total = 0
        try:
            for item in path.rglob("*"):
                if item.is_file():
                    total += item.stat().st_size
        except (OSError, PermissionError):
            pass
        return total

    # Clean worktrees
    if WORKTREES_DIR.exists():
        for item in WORKTREES_DIR.iterdir():
            if item.is_dir():
                size = get_dir_size(item)
                results["worktrees"].append({"path": str(item), "size": size})
                results["total_bytes"] += size
                if not dry_run:
                    shutil.rmtree(item, ignore_errors=True)

    # Clean repos (and prune their worktrees first)
    if REPOS_DIR.exists():
        for item in REPOS_DIR.iterdir():
            if item.is_dir():
                # Try to prune git worktrees first
                try:
                    subprocess.run(
                        ["git", "worktree", "prune"],
                        cwd=item,
                        capture_output=True,
                        timeout=10,
                    )
                except (subprocess.SubprocessError, OSError):
                    pass

                size = get_dir_size(item)
                results["repos"].append({"path": str(item), "size": size})
                results["total_bytes"] += size
                if not dry_run:
                    shutil.rmtree(item, ignore_errors=True)

    return results


def format_bytes(num_bytes: int) -> str:
    """Format bytes as human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


def parse_cli_args(args: list[str]) -> CLIConfig:
    """Parse command-line arguments.

    If a config file is specified with --config, its values are loaded first
    and then overridden by any CLI arguments explicitly provided.

    Supports multiple repository formats:
    - Single repo: preview-server /path/to/repo
    - Single repo with label: preview-server myapp:/path/to/repo
    - Multiple repos: preview-server frontend:/path/a backend:/path/b

    Args:
        args: List of command-line arguments (excluding program name)

    Returns:
        CLIConfig object with parsed arguments

    Raises:
        SystemExit: If required arguments are missing or invalid
    """
    description = """\
Preview deployment server for git repositories.

Serves any branch of a git repository as a separate preview site,
accessible via subdomain-style URLs like http://main.localhost:8000
or http://feature-branch.localhost:8000.

Specifying repositories:

  There are three ways to specify a git repository:

  1. Local path (single repo mode):
     preview-server /path/to/repo

  2. Git URL - clones to ~/.cache/preview-server/repos/:
     preview-server https://github.com/user/repo.git
     preview-server git@github.com:user/repo.git

  3. Labeled repos (multi-repo mode):
     preview-server frontend:/path/to/frontend backend:/path/to/backend
     preview-server api:https://github.com/user/api.git

     In multi-repo mode, access branches via:
     http://<repo>--<branch>.localhost:8000
     e.g., http://frontend--main.localhost:8000"""

    epilog = """\
Examples:

  # Serve a local repository on port 8000
  preview-server /path/to/my-project

  # Clone and serve a GitHub repository
  preview-server https://github.com/simonw/datasette.git

  # Serve multiple repositories with labels
  preview-server frontend:/path/to/frontend api:/path/to/api

  # Use a config file
  preview-server -c config.toml

  # Enable basic auth
  preview-server /path/to/repo --basic-auth user:pass

  # Start with no repos, enable admin API for runtime configuration
  preview-server --admin-secret mysecret

  # Clean up cached worktrees and cloned repos
  preview-server --cleanup

For full configuration file documentation and more details, see:
https://github.com/simonw/preview-server"""

    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
        prog="preview-server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,  # Disable default -h so we can use it for --host
    )

    # Add --help manually (without -h shortcut since we use it for --host)
    parser.add_argument(
        "--help",
        action="help",
        help="Show this help message and exit",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "repos_args",
        nargs="*",
        metavar="REPO",
        help="Repository path(s). Single: /path or label:/path. Multiple: label1:/path1 label2:/path2",
    )

    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove all cached worktrees and repos, then exit",
    )

    parser.add_argument(
        "--cleanup-yes",
        action="store_true",
        help="Remove all cached worktrees and repos without confirmation",
    )

    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=None,
        help="Server port (default: 8000)",
    )

    parser.add_argument(
        "-h",
        "--host",
        default=None,
        help="Host to bind to (default: 127.0.0.1)",
    )

    parser.add_argument(
        "--idle-ttl",
        default=None,
        help="Idle timeout before terminating sub-server (default: 5m)",
    )

    parser.add_argument(
        "--auto-pull",
        default=None,
        help="Auto-pull branches if not requested within this duration (e.g., 5m, 1h). Disabled by default.",
    )

    parser.add_argument(
        "--basic-auth",
        default=None,
        help="Basic auth credentials in format USER:PASS (optional)",
    )

    parser.add_argument(
        "--log-file",
        default=None,
        help="JSON logs output file (default: stderr)",
    )

    parser.add_argument(
        "-c",
        "--config",
        default=None,
        help="Path to TOML configuration file (optional)",
    )

    parser.add_argument(
        "--secret",
        default=None,
        help="Signing secret for hostname verification. When set, only signed hostnames are allowed.",
    )

    parser.add_argument(
        "--sign",
        default=None,
        metavar="HOSTNAME",
        help="Sign a hostname and print the result. Requires --secret.",
    )

    parser.add_argument(
        "--admin-secret",
        default=None,
        help="Secret for admin API access. Enables repo management endpoints and allows starting with no repos.",
    )

    parser.add_argument(
        "--persist-repos",
        default=None,
        metavar="PATH",
        help="JSON file path for persisting repo configuration. If set, repo changes are saved to this file.",
    )

    parser.add_argument(
        "--base-domain",
        default=None,
        metavar="DOMAIN",
        help="Base domain for hostname parsing (default: localhost). Use for custom wildcard domains like example.com.",
    )

    # Show help if no arguments provided
    if not args:
        parser.print_help()
        sys.exit(0)

    parsed = parser.parse_args(args)

    # Handle --sign command first (doesn't need repos)
    if parsed.sign is not None:
        if parsed.secret is None:
            parser.error("--sign requires --secret")
        # Return minimal config for sign command
        return CLIConfig(
            sign=parsed.sign,
            secret=parsed.secret,
        )

    # Start with defaults
    port = 8000
    host = "127.0.0.1"
    idle_ttl = "5m"
    auto_pull = None
    basic_auth = None
    log_file = None
    secret = None
    repo = None
    repos = None
    admin_secret = None
    persist_repos = None
    base_domain = "localhost"

    # Load config file if specified
    if parsed.config:
        config = load_config(parsed.config)
        if config.port is not None:
            port = config.port
        if config.host is not None:
            host = config.host
        if config.idle_ttl is not None:
            idle_ttl = config.idle_ttl
        if config.auto_pull is not None:
            auto_pull = config.auto_pull
        if config.basic_auth is not None:
            basic_auth = config.basic_auth
        if config.log_file is not None:
            log_file = config.log_file
        if config.secret is not None:
            secret = config.secret
        if config.repo is not None:
            repo = config.repo
        if config.repos is not None:
            repos = config.repos
        if config.admin_secret is not None:
            admin_secret = config.admin_secret
        if config.persist_repos is not None:
            persist_repos = config.persist_repos
        if config.base_domain is not None:
            base_domain = config.base_domain

    # CLI arguments override config file
    if parsed.port is not None:
        port = parsed.port
    if parsed.host is not None:
        host = parsed.host
    if parsed.idle_ttl is not None:
        idle_ttl = parsed.idle_ttl
    if parsed.auto_pull is not None:
        auto_pull = parsed.auto_pull
    if parsed.basic_auth is not None:
        basic_auth = parsed.basic_auth
    if parsed.log_file is not None:
        log_file = parsed.log_file
    if parsed.secret is not None:
        secret = parsed.secret
    if parsed.admin_secret is not None:
        admin_secret = parsed.admin_secret
    if parsed.persist_repos is not None:
        persist_repos = parsed.persist_repos
    if parsed.base_domain is not None:
        base_domain = parsed.base_domain

    # Parse repo arguments from CLI
    if parsed.repos_args:
        try:
            cli_repo, cli_repos = parse_repo_args(parsed.repos_args)
        except ValueError as e:
            parser.error(str(e))

        # CLI repos override config
        if cli_repo is not None:
            repo = cli_repo
            repos = None  # Single repo mode takes precedence
        if cli_repos is not None:
            repos = cli_repos
            repo = None  # Multi-repo mode takes precedence

    # Handle cleanup mode - doesn't need repos
    # --cleanup-yes implies --cleanup
    if parsed.cleanup or parsed.cleanup_yes:
        return CLIConfig(
            repo=repo,
            repos=repos,
            port=port,
            host=host,
            idle_ttl=idle_ttl,
            auto_pull=auto_pull,
            basic_auth=basic_auth,
            log_file=log_file,
            secret=secret,
            cleanup=True,
            cleanup_yes=parsed.cleanup_yes,
            admin_secret=admin_secret,
            persist_repos=persist_repos,
            base_domain=base_domain,
        )

    # Validate that we have a repo source
    # In multi-repo mode ([repos] section), we don't need a single repo
    # In single-repo mode, we need repo from CLI or config
    # With admin-secret, no repos are required (can be configured at runtime)
    if repos is None and repo is None and admin_secret is None:
        parser.error("the following arguments are required: REPO")

    return CLIConfig(
        repo=repo,
        repos=repos,
        port=port,
        host=host,
        idle_ttl=idle_ttl,
        auto_pull=auto_pull,
        basic_auth=basic_auth,
        log_file=log_file,
        secret=secret,
        cleanup=False,
        admin_secret=admin_secret,
        persist_repos=persist_repos,
        base_domain=base_domain,
    )


def main_sign(hostname: str, secret: str) -> str:
    """Sign a hostname with the given secret.

    This function is used by the --sign CLI command.

    Args:
        hostname: The hostname to sign (e.g., "main" or "backend--feature")
        secret: The shared secret for signing

    Returns:
        The signed hostname (e.g., "main--abc123def456")
    """
    from preview_server.signing import sign_hostname

    return sign_hostname(hostname, secret)
