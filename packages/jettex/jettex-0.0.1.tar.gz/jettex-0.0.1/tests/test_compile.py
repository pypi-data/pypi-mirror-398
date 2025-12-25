"""Tests for compilation functions."""

import pytest
from pathlib import Path
from jettex.compile import CompileResult


def test_compile_result_dataclass():
    """Test CompileResult dataclass."""
    result = CompileResult(
        success=True,
        output_file=Path("/tmp/test.pdf"),
        log_file=Path("/tmp/test.log"),
        stdout="Output",
        stderr="",
        returncode=0,
    )
    assert result.success is True
    assert result.returncode == 0
    assert result.output_file == Path("/tmp/test.pdf")


def test_compile_result_failure():
    """Test CompileResult for failed compilation."""
    result = CompileResult(
        success=False,
        output_file=None,
        log_file=Path("/tmp/test.log"),
        stdout="",
        stderr="Error message",
        returncode=1,
    )
    assert result.success is False
    assert result.output_file is None
    assert result.returncode == 1
