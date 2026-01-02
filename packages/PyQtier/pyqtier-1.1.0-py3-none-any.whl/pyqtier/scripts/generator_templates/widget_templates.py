INIT = '''from .main_window import MainWindow
from .settings_window import SettingsWindow
from .about_window import AboutWindow

'''

ABOUT_WINDOW = '''from pyqtier.widgets import PyQtierWidgetBase


class AboutWindow(PyQtierWidgetBase):
    def setup_view(self):
        self.setWindowTitle("About App")
        self.view.lb_app_name.setText(self.configs.APP_NAME)
        self.view.lb_app_version.setText(self.configs.APP_VERSION)
        self.view.lb_company_name.setText(self.configs.COMPANY_NAME)

'''

MAIN_WINDOW = '''from pyqtier.widgets import PyQtierMainWindow
from PyQt5.QtCore import pyqtSignal


class MainWindow(PyQtierMainWindow):
    open_settings = pyqtSignal()
    open_about = pyqtSignal()

    def create_behavior(self):
        self.view.actionSettings.triggered.connect(self.open_settings.emit)
        self.view.actionAbout.triggered.connect(self.open_about.emit)

'''

SETTINGS_WINDOW = '''from pyqtier.widgets import PyQtierWidgetBase


class SettingsWindow(PyQtierWidgetBase):
    ...

'''
