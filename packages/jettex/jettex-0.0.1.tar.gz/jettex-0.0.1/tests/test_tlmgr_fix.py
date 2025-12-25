
from unittest.mock import patch, MagicMock
from jettex.tlmgr import find_package_for_file

def test_find_package_for_file_with_extension():
    """Test that find_package_for_file strips extension if package name matches filename."""
    # Simulation of the bug: tlmgr search returns "acmart.sty" as the package name
    mock_results = [{"package": "acmart.sty"}]
    
    with patch("jettex.tlmgr.tlmgr_search", return_value=mock_results):
        package = find_package_for_file("acmart.sty")
        # Should be "acmart", not "acmart.sty"
        assert package == "acmart"

def test_find_package_for_file_normal():
    """Test that find_package_for_file works normally when package name is correct."""
    mock_results = [{"package": "geometry"}]
    
    with patch("jettex.tlmgr.tlmgr_search", return_value=mock_results):
        package = find_package_for_file("geometry.sty")
        assert package == "geometry"
