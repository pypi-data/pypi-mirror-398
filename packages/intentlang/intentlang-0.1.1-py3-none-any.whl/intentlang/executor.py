import asyncio
import json
from types import SimpleNamespace
from pathlib import Path
from jinja2 import Template
from .models import IntentResult, OutputModel, PythonExecResult
from .runtime import PythonRuntime
from .llm import LLM
from .intent import Intent


def reason(prompt: str) -> str:
    infer_system_prompt_path = Path(
        __file__).parent / "prompts" / "reason.md"
    llm = LLM(system_prompt=infer_system_prompt_path.read_text())
    return llm.chat(prompt)


class LLMIntentExecutor:
    def __init__(self, intent: Intent, max_iterations: int = 30):
        self._intent = intent
        self._max_iterations = max_iterations

    def _build_system_prompt(self, intent_prompt: str):
        system_template_path = Path(__file__).parent / "prompts" / "system.md"
        system_template = Template(system_template_path.read_text())
        system_prompt = system_template.render(intent=intent_prompt)
        return system_prompt

    def _build_user_prompt(self, exec_result: PythonExecResult):
        user_template_path = Path(__file__).parent / "prompts/user.md"
        user_template = Template(user_template_path.read_text())
        user_prompt = user_template.render(
            prints=json.dumps(exec_result.prints, indent=2,
                              ensure_ascii=False),
            error=exec_result.error
        )
        return user_prompt

    async def run(self) -> IntentResult:
        tools = SimpleNamespace(
            **{func.__name__: func for func in self._intent._ctx.funcs})
        runtime = PythonRuntime(
            reason, self._intent._input, tools, self._intent._output)

        system_prompt = self._build_system_prompt(self._intent._build_ir())
        user_prompt = "start"
        llm = LLM(system_prompt)
        output = None
        for _ in range(self._max_iterations):
            output = runtime.get_output()
            if output:
                break
            else:
                code_response = llm.chat(user_prompt)
                exec_result = await runtime.exec(code_response)
                user_prompt = self._build_user_prompt(exec_result)
        else:
            raise RuntimeError(
                f"Intent execution failed: no result produced after {self._max_iterations} iterations"
            )

        if not isinstance(output, OutputModel):
            raise TypeError(
                f"Intent execution failed: invalid output type\n"
                f"Expected: {self._intent._output.__name__}\n"
                f"Got: {type(output).__name__}\n"
                f"Output: {output}"
            )

        return IntentResult(output=output)

    def run_sync(self) -> IntentResult:
        return asyncio.run(self.run())
