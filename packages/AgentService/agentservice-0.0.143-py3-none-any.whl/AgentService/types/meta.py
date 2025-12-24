
from datetime import datetime, UTC

from pydantic import BaseModel, Field
from beanie import before_event, Insert


class TimestampMixin(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @before_event(Insert)
    def set_created_at(self):
        self.created_at = datetime.now(UTC)
