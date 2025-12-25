"""Command-line interface for jettex."""

import argparse
import sys
from pathlib import Path

from .console import (
    setup_logging,
    Verbosity,
    get_logger,
    print_success,
    print_error,
    print_info,
    download_progress,
    spinner,
    print_package_list,
    print_package_info,
    print_search_results,
    print_tinytex_info,
    print_compile_result,
)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="jettex",
        description="jettex - A lightweight Python wrapper for TinyTeX",
    )

    # Global arguments
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output (debug level)",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress all output except errors",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        metavar="FILE",
        help="Write debug logs to file",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Install command
    install_parser = subparsers.add_parser("install", help="Install TinyTeX")
    install_parser.add_argument(
        "--version",
        type=int,
        default=1,
        choices=[0, 1, 2],
        help="TinyTeX version: 0=minimal, 1=default, 2=extended",
    )
    install_parser.add_argument(
        "--dir",
        type=str,
        help="Custom installation directory",
    )
    install_parser.add_argument(
        "--force",
        action="store_true",
        help="Force reinstall",
    )

    # Uninstall command
    subparsers.add_parser("uninstall", help="Uninstall TinyTeX")

    # Compile command
    compile_parser = subparsers.add_parser(
        "compile", help="Compile a LaTeX document"
    )
    compile_parser.add_argument("file", type=str, help="LaTeX file to compile")
    compile_parser.add_argument(
        "--engine",
        type=str,
        default="pdflatex",
        choices=["pdflatex", "xelatex", "lualatex", "latexmk"],
        help="LaTeX engine",
    )
    compile_parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory",
    )
    compile_parser.add_argument(
        "--no-auto-install",
        action="store_true",
        help="Disable automatic package installation",
    )

    # Package commands
    pkg_parser = subparsers.add_parser("install-pkg", help="Install LaTeX packages")
    pkg_parser.add_argument("packages", nargs="+", help="Packages to install")

    remove_parser = subparsers.add_parser("remove-pkg", help="Remove LaTeX packages")
    remove_parser.add_argument("packages", nargs="+", help="Packages to remove")

    search_parser = subparsers.add_parser("search", help="Search for packages")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "--file",
        action="store_true",
        help="Search by filename",
    )

    # Update command
    update_parser = subparsers.add_parser("update", help="Update packages")
    update_parser.add_argument(
        "--all",
        action="store_true",
        help="Update all packages",
    )
    update_parser.add_argument(
        "--self",
        action="store_true",
        help="Update tlmgr itself",
    )

    # List command
    subparsers.add_parser("list", help="List installed packages")

    # Info command
    info_parser = subparsers.add_parser("info", help="Show TinyTeX info")
    info_parser.add_argument(
        "package",
        nargs="?",
        help="Package to get info about",
    )

    # Version command
    subparsers.add_parser("version", help="Show jettex version")

    args = parser.parse_args()

    # Determine verbosity
    if args.quiet:
        verbosity = Verbosity.QUIET
    elif args.verbose:
        verbosity = Verbosity.VERBOSE
    else:
        verbosity = Verbosity.NORMAL

    # Setup logging
    log_file = Path(args.log_file) if args.log_file else None
    setup_logging(verbosity=verbosity, log_file=log_file)
    logger = get_logger()

    if args.command is None:
        parser.print_help()
        return 0

    # Import here to avoid slow startup for --help
    from . import (
        install_tinytex,
        uninstall_tinytex,
        compile_tex,
        pdflatex,
        xelatex,
        lualatex,
        latexmk,
        tlmgr_install,
        tlmgr_remove,
        tlmgr_search,
        tlmgr_update,
        tlmgr_list,
        tlmgr_info,
        tinytex_root,
        tinytex_version,
        is_tinytex_installed,
        __version__,
    )

    try:
        if args.command == "install":
            return _cmd_install(args, install_tinytex, logger)

        elif args.command == "uninstall":
            return _cmd_uninstall(uninstall_tinytex)

        elif args.command == "compile":
            return _cmd_compile(
                args, compile_tex, pdflatex, xelatex, lualatex, latexmk, logger
            )

        elif args.command == "install-pkg":
            return _cmd_install_pkg(args, tlmgr_install, logger)

        elif args.command == "remove-pkg":
            return _cmd_remove_pkg(args, tlmgr_remove, logger)

        elif args.command == "search":
            return _cmd_search(args, tlmgr_search)

        elif args.command == "update":
            return _cmd_update(args, tlmgr_update, logger)

        elif args.command == "list":
            return _cmd_list(tlmgr_list)

        elif args.command == "info":
            return _cmd_info(
                args, tlmgr_info, is_tinytex_installed, tinytex_root, tinytex_version
            )

        elif args.command == "version":
            print_info(f"jettex version {__version__}")
            return 0

    except KeyboardInterrupt:
        print_info("\nOperation cancelled.")
        return 130
    except Exception as e:
        logger.exception("Unexpected error")
        print_error(str(e))
        return 1

    return 0


