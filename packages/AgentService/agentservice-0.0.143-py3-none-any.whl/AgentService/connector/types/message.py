
from .meta import TimestampMixin
from .tool import Tool, ToolAnswer

from ...enums.message import MessageType


class Message(TimestampMixin):
    chat_id: str
    type: MessageType
    text: str | None = None
    tools: list[Tool] | None = None
    tool_answer: ToolAnswer | None = None

    @property
    def openai_model_dump(self) -> dict:
        if self.type == MessageType.tools:
            return [
                {
                    "type": "function_call",
                    "call_id": tool.tool_id,
                    "name": tool.name,
                    "arguments": tool.arguments
                }
                for tool in self.tools
            ]

        elif self.type == MessageType.tool_answer:
            return {
                "type": "function_call_output",
                "call_id": self.tool_answer.tool_id,
                "output": self.tool_answer.text
            }

        elif self.type == MessageType.assistant_skip:
            return {
                "role": "assistant",
                "content": self.text
            }

        else:
            return {
                "role": self.type.value,
                "content": self.text
            }

