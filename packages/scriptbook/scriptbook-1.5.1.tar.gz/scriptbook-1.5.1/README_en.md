# Scriptbook - Executable Markdown Server

[中文](README.md)

An online Markdown server with script execution support. Inspired by Jupyter Notebook, it allows embedding and running scripts directly within Markdown documents, making it ideal for SOP (Standard Operating Procedure) automation and interactive documentation.

## Features

- **Interactive Documents** - Embed executable scripts in Markdown, similar to Jupyter Notebook
- **Interactive Input** - Support user input during script execution (e.g., `read` command)
- **Real-time Execution** - WebSocket-based real-time script output streaming
- **Independent Output** - Each script block has its own output area below
- **Result Persistence** - Auto-restore script execution results after page refresh (localStorage)
- **Stop Execution** - Support terminating running scripts anytime
- **Multi-document Support** - Switch between multiple documents, results saved independently
- **Theme Switching** - Support for light, dark, and GitHub themes
- **Terminal Themes** - Terminal colors match theme style
- **ANSI Color Support** - Script output colors and formatting displayed correctly in browser
- **Navbar Layout** - Top navigation bar with file selection and theme switching
- **GitHub Link** - GitHub repository link in top-right corner
- **xterm.js Terminal** - Professional terminal emulator for script output rendering
- **WebSocket Optimization** - Improved concurrency handling, supports page refresh scenarios
- **SOP Automation** - Ideal for displaying and executing enterprise standard operating procedures
- **Comprehensive Testing** - Includes 192 unit and integration tests

## Screenshot

![Scriptbook Interface](docs/screenshot-2025-12-25.png)

## Quick Start

### Requirements
- Python 3.10+
- Modern browser

### Installation

```bash
# Direct installation (recommended)
pip install scriptbook

# Or install from source
git clone https://github.com/lengmoXXL/scriptbook.git
cd scriptbook
pip install .
```

### Usage

```bash
# Start the server (using default content directory)
scriptbook content/

# Specify a custom document directory
scriptbook /path/to/my/documents/

# Specify a port
scriptbook content/ --port 9000

# Allow external access
scriptbook content/ --host 0.0.0.0

# Access the application
open http://localhost:8000
```

**Note**: After modifying the code, please restart the server manually to apply changes.

## Package Information

### PyPI Installation

```bash
pip install scriptbook
```

**PyPI Link**: https://pypi.org/project/scriptbook/

### Version

- Current Version: 1.5.1
- Python Requirement: >=3.10

### Changelog

#### v1.5.1 (2025-12-26)
- **Terminal Output Scrollbar Optimization**
  - Fixed multiple scrollbars display issue
  - Terminal output now shows only one scrollbar
  - Terminal content auto-expands, scrollbar enabled at 400px height

#### v1.5.0 (2025-12-25)
- **New Theme: GitHub Style**
  - Added GitHub style theme with consistent Markdown rendering
  - Optimized code blocks, tables, blockquotes, etc.
- **Terminal Theme Integration**
  - Terminal colors match theme style
  - Terminal theme config via plugin manifest.json
- **Theme System Refactoring**
  - Unified theme naming (theme-light, theme-dark, theme-github)
  - Plugin system supports terminal theme config
- **Navbar Layout Optimization**
  - Top navigation bar with file selection and theme switching
  - Removed standalone controls area
  - Added GitHub repository link icon
- **Code Cleanup**
  - Removed "Markdown Preview" title
  - Simplified footer content

#### v1.4.4 (2025-12-25)
- **Python 3.10 Compatibility Fix**
  - Use `asyncio.wait_for` instead of `asyncio.timeout`
  - Fix async generator timeout handling

#### v1.4.3 (2025-12-25)
- **PTY Support** - Fixed Python 3.10~3.14 compatibility
  - Use `pty.openpty()` instead of removed `pty` parameter
  - Support `tty` command and TTY-required commands (e.g., `docker exec -it`)
- **Code Refactoring** - Refactored `script_executor.py`
  - Extracted `_cleanup()` method for simpler resource cleanup
  - Use `asyncio.wait_for` instead of `asyncio.timeout` for Python 3.10 support