def _cmd_install(args, install_tinytex, logger):
    """Handle install command with Rich progress bar."""
    logger.info("Installing TinyTeX...")

    install_dir = Path(args.dir) if args.dir else None

    with download_progress("Downloading TinyTeX") as progress:
        task = progress.add_task("Downloading", total=None)

        def progress_callback(stage, downloaded, total):
            if stage == "downloading":
                if total > 0:
                    progress.update(task, total=total, completed=downloaded)
            elif stage == "extracting":
                progress.update(task, description="Extracting...", total=None)
            elif stage == "installing":
                progress.update(task, description="Installing...", total=None)

        path = install_tinytex(
            version=args.version,
            install_dir=install_dir,
            force=args.force,
            progress_callback=progress_callback,
        )

    print_success(f"Installed to: [path]{path}[/path]", title="TinyTeX Installed")
    return 0


def _cmd_uninstall(uninstall_tinytex):
    """Handle uninstall command."""
    with spinner("Uninstalling TinyTeX..."):
        success = uninstall_tinytex()

    if success:
        print_success("TinyTeX has been removed.", title="Uninstalled")
        return 0
    else:
        print_error("TinyTeX not found or could not be uninstalled.")
        return 1


def _cmd_compile(args, compile_tex, pdflatex, xelatex, lualatex, latexmk, logger):
    """Handle compile command with spinner."""
    logger.debug(f"Compiling {args.file} with {args.engine}")

    with spinner(f"Compiling {args.file}..."):
        if args.no_auto_install:
            engines = {
                "pdflatex": pdflatex,
                "xelatex": xelatex,
                "lualatex": lualatex,
                "latexmk": latexmk,
            }
            result = engines[args.engine](
                args.file,
                output_dir=args.output_dir,
                quiet=True,
            )
        else:
            result = compile_tex(
                args.file,
                engine=args.engine,
                output_dir=args.output_dir,
                quiet=True,
            )

    print_compile_result(result.success, result.output_file, result.stderr)
    return 0 if result.success else 1


def _cmd_install_pkg(args, tlmgr_install, logger):
    """Handle install-pkg command."""
    packages = args.packages
    logger.info(f"Installing packages: {', '.join(packages)}")

    with spinner(f"Installing {len(packages)} package(s)..."):
        success = tlmgr_install(packages)

    if success:
        print_success(
            f"Installed: [package]{', '.join(packages)}[/package]",
            title="Packages Installed"
        )
        return 0
    else:
        print_error(f"Failed to install packages: {', '.join(packages)}")
        return 1


def _cmd_remove_pkg(args, tlmgr_remove, logger):
    """Handle remove-pkg command."""
    packages = args.packages
    logger.info(f"Removing packages: {', '.join(packages)}")

    with spinner(f"Removing {len(packages)} package(s)..."):
        success = tlmgr_remove(packages)

    if success:
        print_success(
            f"Removed: [package]{', '.join(packages)}[/package]",
            title="Packages Removed"
        )
        return 0
    else:
        print_error(f"Failed to remove packages: {', '.join(packages)}")
        return 1


def _cmd_search(args, tlmgr_search):
    """Handle search command."""
    with spinner(f"Searching for '{args.query}'..."):
        results = tlmgr_search(args.query, file_search=args.file)

    print_search_results(results)
    return 0


def _cmd_update(args, tlmgr_update, logger):
    """Handle update command."""
    if args.self:
        logger.info("Updating tlmgr...")
        desc = "Updating tlmgr..."
    elif args.all:
        logger.info("Updating all packages...")
        desc = "Updating all packages..."
    else:
        logger.info("Updating packages...")
        desc = "Updating..."

    with spinner(desc):
        success = tlmgr_update(all_packages=args.all, self_update=args.self)

    if success:
        print_success("Update completed successfully.", title="Updated")
        return 0
    else:
        print_error("Update failed.")
        return 1


def _cmd_list(tlmgr_list):
    """Handle list command with Rich table."""
    with spinner("Fetching package list..."):
        packages = tlmgr_list()

    print_package_list(packages, title="Installed Packages")
    return 0


def _cmd_info(args, tlmgr_info, is_tinytex_installed, tinytex_root, tinytex_version):
    """Handle info command."""
    if args.package:
        with spinner(f"Fetching info for '{args.package}'..."):
            info = tlmgr_info(args.package)

        if info:
            print_package_info(info, name=args.package)
            return 0
        else:
            print_error(f"Package not found: {args.package}")
            return 1
    else:
        if is_tinytex_installed():
            print_tinytex_info(tinytex_root(), tinytex_version())
            return 0
        else:
            print_error("TinyTeX is not installed.")
            return 1


if __name__ == "__main__":
    sys.exit(main())
