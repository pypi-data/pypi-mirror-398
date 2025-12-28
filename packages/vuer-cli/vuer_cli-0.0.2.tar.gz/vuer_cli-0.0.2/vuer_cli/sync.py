"""Sync command - pull all environments from environment.json dependencies (npm-style)."""

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List

from .envs_publish import Hub
from .envs_pull import pull_from_registry
from .utils import (
    is_dry_run,
    print_error,
    parse_env_spec,
)


@dataclass
class Sync:
    """Sync environments listed in environment.json dependencies (like npm install).

    Reads environment.json, validates dependencies with backend, and downloads
    all environments and their transitive dependencies to vuer_environments/ directory.
    """

    output: str = "vuer_environments"  # Destination directory (default: vuer_environments)
    timeout: int = 3000  # Request timeout in seconds
    concurrent: bool = False  # Download concurrently (future enhancement)

    def __call__(self) -> int:
        """Execute sync command."""
        try:
            dry_run = is_dry_run()

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

            # Step 1: Find and parse environment.json
            print(
                "[INFO] Looking for environment.json in current directory...")
            current_dir = Path.cwd()
            env_json_path = current_dir / "environment.json"
            if not env_json_path.exists():
                raise FileNotFoundError(
                    f"environment.json not found in {current_dir}. "
                    "Please run this command in a directory containing environment.json."
                )

            # Step 2: Parse dependencies
            print(f"[INFO] Reading environment.json from {current_dir}...")
            dependencies = parse_dependencies(env_json_path)

            # Step 3: Prepare output directory and lockfile path (environments-lock.yaml is
            # located alongside the vuer_environments directory)
            output_dir = Path(self.output).expanduser().resolve()
            output_dir.mkdir(parents=True, exist_ok=True)
            lock_path = output_dir.parent / "environments-lock.yaml"

            # Step 4: Handle empty dependencies case - still need to clean up Module/
            if not dependencies:
                print(
                    "[INFO] No environments to sync. environment.json has no dependencies.")
                # Still reconcile: remove all environments if lockfile exists
                previous_deps = read_environments_lock(lock_path)
                desired_deps = []  # Empty list since no dependencies
                write_environments_lock(lock_path, desired_deps)
                print(f"[INFO] Wrote environments lock to {lock_path}")
                
                # Remove all environments that are no longer needed
                removed = remove_unneeded_env_dirs(output_dir, previous_deps, desired_deps)
                if removed:
                    print(f"[INFO] Removed {removed} unused environment directories from {output_dir}")
                else:
                    print("[INFO] No environments to remove from vuer_environments/")
                return 0

            print(f"[INFO] Found {len(dependencies)} dependencies to sync.")

            # Step 5: Validate dependencies with backend
            print("[INFO] Validating dependencies with backend...")
            resolved_deps = validate_and_get_dependencies(dependencies, dry_run)

            # Step 6: Collect all environments (direct + transitive)
            all_environments = collect_all_environments(dependencies, resolved_deps)
            print(
                f"[INFO] Total environments to download: {len(all_environments)}")

            # Step 7: Download all environments to Module/ directory
            # Step 10/11: Reconcile dependencies.toml to match current resolution
            # (If user removes deps from environment.json, we also remove them from Module/.)
            previous_deps = read_environments_lock(lock_path)
            desired_deps = dedupe_keep_order(all_environments)
            write_environments_lock(lock_path, desired_deps)
            print(f"[INFO] Wrote environments lock to {lock_path}")

            print(f"[INFO] Downloading environments to {output_dir}...")
            # Remove environments that are no longer needed.
            removed = remove_unneeded_env_dirs(output_dir, previous_deps, desired_deps)
            if removed:
                print(f"[INFO] Removed {removed} unused environment directories from {output_dir}")

            for env_spec in desired_deps:
                # map to nested path: vuer_environments/<name>/<version>
                name, version = parse_env_spec(env_spec)
                env_path = output_dir / name / version
                if env_path.exists():
                    print(f"[INFO] Skipping already-synced {env_spec}")
                    continue
                print(f"[INFO] Downloading {env_spec}...")
                _env_dir = pull_from_registry(
                    env_flag=env_spec,
                    output_dir=str(output_dir),
                    # Use filesystem-safe filename derived from name-version
                    filename=f"{name}-{version}.tgz",
                    version=None,
                    timeout=self.timeout,
                    skip_progress=False,
                )

                # Keep downloaded environment.json files intact per new policy.

            print(
                f"[SUCCESS] Synced {len(all_environments)} environments to {output_dir}")
            return 0

        except FileNotFoundError as e:
            print_error(str(e))
            return 1
        except ValueError as e:
            print_error(str(e))
            return 1
        except RuntimeError as e:
            print_error(str(e))
            return 1
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            return 1


# -- Helper functions --


def parse_dependencies(env_json_path: Path) -> List[str]:
    """Parse environment.json and extract dependencies list.

    Returns:
        List of dependency specs like ["some-dependency/^1.2.3", ...]
    """
    try:
        with env_json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid environment.json: {e}") from e

    deps_dict = data.get("dependencies", {})
    if not isinstance(deps_dict, dict):
        raise ValueError(
            "environment.json 'dependencies' field must be an object")

    dependencies = []
    for name, version_spec in deps_dict.items():
        if not isinstance(version_spec, str):
            version_spec = str(version_spec)
        dependencies.append(f"{name}/{version_spec}")

    return dependencies


