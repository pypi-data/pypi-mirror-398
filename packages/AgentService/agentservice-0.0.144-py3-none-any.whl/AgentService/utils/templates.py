
from string import Template
from os import rename
import os
import re


def is_project_name(project_name: str) -> bool:
    return not re.search(r'^[_a-zA-Z]\w*$', project_name) is None


def is_project(project_path: os.PathLike) -> bool:
    return os.path.isfile(os.path.join(project_path, "agent.cfg"))


def process_template(path, **kwargs):
    with open(path, "rb") as f:
        raw = f.read().decode("utf8")

    content = Template(raw).substitute(**kwargs)

    new_path = path[:-len('.tmpl')] if path.endswith(".tmpl") else path

    if path.endswith(".tmpl"):
        rename(path, new_path)

    with open(new_path, "wb") as f:
        f.write(content.encode("utf8"))
