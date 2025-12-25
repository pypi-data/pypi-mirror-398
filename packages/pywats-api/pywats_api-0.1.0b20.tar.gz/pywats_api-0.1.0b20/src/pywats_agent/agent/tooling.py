from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Type, TypeVar
from pydantic import BaseModel, ConfigDict


class ToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


TInput = TypeVar("TInput", bound=ToolInput)


class AgentTool(ABC, Generic[TInput]):
    """Canonical tool interface for the SDK-side agent layer."""

    name: str
    description: str
    input_model: Type[TInput]

    def __init__(self, api: Any):
        self._api = api

    @classmethod
    def openai_definition(cls) -> Dict[str, Any]:
        schema = cls.input_model.model_json_schema()
        return {
            "name": cls.name,
            "description": cls.description,
            "parameters": {
                "type": "object",
                "properties": schema.get("properties", {}),
                "required": schema.get("required", []),
            },
        }

    def execute(self, params: Dict[str, Any]) -> Any:
        """Executes tool and returns a tuple.

        Supported return shapes:
        - (ok, summary, data, metadata)
        - (ok, summary, data, metadata, viz_payload)

        Data and viz_payload can be arbitrarily large; the executor stores them
        out-of-band in a DataStore and returns only handles + bounded preview.
        """
        input_obj = self.input_model.model_validate(params)
        return self.run(input_obj)

    @abstractmethod
    def run(self, input_obj: TInput) -> Any:
        raise NotImplementedError
