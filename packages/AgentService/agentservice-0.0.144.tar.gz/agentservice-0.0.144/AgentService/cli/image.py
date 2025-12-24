
import click
import subprocess
import os
from importlib.metadata import version

import AgentService


@click.group()
def group():
    pass


@group.command('image', help="Command that creates docker image")
def update_image():
    image_dir = os.path.join(AgentService.__path__[0], "templates", "agent-image")
    dockerfile_tmpl = os.path.join(image_dir, "Dockerfile.tmpl")
    dockerfile = os.path.join(image_dir, "Dockerfile")

    with open(dockerfile_tmpl, "r") as f:
        text = f.read()

    with open(dockerfile, "w") as f:
        f.write(text.format(version=version("AgentService")))

    subprocess.run(
        "docker build -t agentservice-base .",
        shell=True,
        text=True,
        cwd=image_dir
    )
