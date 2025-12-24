
from beanie import Document
from beanie import init_beanie

from motor.motor_asyncio import AsyncIOMotorClient

from .agent import AgentResponse
from .chat import Chat, ChatToolState
from .message import Message
from .storage import Storage, StorageItem
from .tool import Tool, ToolAnswer


async def setup_database(uri: str, name: str):
    client = AsyncIOMotorClient(uri)[name]
    await init_beanie(client, document_models=Document.__subclasses__())
