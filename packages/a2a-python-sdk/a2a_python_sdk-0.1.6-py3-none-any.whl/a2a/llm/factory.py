from a2a.llm.openai import OpenAILLM
from a2a.llm.gemini import GeminiLLM
from a2a.llm.groq import GroqLLM
from a2a.llm.ollama import OllamaLLM
from a2a.config.llm_config import LLMConfig

def create_llm(config: LLMConfig, secrets: dict):
    provider = config.provider.lower()

    if provider == "openai":
        return OpenAILLM(secrets["api_key"], config)

    if provider == "gemini":
        return GeminiLLM(secrets["api_key"], config)

    if provider == "groq":
        return GroqLLM(secrets["api_key"], config)

    if provider == "ollama":
        return OllamaLLM(config, secrets.get("base_url"))

    raise ValueError(f"Unsupported LLM provider: {provider}")
