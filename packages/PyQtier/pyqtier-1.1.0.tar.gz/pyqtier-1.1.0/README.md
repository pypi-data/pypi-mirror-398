# PyQtier

PyQtier is a command-line tool and architecture solution that helps you work with PyQt5 projects simpler and faster,
providing convenient commands for project creation, UI file conversion, and Qt Designer integration.

![screenshot_1.png](docs/img/screenshot_1.png)

## Features

- Command-line interface for project management
- Built-in GUI application with modern interface
- Qt Designer integration
- Automatic UI and resource file conversion
- Project scaffolding and architecture solutions

## Installation

```bash
pip install pyqtier
```

## Commands

> **Note:** You can use `pyqtier` or shorter `pqr` command to run the commands.

### Start a New Project

Create a new PyQt5 project structure:

```bash
pyqtier startproject PROJECT_NAME
```

- `PROJECT_NAME`: Name and path of your project. Use `.` to create the project in the current directory.

### Open Qt Designer

Launch Qt Designer for creating UI files:

```bash
pyqtier designer
```

Note: Requires `qt5-tools` to be installed on your system.

### Convert UI Files

Convert Qt Designer `.ui` files to Python `.py` files:

```bash
# Convert all .ui files in the project
pyqtier convertui

# Convert a specific .ui file
pyqtier convertui filename.ui

# Convert .ui files and automatically convert associated .qrc files
pyqtier convertui --autorc
```

### Convert Resource Files

Convert Qt resource `.qrc` files to Python `.py` files:

```bash
# Convert all .qrc files in the project
pyqtier convertqrc

# Convert a specific .qrc file
pyqtier convertqrc filename.qrc
```

## Examples

1. Create a new project:
   ```bash
   pyqtier startproject .
   ```

2. Design your UI:
   ```bash
   pyqtier designer
   ```

3. Convert UI and resource files:
   ```bash
   # Convert all UI files and automatically convert QRC files
   pyqtier convertui --autorc
   
   # Convert a specific UI file
   pyqtier convertui main_window.ui
   
   # Convert a specific resource file
   pyqtier convertqrc resources.qrc
   ```

## Requirements

- Python 3.x
- PyQt5
- qt5-tools (for Qt Designer)
- click (for CLI interface)

## License

**MIT**


