"""Configuration loading for preview server using TOML."""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ServerConfig:
    """Server configuration loaded from TOML file.

    All fields are optional - they can be overridden by CLI arguments.
    """

    port: Optional[int] = None
    host: Optional[str] = None
    idle_ttl: Optional[str] = None
    auto_pull: Optional[str] = None
    basic_auth: Optional[str] = None
    log_file: Optional[str] = None
    secret: Optional[str] = None
    repo: Optional[str] = None
    repos: Optional[dict[str, str]] = None
    admin_secret: Optional[str] = None
    persist_repos: Optional[str] = None
    base_domain: Optional[str] = None

    @property
    def is_multi_repo(self) -> bool:
        """Check if multi-repo mode is enabled.

        Returns True if [repos] section is defined with at least one repo.
        """
        return self.repos is not None and len(self.repos) > 0


def load_config(config_path: str) -> ServerConfig:
    """Load server configuration from a TOML file.

    The TOML file format is:

        # Server port (default: 8000)
        port = 8000

        # Idle timeout before terminating sub-server (default: 5m)
        idle-ttl = "10m"

        # Basic auth credentials (optional)
        basic-auth = "user:password"

        # JSON logs output file (default: stderr)
        log-file = "/var/log/preview-server.log"

        # Single repo mode (backwards compatible)
        repo = "/path/to/repo"

        # Multi-repo mode (takes precedence over 'repo')
        [repos]
        project1 = "/path/to/repo1"
        project2 = "https://github.com/user/repo2"

    Args:
        config_path: Path to the TOML configuration file

    Returns:
        ServerConfig with loaded values

    Raises:
        FileNotFoundError: If the config file doesn't exist
        tomllib.TOMLDecodeError: If the TOML is invalid
        ValueError: If configuration values are invalid
    """
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(path, "rb") as f:
        data = tomllib.load(f)

    # Extract values with validation
    port = data.get("port")
    if port is not None:
        if not isinstance(port, int):
            raise ValueError(f"port must be an integer, got {type(port).__name__}")
        if not (1 <= port <= 65535):
            raise ValueError(f"port must be between 1 and 65535, got {port}")

    host = data.get("host")
    if host is not None:
        if not isinstance(host, str):
            raise ValueError(f"host must be a string, got {type(host).__name__}")

    idle_ttl = data.get("idle-ttl")
    if idle_ttl is not None:
        if not isinstance(idle_ttl, str):
            raise ValueError(
                f"idle-ttl must be a string, got {type(idle_ttl).__name__}"
            )

    auto_pull = data.get("auto-pull")
    if auto_pull is not None:
        if not isinstance(auto_pull, str):
            raise ValueError(
                f"auto-pull must be a string, got {type(auto_pull).__name__}"
            )

    basic_auth = data.get("basic-auth")
    if basic_auth is not None:
        if not isinstance(basic_auth, str):
            raise ValueError(
                f"basic-auth must be a string, got {type(basic_auth).__name__}"
            )
        if ":" not in basic_auth:
            raise ValueError("basic-auth must be in 'user:pass' format")

    log_file = data.get("log-file")
    if log_file is not None:
        if not isinstance(log_file, str):
            raise ValueError(
                f"log-file must be a string, got {type(log_file).__name__}"
            )

    secret = data.get("secret")
    if secret is not None:
        if not isinstance(secret, str):
            raise ValueError(f"secret must be a string, got {type(secret).__name__}")

    # Single repo field
    repo = data.get("repo")
    if repo is not None:
        if not isinstance(repo, str):
            raise ValueError(f"repo must be a string, got {type(repo).__name__}")

    # Multi-repo [repos] section
    repos = None
    if "repos" in data:
        repos_data = data["repos"]
        if not isinstance(repos_data, dict):
            raise ValueError(
                f"[repos] must be a table, got {type(repos_data).__name__}"
            )
        repos = {}
        for name, path in repos_data.items():
            if not isinstance(path, str):
                raise ValueError(
                    f"repo path for '{name}' must be a string, got {type(path).__name__}"
                )
            repos[name] = path

    # Admin secret for management API
    admin_secret = data.get("admin-secret")
    if admin_secret is not None:
        if not isinstance(admin_secret, str):
            raise ValueError(
                f"admin-secret must be a string, got {type(admin_secret).__name__}"
            )

    # Persistence file path for repos
    persist_repos = data.get("persist-repos")
    if persist_repos is not None:
        if not isinstance(persist_repos, str):
            raise ValueError(
                f"persist-repos must be a string, got {type(persist_repos).__name__}"
            )

    # Base domain for hostname parsing (default: localhost)
    base_domain = data.get("base-domain")
    if base_domain is not None:
        if not isinstance(base_domain, str):
            raise ValueError(
                f"base-domain must be a string, got {type(base_domain).__name__}"
            )

    return ServerConfig(
        port=port,
        host=host,
        idle_ttl=idle_ttl,
        auto_pull=auto_pull,
        basic_auth=basic_auth,
        log_file=log_file,
        secret=secret,
        repo=repo,
        repos=repos,
        admin_secret=admin_secret,
        persist_repos=persist_repos,
        base_domain=base_domain,
    )
