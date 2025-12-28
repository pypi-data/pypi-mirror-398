# Vuer Hub Environment Manager

Vuer HUB and the vuer command line tool enable you to manage, version-control,
and distribute physical simulation environments the same way you manage
software packages.

## Installation

```bash
pip install vuer-cli
```

## Environment Variables

| Variable          | Required | Description                                                              |
|-------------------|----------|--------------------------------------------------------------------------|
| `VUER_AUTH_TOKEN` | ✅        | JWT token used for all authenticated requests                            |
| `VUER_HUB_URL`    | ✅        | Base URL of the Vuer Hub API (required — no default; e.g. `https://hub.vuer.ai/api`) |

## Commands

| Command        | Description                                                           |
|----------------|-----------------------------------------------------------------------|
| `vuer`         | Show top-level help and list available commands                       |
| `vuer --help`  | Show detailed CLI help                                                 |
| `sync`         | Sync all environments from environment.json dependencies (like npm install) |
| `add`          | Add an environment dependency to environment.json                     |
| `remove`       | Remove an environment dependency from environment.json                |
| `upgrade`      | Upgrade an environment dependency in environment.json to latest       |
| `envs-publish` | Publish an environment version                                        |
| `envs-pull`    | Download an environment by ID or `name/version`                       |

## Usage

Quick start — configure environment variables

`VUER_HUB_URL` is required and has no default. Set it to the base URL of your Vuer Hub API.

```bash
export VUER_HUB_URL="https://hub.vuer.ai/api"
# Optional: token for private hubs or authenticated operations
export VUER_AUTH_TOKEN="eyJhbGci..."
# Optional: enable dry-run mode to simulate operations (no network changes)
export VUER_CLI_DRY_RUN="1"
```

```bash
# Sync all environments from environment.json dependencies
# Reads environment.json in current directory, validates dependencies,
# and downloads all environments (including transitive deps) to vuer_environments/
vuer sync
vuer sync --output ./my-envs

# Publish an environment (requires environment.json in the directory)
vuer envs-publish --directory ./my-environment

# Pull an environment (download and unpack into a directory)
vuer envs-pull <environmentId>
vuer envs-pull my-environment/1.0.0

# Add an environment
vuer add --env <environmentId>
```

### Sync Command Details

The `sync` command works like `npm install`:

1. Reads `environment.json` from the current directory
2. Parses the `dependencies` field (e.g., `{"some-dependency": "1.2.3"}`)
3. Validates all dependencies exist in the backend
4. Fetches transitive dependencies for each environment
5. Downloads all environments (direct + transitive) to `vuer_environments/` directory
6. Preserves `environment.json` inside downloaded environment directories

Publishing metadata (used by `envs-publish`)

```json
{
  "name": "my-environment",
  "version": "v1.0.0",
  "description": "Demo robotic arm env",
  "visibility": "PUBLIC",
  "env-type": "isaac",
  "dependencies": {
    "my-environment-1": "v4.0.0"
  }
}
```

Fields and recommendations for publishing metadata
- **name** (string, required): logical name of the environment (no slashes). This becomes the directory name under `vuer_environments/<name>/<version>/` when downloaded.
- **version** (string, required): environment version string. Use a stable, reproducible format (we recommend semantic style like `v1.0.0`).
- **description** (string, optional): short human-readable description of the environment.
- **visibility** (string, optional): publishing visibility, commonly `PUBLIC` or `PRIVATE`.
- **env-type** (string, optional): environment runtime/type identifier (for example `isaac`, `gazebo`, etc.).
- **dependencies** (object, optional): mapping of dependency-name → version (e.g. `"some-dependency": "v1.2.3"`). These declare upstream environment dependencies and are validated during publish.

Publishing notes
- `envs-publish` expects the target directory to contain a valid `environment.json`. At minimum `name` and `version` must be present; `envs-publish` will validate metadata before uploading to `VUER_HUB_URL`.
- The `environment.json` baked into an environment package is preserved when that package is later downloaded to `vuer_environments/<name>/<version>/`.
- Keep the publishing `environment.json` authoritative: use `dependencies` to declare exact `name → version` mappings for transitive resolution.

Project-level `environment.json` used by `vuer sync`

For projects that consume environments (i.e., run `vuer sync`), you usually keep a simple `environment.json` at the project root that focuses on the `dependencies` map:

```json
{
  "dependencies": {
    "some-dependency": "v1.2.3",
    "another-dependency": "v4.5.6"
  }
}
```

Note: The project-level `environment.json` used by `vuer sync` typically only needs a `dependencies` mapping. The publishing `environment.json` (shown above) must include `name` and `version`.

Use `vuer <command> --help` for full options.

### Add Command Details

- Purpose: add an environment dependency to the current directory's `environment.json`.
- Input: an environment identifier in canonical `name/version` form or a hub-specific environment ID (example: `my-environment/1.0.0`).
- Behavior: validates the environment exists on the configured `VUER_HUB_URL` and updates the `dependencies` section of `environment.json`. Run `vuer sync` afterwards to download the environment and its transitive dependencies into `vuer_environments/`.

### Remove Command Details

- Purpose: remove a specific environment dependency from the current directory's `environment.json`.
- Input: a canonical `name/version` spec (exact match required).
- Behavior: removes only the exact `name/version` entry from `environment.json`. If the corresponding version directory exists under `vuer_environments/<name>/<version>/`, the local copy will be removed; empty parent directories are cleaned up automatically.

### Upgrade Command Details

- Purpose: update an existing dependency in `environment.json` to a newer version.
- Input: a dependency name (to upgrade to the latest available) or an explicit `name/version` to target.
- Behavior: queries the configured hub for available versions, updates `environment.json` with the selected version, and leaves installation to `vuer sync`.

### envs-publish Command Details

- Purpose: publish a prepared environment directory to the configured hub.
- Input: a local directory containing an `environment.json` and environment content.
- Behavior: validates the local environment metadata, then uploads the environment as a new version to `VUER_HUB_URL`. Authenticated operations require `VUER_AUTH_TOKEN`.

### envs-pull Command Details

- Purpose: download an environment from the hub and place it into a local directory.
- Input: a hub environment ID or canonical `name/version` (e.g., `my-environment/1.0.0`).
- Behavior: downloads the environment and creates the nested path `vuer_environments/<name>/<version>/` (or an alternate `--output` path), preserving the bundled `environment.json` metadata.
