import inspect
import json
from typing import Self, Type
from pathlib import Path
from jinja2 import Template
from .models import ContextSpace, InputModel, RuleList, OutputModel, IntentExecutor


class Intent:

    def __init__(self):
        self._goal: str = None
        self._ctx: ContextSpace = ContextSpace()
        self._input: InputModel = None
        self._how: str = None
        self._rules: RuleList = RuleList()
        self._output: Type[OutputModel] = None

    def goal(self, goal: str) -> Self:
        self._goal = goal
        return self

    def ctx(self, ctx: ContextSpace) -> Self:
        self._ctx = ctx
        return self

    def input(self, input: InputModel) -> Self:
        self._input = input
        return self

    def how(self, how: str) -> Self:
        self._how = how
        return self

    def rules(self, rules: RuleList) -> Self:
        self._rules = rules
        return self

    def output(self, output: Type[OutputModel]) -> Self:
        self._output = output
        return self

    def _validate(self):
        if not self._goal:
            raise ValueError("Intent.goal is required")
        if not self._input:
            raise ValueError("Intent.input is required")
        if not self._output:
            raise ValueError("Intent.output is required")

    def _build_ir(self):
        self._validate()
        intent_template_path = Path(__file__).parent / "prompts" / "intent.xml"
        intent_template = Template(intent_template_path.read_text())

        context_funcs = []
        for func in self._ctx.funcs:
            context_funcs.append({
                "name": func.__name__,
                "doc": func.__doc__,
                "signature": str(inspect.signature(func)),
                "is_async": inspect.iscoroutinefunction(func)
            })
        input_schema = self._input.model_json_schema()
        output_schema = self._output.model_json_schema()
        return intent_template.render(
            goal=self._goal,
            context_texts=self._ctx.texts,
            context_funcs=json.dumps(
                context_funcs, indent=2, ensure_ascii=False),
            input_schema=json.dumps(
                input_schema, indent=2, ensure_ascii=False),
            how=self._how,
            rules_texts=self._rules.texts,
            output_schema=json.dumps(
                output_schema, indent=2, ensure_ascii=False),
        )

    def compile(self, max_iterations: int = 30) -> IntentExecutor:
        from .executor import LLMIntentExecutor
        self._validate()
        return LLMIntentExecutor(self, max_iterations=max_iterations)
