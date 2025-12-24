
import configparser
import json
import os
import importlib

from AgentService.utils.singleton import SingletonMeta
from AgentService.agent import Agent


class Config(metaclass=SingletonMeta):
    def __init__(self, project_path):
        config_path = os.path.join(project_path, "agent.cfg")
        config = configparser.ConfigParser()
        config.read(config_path)

        self.agent = None
        self.agent_data = None
        self.tools_data = None
        self.secrets_data = None
        self.is_nocode = False

        if os.path.isfile("agent.json"):
            data = json.load(open("agent.json", "r"))

            self.agent_data = data["agent"]
            self.tools_data = data["tools"]
            self.secrets_data = data["secrets"]
            self.is_nocode = True

        self.project_name = config["project"]["name"]
        self.agent_path = config["project"]["agent_source"]
        self.tools_path = config["project"]["tools_source"]
        self.app_host = config["app"]["host"]
        self.app_port = int(config["app"]["port"])
        self.log_level = config["logging"]["level"]
        self.log_path = config["logging"]["path"]

        if self.is_nocode:
            self.openai_key = self.secrets_data.get("openai_key")
            self.db_name = self.secrets_data.get("db_name", "AgentService")
            self.db_uri = self.secrets_data.get("db_uri")

        else:
            importlib.import_module(self.agent_path)
            importlib.import_module(self.tools_path)

            self.openai_key = os.getenv("openai_key")
            self.db_name = os.getenv("db_name", default="AgentService")
            self.db_uri = os.getenv("db_uri")

    def set_agent(self, agent: Agent):
        self.agent = agent
