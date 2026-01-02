import requests
from a2a.llm.base import BaseLLM

class OllamaLLM(BaseLLM):
    def __init__(self, config, base_url="http://localhost:11434"):
        super().__init__(config)
        self.base_url = base_url

    def invoke(self, messages):
        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "num_predict": self.config.max_tokens,
                **self.config.extra
            }
        }

        r = requests.post(f"{self.base_url}/api/chat", json=payload)
        r.raise_for_status()
        return r.json()["message"]["content"]
