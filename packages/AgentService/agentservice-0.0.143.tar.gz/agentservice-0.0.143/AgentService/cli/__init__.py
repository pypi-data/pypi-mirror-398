
from . import create
from . import start
from . import tool

from . import create_nocode
from . import start_nocode

from . import image

import click
import os

from AgentService.utils.templates import is_project
from AgentService.utils.logger import setup_logger
from AgentService.config import Config


__execute = click.CommandCollection(
    sources=[
        create.group,
        create_nocode.group,
        image.group
    ],
    help='Use "agent <command> -h/--help" to see more info about a command',
)

__execute_project = click.CommandCollection(
    sources=[
        tool.group,
        start.group
    ],
    help='Use "python3.11 manage.py <command> -h/--help" to see more info about a command',
)

__execute_project_nocode = click.CommandCollection(
    sources=[
        start_nocode.group
    ],
    help='Use "python3.11 manage.py <command> -h/--help" to see more info about a command',
)


def execute():
    __execute()


def execute_project():
    current_path = os.getcwd()
    if not is_project(current_path):
        print(f'Error: no AgentService project found in {current_path}')
        return

    config = Config(current_path)
    setup_logger(config.log_path, config.log_level)

    if config.is_nocode:
        __execute_project_nocode()

    else:
        __execute_project()
