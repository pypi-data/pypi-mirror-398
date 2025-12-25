
import pytest
from unittest.mock import patch, MagicMock
from jettex.tlmgr import tlmgr_search

# Mock outputs simulating Windows tlmgr behavior
MOCK_OUTPUT_SAME_LINE_BACKSLASH = """
lwarp: texmf-dist\\tex\\latex\\lwarp\\lwarp-manyfoot.sty
ncctools: texmf-dist\\tex\\latex\\ncctools\\manyfoot.sty
"""

MOCK_OUTPUT_MULTILINE_BACKSLASH = """
lwarp:
    texmf-dist\\tex\\latex\\lwarp\\lwarp-manyfoot.sty
ncctools:
    texmf-dist\\tex\\latex\\ncctools\\manyfoot.sty
"""

MOCK_OUTPUT_MIXED = """
tlmgr: package repository http://mirror.ctan.org/systems/texlive/tlnet (verified)
lwarp: texmf-dist/tex/latex/lwarp/lwarp-manyfoot.sty
ncctools:
  texmf-dist\\tex\\latex\\ncctools\\manyfoot.sty
"""

MOCK_OUTPUT_WEIRD = """
some-pkg: C:\\Program Files\\TinyTeX\\texmf-dist\\tex\\latex\\some-pkg\\pkg.sty
"""

@pytest.fixture
def mock_run_command():
    with patch("jettex.tlmgr.run_command") as mock_run, \
         patch("jettex.tlmgr._get_tlmgr") as mock_get:
        mock_get.return_value = "/mock/path/to/tlmgr"
        yield mock_run

def test_tlmgr_search_same_line_backslash(mock_run_command):
    mock_run_command.return_value.returncode = 0
    mock_run_command.return_value.stdout = MOCK_OUTPUT_SAME_LINE_BACKSLASH
    
    results = tlmgr_search("manyfoot.sty", file_search=True)
    
    assert len(results) == 2
    assert results[0]["package"] == "lwarp"
    assert "lwarp-manyfoot.sty" in results[0]["file"]
    assert "\\" in results[0]["file"]
    
    assert results[1]["package"] == "ncctools"
    assert "manyfoot.sty" in results[1]["file"]
    assert "\\" in results[1]["file"]

def test_tlmgr_search_multiline_backslash(mock_run_command):
    mock_run_command.return_value.returncode = 0
    mock_run_command.return_value.stdout = MOCK_OUTPUT_MULTILINE_BACKSLASH
    
    results = tlmgr_search("manyfoot.sty", file_search=True)
    
    assert len(results) == 2
    assert results[0]["package"] == "lwarp"
    assert results[1]["package"] == "ncctools"

def test_tlmgr_search_mixed(mock_run_command):
    mock_run_command.return_value.returncode = 0
    mock_run_command.return_value.stdout = MOCK_OUTPUT_MIXED
    
    results = tlmgr_search("manyfoot.sty", file_search=True)
    
    assert len(results) == 2
    assert results[0]["package"] == "lwarp"
    assert results[1]["package"] == "ncctools"

def test_tlmgr_search_sanity_check(mock_run_command):
    # Test that paths interpreted as packages are filtered out
    # e.g. if formatting is just "path\to\file" without "package:" prefix?
    # Or if formatting is "path\to\package: ..." 
    
    bad_output = """
C:\\Bad\\Path: somefile
good-pkg: somefile
    """
    mock_run_command.return_value.returncode = 0
    mock_run_command.return_value.stdout = bad_output
    
    results = tlmgr_search("query", file_search=True)
    
    assert len(results) == 1
    assert results[0]["package"] == "good-pkg"
    # C:\Bad\Path should be filtered out by sanity check "\ in package"

