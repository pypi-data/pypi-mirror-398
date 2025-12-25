# jettex

A lightweight Python wrapper for [TinyTeX](https://yihui.org/tinytex/), providing easy LaTeX installation, compilation, and automatic package management.

## Features

- **Easy Installation**: Install TinyTeX with a single function call
- **LaTeX Compilation**: Compile documents with pdflatex, xelatex, or lualatex
- **Automatic Package Installation**: Automatically detect and install missing LaTeX packages (like R's tinytex)
- **Package Management**: Full tlmgr wrapper for installing, removing, and updating packages
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Installation

```bash
pip install jettex
```

## Quick Start

```python
import jettex

# Install TinyTeX (only needed once)
jettex.install_tinytex()

# Compile a document with automatic package installation
result = jettex.compile_tex("document.tex")

if result.success:
    print(f"PDF created: {result.output_file}")
```

## Usage

### Installing TinyTeX

```python
import jettex

# Install default version (~90 packages)
jettex.install_tinytex()

# Install minimal version (no packages)
jettex.install_tinytex(version=0)

# Install extended version (more packages)
jettex.install_tinytex(version=2)

# Force reinstall
jettex.install_tinytex(force=True)

# Check if installed
if jettex.is_tinytex_installed():
    print(f"TinyTeX is at: {jettex.tinytex_root()}")
```

### Compiling Documents

```python
import jettex

# Compile with auto-install (recommended)
# Automatically installs missing packages
result = jettex.compile_tex("document.tex")

# Use a specific engine
result = jettex.compile_tex("document.tex", engine="xelatex")
result = jettex.compile_tex("document.tex", engine="lualatex")

# Compile without auto-install
result = jettex.pdflatex("document.tex")
result = jettex.xelatex("document.tex")
result = jettex.lualatex("document.tex")

# Use latexmk for complex documents
result = jettex.latexmk("document.tex", engine="pdflatex")

# Check result
if result.success:
    print(f"Output: {result.output_file}")
else:
    print(f"Failed: {result.stderr}")
```

### Package Management

```python
import jettex

# Install packages
jettex.tlmgr_install(["geometry", "amsmath", "hyperref"])

# Remove packages
jettex.tlmgr_remove(["unused-package"])

# Update all packages
jettex.tlmgr_update(all_packages=True)

# Update tlmgr itself
jettex.tlmgr_update(self_update=True)

# List installed packages
packages = jettex.tlmgr_list()

# Search for a package
results = jettex.tlmgr_search("tikz")

# Find which package provides a file
package = jettex.find_package_for_file("geometry.sty")
```

## Command Line Interface

jettex also provides a CLI:

```bash
# Install TinyTeX
jettex install

# Compile a document
jettex compile document.tex

# Compile with specific engine
jettex compile document.tex --engine xelatex

# Install packages
jettex install-pkg geometry amsmath

# Search for packages
jettex search tikz

# List installed packages
jettex list

# Update all packages
jettex update --all

# Show TinyTeX info
jettex info
```

## TinyTeX Versions

| Version | Description | Size |
|---------|-------------|------|
| 0 | Infraonly (minimal, no packages) | ~1 MB |
| 1 | Default (~90 common packages) | ~100 MB |
| 2 | Extended (more packages) | ~200+ MB |

## Comparison with R's tinytex

This package aims to provide feature parity with R's tinytex:

| Feature | R tinytex | jettex |
|---------|-----------|-----------|
| Install TinyTeX | ✅ | ✅ |
| Compile LaTeX | ✅ | ✅ |
| Auto-install packages | ✅ | ✅ |
| tlmgr wrapper | ✅ | ✅ |
| Cross-platform | ✅ | ✅ |

## Requirements

- Python 3.8+
- `requests` library (for downloading TinyTeX)

## License

MIT License

TinyTeX itself is licensed under GPL-2.