def validate_and_get_dependencies(
        dependencies: List[str], dry_run: bool
) -> List[str]:
    """Validate dependencies with backend and get transitive dependencies.

    Args:
        dependencies: List of dependency specs like ["name@version", ...]
        dry_run: Whether to run in dry-run mode

    Returns:
        A flat list (not deduplicated) of all resolved environment specs,
        as returned by the backend:
            {"dependencies": ["some-dependency@1.2.5", "numpy@1.24.3", ...]}

    Raises:
        RuntimeError: If some environments don't exist
    """
    if dry_run:
        # Dry-run: return mock data
        print("[INFO] (dry-run) Validating dependencies (simulated)...")
        resolved: List[str] = []
        for dep in dependencies:
            # Include the requested deps, plus some mock transitive deps (with possible duplicates)
            resolved.append(dep)
            if "new-dependency" in dep:
                continue
            if "another-dependency" in dep:
                resolved.extend(["react/^18.2.0", "react-dom/^18.2.0", "react/^18.2.0"])
            else:
                resolved.extend(["numpy/^1.24.0", "pandas/~2.0.0", "numpy/^1.24.0"])
        return resolved

    # Real API call
    import requests

    url = f"{Hub.url.rstrip('/')}/environments/dependencies"
    headers = {
        "Authorization": f"Bearer {Hub.auth_token}"} if Hub.auth_token else {}
    headers["Content-Type"] = "application/json"

    payload = {"name_versionId_list": dependencies}

    try:
        response = requests.post(url, json=payload, headers=headers,
                                 timeout=300)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        resp = getattr(e, "response", None)
        status = resp.status_code if resp is not None else "unknown"
        detail = _extract_backend_error(resp)
        raise RuntimeError(
            f"Failed to validate dependencies ({status}): {detail}"
        ) from e
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to validate dependencies: {e}") from e

    data = response.json()

    # Check for errors (environments not found)
    if "error" in data:
        error_msg = data["error"]
        raise RuntimeError(f"Dependency validation failed: {error_msg}")

    deps = data.get("dependencies", None)
    if deps is None:
        raise ValueError("Invalid response format: missing 'dependencies' field")
    if not isinstance(deps, list) or not all(isinstance(x, str) for x in deps):
        raise ValueError("Invalid response format: 'dependencies' must be a list of strings")
    return deps


def _extract_backend_error(response: Any) -> str:
    """Extract a concise error message from an HTTP response."""
    if response is None:
        return "No response body"
    try:
        payload = response.json()
        if isinstance(payload, dict):
            msg = payload.get("error") or payload.get("message")
            if msg:
                return str(msg)
        return json.dumps(payload, ensure_ascii=False)
    except Exception:
        text = getattr(response, "text", "") or ""
        text = text.strip()
        return text if text else "Empty response body"


def write_environments_lock(path: Path, dependencies: List[str]) -> None:
    """Write the environments lock file (YAML) next to `vuer_environments`."""
    deps = dedupe_keep_order(dependencies)
    lines = [
        "# This file is generated by `vuer sync`.",
        "# DO NOT EDIT THIS FILE MANUALLY.",
        "# This file is maintained by the system.",
        "# It lists the resolved (deduplicated) environment dependencies.",
        "",
        "environments:",
    ]
    for dep in deps:
        escaped = dep.replace('"', '\\"')
        lines.append(f'  - "{escaped}"')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def dedupe_keep_order(items: List[str]) -> List[str]:
    """Deduplicate list while preserving first-seen order."""
    return list(dict.fromkeys(items))


def read_environments_lock(path: Path) -> List[str]:
    """Read environments from environments-lock.yaml.

    The file format is expected to be a YAML list under `environments:`. This
    reader implements a minimal parser that extracts entries starting with '-'.
    """
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    lines = []
    for raw in text.splitlines():
        s = raw.strip()
        if s.startswith("-"):
            item = s[1:].strip()
            # strip optional quotes
            if (item.startswith('"') and item.endswith('"')) or (item.startswith("'") and item.endswith("'")):
                item = item[1:-1]
            lines.append(item)
    return lines


def remove_unneeded_env_dirs(output_dir: Path, previous: List[str], desired: List[str]) -> int:
    """Remove env directories that were previously synced but are no longer desired.

    We only remove directories that correspond to entries in the old dependencies.toml,
    to avoid deleting unrelated user folders under Module/.
    """
    prev_set = set(previous)
    desired_set = set(desired)
    to_remove = [d for d in previous if d in prev_set and d not in desired_set]
    removed = 0
    for env_spec in to_remove:
        name, version = parse_env_spec(env_spec)
        env_dir = output_dir / name / version
        if env_dir.exists() and env_dir.is_dir():
            shutil.rmtree(env_dir, ignore_errors=True)
            removed += 1
            # If parent directory (name) is now empty, remove it as well.
            parent_dir = output_dir / name
            try:
                if parent_dir.exists() and parent_dir.is_dir() and not any(parent_dir.iterdir()):
                    shutil.rmtree(parent_dir, ignore_errors=True)
                    # Do not increment removed again — count represents removed version dirs.
            except Exception:
                # If listing or removal fails for any reason, ignore to avoid breaking sync.
                pass
    return removed


def collect_all_environments(
        direct_deps: List[str], dependencies_data: List[str]
) -> List[str]:
    """Collect all environments (direct + transitive) and deduplicate.

    Args:
        direct_deps: Direct dependencies from environment.json
        dependencies_data: Flat list of deps returned by backend (may include duplicates)

    Returns:
        List of unique environment specs (direct deps first)
    """
    # Ensure direct deps stay first, then append backend deps in their given order.
    return dedupe_keep_order(list(direct_deps) + list(dependencies_data))
