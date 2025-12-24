
import enum


class AgentResponseType(enum.Enum):
    tools = "tools"
    answer = "answer"
    chat = "chat"
    version = "version"
