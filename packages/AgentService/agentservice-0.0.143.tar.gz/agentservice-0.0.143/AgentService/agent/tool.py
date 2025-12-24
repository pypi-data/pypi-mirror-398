
from pydantic import BaseModel


class AgentTool:
    name: str = "tool"
    description: str = "this is tool"
    parameters: BaseModel | dict = None

    @property
    def openai_model_dump(self) -> dict:
        if isinstance(self.parameters, BaseModel):
            parameters = self.parameters.model_json_schema()

        else:
            parameters = self.parameters

        if not self.parameters:
            parameters = {}

        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": parameters
        }
