"""Git repository management."""

import shutil
import subprocess
from pathlib import Path
from typing import List, Optional


class GitManager:
    """Manages git repository operations."""

    def __init__(self, repo_path: str, clone_path: str):
        """Initialize GitManager.

        Args:
            repo_path: Path or URL of the git repository
            clone_path: Path where to clone the repository
        """
        self.repo_path = repo_path
        self.clone_path = clone_path
        self.cloned = False

    def clone(self) -> None:
        """Clone the repository to the clone path."""
        clone_dir = Path(self.clone_path)
        clone_dir.parent.mkdir(parents=True, exist_ok=True)

        # If the directory already exists, just fetch/pull
        if clone_dir.exists():
            self.cloned = True
            self.pull()
            return

        subprocess.run(
            ["git", "clone", self.repo_path, str(clone_dir)],
            capture_output=True,
            check=True,
        )
        self.cloned = True

    def pull(self) -> None:
        """Pull latest changes from the repository."""
        if not self.cloned:
            raise RuntimeError("Repository not cloned yet")

        subprocess.run(
            ["git", "-C", self.clone_path, "pull"],
            capture_output=True,
            check=False,
        )

    def fetch(self) -> None:
        """Fetch latest changes without merging."""
        if not self.cloned:
            raise RuntimeError("Repository not cloned yet")

        subprocess.run(
            ["git", "-C", self.clone_path, "fetch"],
            capture_output=True,
            check=False,
        )

    async def async_fetch_with_timeout(self, timeout: float = 5.0) -> bool:
        """Fetch latest changes with timeout.

        Args:
            timeout: Maximum time to wait for fetch in seconds

        Returns:
            True if fetch succeeded, False if timeout or error
        """
        import asyncio
        import logging

        logger = logging.getLogger(__name__)

        if not self.cloned:
            logger.error("Repository not cloned yet")
            return False

        try:
            # Run the fetch in a thread pool with timeout
            await asyncio.wait_for(asyncio.to_thread(self.fetch), timeout=timeout)
            logger.debug("Git fetch completed successfully")
            return True

        except asyncio.TimeoutError:
            logger.warning(f"Git fetch timed out after {timeout}s")
            return False
        except Exception as e:
            logger.error(f"Git fetch failed: {e}")
            return False

    def get_current_head(self) -> str:
        """Get the current HEAD commit hash.

        Returns:
            The full commit hash of HEAD
        """
        if not self.cloned:
            raise RuntimeError("Repository not cloned yet")

        result = subprocess.run(
            ["git", "-C", self.clone_path, "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def get_branches(self) -> List[str]:
        """Get list of all branches (local and remote).

        Returns:
            List of branch names
        """
        if not self.cloned:
            raise RuntimeError("Repository not cloned yet")

        result = subprocess.run(
            ["git", "-C", self.clone_path, "branch", "-a"],
            capture_output=True,
            text=True,
            check=True,
        )

        branches = []
        for line in result.stdout.split("\n"):
            line = line.strip()
            if line and not line.startswith("->"):
                # Remove remotes/ prefix if present
                if line.startswith("remotes/"):
                    line = line.replace("remotes/origin/", "")
                # Remove the leading * for current branch
                line = line.lstrip("* ")
                if line:
                    branches.append(line)

        return sorted(list(set(branches)))

    def is_branch(self, ref: str) -> bool:
        """Check if a ref is a branch (not a tag or commit).

        Args:
            ref: The ref to check

        Returns:
            True if the ref is a branch, False if it's a tag or commit
        """
        if not self.cloned:
            raise RuntimeError("Repository not cloned yet")

        # Check if it's a local branch
        result = subprocess.run(
            ["git", "-C", self.clone_path, "show-ref", "--verify", f"refs/heads/{ref}"],
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            return True

        # Check if it's a remote branch
        result = subprocess.run(
            [
                "git",
                "-C",
                self.clone_path,
                "show-ref",
                "--verify",
                f"refs/remotes/origin/{ref}",
            ],
            capture_output=True,
            check=False,
        )
        return result.returncode == 0

    def pull_worktree(self, worktree_path: str, branch: str) -> bool:
        """Pull latest changes in a worktree.

        Args:
            worktree_path: Path to the worktree
            branch: The branch to pull

        Returns:
            True if pull succeeded, False otherwise
        """
        # First fetch to get latest refs
        result = subprocess.run(
            ["git", "-C", worktree_path, "fetch", "origin", branch],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            return False

        # Then reset to the fetched branch (handles force pushes too)
        result = subprocess.run(
            ["git", "-C", worktree_path, "reset", "--hard", f"origin/{branch}"],
            capture_output=True,
            check=False,
        )
        return result.returncode == 0

    async def async_pull_worktree(
        self, worktree_path: str, branch: str, timeout: float = 30.0
    ) -> bool:
        """Pull latest changes in a worktree with timeout.

        Args:
            worktree_path: Path to the worktree
            branch: The branch to pull
            timeout: Maximum time to wait for pull in seconds

        Returns:
            True if pull succeeded, False if timeout or error
        """
        import asyncio
        import logging

        logger = logging.getLogger(__name__)

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(self.pull_worktree, worktree_path, branch),
                timeout=timeout,
            )
            if result:
                logger.debug(f"Git pull completed for {branch}")
            else:
                logger.warning(f"Git pull failed for {branch}")
            return result

        except asyncio.TimeoutError:
            logger.warning(f"Git pull timed out after {timeout}s for {branch}")
            return False
        except Exception as e:
            logger.error(f"Git pull failed for {branch}: {e}")
            return False

    def is_ref_valid(self, ref: str) -> bool:
        """Check if a ref (branch, tag, commit) exists.

        Args:
            ref: The ref to check (branch, tag, or commit hash)

        Returns:
            True if the ref exists, False otherwise
        """
        if not self.cloned:
            raise RuntimeError("Repository not cloned yet")

        # Try the ref as-is first
        result = subprocess.run(
            [
                "git",
                "-C",
                self.clone_path,
                "rev-parse",
                "--verify",
                f"{ref}^{{object}}",
            ],
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            return True

        # Try as a remote branch
        result = subprocess.run(
            [
                "git",
                "-C",
                self.clone_path,
                "rev-parse",
                "--verify",
                f"origin/{ref}^{{object}}",
            ],
            capture_output=True,
            check=False,
        )
        return result.returncode == 0

    def resolve_ref(self, ref: str) -> str:
        """Resolve a ref to a commit hash.

        Args:
            ref: The ref to resolve (branch, tag, or commit hash)

        Returns:
            The full commit hash

        Raises:
            RuntimeError: If the ref cannot be resolved
        """
        if not self.cloned:
            raise RuntimeError("Repository not cloned yet")

        result = subprocess.run(
            ["git", "-C", self.clone_path, "rev-parse", ref],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return result.stdout.strip()

        # Try as a remote branch
        result = subprocess.run(
            ["git", "-C", self.clone_path, "rev-parse", f"origin/{ref}"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return result.stdout.strip()

        raise RuntimeError(f"Cannot resolve ref: {ref}")

    def create_worktree(self, ref: str, worktree_path: str) -> None:
        """Create a git worktree (or checkout) for a specific ref.

        For remote repositories, attempts to use git worktree. For local
        repositories, falls back to creating a separate checkout directory.

        Args:
            ref: The ref to check out (branch, tag, or commit)
            worktree_path: Path where to create the worktree
        """
        if not self.cloned:
            raise RuntimeError("Repository not cloned yet")

        worktree_dir = Path(worktree_path)

        # If the worktree already exists, just checkout the ref
        if worktree_dir.exists():
            subprocess.run(
                ["git", "-C", str(worktree_dir), "checkout", ref],
                capture_output=True,
                check=False,  # Don't fail if already on this ref
            )
            return

        worktree_dir.parent.mkdir(parents=True, exist_ok=True)

        # Try worktree first with the ref as-is
        result = subprocess.run(
            ["git", "-C", self.clone_path, "worktree", "add", str(worktree_dir), ref],
            capture_output=True,
            check=False,
        )

        # If that fails, try with origin/ prefix (for remote branches)
        if result.returncode != 0:
            result = subprocess.run(
                [
                    "git",
                    "-C",
                    self.clone_path,
                    "worktree",
                    "add",
                    str(worktree_dir),
                    f"origin/{ref}",
                ],
                capture_output=True,
                check=False,
            )

        # Fall back to a manual checkout if worktree fails
        if result.returncode != 0:
            # Clone a separate copy for this ref
            # Try the ref as-is first
            result = subprocess.run(
                ["git", "clone", "-b", ref, self.repo_path, str(worktree_dir)],
                capture_output=True,
                check=False,
            )

            # If that fails, the repo source might not support -b with the exact ref
            # so just do a general clone and checkout
            if result.returncode != 0:
                subprocess.run(
                    ["git", "clone", self.repo_path, str(worktree_dir)],
                    capture_output=True,
                    check=True,
                )
                subprocess.run(
                    ["git", "-C", str(worktree_dir), "checkout", ref],
                    capture_output=True,
                    check=True,
                )

    def cleanup_worktree(self, worktree_path: str) -> None:
        """Clean up a git worktree or checkout.

        Args:
            worktree_path: Path to the worktree to remove
        """
        if not self.cloned:
            raise RuntimeError("Repository not cloned yet")

        worktree_dir = Path(worktree_path)

        # Try to remove as a worktree first
        subprocess.run(
            ["git", "-C", self.clone_path, "worktree", "remove", str(worktree_dir)],
            capture_output=True,
            check=False,
        )

        # Always remove the directory if it still exists
        if worktree_dir.exists():
            shutil.rmtree(worktree_dir)
