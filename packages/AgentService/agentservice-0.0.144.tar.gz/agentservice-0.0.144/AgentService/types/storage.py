
import io
import json
import typing

from . import Document
from beanie.odm.documents import PydanticObjectId

from pydantic import model_validator, ValidationInfo

from .meta import TimestampMixin

from AgentService.utils import string_to_uuid


class Storage(TimestampMixin, Document):
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


class StorageItem(TimestampMixin, Document):
    storage_id: PydanticObjectId
    data: dict

    key_id: typing.Optional[str] = None

    @model_validator(mode="after")
    def set_unique_id(self, values: ValidationInfo):
        if self.key_id:
            return self

        key = {
            "storage_id": str(self.storage_id),
            "data": self.data.get("key", self.data)
        }
        self.key_id = string_to_uuid(json.dumps(key, sort_keys=True))
        return self
