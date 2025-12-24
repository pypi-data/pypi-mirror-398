
from typing import Dict, List, Optional
from pydantic import BaseModel

from AgentService.types.storage import StorageItem
from AgentService.enums.response import ResposneStatus


class GetStorageRequest(BaseModel):
    key: str


class GetStorageResponse(BaseModel):
    data: List[StorageItem]
    description: Optional[str] = None
    status: ResposneStatus


class AddStorageRequest(BaseModel):
    key: str
    data: List[Dict] | Dict


class AddStorageResponse(BaseModel):
    description: Optional[str] = None
    status: ResposneStatus


class RemoveStorageRequest(BaseModel):
    key: str
    data: List[Dict] | Dict


class RemoveStorageResponse(BaseModel):
    description: Optional[str] = None
    status: ResposneStatus


class UpdateStorageRequest(BaseModel):
    key: str
    data: Dict
    new_data: Dict


class UpdateStorageResponse(BaseModel):
    description: Optional[str] = None
    status: ResposneStatus
