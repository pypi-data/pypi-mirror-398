"""Utility functions for jettex."""

import os
import platform
import subprocess
from pathlib import Path
from typing import Optional, List

# TinyTeX release URLs
TINYTEX_RELEASES_API = "https://api.github.com/repos/rstudio/tinytex-releases/releases/latest"
TINYTEX_RELEASES_BASE = "https://github.com/rstudio/tinytex-releases/releases/download"

# Cache the latest release version
_cached_release_version: str = ""


def get_platform() -> str:
    """Get the current platform identifier.

    Returns:
        str: 'windows', 'darwin', or 'linux'
    """
    system = platform.system().lower()
    if system == "darwin":
        return "darwin"
    elif system == "windows":
        return "windows"
    else:
        return "linux"


def get_arch() -> str:
    """Get the current CPU architecture.

    Returns:
        str: 'x86_64', 'aarch64', or 'i386'
    """
    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        return "x86_64"
    elif machine in ("arm64", "aarch64"):
        return "aarch64"
    elif machine in ("i386", "i686"):
        return "i386"
    return machine


def get_tinytex_bundle_name(version: int = 1) -> str:
    """Get the TinyTeX bundle name for download.

    Args:
        version: 0 (infraonly), 1 (default ~90 packages), 2 (extended)

    Returns:
        str: Bundle name like 'TinyTeX-1' or 'TinyTeX'
    """
    if version == 0:
        return "TinyTeX-0"
    elif version == 1:
        return "TinyTeX-1"
    elif version == 2:
        return "TinyTeX-2"
    else:
        return "TinyTeX"  # Default community version


def get_latest_release_version() -> str:
    """Get the latest TinyTeX release version from GitHub.

    Returns:
        str: Release version tag (e.g., 'v2025.12')
    """
    global _cached_release_version

    if _cached_release_version:
        return _cached_release_version

    try:
        import urllib.request
        import json

        with urllib.request.urlopen(TINYTEX_RELEASES_API, timeout=10) as response:
            data = json.loads(response.read().decode())
            _cached_release_version = data.get("tag_name", "v2025.12")
            return _cached_release_version
    except Exception:
        # Fallback to a known version
        return "v2025.12"


def get_download_url(version: int = 1, release_version: str = "") -> str:
    """Get the download URL for TinyTeX.

    Args:
        version: TinyTeX version (0, 1, or 2)
        release_version: Specific release version (e.g., 'v2025.12'), or empty for latest

    Returns:
        str: Full download URL
    """
    plat = get_platform()

    # Get release version
    if not release_version:
        release_version = get_latest_release_version()

    # Determine file extension by platform
    if plat == "windows":
        ext = "zip"
    elif plat == "darwin":
        ext = "tgz"
    else:
        ext = "tar.gz"

    # Build filename: TinyTeX-{0,1,or nothing}-{release_version}.{ext}
    if version == 0:
        filename = f"TinyTeX-0-{release_version}.{ext}"
    elif version == 1:
        filename = f"TinyTeX-1-{release_version}.{ext}"
    else:
        # Version 2 or default uses just "TinyTeX"
        filename = f"TinyTeX-{release_version}.{ext}"

    return f"{TINYTEX_RELEASES_BASE}/{release_version}/{filename}"


def get_default_install_dir() -> Path:
    """Get the default TinyTeX installation directory.

    Returns:
        Path: Default installation directory
    """
    plat = get_platform()

    if plat == "windows":
        # Use APPDATA on Windows
        appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
        return Path(appdata) / "TinyTeX"
    elif plat == "darwin":
        # Use ~/Library/TinyTeX on macOS
        return Path.home() / "Library" / "TinyTeX"
    else:
        # Use ~/.TinyTeX on Linux
        return Path.home() / ".TinyTeX"


def get_tinytex_root() -> Optional[Path]:
    """Get the TinyTeX root directory if installed.

    Checks environment variable TINYTEX_HOME first, then default location.

    Returns:
        Path or None: TinyTeX root directory if found
    """
    # Check environment variable first
    env_home = os.environ.get("TINYTEX_HOME")
    if env_home:
        path = Path(env_home)
        if path.exists():
            return path

    # Check default location
    default = get_default_install_dir()
    if default.exists():
        return default

    return None


