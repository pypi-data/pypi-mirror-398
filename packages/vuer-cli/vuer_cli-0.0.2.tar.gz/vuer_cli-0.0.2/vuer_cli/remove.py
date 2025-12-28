"""Remove command - remove an environment spec from environment.json then sync."""

from dataclasses import dataclass
from pathlib import Path
# typing imports not required

import json

from .sync import Sync, read_environments_lock
from .utils import print_error, parse_env_spec, normalize_env_spec


# Use shared parser from utils; legacy '@' syntax is not supported.


@dataclass
class Remove:
    """Remove an environment from environment.json and run `vuer sync`.

    Example:
        vuer remove some-environment/v1.2.3
    """

    # Primary usage is positional: `vuer remove name/version`.
    env: str = ""  # Environment spec to remove, e.g. "some-environment/v1.2.3"

    def __call__(self) -> int:
        """Execute remove command."""
        try:
            env_spec = self.env
            if not env_spec:
                raise ValueError(
                    "Missing environment spec. Usage: vuer remove some-environment/v1.2.3"
                )

            name, version = parse_env_spec(env_spec)
            env_spec_normalized = normalize_env_spec(f"{name}/{version}")

            cwd = Path.cwd()
            module_dir = cwd / "vuer_environments"
            lock_path = cwd / "environments-lock.yaml"

            # Step 2: Ensure vuer_environments/dependencies.toml exists
            if not module_dir.exists() or not lock_path.exists():
                raise FileNotFoundError(
                    "vuer_environments directory or environments-lock.yaml not found. "
                    "Please run `vuer sync` first to generate environments-lock.yaml."
                )
            existing_deps = read_environments_lock(lock_path)
            if env_spec_normalized not in existing_deps:
                print(f"[INFO] Environment {env_spec_normalized} is not present in {lock_path}")
                return 0

            # Step 3: Remove from environment.json dependencies, then run sync
            env_json_path = cwd / "environment.json"
            if not env_json_path.exists():
                raise FileNotFoundError(
                    "environment.json not found. Cannot remove dependency."
                )

            with env_json_path.open("r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as e:
                    raise ValueError(
                        f"Invalid environment.json: {e}"
                    ) from e

            deps = data.get("dependencies")
            if deps is None:
                deps = {}
            if not isinstance(deps, dict):
                raise ValueError(
                    "environment.json 'dependencies' field must be an object"
                )

            # Remove the dependency if present and version matches exactly.
            current_version = deps.get(name)
            if current_version is None:
                print(f"[INFO] Dependency {env_spec_normalized} not found in environment.json. Skipping removal.")
            else:
                # Only remove if the version in environment.json matches the requested version.
                if current_version != version:
                    print(
                        f"[INFO] Skipping removal: environment '{name}' is pinned to version "
                        f"'{current_version}' in environment.json (requested '{version}')."
                    )
                else:
                    deps.pop(name, None)
                    print(f"[INFO] Removed {env_spec_normalized} from environment.json dependencies.")

            data["dependencies"] = deps
            with env_json_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")

            print("[INFO] Running sync to reconcile vuer_environments/ with updated dependencies...")
            return Sync()()

        except (FileNotFoundError, ValueError, RuntimeError) as e:
            print_error(str(e))
            return 1
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            return 1
