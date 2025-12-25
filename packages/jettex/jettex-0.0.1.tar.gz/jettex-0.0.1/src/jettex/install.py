"""TinyTeX installation and management."""

import shutil
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Callable

import requests

from .utils import (
    get_default_install_dir,
    get_download_url,
    get_tinytex_root,
    is_tinytex_installed,
    get_bin_dir,
    add_to_path,
)


def download_file(
    url: str,
    dest: Path,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> None:
    """Download a file from URL to destination.

    Args:
        url: URL to download from
        dest: Destination file path
        progress_callback: Optional callback(downloaded_bytes, total_bytes)
    """
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))
    downloaded = 0

    with open(dest, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if progress_callback:
                    progress_callback(downloaded, total_size)


def extract_archive(archive_path: Path, dest_dir: Path) -> None:
    """Extract a tar.gz, tgz, or zip archive.

    Args:
        archive_path: Path to archive file
        dest_dir: Destination directory
    """
    archive_str = str(archive_path).lower()

    if archive_str.endswith(".zip"):
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(dest_dir)
    elif archive_str.endswith((".tar.gz", ".tgz")):
        with tarfile.open(archive_path, "r:gz") as tf:
            tf.extractall(dest_dir)
    elif archive_str.endswith(".tar"):
        with tarfile.open(archive_path, "r:") as tf:
            tf.extractall(dest_dir)
    else:
        raise ValueError(f"Unsupported archive format: {archive_path}")


def install_tinytex(
    version: int = 1,
    install_dir: Optional[Path] = None,
    force: bool = False,
    add_path: bool = True,
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
) -> Path:
    """Download and install TinyTeX.

    Args:
        version: TinyTeX version to install
            - 0: infraonly (minimal, no packages)
            - 1: default (~90 packages for common documents)
            - 2: extended (more packages)
        install_dir: Custom installation directory (default: platform-specific)
        force: Force reinstall even if already installed
        add_path: Add TinyTeX bin to PATH
        progress_callback: Optional callback(stage, downloaded, total)

    Returns:
        Path: Installation directory

    Raises:
        RuntimeError: If installation fails
    """
    if install_dir is None:
        install_dir = get_default_install_dir()
    else:
        install_dir = Path(install_dir)

    # Check if already installed
    if not force and is_tinytex_installed():
        existing = get_tinytex_root()
        if existing:
            if add_path:
                bin_dir = get_bin_dir()
                if bin_dir:
                    add_to_path(bin_dir)
            return existing

    # Remove existing installation if force
    if force and install_dir.exists():
        shutil.rmtree(install_dir)

    # Create installation directory
    install_dir.mkdir(parents=True, exist_ok=True)

    # Get download URL
    url = get_download_url(version)

    # Determine archive filename
    archive_name = url.split("/")[-1]

    # Download to temp file
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        archive_path = tmpdir_path / archive_name

        # Download
        def download_progress(downloaded: int, total: int) -> None:
            if progress_callback:
                progress_callback("downloading", downloaded, total)

        try:
            download_file(url, archive_path, download_progress)
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to download TinyTeX: {e}") from e

        # Extract
        if progress_callback:
            progress_callback("extracting", 0, 0)

        try:
            extract_archive(archive_path, tmpdir_path)
        except Exception as e:
            raise RuntimeError(f"Failed to extract TinyTeX: {e}") from e

        # Find extracted directory (usually named TinyTeX or .TinyTeX)
        extracted_dirs = [
            d for d in tmpdir_path.iterdir()
            if d.is_dir() and d.name != "__MACOSX"
        ]

        if not extracted_dirs:
            raise RuntimeError("No directory found in extracted archive")

        extracted_dir = extracted_dirs[0]

        # Move to installation directory
        if progress_callback:
            progress_callback("installing", 0, 0)

        # If the install_dir is the target, move contents into it
        for item in extracted_dir.iterdir():
            dest = install_dir / item.name
            if dest.exists():
                if dest.is_dir():
                    shutil.rmtree(dest)
                else:
                    dest.unlink()
            shutil.move(str(item), str(dest))

    # Add to PATH if requested
    if add_path:
        bin_dir = get_bin_dir()
        if bin_dir:
            add_to_path(bin_dir)

    if progress_callback:
        progress_callback("complete", 100, 100)

    return install_dir


def uninstall_tinytex(install_dir: Optional[Path] = None) -> bool:
    """Uninstall TinyTeX.

    Args:
        install_dir: Installation directory to remove (default: detect automatically)

    Returns:
        bool: True if uninstalled successfully
    """
    if install_dir is None:
        install_dir = get_tinytex_root()

    if install_dir is None or not install_dir.exists():
        return False

    try:
        shutil.rmtree(install_dir)
        return True
    except Exception:
        return False


def tinytex_root() -> Optional[Path]:
    """Get the TinyTeX installation root directory.

    Returns:
        Path or None: Installation directory if found
    """
    return get_tinytex_root()


def tinytex_version() -> Optional[str]:
    """Get the installed TinyTeX/TeX Live version.

    Returns:
        str or None: Version string if available
    """
    from .tlmgr import tlmgr_version
    return tlmgr_version()
