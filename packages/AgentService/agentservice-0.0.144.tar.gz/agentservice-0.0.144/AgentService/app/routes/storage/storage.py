
import fastapi

from .models import (
    GetStorageRequest, GetStorageResponse,
    AddStorageRequest, AddStorageResponse,
    RemoveStorageRequest, RemoveStorageResponse,
)

from AgentService.config import Config
from AgentService.types import Storage, StorageItem


storage_router = fastapi.APIRouter(prefix="/storage")


@storage_router.get("")
async def get_storage(request: GetStorageRequest) -> GetStorageResponse:
    storage = await Storage.find_one(Storage.key == request.key)
    storage_items = await StorageItem.find_many(StorageItem.storage_id == storage.id).to_list()

    return GetStorageResponse(
        data=storage_items,
        status="ok"
    )


@storage_router.post("/add")
async def add_to_storage(request: AddStorageRequest):
    key = request.key
    data = request.data

    agent = Config().agent

    if not isinstance(data, list):
        data = [data]

    storage = await Storage.find_one(Storage.key == key)
    if not storage:
        storage = await agent.create_storage(key=key)
        await storage.insert()

    for item in data:
        storage_item = StorageItem(
            storage_id=storage.id,
            data=item
        )

        existing = await StorageItem.find_one(StorageItem.key_id == storage_item.key_id)
        if existing:
            await existing.replace(item)

        else:
            await storage_item.insert()

    buffer = await Storage.get_packed(key)
    await agent.update_storage(buffer, storage.vector_store_id)

    return AddStorageResponse(
        status="ok"
    )


@storage_router.post("/remove")
async def remove_from_storage(request: RemoveStorageRequest) -> RemoveStorageResponse:
    key = request.key
    data = request.data

    agent = Config().agent

    if not isinstance(data, list):
        data = [data]

    storage = await Storage.find_one(Storage.key == key)
    for item in data:
        storage_item = StorageItem(
            storage_id=storage.id,
            data=item
        )

        existing = await StorageItem.find_one(StorageItem.key_id == storage_item.key_id)
        if existing:
            await existing.delete()

        else:
            return RemoveStorageResponse(
                description=f"No such storage item -> {storage_item}",
                status="error"
            )

    storage = await Storage.find_one(Storage.key == key)
    buffer = await Storage.get_packed(key)
    await agent.update_storage(buffer, storage.vector_store_id)

    return RemoveStorageResponse(
        status="ok"
    )
