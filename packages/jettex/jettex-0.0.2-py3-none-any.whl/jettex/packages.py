"""Automatic package detection and installation.

This module provides the key feature for R-tinytex parity: automatically
detecting missing LaTeX packages from compilation errors and installing them.
"""

import re
from pathlib import Path
from typing import List, Set, Optional, Union
from dataclasses import dataclass

from .compile import CompileResult, pdflatex, xelatex, lualatex, latexmk
from .tlmgr import tlmgr_install, find_package_for_file, tlmgr_list
from .console import get_logger, is_quiet


@dataclass
class PackageInfo:
    """Information about a missing package."""

    filename: str
    """The missing file (e.g., 'geometry.sty')."""

    package: Optional[str]
    """The package that provides this file, if found."""

    error_message: str
    """The original error message."""


# Regex patterns for detecting missing packages in LaTeX log files
MISSING_FILE_PATTERNS = [
    # ! LaTeX Error: File `xxx.sty' not found.
    r"! LaTeX Error: File [`']([^'`]+)[`'] not found",
    # ! LaTeX Error: File `xxx.cls' not found.
    r"LaTeX Error: File [`']([^'`]+\.cls)[`'] not found",
    # Package xxx Error: File `yyy.sty' not found
    r"Package \w+ Error:.*File [`']([^'`]+)[`'] not found",
    # ! I can't find file `xxx'.
    r"! I can't find file [`']([^'`]+)[`']",
    # kpathsea: Running mktextfm xxx.tfm
    # followed by failure indicates missing font
    r"mktex(?:tfm|pk|mf)\s+([^\s]+)\s*$",
    # ! Font \xxx=xxx not loadable
    r"! Font [^=]+=([^\s]+) (?:at \d+(?:\.\d+)?pt )?not loadable",
    # ! Package fontspec Error: The font "xxx" cannot be found.
    r'! Package fontspec Error: The font "([^"]+)" cannot be found',
    # Missing character: There is no xxx in font yyy!
    r"Missing character:.*in font ([^\s!]+)",
]

# Patterns for missing package declarations (not files)
MISSING_PACKAGE_PATTERNS = [
    # ! Package xxx Error: xxx requires yyy
    r"! Package (\w+) Error:.*requires\s+(\w+)",
    # ! Undefined control sequence ... \xxx
    r"Undefined control sequence.*\\(\w+)",
]

# Regex for parsing package usage in source code
# \usepackage{pkg}, \usepackage[opt]{pkg}, \RequirePackage{pkg}, \documentclass{class}
# Regex for parsing package usage in source code
# \usepackage{pkg}, \usepackage[opt]{pkg}, \RequirePackage{pkg}, \documentclass{class}
# Matches: (options, packages)
PACKAGE_USAGE_PATTERN = r"\\(?:usepackage|RequirePackage|documentclass)(?:\[([^\]]*)\])?\{([^}]+)\}"


