
from . import Document
from beanie.odm.documents import PydanticObjectId

from .meta import TimestampMixin

from ..enums.chat import ChatStatus, ChatToolStateStatus


class Chat(TimestampMixin, Document):
    chat_id: str
    status: ChatStatus = ChatStatus.created
    data: dict


class ChatToolState(TimestampMixin, Document):
    chat_id: PydanticObjectId
    status: ChatToolStateStatus = ChatToolStateStatus.in_progress
    tool_id: str
    name: str
    arguments: str
