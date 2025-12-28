"""Shared utilities for Vuer CLI."""

import itertools
import threading
import time

from params_proto import EnvVar, proto


@proto.prefix
class Config:
    """CLI configuration settings."""

    def _get_dry_run(self) -> bool:
        """Whether to run in dry-run mode (no real network calls).

        Controlled by VUER_CLI_DRY_RUN environment variable:
            - unset  -> False (real API calls, default)
            - "0"    -> False (real API calls)
            - "false"/"False" -> False
            - anything else   -> True (dry-run)
        """
        # Use EnvVar with default=None to detect if it's actually set
        dry_run_env = EnvVar("VUER_CLI_DRY_RUN", default=None)
        value = dry_run_env.get()
        if value is not None:
            # Environment variable is set, check its value
            return value not in ("0", "false", "False")

        # Default to real execution when nothing is set
        return False

    # Use a property to compute dry_run dynamically
    @property
    def dry_run(self) -> bool:
        return self._get_dry_run()


# Create singleton instance
_config = Config()


def is_dry_run() -> bool:
    """Whether to run in dry-run mode (no real network calls).
    
    This is a convenience function that uses the Config singleton.
    """
    return _config.dry_run


def print_error(message: str) -> None:
    """Print error message in bright red color for better visibility."""
    # ANSI escape codes: \033[91m = bright red, \033[0m = reset
    print(f"\033[91m[ERROR] {message}\033[0m")


def spinner(message: str, stop_event: threading.Event,
            interval: float = 0.1) -> None:
    """Cool spinner: message + blinking dots + rotating slash (| / - \\) at the end."""
    # Rotating slash: | / - \
    spinner_chars = itertools.cycle(["|", "/", "-", "\\"])
    # Blinking dots: show/hide every 2 frames
    frame_count = 0
    while not stop_event.is_set():
        char = next(spinner_chars)
        frame_count += 1
        # Blink dots every 2 frames (show on even frames, hide on odd frames)
        dots = "..." if frame_count % 2 == 0 else "   "
        print(f"\r{message}{dots} {char}", end="", flush=True)
        time.sleep(interval)
    # Clear the line
    print("\r" + " " * (len(message) + 6) + "\r", end="", flush=True)


def parse_env_spec(env_spec: str) -> tuple[str, str]:
    """Parse an environment spec and return (name, version).

    Accepts the canonical separator '/' (e.g. 'name/version').
    Raises ValueError for invalid formats. Legacy '@' syntax is no longer supported.
    """
    if not env_spec or not isinstance(env_spec, str):
        raise ValueError(
            f"Invalid environment spec '{env_spec}'. Expected format: name/version")

    # Prefer '/' as the canonical separator
    if "/" in env_spec:
        parts = env_spec.rsplit("/", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError(
                f"Invalid environment spec '{env_spec}'. Expected format: name/version")
        return parts[0], parts[1]

    # Do not accept legacy '@' syntax anymore
    raise ValueError(
        f"Invalid environment spec '{env_spec}'. Expected format: name/version")


def normalize_env_spec(env_spec: str) -> str:
    """Return the canonical env spec string using '/' as separator: 'name/version'."""
    name, version = parse_env_spec(env_spec)
    return f"{name}/{version}"
