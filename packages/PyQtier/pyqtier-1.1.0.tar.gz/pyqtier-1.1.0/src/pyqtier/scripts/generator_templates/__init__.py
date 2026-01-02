from .main_templates import MAIN
from .manager_templates import MANAGER, MANAGER_INIT
from .config_templates import CONFIG
from .widget_templates import MAIN_WINDOW, ABOUT_WINDOW, SETTINGS_WINDOW, INIT
from .views_templates import INIT_VIEWS
from .ui_templates import ABOUT_WINDOW_INTERFACE_UI, MAIN_WINDOW_INTERFACE_UI, SIMPLE_INTERFACE_UI
from .resources_templates import RESOURCES_QRC
from ..config import *

# Creating relative imports
app_dir = APP_DIR.relative_to(ROOT_DIR)
widgets_dir = WIDGETS_DIR.relative_to(ROOT_DIR)
views_dir = VIEWS_DIR.relative_to(ROOT_DIR)
ui_dir = UI_DIR.relative_to(ROOT_DIR)

TEMPLATES = {
    "main.py": MAIN,

    str(app_dir / "__init__.py"): MANAGER_INIT,
    str(app_dir / "app_manager.py"): MANAGER,
    str(app_dir / "config.py"): CONFIG,

    str(widgets_dir / "__init__.py"): INIT,
    str(widgets_dir / "about_window.py"): ABOUT_WINDOW,
    str(widgets_dir / "main_window.py"): MAIN_WINDOW,
    str(widgets_dir / "settings_window.py"): SETTINGS_WINDOW,

    str(views_dir / "__init__.py"): INIT_VIEWS,

    str(ui_dir / "about_window_interface.ui"): ABOUT_WINDOW_INTERFACE_UI,
    str(ui_dir / "main_window_interface.ui"): MAIN_WINDOW_INTERFACE_UI,
    str(ui_dir / "simple_interface.ui"): SIMPLE_INTERFACE_UI,
    str(ui_dir / "resources.qrc"): RESOURCES_QRC,
}
