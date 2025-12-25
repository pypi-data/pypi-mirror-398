"""Tests for utility functions."""

import pytest
from jettex.utils import (
    get_platform,
    get_arch,
    get_tinytex_bundle_name,
    get_download_url,
    get_default_install_dir,
)


def test_get_platform():
    """Test platform detection."""
    platform = get_platform()
    assert platform in ("windows", "darwin", "linux")


def test_get_arch():
    """Test architecture detection."""
    arch = get_arch()
    assert arch in ("x86_64", "aarch64", "i386", "arm64")


def test_get_tinytex_bundle_name():
    """Test bundle name generation."""
    assert get_tinytex_bundle_name(0) == "TinyTeX-0"
    assert get_tinytex_bundle_name(1) == "TinyTeX-1"
    assert get_tinytex_bundle_name(2) == "TinyTeX-2"
    assert get_tinytex_bundle_name(99) == "TinyTeX"


def test_get_download_url():
    """Test download URL generation."""
    url = get_download_url(1)
    assert "TinyTeX-1" in url
    assert "github.com" in url or "yihui.org" in url


def test_get_default_install_dir():
    """Test default installation directory."""
    path = get_default_install_dir()
    assert path is not None
    platform = get_platform()
    if platform == "darwin":
        assert "Library" in str(path)
    elif platform == "windows":
        assert "TinyTeX" in str(path)
    else:
        assert ".TinyTeX" in str(path)
