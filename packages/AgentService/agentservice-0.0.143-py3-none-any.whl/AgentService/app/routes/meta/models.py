
from typing import Optional, Dict
from pydantic import BaseModel, Field

from AgentService.enums.response import ResposneStatus


class GetVersionResponse(BaseModel):
    data: Dict = Field(default_factory=dict)
    description: Optional[str] = None
    status: ResposneStatus
