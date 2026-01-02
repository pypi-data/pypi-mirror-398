from typing import Dict, Optional

from PyQt5.QtWidgets import QWidget, QStatusBar


class PyQtierPlugin:
    def __init__(self):
        self._name: str = self.__class__.__name__
        self._version: str = "0.1"
        self._description: str = ""
        self._widgets: Dict[str, QWidget] = {}

        self._ui = None
        self._widget: Optional[QWidget] = None
        self._statusbar: Optional[QStatusBar] = None

    def setup_view(self, widget: QWidget, statusbar: QStatusBar = None):
        if not isinstance(widget, QWidget):
            raise TypeError("Widget must be of type QWidget")

        if not isinstance(statusbar, QStatusBar):
            raise TypeError("Widget must be of type QStatusBar")

        self._widget = widget
        self._statusbar = statusbar
        self._ui.setupUi(self._widget)

    def create_behavior(self):
        ...

    @property
    def name(self):
        return self._name

    @property
    def version(self):
        return self._version

    @property
    def description(self):
        return self._description
