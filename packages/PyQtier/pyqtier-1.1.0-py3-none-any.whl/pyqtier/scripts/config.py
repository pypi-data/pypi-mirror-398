from pathlib import Path

# Root dir of our project
ROOT_DIR = Path.cwd()

# Main folder with all project's files
APP_DIR = ROOT_DIR / 'app'

# Placing of project's widgets
WIDGETS_DIR = APP_DIR / 'widgets'

# Placing of view files which created by pyuic5
VIEWS_DIR = APP_DIR / 'views'

# Placing of .ui files which created by Qt Designer
UI_DIR = VIEWS_DIR / 'templates'

IMG_DIR = UI_DIR / 'img'

# Placing of .qrc files and images
RESOURCES_DIR = UI_DIR

# Structure of project's directories
DIRS_OF_PROJECT = [
    APP_DIR,
    WIDGETS_DIR,
    VIEWS_DIR,
    UI_DIR
]
