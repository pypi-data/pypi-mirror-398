"""EnvsPublish command - publish an environment version (npm-style workflow)."""

import json
import tarfile
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from params_proto import EnvVar, proto

from .utils import is_dry_run, print_error, spinner, normalize_env_spec


# -- Configuration with environment variable defaults --

@proto.prefix
class Hub:
    """Vuer Hub connection settings."""

    url: str = EnvVar("VUER_HUB_URL", default="")  # Base URL of the Vuer Hub API
    auth_token: str = EnvVar("VUER_AUTH_TOKEN", default="")  # JWT token for authentication


# -- Subcommand dataclass --

@dataclass
class EnvsPublish:
    """Publish environment to registry (npm-style).

    Reads environment.json, creates tgz archive, and uploads to the hub.
    """

    directory: str = "."  # Directory containing environment.json
    timeout: int = 300  # Request timeout in seconds
    tag: str = "latest"  # Version tag
    dry_run: bool = False  # Simulate without uploading

    def __call__(self) -> int:
        """Execute envs-publish command."""
        try:
            dry_run = self.dry_run or is_dry_run()

            if not dry_run:
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

            print(f"[INFO] Reading environment.json from {self.directory}...")
            metadata, envs_metadata = parse_environments_json(self.directory)
            print(f"[INFO] Found package: {metadata['name']}/{metadata['version']}")

            # Validate dependencies if present
            dependencies = extract_dependencies(envs_metadata)
            if dependencies:
                print(f"[INFO] Validating {len(dependencies)} dependencies...")
                validate_dependencies(dependencies, dry_run, Hub.url, Hub.auth_token)
                print("[INFO] All dependencies are valid.")
            else:
                print("[INFO] No dependencies to validate.")

            print("[INFO] Creating tgz archive...")
            archive_path = create_tgz_archive(self.directory, metadata)
            print(f"[INFO] Archive created: {archive_path}")

            publish_to_registry(
                archive_path=archive_path,
                metadata=metadata,
                envs_metadata=envs_metadata,
                hub_url=Hub.url,
                auth_token=Hub.auth_token,
                timeout=self.timeout,
                dry_run=dry_run,
            )

            return 0
        except FileNotFoundError as e:
            print_error(str(e))
            return 1
        except ValueError as e:
            print_error(str(e))
            return 1
        except RuntimeError as e:
            # RuntimeError from validate_dependencies already prints error message
            # Only print if it wasn't already printed
            if "Dependency validation failed" not in str(e):
                print_error(str(e))
            return 1
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            return 1


# -- Helper functions --

