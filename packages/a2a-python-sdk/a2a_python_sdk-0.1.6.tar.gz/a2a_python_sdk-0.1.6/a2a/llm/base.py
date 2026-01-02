from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncIterator, Union
from a2a.config.llm_config import LLMConfig

Message = Dict[str, str]

class BaseLLM(ABC):
    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    def invoke(self, messages: List[Message]) -> Union[str, Dict[str, Any]]:
        pass

    async def stream(self, messages: List[Message]) -> AsyncIterator[str]:
        raise NotImplementedError
