
import fastapi

from beanie.operators import And

from AgentService.config import Config

from AgentService.types.chat import ChatToolState, Chat
from AgentService.types.message import Message
from AgentService.enums.chat import ChatToolStateStatus

from .models import (
    SendMessageRequest, SendMessageResponse,
    GetStatesRequest, GetStatesResponse,
    GetChatRequest, GetChatResponse
)


chat_router = fastapi.APIRouter(prefix="/chat")


@chat_router.post("")
async def send_message(request: SendMessageRequest) -> SendMessageResponse:
    agent = Config().agent

    response = await agent.answer(
        chat_id=request.chat_id,
        text=request.text,
        context=request.context,
        tool_answers=request.tool_answers
    )

    return SendMessageResponse(
        data=response,
        status="ok"
    )


@chat_router.get("")
async def get_chat(chat_id: str) -> GetChatResponse:
    agent = Config().agent

    chat = await agent.get_chat(chat_id=chat_id, create=False)
    if not chat:
        return GetChatResponse(
            data=[],
            status="ok"
        )

    messages = await Message.find_many(Message.chat_id == chat.id).to_list()

    return GetChatResponse(
        data=messages,
        status="ok"
    )


@chat_router.get("/states")
async def get_states() -> GetStatesResponse:
    states = await ChatToolState.find_many(ChatToolState.status == ChatToolStateStatus.in_progress).to_list()

    chat_ids = {}
    for state in states:
        chat = await Chat.find_one(Chat.id == state.chat_id)
        chat_ids.update({str(state.chat_id): chat.chat_id})

    return GetStatesResponse(
        data=states,
        chat_ids=chat_ids,
        status="ok"
    )


@chat_router.get("/state")
async def get_state(request: GetStatesRequest) -> GetStatesResponse:
    chat = await Chat.find_one(Chat.chat_id == request.chat_id)

    if not chat:
        return GetStatesResponse(
            description=f"Can't find such chat {request.chat_id}",
            status="error"
        )

    states = await ChatToolState.find_many(
        And(
            ChatToolState.chat_id == chat.id,
            ChatToolState.status == ChatToolStateStatus.in_progress
        )
    ).to_list()

    return GetStatesResponse(
        data=states,
        status="ok"
    )
