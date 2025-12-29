import random
from openai import OpenAI
from openai import AzureOpenAI
from typing import Iterator

class LLM():
    def __init__(self, api_key: str, base_url: str, timeout: int, api_version: str | None = None):
        if api_version is not None:
            self.client = AzureOpenAI(
                api_key=api_key,
                azure_endpoint=base_url,
                timeout=timeout,
                api_version=api_version,
            )
        else:
            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=timeout,
            )

    def chat(self, input: str, system_prompt: str, model: str, temperature: float) -> str:
        if model.startswith("azure"):
            model = model.replace("azure-", "")

        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input},
            ],
            temperature=temperature,
        )

        if response.choices[0].message.content is None:
            return "Error"
        else:
            return response.choices[0].message.content

    def chat_stream(self, input: str, system_prompt: str, model: str, temperature: float) -> Iterator[str]:
        if model.startswith("azure"):
            model = model.replace("azure-", "")

        stream = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input},
            ],
            temperature=temperature,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