def parse_environments_json(directory: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Parse environment.json and extract metadata plus full content.

    Returns:
        (metadata, full_data)
    """
    envs_path = Path(directory) / "environment.json"
    if not envs_path.exists():
        raise FileNotFoundError(f"environment.json not found in {directory}")

    try:
        with envs_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid environment.json: {e}") from e

    metadata = {
        "name": data.get("name", ""),
        "version": data.get("version", ""),
        "description": data.get("description", ""),
        "visibility": data.get("visibility", "PUBLIC"),
        "env_type": data.get("env-type", "") or data.get("env_type", ""),
    }

    if not metadata["name"]:
        raise ValueError("environment.json must contain 'name' field")
    if not metadata["version"]:
        raise ValueError("environment.json must contain 'version' field")

    return metadata, data


def extract_dependencies(envs_metadata: Dict[str, Any]) -> List[str]:
    """Extract dependencies from environment.json and convert to list format.

    Args:
        envs_metadata: Full environment.json content

    Returns:
        List of dependency specs like ["some-dependency/^1.2.3", ...]
        Returns empty list if no dependencies or dependencies is empty.
    """
    deps_dict = envs_metadata.get("dependencies", {})
    if not deps_dict or not isinstance(deps_dict, dict):
        return []

    dependencies = []
    for name, version_spec in deps_dict.items():
        if not isinstance(version_spec, str):
            version_spec = str(version_spec)
        dependencies.append(normalize_env_spec(f"{name}/{version_spec}"))

    return dependencies


def validate_dependencies(
    dependencies: List[str],
    dry_run: bool,
    hub_url: str,
    auth_token: str,
) -> None:
    """Validate dependencies with backend API.

    Args:
        dependencies: List of dependency specs like ["name/version", ...]
        dry_run: Whether to run in dry-run mode
        hub_url: Vuer Hub base URL
        auth_token: Authentication token

    Raises:
        RuntimeError: If validation fails (non-200 status or error in response)
    """
    if dry_run or is_dry_run():
        print("[INFO] (dry-run) Validating dependencies (simulated)...")
        return

    if not hub_url:
        raise RuntimeError(
            "Missing VUER_HUB_URL. Cannot validate dependencies without hub URL."
        )

    import requests

    url = f"{hub_url.rstrip('/')}/environments/dependencies"
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    headers["Content-Type"] = "application/json"

    payload = {"name_versionId_list": dependencies}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=300)
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to validate dependencies: {e}") from e

    status = response.status_code

    # Handle non-200 status codes
    if status != 200:
        error_msg = ""
        try:
            data = response.json()
            if isinstance(data, dict):
                error_msg = data.get("error") or data.get("message", "")
                if not error_msg:
                    error_msg = json.dumps(data, ensure_ascii=False)
            else:
                error_msg = json.dumps(data, ensure_ascii=False)
        except Exception:
            text = (response.text or "").strip()
            error_msg = text if text else "Unknown error"

        if error_msg:
            print_error(f"Dependency validation failed ({status}): {error_msg}")
        else:
            print_error(f"Dependency validation failed ({status})")
        raise RuntimeError(f"Dependency validation failed with status {status}")

    # Status 200: check for error field in response body
    try:
        data = response.json()
        if isinstance(data, dict) and "error" in data:
            error_msg = data["error"]
            print_error(f"Dependency validation failed: {error_msg}")
            raise RuntimeError(f"Dependency validation failed: {error_msg}")
    except (json.JSONDecodeError, ValueError):
        # Response is not JSON or doesn't have error field, assume success
        pass


def create_tgz_archive(directory: str, metadata: Dict[str, Any]) -> str:
    """Create a tgz archive from environment files."""
    archive_name = f"{metadata['name']}-{metadata['version']}.tgz"
    temp_dir = Path(tempfile.gettempdir())
    archive_path = str(temp_dir / archive_name)

    directory_path = Path(directory).resolve()

    with tarfile.open(archive_path, "w:gz") as tar:
        for file_path in directory_path.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(directory_path)
                tar.add(file_path, arcname=arcname)

    return archive_path


def upload_with_progress(archive_path: str, metadata: Dict[str, Any], timeout: int) -> None:
    """Simulate an upload in dry-run mode."""
    file_path = Path(archive_path)
    total_size = file_path.stat().st_size
    print(f"[INFO] (dry-run) Uploading {file_path.name} ({total_size} bytes)...")
    time.sleep(min(2.0, max(0.1, total_size / (10 * 1024 * 1024))))


def publish_to_registry(
    archive_path: str,
    metadata: Dict[str, Any],
    envs_metadata: Dict[str, Any],
    hub_url: str,
    auth_token: str,
    timeout: int,
    dry_run: bool,
) -> None:
    """Publish package to registry via API."""
    print(f"[INFO] Publishing {metadata['name']}/{metadata['version']} to registry...")
    print(f"[INFO] Archive: {archive_path}")
    print(f"[INFO] Metadata: {json.dumps(metadata, indent=2)}")
    print(f"[INFO] environment.json: {json.dumps(envs_metadata, indent=2)}")
    print(f"[INFO] Hub URL: {hub_url}")
    print(f"[INFO] Timeout: {timeout}s")

    if dry_run or is_dry_run():
        upload_with_progress(archive_path, metadata, timeout)
        print(f"[SUCCESS] (dry-run) Published {metadata['name']}/{metadata['version']} (no network call).")
        return

    # Import requests lazily to avoid SSL/cert loading in restricted envs.
    import requests

    url = f"{hub_url.rstrip('/')}/environments/upload"
    file_path = Path(archive_path)

    with file_path.open("rb") as f:
        files = {
            "package": (file_path.name, f, "application/octet-stream"),
        }
        data = {
            "name": str(metadata["name"]),
            "versionId": str(metadata["version"]),
            "description": str(metadata.get("description", "")),
            "type": str(metadata.get("env_type", "")),
            "visibility": str(metadata.get("visibility", "PUBLIC")),
        }
        # Send full environment.json content as metadata field.
        data["metadata"] = json.dumps(envs_metadata, ensure_ascii=False)

        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        stop_event = threading.Event()
        spinner_thread = threading.Thread(
            target=spinner,
            args=(f"[INFO] Uploading {file_path.name} ", stop_event),
            daemon=True,
        )
        spinner_thread.start()
        try:
            response = requests.post(
                url,
                data=data,
                files=files,
                headers=headers,
                timeout=timeout,
            )
        finally:
            stop_event.set()
            spinner_thread.join()

    status = response.status_code
    text = (response.text or "").strip()

    if status >= 300:
        inline_msg = ""
        try:
            data = response.json()
            if isinstance(data, dict):
                msg = data.get("message")
                err = data.get("error")
                if msg:
                    inline_msg = str(msg)
                elif err:
                    inline_msg = str(err)
                else:
                    inline_msg = json.dumps(data, ensure_ascii=False)
            else:
                inline_msg = json.dumps(data, ensure_ascii=False)
        except Exception:
            inline_msg = text

        inline_msg = (inline_msg or "").strip()
        if inline_msg:
            raise RuntimeError(f"Publish failed ({status}): {inline_msg}")
        raise RuntimeError(f"Publish failed ({status})")

    env_id = None
    env_name = metadata.get("name")
    env_version = metadata.get("version")
    try:
        payload = response.json()
        env = payload.get("environment", payload) if isinstance(payload, dict) else {}
        env_id = env.get("environmentId") or env.get("id")
        env_name = env.get("name", env_name)
        env_version = env.get("versionId", env_version)
    except Exception:
        pass

    print("\n=== Publish Success ===")
    if env_id:
        print(f"ID        : {env_id}")
    print(f"Name      : {env_name}")
    print(f"Version   : {env_version}")
    visibility = metadata.get("visibility", "PUBLIC")
    print(f"Visibility: {visibility}")

