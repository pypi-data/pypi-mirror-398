
import enum


class ChatStatus(enum.Enum):
    created = "created"
    error = "error"
    idle = "idle"
    tools = "tools"
    generating = "generating"
    finished = "finished"


class ChatToolStateStatus(enum.Enum):
    in_progress = "in_progress"
    completed = "completed"
    error = "error"
