"""LaTeX compilation functions."""

from pathlib import Path
from typing import Optional, List, Union
from dataclasses import dataclass

from .utils import get_executable, ensure_tinytex_in_path, run_command


@dataclass
class CompileResult:
    """Result of a LaTeX compilation."""

    success: bool
    """Whether compilation succeeded."""

    output_file: Optional[Path]
    """Path to the output PDF file if successful."""

    log_file: Optional[Path]
    """Path to the compilation log file."""

    stdout: str
    """Standard output from the compiler."""

    stderr: str
    """Standard error from the compiler."""

    returncode: int
    """Return code from the compiler."""


def _get_engine(name: str) -> Path:
    """Get a LaTeX engine executable.

    Args:
        name: Engine name (pdflatex, xelatex, lualatex, latexmk)

    Returns:
        Path: Path to engine executable

    Raises:
        RuntimeError: If engine not found
    """
    ensure_tinytex_in_path()
    engine = get_executable(name)
    if engine is None:
        raise RuntimeError(
            f"{name} not found. Is TinyTeX installed? Run install_tinytex() first."
        )
    return engine


def _compile_latex(
    engine: str,
    input_file: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    interaction: str = "nonstopmode",
    synctex: bool = False,
    shell_escape: bool = False,
    extra_args: Optional[List[str]] = None,
    quiet: bool = False,
    timeout: Optional[int] = None,
) -> CompileResult:
    """Compile a LaTeX file with the specified engine.

    Args:
        engine: Engine name (pdflatex, xelatex, lualatex)
        input_file: Path to .tex file
        output_dir: Directory for output files (default: same as input)
        interaction: Interaction mode (nonstopmode, batchmode, scrollmode, errorstopmode)
        synctex: Enable SyncTeX
        shell_escape: Enable shell escape
        extra_args: Additional arguments to pass to engine
        quiet: Suppress output
        timeout: Compilation timeout in seconds

    Returns:
        CompileResult: Compilation result
    """
    input_path = Path(input_file).resolve()

    if not input_path.exists():
        return CompileResult(
            success=False,
            output_file=None,
            log_file=None,
            stdout="",
            stderr=f"Input file not found: {input_path}",
            returncode=1,
        )

    if output_dir:
        output_path = Path(output_dir).resolve()
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = input_path.parent

    # Build command
    engine_path = _get_engine(engine)
    cmd = [str(engine_path)]

    cmd.append(f"-interaction={interaction}")

    if output_dir:
        cmd.append(f"-output-directory={output_path}")

    if synctex:
        cmd.append("-synctex=1")

    if shell_escape:
        cmd.append("-shell-escape")

    if quiet and engine != "latexmk":
        cmd.append("-quiet")

    if extra_args:
        cmd.extend(extra_args)

    cmd.append(str(input_path))

    # Run compilation
    result = run_command(
        cmd,
        cwd=input_path.parent,
        capture_output=True,
        check=False,
        timeout=timeout,
    )

    # Determine output paths
    stem = input_path.stem
    output_pdf = output_path / f"{stem}.pdf"
    log_file = output_path / f"{stem}.log"

    return CompileResult(
        success=result.returncode == 0 and output_pdf.exists(),
        output_file=output_pdf if output_pdf.exists() else None,
        log_file=log_file if log_file.exists() else None,
        stdout=result.stdout,
        stderr=result.stderr,
        returncode=result.returncode,
    )


def pdflatex(
    input_file: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    interaction: str = "nonstopmode",
    synctex: bool = False,
    shell_escape: bool = False,
    extra_args: Optional[List[str]] = None,
    quiet: bool = False,
    timeout: Optional[int] = None,
) -> CompileResult:
    """Compile a LaTeX file using pdflatex.

    Args:
        input_file: Path to .tex file
        output_dir: Directory for output files
        interaction: Interaction mode
        synctex: Enable SyncTeX
        shell_escape: Enable shell escape
        extra_args: Additional arguments
        quiet: Suppress output
        timeout: Compilation timeout in seconds

    Returns:
        CompileResult: Compilation result

    Example:
        >>> result = pdflatex("document.tex")
        >>> if result.success:
        ...     print(f"PDF created: {result.output_file}")
    """
    return _compile_latex(
        "pdflatex",
        input_file,
        output_dir=output_dir,
        interaction=interaction,
        synctex=synctex,
        shell_escape=shell_escape,
        extra_args=extra_args,
        quiet=quiet,
        timeout=timeout,
    )


def xelatex(
    input_file: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    interaction: str = "nonstopmode",
    synctex: bool = False,
    shell_escape: bool = False,
    extra_args: Optional[List[str]] = None,
    quiet: bool = False,
    timeout: Optional[int] = None,
) -> CompileResult:
    """Compile a LaTeX file using xelatex.

    XeLaTeX supports OpenType fonts and Unicode natively.

    Args:
        input_file: Path to .tex file
        output_dir: Directory for output files
        interaction: Interaction mode
        synctex: Enable SyncTeX
        shell_escape: Enable shell escape
        extra_args: Additional arguments
        quiet: Suppress output
        timeout: Compilation timeout in seconds

    Returns:
        CompileResult: Compilation result
    """
    return _compile_latex(
        "xelatex",
        input_file,
        output_dir=output_dir,
        interaction=interaction,
        synctex=synctex,
        shell_escape=shell_escape,
        extra_args=extra_args,
        quiet=quiet,
        timeout=timeout,
    )


