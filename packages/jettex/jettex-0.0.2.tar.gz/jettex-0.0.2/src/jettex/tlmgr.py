"""TeX Live Manager (tlmgr) wrapper."""

import re
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any

from .utils import get_executable, run_command, ensure_tinytex_in_path


def _get_tlmgr() -> Path:
    """Get tlmgr executable path.

    Returns:
        Path: Path to tlmgr

    Raises:
        RuntimeError: If tlmgr is not found
    """
    ensure_tinytex_in_path()
    tlmgr = get_executable("tlmgr")
    if tlmgr is None:
        raise RuntimeError(
            "tlmgr not found. Is TinyTeX installed? Run install_tinytex() first."
        )
    return tlmgr


def _run_tlmgr(args: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run tlmgr with arguments.

    Args:
        args: Arguments to pass to tlmgr
        check: Raise exception on non-zero exit

    Returns:
        CompletedProcess: Result
    """
    tlmgr = _get_tlmgr()
    cmd = [str(tlmgr)] + args
    return run_command(cmd, check=check)


def tlmgr_install(packages: List[str]) -> bool:
    """Install LaTeX packages.

    Args:
        packages: List of package names to install

    Returns:
        bool: True if installation succeeded

    Example:
        >>> tlmgr_install(['amsmath', 'geometry'])
    """
    if not packages:
        return True

    result = _run_tlmgr(["install"] + packages, check=False)
    return result.returncode == 0


def tlmgr_remove(packages: List[str]) -> bool:
    """Remove LaTeX packages.

    Args:
        packages: List of package names to remove

    Returns:
        bool: True if removal succeeded
    """
    if not packages:
        return True

    result = _run_tlmgr(["remove"] + packages, check=False)
    return result.returncode == 0


def tlmgr_update(
    packages: Optional[List[str]] = None,
    all_packages: bool = False,
    self_update: bool = False,
) -> bool:
    """Update LaTeX packages or tlmgr itself.

    Args:
        packages: Specific packages to update (optional)
        all_packages: Update all installed packages
        self_update: Update tlmgr itself

    Returns:
        bool: True if update succeeded
    """
    args = ["update"]

    if self_update:
        args.append("--self")

    if all_packages:
        args.append("--all")
    elif packages:
        args.extend(packages)
    else:
        # Nothing to update
        return True

    result = _run_tlmgr(args, check=False)
    return result.returncode == 0


def tlmgr_list(only_installed: bool = True) -> List[str]:
    """List packages.

    Args:
        only_installed: Only list installed packages

    Returns:
        List[str]: Package names
    """
    args = ["list"]
    if only_installed:
        args.append("--only-installed")

    result = _run_tlmgr(args, check=False)
    if result.returncode != 0:
        return []

    packages = []
    for line in result.stdout.splitlines():
        # Parse tlmgr list output: "i packagename: description"
        match = re.match(r"^i\s+(\S+):", line)
        if match:
            packages.append(match.group(1))

    return packages


def tlmgr_search(
    query: str,
    file_search: bool = False,
    global_search: bool = True,
) -> List[Dict[str, str]]:
    """Search for packages.

    Args:
        query: Search query (package name or filename)
        file_search: Search by filename instead of package name
        global_search: Search all available packages, not just installed

    Returns:
        List of dicts with 'package' and optionally 'file' keys
    """
    args = ["search"]

    if global_search:
        args.append("--global")

    if file_search:
        args.append("--file")

    args.append(query)

    result = _run_tlmgr(args, check=False)
    if result.returncode != 0:
        return []

    results = []
    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # Ignore tlmgr info messages (e.g. "tlmgr: package repository...")
        if line.startswith("tlmgr:"):
            continue

        if file_search:
            # Format: "package:\n    path/to/file"
            # or "package: path/to/file"
            
            # Check for indentation in raw line indicating a file path
            if (raw_line.startswith(" ") or raw_line.startswith("\t")) and results:
                results[-1]["file"] = line
            elif ":" in line:
                # Format: "package: file" or just "package:"
                parts = line.split(":", 1)
                package = parts[0].strip()
                
                # Sanity check: package names generally don't have backslashes/slashes
                if "\\" in package or "/" in package:
                    continue
                
                # Heuristic: tlmgr output "package: file" always has a space after colon.
                # If there's no space and the suffix is non-empty, it's likely a path (C:\...) or URL (http://...)
                # split(":", 1) preserves leading whitespace in the second part.
                if len(parts) > 1:
                    suffix = parts[1]
                    if suffix and not suffix[0].isspace():
                        continue

                entry = {"package": package}
                
                if file_search and len(parts) > 1:
                    rest = parts[1].strip()
                    if rest:
                        entry["file"] = rest
                
                results.append(entry)
        else:
            # Package search format varies
            match = re.match(r"^(\S+)\s*[-:]", line)
            if match:
                results.append({"package": match.group(1)})

    return results


def tlmgr_info(package: str) -> Optional[Dict[str, Any]]:
    """Get information about a package.

    Args:
        package: Package name

    Returns:
        Dict with package info or None if not found
    """
    result = _run_tlmgr(["info", package], check=False)
    if result.returncode != 0:
        return None

    info = {"name": package}

    for line in result.stdout.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip().lower().replace(" ", "_")
            value = value.strip()
            if key and value:
                info[key] = value

    return info


def tlmgr_path(action: str = "add") -> bool:
    """Manage TinyTeX in system PATH.

    Args:
        action: 'add' or 'remove'

    Returns:
        bool: True if successful
    """
    if action not in ("add", "remove"):
        raise ValueError("action must be 'add' or 'remove'")

    result = _run_tlmgr(["path", action], check=False)
    return result.returncode == 0


def tlmgr_version() -> Optional[str]:
    """Get tlmgr/TeX Live version.

    Returns:
        str or None: Version string
    """
    result = _run_tlmgr(["--version"], check=False)
    if result.returncode != 0:
        return None

    # Parse version from output
    for line in result.stdout.splitlines():
        if "version" in line.lower():
            return line.strip()

    return result.stdout.strip().split("\n")[0] if result.stdout else None


def find_package_for_file(filename: str) -> Optional[str]:
    """Find which package provides a file.

    This is the key function for auto-installing missing packages.

    Args:
        filename: File to search for (e.g., 'geometry.sty')

    Returns:
        str or None: Package name that provides the file
    """
    results = tlmgr_search(filename, file_search=True, global_search=True)

    if results:
        # Prioritize exact file matches
        # tlmgr search --file returns partial matches too (e.g. lwarp-manyfoot.sty for manyfoot.sty)
        for res in results:
            file_path = res.get("file")
            if file_path and Path(file_path).name == filename:
                return res.get("package")

        # Prioritize package name matching the filename stem
        stem = Path(filename).stem
        for res in results:
            pkg = res.get("package")
            if pkg == stem:
                return pkg

        package = results[0].get("package")
        if package and package == filename:
            # Sometimes tlmgr returns the filename as the package name
            # e.g. "acmart.sty" -> "acmart.sty"
            # We want to install "acmart"
            return Path(filename).stem
        return package

    return None
