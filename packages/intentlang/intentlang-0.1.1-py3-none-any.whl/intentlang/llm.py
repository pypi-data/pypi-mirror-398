import os
import json
from typing import Union, List
from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion


class LLM:
    def __init__(self, system_prompt: str):
        self._client = OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self._messages = [{"role": "system", "content": system_prompt}]
        self._total_tokens = 0

    def chat(self, user_prompt: Union[str, List[str]]) -> str:
        if isinstance(user_prompt, str):
            prompts = [user_prompt]
        else:
            prompts = user_prompt

        for prompt in prompts:
            self._messages.append({"role": "user", "content": prompt})

        completion: ChatCompletion = self._client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL_NAME"),
            messages=self._messages,
            stream=False,
            extra_body=json.loads(os.getenv("OPENAI_EXTRA_BODY", "{}"))
        )
        response = completion.choices[0].message.content
        self._messages.append({"role": "assistant", "content": response})
        self._total_tokens += completion.usage.total_tokens
        return response

    def get_tokens(self) -> int:
        return self._total_tokens