def lualatex(
    input_file: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    interaction: str = "nonstopmode",
    synctex: bool = False,
    shell_escape: bool = False,
    extra_args: Optional[List[str]] = None,
    quiet: bool = False,
    timeout: Optional[int] = None,
) -> CompileResult:
    """Compile a LaTeX file using lualatex.

    LuaLaTeX provides Lua scripting and OpenType font support.

    Args:
        input_file: Path to .tex file
        output_dir: Directory for output files
        interaction: Interaction mode
        synctex: Enable SyncTeX
        shell_escape: Enable shell escape
        extra_args: Additional arguments
        quiet: Suppress output
        timeout: Compilation timeout in seconds

    Returns:
        CompileResult: Compilation result
    """
    return _compile_latex(
        "lualatex",
        input_file,
        output_dir=output_dir,
        interaction=interaction,
        synctex=synctex,
        shell_escape=shell_escape,
        extra_args=extra_args,
        quiet=quiet,
        timeout=timeout,
    )


def latexmk(
    input_file: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    engine: str = "pdflatex",
    interaction: str = "nonstopmode",
    synctex: bool = False,
    shell_escape: bool = False,
    clean: bool = False,
    continuous: bool = False,
    extra_args: Optional[List[str]] = None,
    quiet: bool = False,
    timeout: Optional[int] = None,
) -> CompileResult:
    """Compile a LaTeX file using latexmk.

    latexmk automatically runs the correct number of compilations
    and handles bibliography/index generation.

    Args:
        input_file: Path to .tex file
        output_dir: Directory for output files
        engine: Backend engine (pdflatex, xelatex, lualatex)
        clean: Clean auxiliary files after compilation
        continuous: Continuous compilation mode (watch for changes)
        extra_args: Additional arguments
        timeout: Compilation timeout in seconds

    Returns:
        CompileResult: Compilation result
    """
    input_path = Path(input_file).resolve()

    if not input_path.exists():
        return CompileResult(
            success=False,
            output_file=None,
            log_file=None,
            stdout="",
            stderr=f"Input file not found: {input_path}",
            returncode=1,
        )

    if output_dir:
        output_path = Path(output_dir).resolve()
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = input_path.parent

    latexmk_path = _get_engine("latexmk")
    cmd = [str(latexmk_path), "-pdf"]

    # Set engine
    if engine == "xelatex":
        cmd.append("-xelatex")
    elif engine == "lualatex":
        cmd.append("-lualatex")
    # pdflatex is default with -pdf

    if output_dir:
        cmd.append(f"-output-directory={output_path}")

    if clean:
        cmd.append("-c")

    if continuous:
        cmd.append("-pvc")

    cmd.append(f"-interaction={interaction}")

    if synctex:
        cmd.append("-synctex=1")

    if shell_escape:
        # latexmk passes this to the latex engine
        cmd.append("-shell-escape")

    if quiet:
        cmd.append("-quiet")

    if extra_args:
        cmd.extend(extra_args)

    cmd.append(str(input_path))

    result = run_command(
        cmd,
        cwd=input_path.parent,
        capture_output=True,
        check=False,
        timeout=timeout,
    )

    stem = input_path.stem
    output_pdf = output_path / f"{stem}.pdf"
    log_file = output_path / f"{stem}.log"

    return CompileResult(
        success=result.returncode == 0 and output_pdf.exists(),
        output_file=output_pdf if output_pdf.exists() else None,
        log_file=log_file if log_file.exists() else None,
        stdout=result.stdout,
        stderr=result.stderr,
        returncode=result.returncode,
    )


def clean_auxiliary(
    input_file: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
) -> int:
    """Clean auxiliary files from LaTeX compilation.

    Args:
        input_file: Path to .tex file
        output_dir: Directory containing auxiliary files

    Returns:
        int: Number of files removed
    """
    input_path = Path(input_file).resolve()
    stem = input_path.stem

    if output_dir:
        base_dir = Path(output_dir).resolve()
    else:
        base_dir = input_path.parent

    # Common auxiliary extensions
    aux_extensions = [
        ".aux", ".log", ".out", ".toc", ".lof", ".lot",
        ".fls", ".fdb_latexmk", ".synctex.gz", ".synctex",
        ".bbl", ".blg", ".bcf", ".run.xml",
        ".idx", ".ilg", ".ind",
        ".nav", ".snm", ".vrb",  # Beamer
        ".xdv",  # XeTeX intermediate
    ]

    removed = 0
    for ext in aux_extensions:
        aux_file = base_dir / f"{stem}{ext}"
        if aux_file.exists():
            try:
                aux_file.unlink()
                removed += 1
            except OSError:
                pass

    return removed
