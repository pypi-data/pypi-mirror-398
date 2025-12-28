"""Add command - add an environment spec to environment.json then sync."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import json

from .sync import Sync, read_environments_lock
from .utils import print_error, parse_env_spec, normalize_env_spec


# Use shared parser from utils; legacy '@' syntax is not supported anymore.


@dataclass
class Add:
    """Add an environment to environment.json and run `vuer sync`.

    Example:
        vuer add some-environment/v1.2.3
    """

    # NOTE: We keep these fields for params-proto compatibility, but the primary
    # way to call this command is positional: `vuer add name@version`.
    env: str = ""  # Environment spec to add, e.g. "some-environment/v1.2.3"
    name: Optional[str] = None  # Unused in current workflow
    version: str = "latest"  # Unused in current workflow

    def __call__(self) -> int:
        """Execute add command."""
        try:
            env_spec = self.env
            if not env_spec:
                # If env is empty, params-proto likely didn't map the positional arg;
                # treat this as a usage error.
                raise ValueError(
                    "Missing environment spec. Usage: vuer add some-environment/v1.2.3"
                )

            name, version = parse_env_spec(env_spec)
            env_spec_normalized = normalize_env_spec(f"{name}/{version}")

            cwd = Path.cwd()
            lock_path = cwd / "environments-lock.yaml"

            # Step 2: Check if already present in environments-lock.yaml
            if lock_path.exists():
                existing_deps = read_environments_lock(lock_path)
                if env_spec_normalized in existing_deps:
                    print(f"[INFO] Environment {env_spec_normalized} already present in {lock_path}")
                    return 0

            # Step 3: Ensure environment.json has this dependency, then run sync
            env_json_path = cwd / "environment.json"
            if env_json_path.exists():
                with env_json_path.open("r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError as e:
                        raise ValueError(
                            f"Invalid environment.json: {e}"
                        ) from e
            else:
                data = {}

            deps = data.get("dependencies")
            if deps is None:
                deps = {}
            if not isinstance(deps, dict):
                raise ValueError(
                    "environment.json 'dependencies' field must be an object"
                )

            # Add or update the dependency
            deps[name] = version
            data["dependencies"] = deps

            with env_json_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")

            print(
                f"[INFO] Added {env_spec_normalized} to environment.json dependencies. Running sync..."
            )
            return Sync()()

        except (FileNotFoundError, ValueError, RuntimeError) as e:
            print_error(str(e))
            return 1
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            return 1
