"""Tests for package detection and auto-install."""

import pytest
from jettex.packages import (
    parse_log_for_missing_files,
    PackageInfo,
)


def test_parse_missing_sty():
    """Test parsing missing .sty file error."""
    log = """
! LaTeX Error: File `geometry.sty' not found.

Type X to quit or <RETURN> to proceed,
"""
    missing = parse_log_for_missing_files(log)
    assert "geometry.sty" in missing


def test_parse_missing_cls():
    """Test parsing missing .cls file error."""
    log = """
! LaTeX Error: File `article.cls' not found.
"""
    missing = parse_log_for_missing_files(log)
    assert "article.cls" in missing


def test_parse_missing_font():
    """Test parsing missing font error."""
    log = """
! Font TU/lmr/m/n/10=ec-lmr10 at 10.0pt not loadable: metric data not found.
"""
    missing = parse_log_for_missing_files(log)
    assert any("lmr" in f.lower() or "ec-lmr" in f for f in missing)


def test_parse_file_not_found():
    """Test parsing generic file not found error."""
    log = """
! I can't find file `mypkg.tex'.
"""
    missing = parse_log_for_missing_files(log)
    assert "mypkg.tex" in missing


def test_parse_multiple_missing():
    """Test parsing multiple missing files."""
    log = """
! LaTeX Error: File `geometry.sty' not found.
! LaTeX Error: File `fancyhdr.sty' not found.
! LaTeX Error: File `hyperref.sty' not found.
"""
    missing = parse_log_for_missing_files(log)
    assert "geometry.sty" in missing
    assert "fancyhdr.sty" in missing
    assert "hyperref.sty" in missing


def test_parse_no_missing():
    """Test parsing log with no missing files."""
    log = """
Output written on document.pdf (1 page, 12345 bytes).
Transcript written on document.log.
"""
    missing = parse_log_for_missing_files(log)
    assert len(missing) == 0


def test_package_info():
    """Test PackageInfo dataclass."""
    info = PackageInfo(
        filename="geometry.sty",
        package="geometry",
        error_message="File 'geometry.sty' not found",
    )
    assert info.filename == "geometry.sty"
    assert info.package == "geometry"
