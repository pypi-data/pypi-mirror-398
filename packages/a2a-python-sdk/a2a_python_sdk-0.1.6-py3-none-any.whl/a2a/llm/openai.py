from openai import OpenAI
from a2a.llm.base import BaseLLM
from a2a.config.llm_config import LLMConfig

class OpenAILLM(BaseLLM):
    def __init__(self, api_key: str, config: LLMConfig):
        super().__init__(config)
        self.client = OpenAI(api_key=api_key)

    def invoke(self, messages):
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            max_tokens=self.config.max_tokens,
            presence_penalty=self.config.presence_penalty,
            frequency_penalty=self.config.frequency_penalty,
            stop=self.config.stop,
            seed=self.config.seed,
            response_format=self.config.response_format,
            tools=self.config.tools,
            tool_choice=self.config.tool_choice,
            **self.config.extra  # SAFE passthrough
        )

        return response.choices[0].message.content

    async def stream(self, messages):
        stream = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
