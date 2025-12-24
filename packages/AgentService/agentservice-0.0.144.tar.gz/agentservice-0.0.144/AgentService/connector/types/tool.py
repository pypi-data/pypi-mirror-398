
from .meta import TimestampMixin


class Tool(TimestampMixin):
    tool_id: str
    name: str
    arguments: str


class ToolAnswer(TimestampMixin):
    tool_id: str
    name: str
    text: str
