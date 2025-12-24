
from typing import Optional, Dict, List
from pydantic import BaseModel, Field

from ..types import AgentResponse, ChatToolState, ToolAnswer, Message
from ...enums.response import ResposneStatus


class SendMessageRequest(BaseModel):
    chat_id: str
    text: Optional[str] = None
    context: Dict = Field(default_factory=dict)
    tool_answers: List[ToolAnswer] = Field(default_factory=list)


class SendMessageResponse(BaseModel):
    data: Optional[AgentResponse] = None
    description: Optional[str] = None
    status: ResposneStatus


class GetStatesRequest(BaseModel):
    chat_id: str


class GetStatesResponse(BaseModel):
    data: list[ChatToolState] = Field(default_factory=list)
    description: Optional[str] = None
    status: ResposneStatus


class GetChatRequest(BaseModel):
    chat_id: str


class GetChatResponse(BaseModel):
    data: list[Message] = Field(default_factory=list)
    description: Optional[str] = None
    status: ResposneStatus
