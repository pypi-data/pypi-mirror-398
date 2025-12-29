from abc import ABC, abstractmethod
from typing import Callable
from pydantic import BaseModel, ConfigDict


class ContextSpace(BaseModel):
    texts: list[str] = []
    funcs: list[Callable] = []


class InputModel(BaseModel, ABC):
    model_config = ConfigDict(arbitrary_types_allowed=True)


class RuleList(BaseModel):
    texts: list[str] = []


class OutputModel(BaseModel, ABC):
    model_config = ConfigDict(arbitrary_types_allowed=True)


class PythonExecResult(BaseModel):
    prints: list[str] = []
    error: str = ""


class IntentResult(BaseModel):
    output: OutputModel


class IntentExecutor(ABC):
    @abstractmethod
    async def run(self) -> IntentResult:
        pass

    @abstractmethod
    def run_sync(self) -> IntentResult:
        pass