- **Test Enhancement** - Added TTY command integration test

#### v1.4.2 (2025-12-24)
- **xterm.js Canvas Renderer** - Switched from DOM to Canvas renderer
  - Fixed scrolling issues, smoother scrolling experience
  - Terminal background matches page theme
  - Terminal automatically changes color when theme switches
- **Bug Fixes**
  - Fixed xterm.css issues, downloaded correct stylesheet
  - Fixed xterm.js gray background issue
  - Fixed terminal color not changing when theme switches
  - Fixed terminal initialization as white in dark theme
- **Code Cleanup** - Removed deprecated styles and debug code

#### v1.4.0 (2025-12-24)
- **xterm.js Embedded Terminal** - Professional terminal emulator for script output rendering
  - Full ANSI escape sequence support
  - Better terminal experience (scroll, select, copy)
  - Light theme adaptation (#f5f5f5 background + #333333 text)
  - Color coding: stdout (no color), stderr (red), stdin (cyan), exit (yellow)
- **Technical Improvements**
  - Added `terminal-manager.js` terminal manager class
  - Added `lib/xterm.js` and `lib/xterm.css`
  - Removed deprecated `ansi-html.js` and `ansi-parser.js`
- **Testing Enhancement** - Added 26 TerminalManager unit tests

#### v1.3.1 (2025-12-23)
- **Bug Fixes**
  - Theme persistence on page refresh
  - Document persistence on page refresh
  - Added version query params to JS/CSS to prevent browser caching issues
- **Code Optimization**
  - Removed redundant imports
  - Added `_timestamp()` helper function
  - Added cache TTL (60s) to plugin manager

#### v1.3.0 (2025-12-22)
- **ANSI Escape Sequence Parsing** - Script output colors and formatting displayed correctly
  - Support for 16 basic colors (black, red, green, yellow, blue, purple, cyan, white)
  - Support for bold, italic, underline, inverse formatting
  - Support for `\x1b[]`, `\033[]`, and `[]` format ANSI sequences

#### v1.2.0 (2025-12-22)
- **Documentation** - Added release process and project structure documents

#### v1.1.0 (2025-12-22)
- **Script Result Persistence** - Auto-restore results after page refresh
- **Stop Script Execution** - Terminate running scripts with stop button
- **WebSocket Concurrency** - Improved connection handling for page refresh

#### v1.0.0 (2025-12-21)
- Initial release with interactive input and WebSocket streaming

### License

MIT License

### GitHub Repository

- Source Code: https://github.com/lengmoXXL/scriptbook
- Issues: https://github.com/lengmoXXL/scriptbook/issues

## Testing

This project includes a comprehensive test suite with a total of 192 test cases.

### Run All Tests

```bash
# Run all tests (unit tests + integration tests)
pytest src/ src/integration_tests/ -v

# JavaScript tests
cd src/tests/js
npm test
```

### Test Coverage

- **JavaScript Tests**: 109 test cases (using Jest + JSDOM)
  - TerminalManager: 26 tests
  - Plugin Loader: 16 tests
  - Script Results Persistence: 9 tests
  - Script Results Persistence Integration: 7 tests
  - WebSocket Concurrency: 8 tests
  - Script Stop Functionality: 12 tests
  - App Class: 25 tests
- **Python Unit Tests**: 70 test cases
- **Integration Tests**: 13 test cases
- **Total Tests**: 192, all passing

## Development Guide

### Local Development

```bash
# Clone the repository
git clone https://github.com/lengmoXXL/scriptbook.git
cd scriptbook

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .
pip install -r requirements-test.txt

# Install JavaScript test dependencies (only needed for testing)
cd src/tests/js
npm install

# Return to root directory
cd /path/to/scriptbook

# Run all tests
pytest src/ src/integration_tests/ -v
```

### Publish to PyPI

```bash
# Build the package
python -m build

# Upload to PyPI
twine upload dist/*
```

Or use GitHub Actions for automated publishing.

---

**Scriptbook** - Making documents easier to understand and execute
