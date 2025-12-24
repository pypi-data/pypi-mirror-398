
import asyncio
import enum
import functools
import typing
import aiohttp
import json

from loguru import logger

from .event import ToolEvent

from .types import (
    AgentResponse, Tool,
    ToolAnswer, ChatToolState,
    Message
)

from ..enums.tool import ToolResponse
from ..enums.agent import AgentResponseType

from .models import SendMessageRequest, GetChatRequest


class AgentConnector:
    def __init__(
        self,
        endpoint: str,
        key: str = None
    ):

        self.log = logger.bind(classname=self.__class__.__name__)

        self.endpoint = endpoint[:-1] if endpoint.endswith("/") else endpoint
        self.key = key

        self.callbacks = {}
        self.tools_states_handler = None

    def bind_tool_output(self, tool_name: str, function: typing.Callable):
        self.callbacks.update({tool_name: functools.partial(self.answer_tool, function=function)})
        self.log.debug(f"Binded callback -> {tool_name} -> {function}")

    def bind_tool_states_handler(self, function: typing.Callable):
        self.tools_states_handler = function
        self.log.debug(f"Binded callback -> {function}")

    async def add_to_storage(self, key: str, data: list[dict] | dict):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=f"{self.endpoint}/storage/add",
                json={
                    "key": key,
                    "data": data
                },
                raise_for_status=False
            ) as resp:

                self.log.debug(f"Got response -> {await resp.text()}")
                return await resp.json()

    async def remove_from_storage(self, key: str, data: list[dict] | dict):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=f"{self.endpoint}/storage/remove",
                json={
                    "key": key,
                    "data": data
                },
                raise_for_status=False
            ) as resp:

                self.log.debug(f"Got response -> {await resp.text()}")
                return await resp.json()

    async def update_storage(self, key: str, data: dict, new_data: dict):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=f"{self.endpoint}/storage/update",
                json={
                    "key": key,
                    "data": data,
                    "new_data": new_data
                },
                raise_for_status=False
            ) as resp:

                self.log.debug(f"Got response -> {await resp.text()}")
                return await resp.json()

    async def get_from_storage(self, key: str) -> list[dict]:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=f"{self.endpoint}/storage",
                json={
                    "key": key
                },
                raise_for_status=False
            ) as resp:

                self.log.debug(f"Got response -> {await resp.text()}")
                return await resp.json()

    async def answer_tool(self, event: ToolEvent, function: typing.Callable) -> ToolAnswer:
        try:
            response = await function(data=event.tool.arguments, chat_id=event.chat_id)

            if response in [None, ""]:
                response = "function returned nothing"

            elif isinstance(response, enum.Enum):
                response = response.value

            elif not isinstance(response, str):
                response = str(response)

            return ToolAnswer(
                tool_id=event.tool.tool_id,
                name=event.tool.name,
                text=response
            )

        except Exception as err:
            self.log.exception(err)

            return ToolAnswer(
                tool_id=event.tool.tool_id,
                name=event.tool.name,
                text="function returned nothing"
            )

    async def dispatch_event(self, event: ToolEvent):
        callback = self.callbacks.get(event.tool.name)

        if not callback:
            self.log.warning(f"Can't find callback function \"{event.tool.name}\" in {self.callbacks}")

            return ToolAnswer(
                tool_id=event.tool.tool_id,
                name=event.tool.name,
                text="function not binded"
            )

        while True:
            response: ToolAnswer = await callback(event=event)
            self.log.debug(f"Dispatching event -> {event} -> {callback} -> {response}")

            try:
                ToolResponse[response.text]

            except KeyError:
                break

            await asyncio.sleep(5)

        return response

    async def handle_tools(self, tools: list[Tool], chat_id) -> list[ToolAnswer]:
        tool_answers = [
            await self.dispatch_event(ToolEvent(tool_name=tool.name, tool=tool, chat_id=chat_id))
            for tool in tools
        ]

        return tool_answers

    async def request_post_message(self, request: SendMessageRequest) -> AgentResponse:
        data = json.loads(request.model_dump_json())
        self.log.debug(f"Sending request -> {data}")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=f"{self.endpoint}/chat",
                json=data,
                raise_for_status=False
            ) as resp:

                self.log.debug(f"Got response -> {await resp.text()}")

                response = await resp.json()
                agent_response = AgentResponse(**response["data"])

                return agent_response

    async def request_get_chat(self, request: GetChatRequest) -> AgentResponse:
        self.log.debug(f"Sending request -> {request.model_dump()}")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=f"{self.endpoint}/chat",
                params=request.model_dump(),
                raise_for_status=False
            ) as resp:

                self.log.debug(f"Got response -> {await resp.text()}")

                response = await resp.json()
                agent_response = AgentResponse(
                    type=AgentResponseType.chat,
                    content=response["data"]
                )

                return agent_response

    async def request_get_version(self) -> AgentResponse:
        self.log.debug("Sending request -> {}")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=f"{self.endpoint}/meta/version",
                raise_for_status=False
            ) as resp:

                self.log.debug(f"Got response -> {await resp.text()}")

                response = await resp.json()
                agent_response = AgentResponse(
                    type=AgentResponseType.version,
                    content=response["data"]
                )

                return agent_response

    async def send(self, chat_id: str, text: str = None, context: dict = {}, tool_answers: list[ToolAnswer] = [], is_manual: bool = False) -> AgentResponse:
        agent_response = await self.request_post_message(SendMessageRequest(chat_id=chat_id, text=text, context=context, tool_answers=tool_answers))

        if is_manual:
            return agent_response

        if agent_response.type == AgentResponseType.answer:
            return agent_response

        tool_answers = await self.handle_tools(agent_response.content, chat_id)

        return await self.send(chat_id, tool_answers=tool_answers)

    async def get_chat(self, chat_id: str) -> AgentResponse:
        return await self.request_get_chat(GetChatRequest(chat_id=chat_id))

    async def get_version(self) -> AgentResponse:
        return await self.request_get_version()

    async def send_tool_states(self, tools: list[Tool], chat_id: str):
        tool_answers = await self.handle_tools(tools, chat_id)

        return await self.send(chat_id, tool_answers=tool_answers)

    async def request_tool_states(self) -> tuple[list[ChatToolState], dict]:
        self.log.debug(f"Getting tool states")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=f"{self.endpoint}/chat/states",
                raise_for_status=False
            ) as resp:
                self.log.debug(f"Got response -> {await resp.text()}")

                response = await resp.json()
                tool_states = list(map(lambda x: ChatToolState(**x), response["data"]))

                return tool_states, response["chat_ids"]

    async def with_handler(self, handler: typing.Callable, function: typing.Callable, chat_id: str):
        if not handler:
            self.log.warning(f"No handler provided so skipping...")
            return

        response = await function
        await handler(response, chat_id)

    async def handle_tool_states(self):
        tool_states, chat_ids = await self.request_tool_states()
        tools_by_chat = {}

        for tool_state in tool_states:
            chat_id = chat_ids[tool_state.chat_id]

            if chat_id not in tools_by_chat:
                tools_by_chat[chat_id] = []

            tools_by_chat[chat_id].append(Tool(
                tool_id=tool_state.tool_id,
                name=tool_state.name,
                arguments=tool_state.arguments
            ))

        return await asyncio.gather(*[
            self.with_handler(
                handler=self.tools_states_handler,
                function=self.send_tool_states(tools_by_chat[chat_id], chat_id=chat_id),
                chat_id=chat_id
            )
            for chat_id in tools_by_chat
        ])