def get_texmf_root() -> Optional[Path]:
    """Get the TeX Live texmf root directory.

    Returns:
        Path or None: texmf root directory if found
    """
    root = get_tinytex_root()
    if root is None:
        return None

    plat = get_platform()

    # TinyTeX structure varies by platform
    if plat == "darwin":
        # macOS: TinyTeX/.TinyTeX/texmf-dist or TinyTeX/texmf-dist
        candidates = [
            root / ".TinyTeX" / "texmf-dist",
            root / "texmf-dist",
        ]
    else:
        candidates = [
            root / "texmf-dist",
        ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return None


def get_bin_dir() -> Optional[Path]:
    """Get the TinyTeX bin directory containing executables.

    Returns:
        Path or None: bin directory if found
    """
    root = get_tinytex_root()
    if root is None:
        return None

    plat = get_platform()
    arch = get_arch()

    # Construct platform-specific bin path
    if plat == "windows":
        bin_subdir = "win32"
    elif plat == "darwin":
        if arch == "aarch64":
            bin_subdir = "universal-darwin"
        else:
            bin_subdir = "universal-darwin"
    else:
        if arch == "aarch64":
            bin_subdir = "aarch64-linux"
        else:
            bin_subdir = "x86_64-linux"

    # Check various possible structures
    candidates = [
        root / "bin" / bin_subdir,
        root / ".TinyTeX" / "bin" / bin_subdir,
        root / "bin" / "windows",
        root / ".TinyTeX" / "bin" / "windows",
        root / "bin",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return None


def get_executable(name: str) -> Optional[Path]:
    """Get the path to a TinyTeX executable.

    Args:
        name: Executable name (e.g., 'pdflatex', 'tlmgr')

    Returns:
        Path or None: Full path to executable if found
    """
    bin_dir = get_bin_dir()
    if bin_dir is None:
        return None

    plat = get_platform()

    if plat == "windows":
        # TeX Live on Windows ships tools as .exe or .bat (tlmgr is often .bat).
        for suffix in (".exe", ".bat", ".cmd", ".ps1"):
            exe = bin_dir / f"{name}{suffix}"
            if exe.exists():
                return exe
    else:
        exe = bin_dir / name
        if exe.exists():
            return exe

    return None


def run_command(
    cmd: List[str],
    cwd: Optional[Path] = None,
    capture_output: bool = True,
    check: bool = False,
    timeout: Optional[int] = None,
) -> subprocess.CompletedProcess:
    """Run a command and return the result.

    Args:
        cmd: Command and arguments as list
        cwd: Working directory
        capture_output: Capture stdout/stderr
        check: Raise exception on non-zero exit
        timeout: Command timeout in seconds

    Returns:
        CompletedProcess: Result of the command
    """
    kwargs = {
        "cwd": cwd,
        "capture_output": capture_output,
        "text": True,
    }

    if timeout:
        kwargs["timeout"] = timeout

    result = subprocess.run(cmd, **kwargs)

    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, cmd, result.stdout, result.stderr
        )

    return result


def is_tinytex_installed() -> bool:
    """Check if TinyTeX is installed.

    Returns:
        bool: True if TinyTeX is installed and usable
    """
    bin_dir = get_bin_dir()
    if bin_dir is None:
        return False

    # Check for tlmgr which should always exist
    tlmgr = get_executable("tlmgr")
    return tlmgr is not None and tlmgr.exists()


def add_to_path(directory: Path) -> None:
    """Add a directory to the current process PATH.

    Args:
        directory: Directory to add to PATH
    """
    current_path = os.environ.get("PATH", "")
    dir_str = str(directory)

    if dir_str not in current_path:
        os.environ["PATH"] = f"{dir_str}{os.pathsep}{current_path}"


def ensure_tinytex_in_path() -> bool:
    """Ensure TinyTeX bin directory is in PATH.

    Returns:
        bool: True if TinyTeX is available in PATH
    """
    bin_dir = get_bin_dir()
    if bin_dir is None:
        return False

    add_to_path(bin_dir)
    return True
