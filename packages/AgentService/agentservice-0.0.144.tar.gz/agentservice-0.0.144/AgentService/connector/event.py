
from AgentService.types import Tool
from typing import Any


class BaseEvent:
    data: Any

    def __str__(self):
        fields = ', '.join([
            f"{key}={self.__dict__[key]}"
            for key in self.__dict__ if not key.startswith("__")
        ])

        return f"{self.__class__.__name__}({fields})"


class ToolEvent(BaseEvent):
    def __init__(self, tool_name: str, tool: Tool, chat_id: str):
        self.tool_name = tool_name
        self.tool = tool
        self.chat_id = chat_id
