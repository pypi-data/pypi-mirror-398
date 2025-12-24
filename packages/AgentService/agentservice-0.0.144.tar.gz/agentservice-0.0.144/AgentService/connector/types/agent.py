
from .meta import TimestampMixin
from .tool import Tool
from .message import Message

from ...enums.agent import AgentResponseType


class AgentResponse(TimestampMixin):
    type: AgentResponseType
    content: str | list[Tool] | list[Message] | dict[str, str]
