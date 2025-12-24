
import io
import json

from pydantic import model_validator

from .meta import TimestampMixin

from AgentService.utils import string_to_uuid


class Storage(TimestampMixin):
    vector_store_id: str
    key: str

    @classmethod
    async def get_packed(cls, key: str) -> io.BytesIO:
        storage = await Storage.find_one(Storage.key == key)
        storage_items = await StorageItem.find_many(StorageItem.storage_id == storage.id).to_list()

        data = [
            {
                "text": item.data,
                "metadata": {"id": item.key_id}
            }
            for item in storage_items
        ]

        buffer = io.BytesIO()
        buffer.write((json.dumps(data, ensure_ascii=False)).encode("utf-8"))
        buffer.seek(0)

        return buffer


class StorageItem(TimestampMixin):
    storage_id: str
    data: dict

    key_id: str

    @model_validator(mode="before")
    def set_unique_id(self, values):
        if "key_id" in values or not values["key_id"]:
            return values

        data_key = values["data"].get("key")
        if data_key:
            values["key_id"] = (values["storage_id"], data_key)

        else:
            values["key_id"] = (values["storage_id"], str(values["data"]))

        values["key_id"] = string_to_uuid(''.join(values["key_id"]))
        return values


