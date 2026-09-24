import os

from sentinel.llm.base import LLMProvider


class OpenAIRedTeam(LLMProvider[str]):
    model_name = "gpt-4o"

    def generate(self, prompt: str) -> str:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not configured for the GPT-4o Red Team")
        raise NotImplementedError("OpenAI transport will be enabled through the optional LLM dependency")
