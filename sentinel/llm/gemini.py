import os

from sentinel.llm.base import LLMProvider


class GeminiScout(LLMProvider[str]):
    model_name = "gemini-1.5-flash"

    def __init__(self, model_name: str = "gemini-1.5-flash") -> None:
        self.model_name = model_name

    def generate(self, prompt: str) -> str:
        if not os.getenv("GOOGLE_API_KEY"):
            raise RuntimeError("GOOGLE_API_KEY is not configured for the Gemini Scout")
        raise NotImplementedError("Gemini transport will be enabled through the optional LLM dependency")
