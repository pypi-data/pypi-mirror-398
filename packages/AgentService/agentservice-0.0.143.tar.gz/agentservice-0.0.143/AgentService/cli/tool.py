
import AgentService
from AgentService.utils.templates import process_template


import click
import os
from shutil import copy


@click.group()
def group():
    pass


@group.command('add_tool', help="Command to add the tool to AgentService project")
@click.argument('tool', type=str)
@click.option('-t', '--template', default="default")
def add_middleware(tool: str, template: str):
    current_path = os.getcwd()
    templates_dir = os.path.join(AgentService.__path__[0], "templates", "tool")

    tool_path = os.path.join(current_path, "tools", tool.lower())
    if os.path.isdir(tool_path):
        return print(f"Error: tool {tool} has already been added in {tool_path}")

    tool_template = os.path.join(templates_dir, f"{template}.py.tmpl")
    if not os.path.isfile(tool_template):
        return print(f"Error: no such template {template}")

    new_tool_path = os.path.join(current_path, "tools", f"{tool.lower()}.py.tmpl")
    copy(tool_template, new_tool_path)

    process_template(new_tool_path, tool_name=tool.capitalize())

    init_file = os.path.join(current_path, "tools", "__init__.py")
    with open(init_file, "a") as f:
        f.write(f"from .{tool.lower()} import {tool.capitalize()}Tool\n")

    return print(f"Added {tool.capitalize()}Tool in {new_tool_path}")
