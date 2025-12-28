"""Vuer CLI - Environment Manager for Vuer Hub."""

import sys
from typing import Dict, Iterable, List

from params_proto import proto

from .add import Add
from .envs_publish import EnvsPublish
from .envs_pull import EnvsPull
from .remove import Remove
from .sync import Sync
from .upgrade import Upgrade


def _normalize_subcommand_args() -> None:
    """Allow users to omit the `--command.` prefix for subcommand options."""
    argv = sys.argv
    if len(argv) < 2:
        return

    cmd = argv[1]
    cmd_option_map: Dict[str, Iterable[str]] = {
        "sync": {"output", "timeout"},
        "add": {"env", "name", "version"},
        "remove": {"env"},
        "upgrade": {"env", "version"},
        "envs-publish": {"directory", "timeout", "tag", "dry-run"},
        "envs-pull": {"flag", "output", "filename", "version", "timeout",
                      "skip-progress"},
    }
    options = cmd_option_map.get(cmd)
    if not options:
        return

    new_argv: List[str] = [argv[0], argv[1]]

    # Special handling for positional env spec for `add`, `remove`, and `upgrade`:
    #   vuer add some-env@v1.2.3
    #   vuer remove some-env@v1.2.3
    #   vuer upgrade some-environment-name
    # Convert the first non-flag token after the subcommand into:
    #   --command.env <value>
    i = 2
    if cmd in {"add", "remove", "upgrade"} and len(argv) > 2:
        first = argv[2]
        if not first.startswith("-"):
            new_argv.append("--command.env")
            new_argv.append(first)
            i = 3

    while i < len(argv):
        token = argv[i]
        if token.startswith("--") and not token.startswith("--command."):
            if "=" in token:
                name_part, value_part = token[2:].split("=", 1)
                flag_name = name_part
                remainder = "=" + value_part
            else:
                flag_name = token[2:]
                remainder = ""

            if flag_name in options:
                new_argv.append(f"--command.{flag_name}{remainder}")
            else:
                new_argv.append(token)
        else:
            new_argv.append(token)
        i += 1

    sys.argv = new_argv


def entrypoint() -> int:
    """Console script entry point (wrapper)."""
    _normalize_subcommand_args()
    return _cli_entrypoint() or 0


@proto.cli(prog="vuer")
def _cli_entrypoint(
    command: Sync | Add | Remove | Upgrade | EnvsPublish | EnvsPull,
):
    """Vuer Hub Environment Manager.

    Available commands:
      sync          - Sync environments from environment.json dependencies (like npm install)
      add           - Add an environment to environment.json and run sync
      remove        - Remove an environment from environment.json and run sync
      upgrade       - Upgrade an environment to the latest version
      envs-publish  - Publish an environment to the Vuer Hub
      envs-pull     - Pull/download an environment from the Vuer Hub
    
    Examples:
      vuer sync                    Sync all dependencies from environment.json
      vuer add my-env/1.2.3        Add an environment and sync
      vuer remove my-env/1.2.3     Remove an environment and sync
      vuer upgrade my-env          Upgrade an environment to latest version
      vuer envs-publish            Publish current environment to hub
      vuer envs-pull my-env/1.2.3  Pull an environment from hub
    
    Environment variables:
      VUER_HUB_URL     - Base URL of the Vuer Hub API
      VUER_AUTH_TOKEN  - JWT token for API authentication
    """
    return command()
