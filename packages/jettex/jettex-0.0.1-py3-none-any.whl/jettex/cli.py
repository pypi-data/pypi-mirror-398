"""Command-line interface for jettex."""

import argparse
import sys
from pathlib import Path


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="jettex",
        description="jettex - A lightweight Python wrapper for TinyTeX",
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
        choices=["pdflatex", "xelatex", "lualatex"],
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
    compile_parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output",
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

    args = parser.parse_args()

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
        tlmgr_install,
        tlmgr_remove,
        tlmgr_search,
        tlmgr_update,
        tlmgr_list,
        tlmgr_info,
        tinytex_root,
        tinytex_version,
        is_tinytex_installed,
    )

    try:
        if args.command == "install":
            print("Installing TinyTeX...")
            install_dir = Path(args.dir) if args.dir else None

            def progress(stage, downloaded, total):
                if stage == "downloading" and total > 0:
                    pct = (downloaded / total) * 100
                    print(f"\rDownloading: {pct:.1f}%", end="", flush=True)
                elif stage == "extracting":
                    print("\nExtracting...")
                elif stage == "installing":
                    print("Installing...")
                elif stage == "complete":
                    print("Done!")

            path = install_tinytex(
                version=args.version,
                install_dir=install_dir,
                force=args.force,
                progress_callback=progress,
            )
            print(f"TinyTeX installed to: {path}")

        elif args.command == "uninstall":
            if uninstall_tinytex():
                print("TinyTeX uninstalled successfully.")
            else:
                print("TinyTeX not found or could not be uninstalled.")
                return 1

        elif args.command == "compile":
            if args.no_auto_install:
                engines = {
                    "pdflatex": pdflatex,
                    "xelatex": xelatex,
                    "lualatex": lualatex,
                }
                result = engines[args.engine](
                    args.file,
                    output_dir=args.output_dir,
                    quiet=args.quiet,
                )
            else:
                result = compile_tex(
                    args.file,
                    engine=args.engine,
                    output_dir=args.output_dir,
                    quiet=args.quiet,
                )

            if result.success:
                print(f"Success! Output: {result.output_file}")
            else:
                print("Compilation failed.")
                if result.stderr:
                    print(result.stderr)
                return 1

        elif args.command == "install-pkg":
            print(f"Installing: {', '.join(args.packages)}")
            if tlmgr_install(args.packages):
                print("Packages installed successfully.")
            else:
                print("Failed to install packages.")
                return 1

        elif args.command == "remove-pkg":
            print(f"Removing: {', '.join(args.packages)}")
            if tlmgr_remove(args.packages):
                print("Packages removed successfully.")
            else:
                print("Failed to remove packages.")
                return 1

        elif args.command == "search":
            results = tlmgr_search(args.query, file_search=args.file)
            if results:
                for r in results:
                    print(r.get("package", ""))
            else:
                print("No packages found.")

        elif args.command == "update":
            if tlmgr_update(all_packages=args.all, self_update=args.self):
                print("Update completed.")
            else:
                print("Update failed.")
                return 1

        elif args.command == "list":
            packages = tlmgr_list()
            for pkg in packages:
                print(pkg)
            print(f"\n{len(packages)} packages installed.")

        elif args.command == "info":
            if args.package:
                info = tlmgr_info(args.package)
                if info:
                    for key, value in info.items():
                        print(f"{key}: {value}")
                else:
                    print(f"Package not found: {args.package}")
                    return 1
            else:
                if is_tinytex_installed():
                    print(f"TinyTeX root: {tinytex_root()}")
                    print(f"Version: {tinytex_version()}")
                else:
                    print("TinyTeX is not installed.")
                    return 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
