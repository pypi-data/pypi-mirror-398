MANAGER = '''from app import config
from app.views import Ui_MainWindow, Ui_SimpleView, Ui_AboutView
from app.widgets import MainWindow, SettingsWindow, AboutWindow
from pyqtier import PyQtierApplicationManager


class ApplicationManager(PyQtierApplicationManager):
    def setup_manager(self):
        self.main_window = MainWindow(view_class=Ui_MainWindow, config=config)
        self.settings_window = SettingsWindow(view_class=Ui_SimpleView, config=config)
        self.about_window = AboutWindow(view_class=Ui_AboutView, config=config)

    def create_behaviour(self):
        self.main_window.open_settings.connect(self.settings_window.show)
        self.main_window.open_about.connect(self.about_window.show)

'''

MANAGER_INIT = '''from .app_manager import ApplicationManager

__all__ = ['ApplicationManager']

'''
