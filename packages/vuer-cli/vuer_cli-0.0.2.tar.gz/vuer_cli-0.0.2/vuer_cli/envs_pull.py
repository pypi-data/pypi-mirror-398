"""EnvsPull command - download an environment by ID."""

import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional

from tqdm import tqdm

from .envs_publish import Hub
from .utils import is_dry_run, print_error, parse_env_spec


# -- Subcommand dataclass --

@dataclass
class EnvsPull:
    """Download an environment from the registry by ID or name/version."""

    flag: str = ""  # Environment identifier (ID or name/version) to download
    output: str = "downloads"  # Destination directory
    filename: Optional[str] = None  # Override saved filename
    version: Optional[str] = None  # Specific version to download
    timeout: int = 300  # Request timeout in seconds
    skip_progress: bool = False  # Disable progress bar

    def __call__(self) -> int:
        """Execute envs-pull command."""
        try:
            if not is_dry_run():
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

            print(f"[INFO] Pulling environment {self.flag} ...")
            pull_from_registry(
                env_flag=self.flag,
                output_dir=self.output,
                filename=self.filename,
                version=self.version,
                timeout=self.timeout,
                skip_progress=self.skip_progress,
            )
            return 0
        except Exception as e:
            print_error(str(e))
            return 1


# -- Helper functions --

def download_with_progress(
    destination: Path,
    total_size: int,
    stream: Iterable[bytes],
    skip_progress: bool,
) -> None:
    """Write streamed bytes to destination with an optional progress bar."""
    destination.parent.mkdir(parents=True, exist_ok=True)

    if skip_progress:
        with destination.open("wb") as f:
            for chunk in stream:
                f.write(chunk)
        return

    with destination.open("wb") as f, tqdm(
        total=total_size or None,
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
        desc=f"Downloading {destination.name}",
        ncols=100,
    ) as pbar:
        for chunk in stream:
            f.write(chunk)
            pbar.update(len(chunk))


def extract_filename_from_headers(headers: Dict[str, str], default_name: str) -> str:
    """Extract filename from Content-Disposition header (RFC 5987 style)."""
    content_disposition = headers.get("Content-Disposition", "")
    if not content_disposition:
        return default_name

    if "filename*=" in content_disposition:
        part = content_disposition.split("filename*=")[-1].strip()
        if part.lower().startswith("utf-8''"):
            encoded = part[7:]
        else:
            encoded = part
        encoded = encoded.split(";")[0].strip().strip('"')
        try:
            from urllib.parse import unquote
            candidate = unquote(encoded)
            if candidate:
                return candidate
        except Exception:
            pass

    if "filename=" in content_disposition:
        candidate = content_disposition.split("filename=")[-1].strip().strip('"')
        candidate = candidate.split(";")[0].strip()
        if candidate:
            return candidate

    return default_name


def pull_from_registry(
    env_flag: str,
    output_dir: str,
    filename: Optional[str],
    version: Optional[str],
    timeout: int,
    skip_progress: bool,
) -> Path:
    """Download environment by ID or name/version and extract archive into a directory."""
    hub_url = Hub.url
    auth_token = Hub.auth_token
    headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}

    # New API: /api/environments/download?environment_id=<id or name@version>
    from urllib.parse import urlencode

    base_url = f"{hub_url.rstrip('/')}/environments/download"
    query = urlencode({"environment_id": env_flag})
    url = f"{base_url}?{query}"

    output_dir_path = Path(output_dir).expanduser().resolve()
    output_dir_path.mkdir(parents=True, exist_ok=True)

    if is_dry_run():
        # If env_flag is a name/version, create nested dirs name/version
        try:
            name, version = parse_env_spec(env_flag)
            env_dir = output_dir_path / name / version
        except Exception:
            env_dir = output_dir_path / str(env_flag)
        env_dir.mkdir(parents=True, exist_ok=True)
        (env_dir / "README.txt").write_text("Dry-run environment content\n")
        print(f"[SUCCESS] (dry-run) Downloaded to {env_dir}")
        return env_dir

    # Lazy import requests to avoid SSL/cert issues in dry-run/tests.
    import requests

    with requests.get(url, headers=headers, stream=True, timeout=timeout) as resp:
        resp.raise_for_status()
        total_size = int(resp.headers.get("Content-Length", 0))
        # Use filesystem-safe archive name when env_flag contains '/'
        # When env_flag is name/version, use name-version for filename
        try:
            name, version = parse_env_spec(env_flag)
            safe_name = f"{name}-{version}"
        except Exception:
            safe_name = str(env_flag)
        default_archive_name = f"{safe_name}.tgz"
        archive_name = filename or extract_filename_from_headers(resp.headers, default_archive_name)
        archive_path = output_dir_path / archive_name

        stream = (chunk for chunk in resp.iter_content(chunk_size=1024 * 512) if chunk)
        download_with_progress(archive_path, total_size, stream, skip_progress)

    # Derive target directory name from archive filename
    suffixes = "".join(archive_path.suffixes)
    if suffixes.endswith(".tar.gz"):
        base_name = archive_path.name[: -len(".tar.gz")]
    elif suffixes.endswith(".tgz"):
        base_name = archive_path.name[: -len(".tgz")]
    elif suffixes.endswith(".tar"):
        base_name = archive_path.name[: -len(".tar")]
    else:
        base_name = archive_path.stem

    # Prefer nested directory when env_flag is parseable
    try:
        name, version = parse_env_spec(env_flag)
        env_dir = output_dir_path / name / version
    except Exception:
        env_dir = output_dir_path / base_name
    env_dir.mkdir(parents=True, exist_ok=True)

    try:
        if tarfile.is_tarfile(archive_path):
            with tarfile.open(archive_path, "r:*") as tar:
                tar.extractall(env_dir)
            archive_path.unlink(missing_ok=True)
            print(f"[SUCCESS] Downloaded and extracted to {env_dir}")
        else:
            print(f"[WARN] Downloaded file is not a tar archive, kept as {archive_path}")
            env_dir = archive_path
    except Exception as e:
        print_error(f"Failed to extract archive: {e}")
        env_dir = archive_path

    return env_dir


