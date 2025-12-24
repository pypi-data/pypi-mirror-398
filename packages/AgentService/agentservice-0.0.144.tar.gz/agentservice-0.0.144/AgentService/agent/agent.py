
import json
from loguru import logger
from beanie.operators import And, In

from openai import AsyncOpenAI
from openai.types.responses import ResponseFunctionToolCall, ResponseOutputMessage, ResponseOutputText

from AgentService.types import (
    Chat, ChatToolState,
    AgentResponse, Message,
    Storage, StorageItem,
    Tool, ToolAnswer
)

from AgentService.enums.chat import ChatStatus, ChatToolStateStatus
from AgentService.enums.agent import AgentResponseType
from AgentService.enums.message import MessageType

from AgentService.agent.tool import AgentTool


class Agent:
    model: str = "gpt-4.1-nano"
    temperature: float = 1.0
    max_tokens: int = 2048
    top_p: float = 1.0

    instructions: str = "You are a helpful assistant"

    system_prompts: list[str] = []
    prompt: str = "{text}"

    is_one_shot: bool = False

    def __init__(
        self,
        openai_key: str,
        tools: list[AgentTool] = None
    ):

        self.log = logger.bind(classname=self.__class__.__name__)

        self.client = AsyncOpenAI(api_key=openai_key)

        self.tools = tools if tools else []
        self.tools_schema = [tool.openai_model_dump for tool in self.tools]

        self.system_prompts = list(map(lambda x: x.replace("\t", ""), self.system_prompts))
        self.instructions = self.instructions.replace("\t", "")

        self.log.debug(f"Created gpt like tools -> {self.tools_schema}")

    async def __system_prompt(self, i: int, context: dict) -> str:
        return self.system_prompts[i].format(**context)

    async def __prompt(self, text: str, context: dict) -> str:
        return self.prompt.format(text=text, **context)

    async def __generate(self, chat: Chat) -> AgentResponse:
        chat.status = ChatStatus.generating
        await chat.save()

        messages = await Message.find_many(Message.chat_id == chat.id).to_list()

        gpt_messages = []
        for message in messages:
            data = message.openai_model_dump

            if isinstance(data, list):
                for row in data:
                    gpt_messages.append(row)

            else:
                gpt_messages.append(data)

        tools_schema = self.tools_schema[:]

        storage_item = await StorageItem.find_one()
        if storage_item:
            storages = await Storage.find_many().to_list()
            limited_storages = storages[:2]

            if len(storages) > 2:
                self.log.warning(f"Filtered out storages (2 max) -> {storages[2:]}")

            tools_schema.append(
                {
                    "type": "file_search",
                    "vector_store_ids": list(map(lambda x: x.vector_store_id, limited_storages))
                }
            )

        try:
            response = await self.client.responses.create(
                model=self.model,
                input=gpt_messages,
                instructions=self.instructions,
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
                top_p=self.top_p,
                tools=tools_schema,
                tool_choice="auto"
            )

        except Exception as err:
            self.log.debug(json.dumps(gpt_messages, indent=2, ensure_ascii=False))
            self.log.debug(json.dumps(tools_schema, indent=2, ensure_ascii=False))

            raise err

        responses = []
        for i in response.output:
            if i.__class__ not in [ResponseFunctionToolCall, ResponseOutputMessage]:
                self.log.warning(f"Unsupported response type -> {i.__class__}")
                continue

            responses.append(i)

        new_responses = []
        if len(responses) != 1:
            for i in responses:
                if i.__class__ in [ResponseFunctionToolCall]:
                    new_responses.append(i)

            responses = new_responses[0]

        if len(responses) == 0:
            self.log.debug(json.dumps(response.model_dump(), indent=2, ensure_ascii=False))
            raise TypeError(f"Got 0 responses -> {responses}")

        if isinstance(responses[0], ResponseFunctionToolCall):
            tools = [
                Tool(
                    tool_id=i.call_id,
                    name=i.name,
                    arguments=i.arguments
                )
                for i in responses
            ]

            states = [
                ChatToolState(
                    chat_id=chat.id,
                    status=ChatToolStateStatus.in_progress,
                    tool_id=tool.tool_id,
                    name=tool.name,
                    arguments=tool.arguments
                )
                for tool in tools
            ]

            await ChatToolState.insert_many(states)

            return AgentResponse(
                type=AgentResponseType.tools,
                content=tools
            )

        elif isinstance(responses[0], ResponseOutputMessage):
            texts = []
            for i in responses:
                for j in i.content:
                    if j.__class__ not in [ResponseOutputText]:
                        self.log.warning(f"Unsupported content type -> {j.__class__}")
                        continue

                    texts.append(j.text)

            return AgentResponse(
                type=AgentResponseType.answer,
                content="\n\n".join(texts)
            )

        else:
            self.log.debug(json.dumps(response.model_dump(), indent=2, ensure_ascii=False))
            raise TypeError(f"Unsupported response type -> {responses[0]}")

    async def generate(self, chat: Chat) -> AgentResponse:
        try:
            return await self.__generate(chat)

        except Exception as err:
            self.log.exception(err)

            return AgentResponse(
                type=AgentResponseType.answer,
                content=str(err)
            )

    async def get_chat(self, chat_id: str, context: dict = None, create: bool = True) -> Chat:
        if not context:
            context = {}

        chat = await Chat.find_one(
            And(
                Chat.chat_id == chat_id,
                In(Chat.status, [ChatStatus.created, ChatStatus.idle, ChatStatus.tools])
            )
        )

        if not chat:
            if not create:
                return None

            chat = Chat(
                chat_id=chat_id,
                status=ChatStatus.created,
                data=context
            )
            await chat.save()

        elif context == {}:
            context.update(chat.data)

        system_message = await Message.find_one(
            And(
                Message.chat_id == chat.id,
                Message.type == MessageType.system
            )
        )
        if not system_message:
            messages = []

            for i in range(len(self.system_prompts)):
                system_message = Message(
                    chat_id=chat.id,
                    text=await self.__system_prompt(i, context),
                    type=MessageType.system
                )
                messages.append(system_message)

            if len(messages):
                await Message.insert_many(messages)

        return chat

    async def proccess_answer(self, answer: AgentResponse, chat: Chat) -> AgentResponse:
        if answer.type == AgentResponseType.tools:
            bot_message = Message(
                chat_id=chat.id,
                type=MessageType.tools,
                tools=answer.content
            )
            chat.status = ChatStatus.tools

        elif answer.type == AgentResponseType.answer:
            bot_message = Message(
                chat_id=chat.id,
                type=MessageType.assistant,
                text=answer.content
            )
            chat.status = ChatStatus.finished if self.is_one_shot else ChatStatus.idle

        else:
            raise ValueError(f"wrong answer type got {answer.type}, expected {AgentResponseType} like")

        await bot_message.insert()
        await chat.save()

        return answer

    async def skip_tools(self, chat: Chat) -> str:
        messages = await Message.find_many(Message.chat_id == chat.id).to_list()
        last_message: Message = messages[-1]

        if not last_message.tools:
            chat.status = ChatStatus.idle
            await chat.save()

            return chat

        new_messages = []
        for tool in last_message.tools:
            tool_state = await ChatToolState.find_one(
                And(
                    ChatToolState.chat_id == chat.id,
                    ChatToolState.tool_id == tool.tool_id,
                )
            )
            if tool_state:
                tool_state.status = ChatToolStateStatus.completed
                await tool_state.save()

            new_messages.append(
                Message(
                    chat_id=chat.id,
                    type=MessageType.tool_answer,
                    tool_answer=ToolAnswer(
                        tool_id=tool.tool_id,
                        name=tool.name,
                        text="Tool call skipped."
                    )
                )
            )

        new_messages.append(
            Message(
                chat_id=chat.id,
                type=MessageType.assistant,
                text="skip"
            )
        )
        await Message.insert_many(new_messages)

        return chat

    async def answer_text(self, chat_id: str, text: str, context: dict = {}) -> AgentResponse:
        chat = await self.get_chat(chat_id, context)
        if chat.status == ChatStatus.tools:
            chat = await self.skip_tools(chat)

        user_message = Message(
            chat_id=chat.id,
            text=await self.__prompt(text, context),
            type=MessageType.user
        )
        await user_message.insert()

        answer = await self.generate(chat=chat)
        await self.proccess_answer(answer, chat)

        return answer

    async def answer_tools(self, chat_id: str, tool_answers: list[ToolAnswer] = None) -> AgentResponse:
        chat = await self.get_chat(chat_id, create=False)
        if not chat:
            return AgentResponse(type=AgentResponseType.answer, content=f"No such chat -> {chat_id}")

        if chat.status != ChatStatus.tools:
            return AgentResponse(type=AgentResponseType.answer, content="No tools to answer")

        new_messages = []
        for tool_answer in tool_answers:
            tool_state = await ChatToolState.find_one(
                And(
                    ChatToolState.chat_id == chat.id,
                    ChatToolState.tool_id == tool_answer.tool_id,
                )
            )
            if tool_state:
                tool_state.status = ChatToolStateStatus.completed
                await tool_state.save()

            new_messages.append(Message(
                chat_id=chat.id,
                type=MessageType.tool_answer,
                tool_answer=tool_answer
            ))

        await Message.insert_many(new_messages)

        answer = await self.generate(chat=chat)
        await self.proccess_answer(answer, chat)

        return answer

    async def answer(self, chat_id: str, text: str = None, context: dict = {}, tool_answers: list[ToolAnswer] = None) -> AgentResponse:
        self.log.debug(f"Answer: {chat_id = }, {text = }, {context = }, {tool_answers = }")

        if text:
            return await self.answer_text(chat_id, text, context)

        elif len(tool_answers):
            return await self.answer_tools(chat_id, tool_answers)

        else:
            raise ValueError("Need text or tool answers to answer")

    async def create_storage(self, key: str) -> Storage:
        from AgentService.config import Config

        vector_store = await self.client.vector_stores.create(name="@".join([Config().project_name, key]))
        self.log.info(f"Created storage -> {vector_store.id}")

        return Storage(
            vector_store_id=vector_store.id,
            key=key
        )

    async def update_storage(self, data: str, storage_id: str):
        files = await self.client.vector_stores.files.list(vector_store_id=storage_id)
        for file in files.data:
            await self.client.vector_stores.files.delete(
                vector_store_id=storage_id,
                file_id=file.id
            )
            self.log.info(f"Removed file from storage -> {storage_id}@{file.id}")

        await self.client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=storage_id,
            files=[("data.json", data)]
        )
        self.log.info(f"Added data to storage -> {storage_id}")
