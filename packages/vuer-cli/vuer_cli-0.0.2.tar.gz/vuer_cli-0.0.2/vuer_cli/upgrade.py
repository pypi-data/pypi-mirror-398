"""Upgrade command - upgrade an environment in environment.json to latest version."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import json

from .envs_publish import Hub
from .sync import Sync, _extract_backend_error
from .utils import is_dry_run, print_error


@dataclass
class Upgrade:
    """Upgrade a single environment in environment.json to the latest version.

    Usage:
        vuer upgrade some-environment-name
    """

    # Primary usage is positional: `vuer upgrade some-environment-name`.
    env: Optional[str] = None  # Environment name to upgrade (no version part)
    # Kept for params-proto compatibility; not used in the new workflow.
    version: Optional[str] = None

    def __call__(self) -> int:
        """Execute upgrade command."""
        try:
            env_name = (self.env or "").strip()
            if not env_name:
                raise ValueError(
                    "Missing environment name. Usage: vuer upgrade some-environment-name"
                )

            cwd = Path.cwd()
            env_json_path = cwd / "environment.json"
            if not env_json_path.exists():
                raise FileNotFoundError(
                    "environment.json not found. Cannot upgrade environments."
                )

            try:
                with env_json_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid environment.json: {e}") from e

            deps = data.get("dependencies") or {}
            if not isinstance(deps, dict):
                raise ValueError(
                    "environment.json 'dependencies' field must be an object"
                )

            current_version = deps.get(env_name)
            if not isinstance(current_version, str) or not current_version:
                raise ValueError(
                    f"Environment '{env_name}' not found in environment.json; nothing to upgrade."
                )

            dry_run = is_dry_run()

            if dry_run:
                print(
                    f"[INFO] (dry-run) Would check latest version for '{env_name}', "
                    f"current version is '{current_version}'."
                )
                print(
                    "[INFO] (dry-run) Skipping upgrade and sync (no network calls).")
                return 0

            # Real upgrade: require hub configuration
            if not Hub.url:
                raise RuntimeError(
                    "Missing VUER_HUB_URL. Please set the VUER_HUB_URL environment variable "
                    "or pass --hub.url on the command line."
                )
            if not Hub.auth_token:
                raise RuntimeError(
                    "Missing VUER_AUTH_TOKEN. Please set the VUER_AUTH_TOKEN environment "
                    "variable or pass --hub.auth-token on the command line."
                )

            latest_version = _fetch_latest_version(env_name)

            if latest_version == current_version:
                print(
                    f"[INFO] Environment '{env_name}' is already at latest version "
                    f"({current_version})."
                )
                return 0

            # Update environment.json with the new version and run sync
            deps[env_name] = latest_version
            data["dependencies"] = deps
            with env_json_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")

            print(
                f"[INFO] Upgraded {env_name} from {current_version} to {latest_version} "
                "in environment.json. Running sync..."
            )
            return Sync()()

        except (FileNotFoundError, ValueError, RuntimeError) as e:
            print_error(str(e))
            return 1
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            return 1


def _fetch_latest_version(env_name: str) -> str:
    """Call backend /environments/latest-by-name to get latest versionId for env_name."""
    import requests  # Lazy import

    params = {"name": env_name}
    url = f"{Hub.url.rstrip('/')}/environments/latest-by-name"
    headers = {
        "Authorization": f"Bearer {Hub.auth_token}"
    } if Hub.auth_token else {}

    try:
        response = requests.get(url, params=params, headers=headers,
                                timeout=300)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        resp = getattr(e, "response", None)
        status = resp.status_code if resp is not None else "unknown"
        detail = _extract_backend_error(resp)
        raise RuntimeError(
            f"Failed to fetch latest version for '{env_name}' ({status}): {detail}"
        ) from e
    except requests.exceptions.RequestException as e:
        raise RuntimeError(
            f"Failed to fetch latest version for '{env_name}': {e}"
        ) from e

    data = response.json()

    # Error response format: {"error": "name is required"}
    if "error" in data:
        raise RuntimeError(
            f"Failed to fetch latest version for '{env_name}': {data['error']}"
        )

    payload = data.get("data")
    if not isinstance(payload, dict):
        raise ValueError(
            "Invalid response format: 'data' field must be an object")

    version_id = payload.get("versionId")
    if not version_id:
        raise ValueError(
            "Invalid response format: 'data.versionId' field is required"
        )

    return str(version_id)
