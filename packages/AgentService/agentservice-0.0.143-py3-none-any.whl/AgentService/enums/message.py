
import enum


class MessageType(enum.Enum):
    system = "system"
    user = "user"
    assistant = "assistant"
    assistant_skip = "assistant_skip"
    tools = "tools"
    tool_answer = "tool_answer"
