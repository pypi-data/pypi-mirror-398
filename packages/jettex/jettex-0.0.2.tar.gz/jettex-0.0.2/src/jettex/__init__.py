"""jettex - A lightweight Python wrapper for TinyTeX.

This package provides a Python interface to TinyTeX, a lightweight LaTeX
distribution based on TeX Live. It includes:

- TinyTeX installation and management
- LaTeX compilation (pdflatex, xelatex, lualatex)
- Automatic missing package detection and installation
- TeX Live package management via tlmgr

Example:
    >>> import jettex
    >>> # Install TinyTeX (only needed once)
    >>> jettex.install_tinytex()
    >>> # Compile a document (auto-installs missing packages)
    >>> result = jettex.compile_tex("document.tex")
    >>> print(result.output_file)
"""

__version__ = "0.1.0"

# Installation
from .install import (
    install_tinytex,
    uninstall_tinytex,
    tinytex_root,
    tinytex_version,
)

# Compilation
from .compile import (
    pdflatex,
    xelatex,
    lualatex,
    latexmk,
    clean_auxiliary,
    CompileResult,
)

# Package management
from .tlmgr import (
    tlmgr_install,
    tlmgr_remove,
    tlmgr_update,
    tlmgr_list,
    tlmgr_search,
    tlmgr_info,
    tlmgr_path,
    tlmgr_version,
    find_package_for_file,
)

# Auto-install compilation (main feature)
from .packages import (
    compile_with_auto_install,
    compile_tex,
    parse_log_file,
    find_packages_for_files,
    install_missing_packages,
    PackageInfo,
)

# Utilities
from .utils import (
    is_tinytex_installed,
    get_tinytex_root,
    get_bin_dir,
    get_executable,
    ensure_tinytex_in_path,
)

# Console/Logging
from .console import (
    setup_logging,
    Verbosity,
    get_logger,
    get_console,
)

__all__ = [
    # Version
    "__version__",
    # Installation
    "install_tinytex",
    "uninstall_tinytex",
    "tinytex_root",
    "tinytex_version",
    # Compilation
    "pdflatex",
    "xelatex",
    "lualatex",
    "latexmk",
    "clean_auxiliary",
    "CompileResult",
    # Package management
    "tlmgr_install",
    "tlmgr_remove",
    "tlmgr_update",
    "tlmgr_list",
    "tlmgr_search",
    "tlmgr_info",
    "tlmgr_path",
    "tlmgr_version",
    "find_package_for_file",
    # Auto-install compilation
    "compile_with_auto_install",
    "compile_tex",
    "parse_log_file",
    "find_packages_for_files",
    "install_missing_packages",
    "PackageInfo",
    # Utilities
    "is_tinytex_installed",
    "get_tinytex_root",
    "get_bin_dir",
    "get_executable",
    "ensure_tinytex_in_path",
    # Console/Logging
    "setup_logging",
    "Verbosity",
    "get_logger",
    "get_console",
]
