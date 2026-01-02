from pathlib import Path
import shutil
import click

from .generator_templates import TEMPLATES
from .converter import convert_ui_to_py
from .config import *


def create_project(project_name: str, project_path: str = '.'):
    """
    Generate a new PyQtier project structure
    Args:
        :param project_name: name of the folder where the project will be created
        :param project_path:
    """
    project_path = Path(project_name)

    # Create main project directory
    project_path.mkdir(exist_ok=True)

    # Create directories structure
    for directory in DIRS_OF_PROJECT:
        dir_path = project_path / directory
        dir_path.mkdir(parents=True, exist_ok=True)

    # Create files from templates
    for file_path, content in TEMPLATES.items():
        full_path = project_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)

    # Copy img folder
    img_source = Path(__file__).parent / 'generator_templates' / 'img'
    img_destination = project_path / IMG_DIR

    if img_source.exists():
        shutil.copytree(img_source, img_destination, dirs_exist_ok=True)
        click.echo('Images copied successfully!')
    else:
        click.echo('Warning: Image templates folder not found')
    click.echo(f'Created PyQtier project: {project_name}')

    click.echo(f'\nConverting templates...')
    convert_ui_to_py(auto_convert_qrc=True)

    click.echo('\nProject structure created successfully!')
    if project_name != '.':
        click.echo('\nTo get started:')
        click.echo(f'  cd {project_name}')
