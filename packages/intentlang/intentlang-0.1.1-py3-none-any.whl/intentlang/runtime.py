import ast
import traceback
from types import SimpleNamespace
from typing import Type, Any, Dict, Callable
from .models import OutputModel, PythonExecResult, InputModel, OutputModel


class PythonRuntime:
    def __init__(self, reason: Callable, input: InputModel, tools: SimpleNamespace, output: Type[OutputModel]):
        self._prints: list[str] = []
        self._globals: Dict[str, Any] = {
            "__builtins__": __builtins__,
            "print": lambda *args, **kwargs: self._prints.append(" ".join(str(a) for a in args)),
            "reason": reason,
            "input": input,
            "tools": tools,
            "OutputModel": output,
            "output": None
        }

    async def exec(self, source: str) -> PythonExecResult:
        error = ""
        try:
            code = compile(
                source=source,
                filename="<runtime>",
                mode="exec",
                flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
            )
            coro = eval(code, self._globals)
            if coro is not None:
                await coro
        except Exception:
            tb = traceback.format_exc()
            error = tb[tb.find('File "<runtime>"'):]
        return PythonExecResult(prints=self._get_prints(), error=error)

    def _get_prints(self) -> list[str]:
        prints = self._prints.copy()
        self._prints.clear()
        return prints

    def get_output(self) -> OutputModel:
        result = self._globals["output"]
        return result