def parse_log_for_missing_files(log_content: str) -> List[str]:
    """Parse LaTeX log content for missing files.

    Args:
        log_content: Content of the .log file

    Returns:
        List of missing filenames
    """
    missing_files: Set[str] = set()

    for pattern in MISSING_FILE_PATTERNS:
        matches = re.findall(pattern, log_content, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            if match:
                # Clean up the filename
                filename = match.strip()
                if filename:
                    missing_files.add(filename)

    return list(missing_files)


def parse_log_file(log_path: Union[str, Path]) -> List[str]:
    """Parse a LaTeX log file for missing files.

    Args:
        log_path: Path to .log file

    Returns:
        List of missing filenames
    """
    log_path = Path(log_path)
    if not log_path.exists():
        return []

    try:
        content = log_path.read_text(encoding="utf-8", errors="replace")
        return parse_log_for_missing_files(content)
    except Exception:
        return []


def find_packages_for_files(filenames: List[str]) -> List[PackageInfo]:
    """Find packages that provide the given files.

    Args:
        filenames: List of missing filenames

    Returns:
        List of PackageInfo with package information
    """
    results = []

    for filename in filenames:
        package = find_package_for_file(filename)
        results.append(
            PackageInfo(
                filename=filename,
                package=package,
                error_message=f"File '{filename}' not found",
            )
        )

    return results


def install_missing_packages(missing: List[PackageInfo]) -> List[str]:
    """Install packages for missing files.

    Args:
        missing: List of PackageInfo from find_packages_for_files

    Returns:
        List of successfully installed package names
    """
    # Collect unique packages to install
    packages_to_install = set()
    for info in missing:
        if info.package:
            packages_to_install.add(info.package)

    if not packages_to_install:
        return []

    # Install all packages at once
    packages_list = list(packages_to_install)
    success = tlmgr_install(packages_list)

    if success:
        return packages_list
    return []


def scan_tex_for_packages(content: str, base_path: Optional[Path] = None) -> List[str]:
    """Scan LaTeX content for package usage, including inputs.
    
    Args:
        content: LaTeX source content
        base_path: Base path to resolve relative inputs (optional)
        
    Returns:
        List of package names found
    """
    packages = set()
    matches = re.findall(PACKAGE_USAGE_PATTERN, content)
    
    for options, package_str in matches:
        # Handle comma-separated list: \usepackage{pkg1,pkg2}
        names = [n.strip() for n in package_str.split(",")]
        for name in names:
            if name:
                packages.add(name)
                
                # Special handling for babel: \usepackage[english]{babel} -> install babel-english
                if name == "babel" and options:
                    langs = [opt.strip() for opt in options.split(",")]
                    # Common babel options that are not languages (ignore them)
                    # This list is not exhaustive but catches common ones.
                    # We optimistically try to install babel-<opt> for everything else.
                    # tlmgr will just fail/ignore if it doesn't exist, checking locally first is expensive.
                    # But we can perhaps filter a bit? 
                    # Actually, better to just check if 'babel-<lang>' is installable? 
                    # For now, simplistic approach:
                    for lang in langs:
                        if lang and not lang.startswith("scale="): # Ignore options like scale=0.9
                            # Map special cases if needed, e.g. "utf8" -> texlive does not have babel-utf8
                            # Usually languages are just "english", "french", etc.
                            packages.add(f"babel-{lang}")

    # Recursively check inputs: \input{file}, \include{file}
    if base_path:
        # Match \input{filename} or \include{filename}
        input_matches = re.findall(r"\\(?:input|include)\{([^}]+)\}", content)
        for input_rel_path in input_matches:
            # Handle typical latex cases: no extension implies .tex
            if not input_rel_path.endswith(".tex"):
                input_candidates = [input_rel_path + ".tex", input_rel_path]
            else:
                input_candidates = [input_rel_path]
                
            for cand in input_candidates:
                full_path = base_path / cand
                if full_path.exists():
                    try:
                        sub_content = full_path.read_text(encoding="utf-8", errors="replace")
                        packages.update(scan_tex_for_packages(sub_content, base_path=full_path.parent))
                    except Exception:
                        pass
                    break # Stop if we found the file
                
    return list(packages)


def install_packages_from_source(
    file_path: Union[str, Path], 
    quiet: bool = False
) -> List[str]:
    """Scan file for required packages and install them if missing.
    
    Args:
        file_path: Path to .tex file
        quiet: Suppress output
        
    Returns:
        List of installed packages
    """
    path = Path(file_path)
    if not path.exists():
        return []
        
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []
        
    required = scan_tex_for_packages(content, base_path=path.parent)
    if not required:
        return []
        
    # Get currently installed packages
    # We use explicit list to avoid re-installing existing ones
    installed = set(tlmgr_list(only_installed=True))
    
    missing = [pkg for pkg in required if pkg not in installed]
    
    if not missing:
        return []

    # Filter likely invalid packages or complex ones (heuristic)
    # We only try to install simple names. 
    # If a name contains path-like chars or is too weird, skip it.
    candidates = [pkg for pkg in missing if re.match(r"^[a-zA-Z0-9\-_]+$", pkg)]
    
    if not candidates:
        return []
        
    if not quiet and not is_quiet():
        logger = get_logger()
        logger.info(f"Pre-installing detected packages: {', '.join(candidates)}")
        
    # Try to install candidates. 
    # We just pass the list to tlmgr. It might assume they are package names.
    # Note: parsing \documentclass{article} gives "article", which is usually fine if tlmgr knows it.
    # But "article" is in latex-base usually.
    # We accept that some might fail or be ignored by tlmgr.
    
    result = tlmgr_install(candidates)
    
    if result:
        return candidates
    return []


def compile_with_auto_install(
    input_file: Union[str, Path],
    engine: str = "pdflatex",
    max_attempts: int = 3,
    output_dir: Optional[Union[str, Path]] = None,
    quiet: bool = False,
    **kwargs,
) -> CompileResult:
    """Compile a LaTeX file with automatic package installation.

    This is the main function that provides R-tinytex parity. It:
    1. Attempts to compile the document
    2. If compilation fails, parses the log for missing packages
    3. Installs missing packages
    4. Retries compilation

    Args:
        input_file: Path to .tex file
        engine: LaTeX engine ('pdflatex', 'xelatex', or 'lualatex')
        max_attempts: Maximum compilation attempts
        output_dir: Output directory for generated files
        quiet: Suppress progress output
        **kwargs: Additional arguments passed to the compiler

    Returns:
        CompileResult: Final compilation result

    Example:
        >>> result = compile_with_auto_install("document.tex")
        >>> if result.success:
        ...     print(f"PDF: {result.output_file}")
        ... else:
        ...     print("Compilation failed")
    """
    input_path = Path(input_file).resolve()

    # Select engine function
    engines = {
        "pdflatex": pdflatex,
        "xelatex": xelatex,
        "lualatex": lualatex,
        "latexmk": latexmk,
    }

    if engine not in engines:
        raise ValueError(f"Unknown engine: {engine}. Use: {list(engines.keys())}")

    compile_func = engines[engine]
    installed_packages: List[str] = []

    # Attempt pre-installation of packages from source
    # This helps avoid multiple compilation cycles for simple dependencies
    try:
        pre_installed = install_packages_from_source(input_path, quiet=quiet)
        if pre_installed:
            installed_packages.extend(pre_installed)
    except Exception:
        # Ignore pre-install errors and fall back to reactive mode
        pass

    for attempt in range(max_attempts):
        # Ignore pre-install errors and fall back to reactive mode
        pass

    # Main compilation loop with auto-installation
    # We allow more iterations for package installation cycles than pure compilation retries.
    MAX_INSTALL_CYCLES = 30
    compilation_retries = 0
    final_result = None

    for iteration in range(MAX_INSTALL_CYCLES):
        # We only count it as a "retry" if we didn't install anything last time,
        # but for simplicity, let's just use the max_attempts argument to control
        # how many times we try to compile *without* fixing anything.
        
        # However, purely relying on max_attempts (default 3) is too low if we have 10 packages to install one-by-one.
        # So we use a hybrid approach:
        # - Continue if we installed packages (doesn't consume 'max_attempts' quota effectively)
        # - Stop if we fail max_attempts times consecutively without any installations?
        # Simpler: Just run compilation. 
        
        if not quiet and not is_quiet():
            logger = get_logger()
            if iteration == 0:
                logger.info(f"Compilation attempt 1/{max_attempts}...")
            else:
                logger.info(f"Compilation attempt {iteration + 1}...")

        result = compile_func(
            input_path,
            output_dir=output_dir,
            quiet=quiet,
            **kwargs,
        )
        final_result = result

        if result.success:
            if installed_packages and not quiet and not is_quiet():
                logger = get_logger()
                logger.info(f"Installed packages: {', '.join(installed_packages)}")
            return result

        # Parse log for missing files
        if result.log_file and result.log_file.exists():
            missing_files = parse_log_file(result.log_file)
        else:
            # Try to extract from stdout/stderr
            missing_files = parse_log_for_missing_files(
                result.stdout + "\n" + result.stderr
            )

        if not missing_files:
            # No identifiable missing packages, can't auto-install.
            # Counting this as a failed attempt.
            compilation_retries += 1
            if compilation_retries >= max_attempts:
                if not quiet and not is_quiet():
                    logger = get_logger()
                    logger.warning("Compilation failed but no missing packages detected.")
                return result
            # Retry blindly? No, usually if no missing files, it's a syntax error.
            # But let's check max_attempts anyway for consistency with original behavior.
            continue 

        if not quiet and not is_quiet():
            logger = get_logger()
            logger.info(f"Missing files detected: {', '.join(missing_files)}")

        # Find packages for missing files
        package_info = find_packages_for_files(missing_files)

        # Filter to packages we found
        installable = [p for p in package_info if p.package]

        if not installable:
            if not quiet and not is_quiet():
                logger = get_logger()
                logger.warning("Could not find packages for missing files.")
            return result

        if not quiet and not is_quiet():
            logger = get_logger()
            packages = [p.package for p in installable]
            logger.info(f"Installing packages: {', '.join(packages)}")

        # Install packages
        newly_installed = install_missing_packages(installable)
        installed_packages.extend(newly_installed)

        if not newly_installed:
            if not quiet and not is_quiet():
                logger = get_logger()
                logger.error("Failed to install packages.")
            # If we couldn't install anything, we should count this as a retry or stop.
            compilation_retries += 1
            if compilation_retries >= max_attempts:
                return result
        else:
            # We successfully installed something!
            # Reset compilation_retries because we changed the environment.
            # This ensures "3 attempts" applies to the final phase where no more packages are missing.
            compilation_retries = 0

    # If we get here, we've exhausted everything
    return final_result


# Convenience alias
compile_tex = compile_with_auto_install
