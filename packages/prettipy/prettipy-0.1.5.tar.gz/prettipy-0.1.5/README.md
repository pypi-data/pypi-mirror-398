# 📄 Prettipy

**Beautiful Python Code to PDF Converter**

Transform your Python source code into professionally formatted, syntax-highlighted PDF documents with ease.

[![PyPI version](https://badge.fury.io/py/prettipy.svg)](https://badge.fury.io/py/prettipy)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- 🎨 **Syntax Highlighting**: Beautiful, GitHub-style syntax highlighting using Pygments
- 🔗 **Auto-linking**: Clickable links from function/variable usage to their declarations (NEW!)
- 📦 **Smart Line Wrapping**: Intelligently wraps long lines at natural break points
- 🎯 **Multiple Input Modes**: Convert entire directories or specific files
- ⚙️ **Highly Configurable**: Customize colors, fonts, page size, and more
- 🚀 **CLI & Python API**: Use from command line or integrate into your projects
- 📋 **Rich Output**: Beautiful progress bars and formatted output (when `rich` is installed)
- 🔍 **Smart Filtering**: Automatically excludes common directories like `venv`, `__pycache__`, etc.
- 📄 **Professional Layout**: Clean, readable formatting with proper spacing and margins
- 🐙 **GitHub Integration**: Clone and convert GitHub repositories directly (NEW!)

## 🚀 Quick Start

### Installation

```bash
# Basic installation
pip install prettipy

# With rich formatting (recommended)
pip install prettipy[rich]
```

### Basic Usage

```bash
# Convert current directory
prettipy

# Convert specific directory
prettipy /path/to/your/project

# Convert specific files
prettipy -f script1.py script2.py utils.py

# Specify output file
prettipy -o my_code.pdf

# Custom line width
prettipy -w 100

# Disable auto-linking
prettipy --no-linking

# Clone and convert a GitHub repository
prettipy --gh https://github.com/user/repo

# Clone a specific branch
prettipy --github https://github.com/user/repo --branch develop
```

## 🐙 GitHub Repository Integration

Prettipy can clone GitHub repositories and convert them to PDF with a single command. This is perfect for:
- Creating offline documentation of open-source projects
- Archiving project code for review or reference
- Sharing code with people who prefer PDF format

### Usage

```bash
# Clone and convert from default branch
prettipy --gh https://github.com/user/repo

# Clone from specific branch
prettipy --gh https://github.com/user/repo --branch develop

# Combine with other options
prettipy --gh https://github.com/user/repo -o project.pdf --sort dependency
```

### Features

- **Automatic Cloning**: Repository is cloned to a temporary directory
- **Branch Support**: Specify any branch with `--branch` or `-b` flag (defaults to repository's default branch)
- **Automatic Cleanup**: Temporary files are automatically removed after conversion
- **Error Handling**: Clear error messages for invalid URLs, missing repos, or network issues

### Examples

```bash
# Convert the popular requests library
prettipy --gh https://github.com/psf/requests -o requests_source.pdf

# Convert a specific branch of Django
prettipy --github https://github.com/django/django -b stable/4.2.x -o django_4.2.pdf

# Convert with custom settings
prettipy --gh https://github.com/user/repo \
  --branch main \
  -o output.pdf \
  --page-size a4 \
  --sort lexicographic \
  -v
```

## 🔗 Auto-linking Feature

Prettipy automatically creates clickable links in the PDF that allow you to navigate from function/variable usage to their declarations. This provides "Go to Definition" style navigation within the PDF document.

### What Gets Linked

- **Function calls** → Function definitions
- **Variable references** → Variable declarations/assignments
- **Class instantiations** → Class definitions

### Example

```python
def calculate_sum(a, b):
    return a + b

result = calculate_sum(5, 10)  # "calculate_sum" is clickable!
```

In the generated PDF, clicking on `calculate_sum` in the second line will jump to its definition on the first line.

### Disabling Auto-linking

If you prefer not to have auto-linking, you can disable it:

```bash
# Command line
prettipy --no-linking

# Configuration file
{
  "enable_linking": false
}

# Python API
config = PrettipyConfig(enable_linking=False)
```

## 📂 File Sorting

Prettipy provides flexible options for sorting files in the generated PDF:

### Sorting Methods

1. **Lexicographic (Alphabetical)** - Default method that sorts files alphabetically by filename
2. **Dependency-Based** - Sorts files based on function call dependencies using topological sort
3. **None** - No sorting, files appear in discovery order

### Dependency-Based Sorting

The dependency sorting method analyzes your Python files to understand which files depend on others:

- Files are treated as nodes in a Directed Acyclic Graph (DAG)
- Dependencies are determined by analyzing function and class calls between files
- Files with no dependencies appear first
- Files that depend on others appear after their dependencies
- When multiple files are at the same dependency level, they are sorted alphabetically
- Uses NetworkX library for robust topological sorting

**Example:**
```bash
# Sort by dependencies - files with dependencies appear after their dependencies
prettipy --sort dependency

# Sort alphabetically (default)
prettipy --sort lexicographic

# No sorting - files in discovery order
prettipy --sort none
```

**Note:** If circular dependencies are detected during dependency sorting, the tool will display a warning and fall back to lexicographic sorting.

### Configuration File

You can also set the sorting method in your configuration file:

```json
{
  "sort_method": "dependency"
}
```

## 📖 Detailed Usage

### Command Line Interface

```bash
usage: prettipy [-h] [-o OUTPUT] [-f FILES [FILES ...]] [-w WIDTH]
                [--config CONFIG] [-t TITLE] [--theme {default}]
                [--page-size {letter,a4}] [--no-linking]
                [--sort {dependency,lexicographic,none}] [-v] [--version]
                [--init-config] [directory]

Convert Python code to beautifully formatted PDFs

positional arguments:
  directory             Directory to scan for Python files (default: current)

optional arguments:
  -h, --help            Show this help message and exit
  -o, --output OUTPUT   Output PDF file path (default: output.pdf)
  -f, --files FILES     Specific Python files to convert
  -w, --width WIDTH     Maximum line width before wrapping (default: 90)
  --config CONFIG       Path to configuration JSON file
  -t, --title TITLE     Custom title for the PDF document
  --theme {default}     Color theme to use
  --page-size {letter,a4}
                        PDF page size (default: letter)
  --no-linking          Disable auto-linking to function/variable definitions
  --sort {dependency,lexicographic,none}
                        File sorting method (default: lexicographic)
  --github, --gh URL    Clone and convert a GitHub repository
  --branch, -b BRANCH   Branch to checkout when cloning (default: repo's default branch)
  -v, --verbose         Enable verbose output
  --version             Show program's version number and exit
  --init-config         Generate a sample configuration file
```

### Examples

#### Convert Current Directory

```bash
prettipy
```

This will create `output.pdf` with all Python files from the current directory.

#### Convert GitHub Repository

```bash
# Clone and convert from default branch
prettipy --gh https://github.com/psf/requests

# Clone from specific branch
prettipy --gh https://github.com/user/repo --branch develop -o output.pdf
```

#### Convert With Custom Settings

```bash
prettipy /path/to/project \
  -o project_code.pdf \
  -w 100 \
  --title "My Awesome Project" \
  --page-size a4
```

#### Convert Specific Files

```bash
prettipy -f main.py utils.py models.py -o core_files.pdf
```

#### Sort Files by Dependencies

```bash
# Automatically organize files so dependencies come before files that use them
prettipy --sort dependency -o organized_code.pdf

# Combine with other options
prettipy /path/to/project --sort dependency --page-size a4 -o sorted_project.pdf
```

#### Use Configuration File

```bash
# Generate sample config
prettipy --init-config

# Edit prettipy-config.json, then use it
prettipy --config prettipy-config.json
```

### Python API

You can also use Prettipy programmatically in your Python code:

```python
from prettipy import PrettipyConverter, PrettipyConfig

# Basic usage with defaults
converter = PrettipyConverter()
converter.convert_directory("./my_project", output="project.pdf")

# Custom configuration
config = PrettipyConfig(
    max_line_width=100,
    page_size='a4',
    title='My Project Documentation',
    sort_method='dependency',  # Sort files by dependencies
    verbose=True
)

converter = PrettipyConverter(config)
converter.convert_directory("./src")

# Convert specific files
converter.convert_files(
    files=['main.py', 'utils.py', 'models.py'],
    output='core.pdf'
)
```

## ⚙️ Configuration

### Configuration File

Generate a sample configuration file:

```bash
prettipy --init-config
```

This creates `prettipy-config.json`:

```json
{
  "exclude_dirs": [
    ".git",
    "venv",
    "__pycache__",
    "node_modules"
  ],
  "exclude_patterns": [],
  "include_patterns": ["*.py"],
  "max_line_width": 90,
  "font_size": 9,
  "line_spacing": 14,
  "page_size": "letter",
  "title": null,
  "show_line_numbers": false,
  "theme": "default",
  "enable_linking": true,
  "sort_method": "lexicographic",
  "output_file": "output.pdf",
  "verbose": false
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `exclude_dirs` | list | See config | Directories to exclude |
| `exclude_patterns` | list | `[]` | File patterns to exclude |
| `include_patterns` | list | `["*.py"]` | File patterns to include |
| `max_line_width` | int | `90` | Max characters before wrapping |
| `font_size` | int | `9` | Font size for code |
| `line_spacing` | int | `14` | Line spacing in points |
| `page_size` | string | `"letter"` | Page size (letter/a4) |
| `title` | string | `null` | PDF title |
| `show_line_numbers` | bool | `false` | Show line numbers (future) |
| `theme` | string | `"default"` | Color theme |
| `enable_linking` | bool | `true` | Enable auto-linking to definitions |
| `sort_method` | string | `"lexicographic"` | File sorting method (dependency/lexicographic/none) |
| `output_file` | string | `"output.pdf"` | Default output path |
| `verbose` | bool | `false` | Verbose output |

## 🎨 Themes

Currently, Prettipy includes a beautiful default theme with GitHub-style syntax highlighting:

- **Keywords**: Green (`#007020`)
- **Functions**: Dark Blue (`#06287e`)
- **Classes**: Teal (`#0e7c7b`)
- **Strings**: Blue (`#4070a0`)
- **Numbers**: Green (`#40a070`)
- **Comments**: Gray-Blue (`#60a0b0`)

More themes coming soon!

## 🛠️ Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/prettipy.git
cd prettipy

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev,rich]"
```

### Run Tests

```bash
pytest
pytest --cov=prettipy  # With coverage
```

### Pre-commit Hooks

Install pre-commit hooks to automatically check code quality before commits:

```bash
# Install pre-commit
pip install pre-commit

# Install the hooks
pre-commit install

# Run manually on all files (optional)
pre-commit run --all-files
```

Pre-commit will automatically run:
- **Black** formatter to ensure consistent code style
- **Pytest** to verify all tests pass

### Code Quality

```bash
# Format code
black .

# Check formatting without changes
black --check .

# Lint
flake8 src/prettipy

# Type checking
mypy src/prettipy
```

### Continuous Integration

GitHub Actions automatically runs on all pushes and pull requests:
- Tests on Python 3.8-3.12
- Black formatting checks
- All checks must pass before merging

## 📦 Building and Publishing

### Build Package

```bash
# Install build tools
pip install build twine

# Build distribution
python -m build
```

This creates files in `dist/`:
- `prettipy-0.1.0-py3-none-any.whl`
- `prettipy-0.1.0.tar.gz`

### Publish to PyPI

```bash
# Test on TestPyPI first
twine upload --repository testpypi dist/*

# Then publish to PyPI
twine upload dist/*
```

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and ensure they pass
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📋 Roadmap

- [ ] Additional color themes (Monokai, Solarized, etc.)
- [ ] Line numbering option
- [ ] Table of contents generation
- [ ] Support for more file types (JavaScript, Java, etc.)
- [ ] Customizable syntax highlighting rules
- [ ] PDF bookmarks for easy navigation
- [ ] Export to other formats (HTML, Markdown)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[ReportLab](https://www.reportlab.com/)** - PDF generation library
- **[Pygments](https://pygments.org/)** - Syntax highlighting
- **[Rich](https://rich.readthedocs.io/)** - Beautiful terminal output

## 📬 Contact

- **Author**: Hyun-Hwan Jeong
- **Email**: hyun-hwan.jeong@bcm.edu
- **GitHub**: [@hyunhwan-bcm](https://github.com/hyunhwan-bcm)

---

Made with ❤️ by developers, for developers.
