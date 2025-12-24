"""Configuration management for Pulso."""

import os
from pathlib import Path
from typing import Optional, Literal, cast


CacheBackend = Literal["filesystem", "redis"]


def _get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Read environment variable supporting legacy PULSO_* values."""
    pulso_key = key.replace("PULSO", "PULSO", 1)
    return os.getenv(pulso_key, os.getenv(key, default))


def _get_env_or_default(key: str, default: str) -> str:
    """Return a string env var ensured to never be None."""
    value = _get_env(key, default)
    return default if value is None else value


class PulsoConfig:
    """Global configuration for the Pulso package."""

    def __init__(self):
        # Load from environment variables
        self.cache_dir: Optional[Path] = self._get_cache_dir()
        self.session_id: str = _get_env_or_default("PULSO_SESSION_ID", "default")
        self.cache_backend: CacheBackend = cast(
            CacheBackend,
            _get_env_or_default("PULSO_CACHE_BACKEND", "filesystem"),
        )
        self.redis_url: Optional[str] = _get_env("PULSO_REDIS_URL")
        self.log_level: str = _get_env_or_default("PULSO_LOG_LEVEL", "INFO")

        # Default domain policies
        self.default_ttl: str = _get_env_or_default("PULSO_DEFAULT_TTL", "1d")
        self.default_driver: str = _get_env_or_default("PULSO_DEFAULT_DRIVER", "requests")
        self.default_max_retries: int = int(_get_env_or_default("PULSO_DEFAULT_MAX_RETRIES", "3"))
        self.default_retry_delay: float = float(_get_env_or_default("PULSO_DEFAULT_RETRY_DELAY", "1.0"))
        self.default_fallback: str = _get_env_or_default("PULSO_DEFAULT_FALLBACK", "return_cached")

        # Playwright settings
        self.playwright_headless: bool = _get_env_or_default("PULSO_PLAYWRIGHT_HEADLESS", "true").lower() == "true"
        self.playwright_timeout: int = int(_get_env_or_default("PULSO_PLAYWRIGHT_TIMEOUT", "30000"))

    def _get_cache_dir(self) -> Optional[Path]:
        """Get cache directory from environment or None for default."""
        cache_dir_env = _get_env("PULSO_CACHE_DIR")
        if cache_dir_env:
            return Path(cache_dir_env).expanduser()
        return None

    def get_session_cache_dir(self, base_dir: Path) -> Path:
        """Get cache directory for current session."""
        if self.session_id == "default":
            return base_dir
        return base_dir / "sessions" / self.session_id

    def set_session(self, session_id: str) -> None:
        """Set the current session ID."""
        self.session_id = session_id

    def load_from_env_file(self, env_file: Path) -> None:
        """Load configuration from .env file."""
        if not env_file.exists():
            return

        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    # Set environment variable
                    os.environ[key] = value

        # Reload configuration
        self.__init__()


# Global configuration instance
config = PulsoConfig()


def set_session(session_id: str) -> None:
    """Set the current session ID for isolated caching.

    Args:
        session_id: Unique identifier for this session

    Example:
        import pulso
        pulso.set_session("user_123")
        # All cache operations now use user_123 session
    """
    config.set_session(session_id)


def get_session() -> str:
    """Get the current session ID.

    Returns:
        Current session ID
    """
    return config.session_id


def load_config(env_file: str = ".env") -> None:
    """Load configuration from environment file.

    Args:
        env_file: Path to .env file (default: .env)
    """
    config.load_from_env_file(Path(env_file))
