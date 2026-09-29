from types import SimpleNamespace

import httpx
import pytest

from sentinel.llm.gemini import GeminiProvider, GeminiScout
from sentinel.llm.ollama import OllamaBlueTeam
from sentinel.llm.openai import OpenAIRedTeam


class JsonClient:
    def __init__(self, payload, status_code=200) -> None:
        self.payload = payload
        self.status_code = status_code
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        request = httpx.Request("POST", url)
        return httpx.Response(self.status_code, json=self.payload, request=request)


def test_gemini_transport_extracts_text(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test")
    client = JsonClient({"candidates": [{"content": {"parts": [{"text": "candidate"}]}}]})
    assert GeminiScout(client=client).generate("prompt") == "candidate"
    assert client.calls[0][1]["headers"]["x-goog-api-key"] == "test"


def test_gemini_provider_accepts_an_agent_model(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test")
    client = JsonClient({"candidates": [{"content": {"parts": [{"text": "draft"}]}}]})
    assert GeminiProvider("gemini-3.5-flash-lite", client=client).generate("prompt") == "draft"
    assert "/models/gemini-3.5-flash-lite:generateContent" in client.calls[0][0]


def test_openai_transport_uses_nonstored_responses(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    calls = []
    client = SimpleNamespace(responses=SimpleNamespace(create=lambda **kwargs: calls.append(kwargs) or SimpleNamespace(output_text="poc")))
    assert OpenAIRedTeam(client=client).generate("prompt") == "poc"
    assert calls == [{"model": "gpt-4o", "input": "prompt", "store": False}]


def test_ollama_transport_uses_local_generate_endpoint() -> None:
    client = JsonClient({"response": "patch"})
    assert OllamaBlueTeam(client=client).generate("prompt") == "patch"
    assert client.calls[0][0] == "http://127.0.0.1:11434/api/generate"


@pytest.mark.parametrize("provider", [GeminiScout(), OpenAIRedTeam()])
def test_key_based_providers_fail_without_keys(provider, monkeypatch) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="not configured"):
        provider.generate("prompt")
