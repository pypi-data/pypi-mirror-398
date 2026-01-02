from PyQt5.QtWidgets import QWidget, QMainWindow
from PyQt5.QtCore import QSettings, QResource
from PyQt5.QtGui import QIcon


class PyQtierBase:
    def __init__(self, view_class, configs):
        self.view = view_class()
        self.view.setupUi(self)
        self.settings = QSettings(configs.COMPANY_SHORT_NAME, configs.APP_SHORT_NAME)
        self.settings.beginGroup(self.__class__.__name__)
        self.configs = configs
        self.setup_view()
        self.create_behavior()

    def setup_view(self):
        ...

    def create_behavior(self):
        ...

    def closeEvent(self, event):
        self.settings.setValue("geometry", self.saveGeometry())
        self._save_additional_state()
        event.accept()

    def showEvent(self, event):
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        self._restore_additional_state()
        event.accept()

    def _save_additional_state(self):
        pass

    def _restore_additional_state(self):
        pass


class PyQtierWidgetBase(PyQtierBase, QWidget):
    def __init__(self, view_class, config, parent=None):
        QWidget.__init__(self, parent)
        PyQtierBase.__init__(self, view_class, config)


class PyQtierMainWindow(PyQtierBase, QMainWindow):
    def __init__(self, view_class, config):
        QMainWindow.__init__(self)
        PyQtierBase.__init__(self, view_class, config)
        self.setWindowTitle(config.APP_NAME)

    def _save_additional_state(self):
        self.settings.setValue("state", self.saveState())

    def _restore_additional_state(self):
        state = self.settings.value("state")
        if state:
            self.restoreState(state)
