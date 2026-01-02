import sys
from typing import Optional

from PyQt5 import QtWidgets
from .widgets import PyQtierMainWindow


class PyQtierApplicationManager:
    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.main_window: Optional[PyQtierMainWindow] = None

        self.setup_manager()
        self.create_behaviour()

    def setup_manager(self):
        ...

    def create_behaviour(self):
        ...
    def show_main_window(self, show_maximized=False, show_full_screen=False):
        if show_maximized:
            self.main_window.showMaximized()
        if show_full_screen:
            self.main_window.showFullScreen()

        self.main_window.show()
        sys.exit(self.app.exec_())
