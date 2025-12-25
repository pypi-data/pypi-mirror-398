"""Sub-server management for per-ref deployments."""

import asyncio
import logging
import os
import shutil
import subprocess
import sys
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Deque, Dict, Optional

from preview_server.git import GitManager
from preview_server.utils import reserve_port, get_serve_command

# Maximum number of restart attempts before giving up on a crashed server
MAX_RESTART_ATTEMPTS = 3


@dataclass
class SubServerInfo:
    """Information about a running sub-server."""

    ref: str
    port: int
    pid: int
    worktree_path: str
    start_time: float
    restart_attempts: int = 0
    process: Optional[subprocess.Popen] = None
    command: str = ""
    recent_logs: Deque[str] = field(default_factory=lambda: deque(maxlen=100))
    last_request_time: float = field(default_factory=lambda: __import__("time").time())

    def add_log(self, message: str) -> None:
        """Add a log message with UTC timestamp.

        Uses a deque with maxlen for O(1) circular buffer behavior.

        Args:
            message: The log message to add
        """
        from datetime import datetime, timezone

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.recent_logs.append(f"[{timestamp}] {message}")


class SubServerManager:
    """Manages the lifecycle of per-ref sub-servers."""

    def __init__(
        self,
        repo_path: str,
        clone_path: str,
        worktree_base_path: str,
        idle_ttl_seconds: float = 300.0,
        auto_pull_seconds: Optional[float] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize SubServerManager.

        Args:
            repo_path: Path or URL of the git repository
            clone_path: Path where to clone the repository
            worktree_base_path: Base path for creating worktrees
            idle_ttl_seconds: Idle timeout in seconds before terminating server (default: 300s/5m)
            auto_pull_seconds: Auto-pull branches if not requested within this many seconds (None=disabled)
            logger: Optional logger instance
        """
        self.repo_path = repo_path
        self.clone_path = clone_path
        self.worktree_base_path = worktree_base_path
        self.idle_ttl_seconds = idle_ttl_seconds
        self.auto_pull_seconds = auto_pull_seconds
        self.logger = logger or logging.getLogger(__name__)

        self.git_manager = GitManager(repo_path, clone_path)
        self.servers: Dict[str, SubServerInfo] = {}
        self._lock = asyncio.Lock()
        self._monitoring_task: Optional[asyncio.Task] = None

    async def initialize(self) -> None:
        """Initialize the repository and start monitoring."""
        self.logger.info(f"Initializing git repository from {self.repo_path}")
        # Run git clone in executor to avoid blocking
        await asyncio.to_thread(self.git_manager.clone)

        # Start monitoring task for idle timeouts and crash recovery
        self._monitoring_task = asyncio.create_task(self._monitor_servers())

    async def get_port_for_ref(self, ref: str) -> int:
        """Get the port for a specific ref, starting the server if needed.

        If auto-pull is enabled and the ref is a branch that hasn't been
        requested within auto_pull_seconds, pulls latest changes before returning.

        Args:
            ref: The git ref (branch, tag, or commit)

        Returns:
            The port the server is running on

        Raises:
            RuntimeError: If the server fails to start
        """
        async with self._lock:
            # Check if already running
            if ref in self.servers and self.is_ref_running(ref):
                info = self.servers[ref]

                # Check if we need to auto-pull
                if await self._should_auto_pull(ref, info):
                    await self._do_auto_pull(ref, info)

                return info.port

            # Start new server
            return await self._start_server_for_ref(ref)

    async def _should_auto_pull(self, ref: str, info: SubServerInfo) -> bool:
        """Check if we should auto-pull for this ref.

        Args:
            ref: The git ref
            info: Server info for the ref

        Returns:
            True if we should pull, False otherwise
        """
        # Auto-pull disabled
        if self.auto_pull_seconds is None:
            return False

        # Check if enough time has passed since last request
        import time

        time_since_request = time.time() - info.last_request_time
        if time_since_request < self.auto_pull_seconds:
            return False

        # Check if this is a branch (tags and commits are immutable)
        try:
            is_branch = await asyncio.to_thread(self.git_manager.is_branch, ref)
            return is_branch
        except Exception as e:
            self.logger.warning(f"Failed to check if {ref} is a branch: {e}")
            return False

    async def _do_auto_pull(self, ref: str, info: SubServerInfo) -> None:
        """Perform auto-pull for a branch.

        Args:
            ref: The git ref (branch)
            info: Server info for the ref
        """
        self.logger.info(f"Auto-pulling latest changes for branch {ref}")
        info.add_log(f"[AUTO-PULL] Pulling latest changes for branch {ref}")

        try:
            success = await self.git_manager.async_pull_worktree(
                info.worktree_path, ref, timeout=30.0
            )
            if success:
                self.logger.info(f"Auto-pull succeeded for {ref}")
                info.add_log(f"[AUTO-PULL] Pull succeeded")
            else:
                self.logger.warning(f"Auto-pull failed for {ref}")
                info.add_log(f"[AUTO-PULL] Pull failed (continuing with existing code)")
        except Exception as e:
            self.logger.error(f"Auto-pull error for {ref}: {e}")
            info.add_log(f"[AUTO-PULL] Error: {e}")

    async def _start_server_for_ref(self, ref: str) -> int:
        """Start a new server for a specific ref.

        Args:
            ref: The git ref to deploy

        Returns:
            The port the server is running on

        Raises:
            RuntimeError: If the server fails to start
        """
        # Validate the ref exists, attempting fetch if not found locally
        if not await asyncio.to_thread(self.git_manager.is_ref_valid, ref):
            self.logger.info(
                f"Ref '{ref}' not found locally, attempting fetch from remote"
            )

            # Try to fetch from remote with timeout
            fetch_success = await self.git_manager.async_fetch_with_timeout(timeout=5.0)

            if fetch_success:
                # Re-check if ref is now valid after fetch
                if await asyncio.to_thread(self.git_manager.is_ref_valid, ref):
                    self.logger.info(f"Ref '{ref}' found after fetch")
                else:
                    # Fetch succeeded but ref still not found
                    raise RuntimeError(
                        f"Ref '{ref}' not found in repository. "
                        f"Verify the ref exists in the remote repository."
                    )
            else:
                # Fetch failed or timed out
                # Try one more time in case it was added during fetch
                if not await asyncio.to_thread(self.git_manager.is_ref_valid, ref):
                    raise RuntimeError(
                        f"Ref '{ref}' not found locally and fetch from remote failed or timed out. "
                        f"Verify the ref exists and the remote repository is accessible."
                    )

        # Create worktree
        worktree_path = Path(self.worktree_base_path) / ref
        self.logger.info(f"Creating worktree for {ref} at {worktree_path}")

        try:
            await asyncio.to_thread(
                self.git_manager.create_worktree, ref, str(worktree_path)
            )
        except Exception as e:
            self.logger.error(f"Failed to create worktree for {ref}: {e}")
            raise RuntimeError(f"Failed to create worktree: {e}")

        # Reserve a port (keeps socket open to prevent race condition)
        port, port_socket = await asyncio.to_thread(reserve_port)

        # Start the server
        self.logger.info(f"Starting server for {ref} on port {port}")
        try:
            # Close the reservation socket BEFORE starting process so it can bind
            # This minimizes the race window - we release just before spawn
            port_socket.close()

            process, command, error_message = await self._start_process(
                str(worktree_path), port
            )

            if process is None or process.poll() is not None:
                # Process failed to start or died immediately
                await self._cleanup_worktree(str(worktree_path))
                raise RuntimeError(error_message or f"Failed to start server for {ref}")

            # Wait for server to be ready
            # Use longer timeout since uv run installs dependencies which can be slow
            if not await self._wait_for_server(port, timeout=15.0):
                self.logger.error(f"Server for {ref} did not respond")
                process.terminate()
                try:
                    await asyncio.to_thread(process.wait, timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    await asyncio.to_thread(process.wait)
                await self._cleanup_worktree(str(worktree_path))
                raise RuntimeError(f"Server for {ref} did not respond")
        except Exception:
            # Ensure socket is closed on any failure (may already be closed)
            try:
                port_socket.close()
            except Exception:
                pass
            raise

        # Record server info
        import time

        self.servers[ref] = SubServerInfo(
            ref=ref,
            port=port,
            pid=process.pid,
            worktree_path=str(worktree_path),
            start_time=time.time(),
            process=process,
            command=command,
        )

        # Add startup log entry
        server_info = self.servers[ref]
        server_info.add_log(f"[STARTUP] Started on port {port} with command: {command}")

        self.logger.info(f"Server for {ref} started on port {port} (PID {process.pid})")
        return port

    async def _start_process(self, worktree_path: str, port: int) -> tuple:
        """Start the server process using server.sh script.

        Executes the server.sh script in the worktree with PORT environment
        variable set to the assigned port.

        Args:
            worktree_path: Path to the worktree
            port: Port to run on

        Returns:
            Tuple of (process, command_string, error_message)
            - If successful: (process, command_string, None)
            - If failed: (None, "", error_message with diagnostics)
        """
        env = os.environ.copy()
        env["PORT"] = str(port)

        # Get the serve command (server.sh)
        try:
            command_str = get_serve_command(worktree_path)
        except RuntimeError as e:
            error_message = str(e)
            self.logger.error(error_message)
            return None, "", error_message

        try:
            self.logger.debug(
                f"Starting process with: {command_str} in {worktree_path}"
            )

            # Use shell=True to handle complex command strings
            process = subprocess.Popen(
                command_str,
                shell=True,
                cwd=worktree_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                preexec_fn=os.setpgrp if hasattr(os, "setpgrp") else None,
            )

            # Give it a moment to see if it starts
            await asyncio.sleep(0.2)

            if process.poll() is None:
                # Process is still running, success!
                self.logger.debug(f"Started process with command: {command_str}")
                return process, command_str, None

            # Process exited immediately - collect diagnostics
            stdout, stderr = await asyncio.to_thread(process.communicate)
            error_output = stderr.decode("utf-8", errors="ignore").strip()

            error_message = (
                f"Failed to start server process with: {command_str}\n\n"
                f"Working directory: {worktree_path}\n"
                f"Exit code: {process.returncode}\n\n"
                f"Error output:\n{error_output if error_output else '(no error output)'}"
            )
            self.logger.error(error_message)
            return None, "", error_message

        except Exception as e:
            error_message = (
                f"Failed to start server process with: {command_str}\n\n"
                f"Working directory: {worktree_path}\n"
                f"Exception: {type(e).__name__}: {e}"
            )
            self.logger.error(error_message)
            return None, "", error_message

    async def _wait_for_server(self, port: int, timeout: float = 5.0) -> bool:
        """Wait for a server to be ready on the given port.

        Args:
            port: Port to check
            timeout: Maximum time to wait in seconds

        Returns:
            True if server is ready, False if timeout
        """
        import httpx

        loop = asyncio.get_running_loop()
        start_time = loop.time()

        while loop.time() - start_time < timeout:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"http://127.0.0.1:{port}/", timeout=0.5
                    )
                    if response.status_code < 500:
                        return True
            except Exception:
                pass

            await asyncio.sleep(0.1)

        return False

    def _capture_process_logs(self, info: SubServerInfo) -> None:
        """Capture available logs from a sub-server process and add to info.recent_logs.

        Reads from both stdout and stderr to capture all application output.

        Args:
            info: The SubServerInfo for the process
        """
        if not info.process:
            return

        import fcntl
        import errno

        # Read from both stdout and stderr
        for stream, stream_name in [
            (info.process.stdout, "stdout"),
            (info.process.stderr, "stderr"),
        ]:
            if not stream:
                continue

            try:
                # Set non-blocking mode
                flags = fcntl.fcntl(stream, fcntl.F_GETFL)
                fcntl.fcntl(stream, fcntl.F_SETFL, flags | os.O_NONBLOCK)

                try:
                    output = stream.read()
                    if output:
                        new_logs = output.decode("utf-8", errors="ignore").split("\n")
                        for line in new_logs:
                            if line.strip():
                                info.add_log(line)
                except (OSError, IOError) as e:
                    if e.errno != errno.EAGAIN:
                        info.add_log(f"[ERROR] Error reading {stream_name}: {e}")
            except Exception as e:
                info.add_log(f"[ERROR] Error capturing {stream_name}: {e}")

    def _get_recent_logs(self, info: SubServerInfo, max_lines: int = 100) -> list:
        """Get recent log lines from a sub-server process.

        Args:
            info: The SubServerInfo for the process
            max_lines: Maximum number of lines to return (default 100)

        Returns:
            List of recent log lines (strings), up to max_lines
        """
        # Capture any new logs from the process
        self._capture_process_logs(info)

        # Convert deque to list for API compatibility
        logs = list(info.recent_logs)
        if len(logs) > max_lines:
            return logs[-max_lines:]
        return logs

    def is_ref_running(self, ref: str) -> bool:
        """Check if a ref is currently running.

        Args:
            ref: The git ref

        Returns:
            True if running, False otherwise
        """
        if ref not in self.servers:
            return False

        info = self.servers[ref]
        if info.process is None:
            return False

        return info.process.poll() is None

    def get_running_refs(self) -> list[str]:
        """Get list of currently running refs.

        Returns:
            List of ref names
        """
        return [ref for ref in self.servers if self.is_ref_running(ref)]

    async def stop_ref(self, ref: str, reason: str = "manual stop") -> None:
        """Stop a sub-server for a specific ref.

        Args:
            ref: The git ref to stop
            reason: Reason for stopping (for logging)
        """
        async with self._lock:
            if ref not in self.servers:
                return

            info = self.servers[ref]

            # Log shutdown event
            info.add_log(f"[SHUTDOWN] Stopping server: {reason}")

            # Terminate the process
            if info.process is not None:
                self.logger.info(f"Stopping server for {ref}: {reason}")
                try:
                    info.process.terminate()
                    try:
                        await asyncio.to_thread(info.process.wait, timeout=2)
                    except subprocess.TimeoutExpired:
                        info.process.kill()
                        await asyncio.to_thread(info.process.wait)
                except Exception as e:
                    self.logger.error(f"Error stopping process for {ref}: {e}")
                    info.add_log(f"[ERROR] Error stopping process: {e}")

            # Clean up worktree
            await self._cleanup_worktree(info.worktree_path)

            # Remove from tracking
            del self.servers[ref]

    def update_last_request_time(self, ref: str) -> None:
        """Update last request time for a ref (resets idle timer).

        Args:
            ref: The git ref
        """
        if ref in self.servers:
            import time

            self.servers[ref].last_request_time = time.time()

    async def _cleanup_worktree(self, worktree_path: str) -> None:
        """Clean up a worktree directory.

        Args:
            worktree_path: Path to the worktree
        """
        try:
            await asyncio.to_thread(self.git_manager.cleanup_worktree, worktree_path)
            self.logger.info(f"Cleaned up worktree at {worktree_path}")
        except Exception as e:
            self.logger.error(f"Error cleaning up worktree: {e}")
            # Still try to remove it
            try:
                shutil.rmtree(worktree_path, ignore_errors=True)
            except Exception:
                pass

    async def _monitor_servers(self) -> None:
        """Monitor servers for crashes and idle timeouts, cleanup dead processes."""
        import time

        while True:
            try:
                await asyncio.sleep(1)

                async with self._lock:
                    # Check for dead processes and idle servers
                    refs_to_clean = []
                    current_time = time.time()

                    refs_to_restart = []

                    for ref, info in list(self.servers.items()):
                        # Check if process crashed
                        if info.process is not None and info.process.poll() is not None:
                            exit_code = info.process.returncode
                            self.logger.warning(
                                f"Server for {ref} crashed (exit code: {exit_code})"
                            )
                            info.add_log(
                                f"[CRASH] Process exited with code {exit_code}"
                            )

                            # Check if we should attempt restart
                            if info.restart_attempts < MAX_RESTART_ATTEMPTS:
                                refs_to_restart.append(ref)
                            else:
                                self.logger.error(
                                    f"Server for {ref} exceeded max restart attempts "
                                    f"({MAX_RESTART_ATTEMPTS}), giving up"
                                )
                                info.add_log(
                                    f"[FATAL] Exceeded max restart attempts "
                                    f"({MAX_RESTART_ATTEMPTS}), giving up"
                                )
                                refs_to_clean.append(
                                    (
                                        ref,
                                        f"exceeded max restarts ({MAX_RESTART_ATTEMPTS})",
                                    )
                                )
                            continue

                        # Check for idle timeout
                        time_since_last_request = current_time - info.last_request_time
                        if time_since_last_request >= self.idle_ttl_seconds:
                            self.logger.info(
                                f"Server for {ref} idle for {time_since_last_request:.0f}s "
                                f"(timeout: {self.idle_ttl_seconds}s), shutting down"
                            )
                            idle_minutes = int(time_since_last_request) // 60
                            idle_seconds = int(time_since_last_request) % 60
                            info.add_log(
                                f"[IDLE] Idle timeout after {idle_minutes}m {idle_seconds}s"
                            )
                            refs_to_clean.append(
                                (ref, f"idle timeout ({idle_minutes}m {idle_seconds}s)")
                            )

                    # Clean up dead and idle servers
                    for ref, reason in refs_to_clean:
                        if ref in self.servers:
                            info = self.servers[ref]
                            # Try to terminate gracefully
                            if info.process is not None and info.process.poll() is None:
                                try:
                                    info.process.terminate()
                                    try:
                                        await asyncio.to_thread(
                                            info.process.wait, timeout=1
                                        )
                                    except subprocess.TimeoutExpired:
                                        info.process.kill()
                                        await asyncio.to_thread(info.process.wait)
                                except Exception:
                                    pass
                            info.add_log(f"[SHUTDOWN] Terminated due to: {reason}")
                            await self._cleanup_worktree(info.worktree_path)
                            del self.servers[ref]

                    # Attempt restarts for crashed servers (still under lock)
                    for ref in refs_to_restart:
                        if ref in self.servers:
                            info = self.servers[ref]
                            info.restart_attempts += 1
                            attempt = info.restart_attempts

                            self.logger.info(
                                f"Attempting restart {attempt}/{MAX_RESTART_ATTEMPTS} "
                                f"for {ref}"
                            )
                            info.add_log(
                                f"[RESTART] Attempting restart "
                                f"{attempt}/{MAX_RESTART_ATTEMPTS}"
                            )

                            # Start new process using same worktree and port
                            process, command, error_message = await self._start_process(
                                info.worktree_path, info.port
                            )

                            if process is not None and process.poll() is None:
                                # Restart successful
                                info.process = process
                                info.pid = process.pid
                                info.command = command
                                self.logger.info(
                                    f"Restart successful for {ref} "
                                    f"(PID {process.pid})"
                                )
                                info.add_log(
                                    f"[RESTART] Success - new PID {process.pid}"
                                )
                            else:
                                # Restart failed immediately
                                self.logger.error(
                                    f"Restart failed for {ref}: {error_message}"
                                )
                                info.add_log(f"[RESTART] Failed: {error_message}")
                                # Process will be detected as crashed on next iteration

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitor task: {e}")

    async def shutdown(self) -> None:
        """Shut down all servers."""
        self.logger.info("Shutting down all servers")

        # Stop all servers
        refs_to_stop = list(self.servers.keys())
        for ref in refs_to_stop:
            await self.stop_ref(ref)

        # Cancel monitoring task
        if self._monitoring_task is not None:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Shutdown complete")
