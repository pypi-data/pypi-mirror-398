"""Entry point for running preview-server from CLI."""

import asyncio
import json
import logging
import sys
from pathlib import Path

import uvicorn

from preview_server.app import create_app, create_multi_repo_app
from preview_server.cli import (
    parse_cli_args,
    run_cleanup,
    format_bytes,
    CACHE_DIR,
    main_sign,
)
from preview_server.sub_server import SubServerManager
from preview_server.utils import parse_duration


def setup_logging(log_file: str = None) -> logging.Logger:
    """Set up structured JSON logging.

    Args:
        log_file: Optional file path for logging (default: stderr)

    Returns:
        The configured logger
    """

    class JSONFormatter(logging.Formatter):
        """Format logs as JSON."""

        def format(self, record: logging.LogRecord) -> str:
            log_data = {
                "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S.%fZ"[:-4]),
                "level": record.levelname,
                "message": record.getMessage(),
            }
            if record.exc_info:
                log_data["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_data)

    logger = logging.getLogger("preview_server")
    logger.setLevel(logging.DEBUG)

    # Choose handler based on log_file
    if log_file:
        handler = logging.FileHandler(log_file)
    else:
        handler = logging.StreamHandler(sys.stderr)

    formatter = JSONFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def main():
    """Main entry point."""
    # Parse arguments
    args = parse_cli_args(sys.argv[1:])

    # Handle cleanup command
    if args.cleanup:
        print(f"Cleaning up preview-server cache at {CACHE_DIR}")
        print()

        # First do a dry run to show what will be deleted
        results = run_cleanup(dry_run=True)

        if not results["worktrees"] and not results["repos"]:
            print("Nothing to clean up.")
            return

        # Show what will be deleted
        if results["worktrees"]:
            print(f"Worktrees ({len(results['worktrees'])}):")
            for item in results["worktrees"]:
                print(f"  - {item['path']} ({format_bytes(item['size'])})")

        if results["repos"]:
            print(f"Cached repos ({len(results['repos'])}):")
            for item in results["repos"]:
                print(f"  - {item['path']} ({format_bytes(item['size'])})")

        print()
        print(f"Total: {format_bytes(results['total_bytes'])}")
        print()

        # Ask for confirmation unless --cleanup-yes was passed
        if not args.cleanup_yes:
            try:
                response = input("Continue? [y/N] ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nAborted.")
                return
            if response not in ("y", "yes"):
                print("Aborted.")
                return

        # Actually delete
        run_cleanup(dry_run=False)
        print("Cleanup complete.")
        return

    # Handle --sign command
    if args.sign is not None:
        signed = main_sign(args.sign, args.secret)
        print(signed)
        return

    # Set up logging
    logger = setup_logging(args.log_file)
    logger.info("Starting preview server")

    # Parse idle TTL
    try:
        idle_ttl_seconds = parse_duration(args.idle_ttl)
    except ValueError as e:
        logger.error(f"Invalid idle-ttl format: {e}")
        sys.exit(1)

    logger.debug(f"Idle TTL: {idle_ttl_seconds} seconds")

    # Parse auto-pull
    auto_pull_seconds = None
    if args.auto_pull:
        try:
            auto_pull_seconds = parse_duration(args.auto_pull)
            logger.debug(f"Auto-pull: {auto_pull_seconds} seconds")
        except ValueError as e:
            logger.error(f"Invalid auto-pull format: {e}")
            sys.exit(1)

    # Check if multi-repo mode (explicit repos OR admin_secret forces multi-repo)
    if args.repos or args.admin_secret:
        # Multi-repo mode
        repos = args.repos or {}
        logger.info(f"Multi-repo mode with {len(repos)} repositories")
        for name, path in repos.items():
            logger.info(f"  {name}: {path}")

        # Create multi-repo app
        app = create_multi_repo_app(
            repos=repos,
            basic_auth=args.basic_auth,
            idle_ttl_seconds=idle_ttl_seconds,
            auto_pull_seconds=auto_pull_seconds,
            secret=args.secret,
            admin_secret=args.admin_secret,
            base_domain=args.base_domain,
        )

        logger.info(f"Starting server on port {args.port}")
        logger.info(f"Server listening on http://{args.base_domain}:{args.port}")
        for name in repos:
            logger.info(f"Try: http://{name}.{args.base_domain}:{args.port} for {name}")
    else:
        # Single-repo mode
        logger.debug(
            f"Args: repo={args.repo}, port={args.port}, idle_ttl={args.idle_ttl}"
        )

        # Prepare directories
        repo_path = args.repo
        clone_path = (
            Path.home() / ".cache" / "preview-server" / "repos" / Path(repo_path).name
        )
        worktree_base_path = Path.home() / ".cache" / "preview-server" / "worktrees"

        logger.info(f"Repository: {repo_path}")
        logger.info(f"Clone path: {clone_path}")
        logger.info(f"Worktree base: {worktree_base_path}")

        # Create sub-server manager
        manager = SubServerManager(
            repo_path=repo_path,
            clone_path=str(clone_path),
            worktree_base_path=str(worktree_base_path),
            idle_ttl_seconds=idle_ttl_seconds,
            auto_pull_seconds=auto_pull_seconds,
            logger=logger,
        )

        # Create ASGI app
        app = create_app(
            manager,
            basic_auth=args.basic_auth,
            secret=args.secret,
            base_domain=args.base_domain,
        )

        logger.info(f"Starting server on port {args.port}")
        logger.info(f"Server listening on http://{args.base_domain}:{args.port}")
        logger.info(f"Try: http://main.{args.base_domain}:{args.port} to test")

    # Run the server
    try:
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_config=None,  # Disable uvicorn's logging, we handle it
        )
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
