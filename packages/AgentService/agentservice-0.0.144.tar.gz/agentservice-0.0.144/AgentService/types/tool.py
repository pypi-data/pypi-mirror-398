
from . import Document

from .meta import TimestampMixin


class Tool(TimestampMixin, Document):
    tool_id: str
    name: str
    arguments: str


class ToolAnswer(TimestampMixin, Document):
    tool_id: str
    name: str
    text: str
