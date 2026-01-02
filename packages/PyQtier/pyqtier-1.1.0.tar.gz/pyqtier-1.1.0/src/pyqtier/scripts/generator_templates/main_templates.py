MAIN = '''# !/usr/bin/env python
"""
Utility for running PyQtier desktop applications.
"""

from app import ApplicationManager


def main():
    try:
        from PyQt5 import QtCore
    except ImportError as exc:
        raise ImportError("Couldn't import PyQt5. Are you sure it's installed?") from exc
    am = ApplicationManager()
    am.show_main_window()


if __name__ == '__main__':
    main()

'''
