from sentinel.llm.base import LLMProvider


class OllamaBlueTeam(LLMProvider[str]):
    model_name = "deepseek-coder:7b"

    def __init__(self, host: str = "http://127.0.0.1:11434") -> None:
        self.host = host

    def generate(self, prompt: str) -> str:
        raise RuntimeError(f"Ollama transport unavailable at {self.host}; no patch was generated")
