
from .meta import TimestampMixin

from ...enums.chat import ChatStatus, ChatToolStateStatus


class Chat(TimestampMixin):
    chat_id: str
    status: ChatStatus = ChatStatus.created
    data: dict


class ChatToolState(TimestampMixin):
    chat_id: str
    status: ChatToolStateStatus = ChatToolStateStatus.in_progress
    tool_id: str
    name: str
    arguments: str
