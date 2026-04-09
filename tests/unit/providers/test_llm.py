"""Tests for LLM provider implementations."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from vibing.providers.llm.base import LLMProvider
from vibing.providers.llm.llama_cpp import LlamaCppProvider


class TestLLMProviderContract:
    """Verify the ABC cannot be instantiated directly."""

    def test_cannot_instantiate_abc(self):
        with pytest.raises(TypeError):
            LLMProvider()

    def test_default_system_prompt_exists(self):
        assert len(LLMProvider.DEFAULT_SYSTEM_PROMPT) > 50


class TestLlamaCppProvider:
    def test_init(self, tmp_path):
        model_file = tmp_path / "model.gguf"
        model_file.touch()
        provider = LlamaCppProvider(model_path=str(model_file))
        assert not provider.is_loaded

    def test_load_model_missing_file(self, tmp_path):
        provider = LlamaCppProvider(model_path=str(tmp_path / "nonexistent.gguf"))
        with pytest.raises(FileNotFoundError):
            provider.load_model()

    def test_correct_empty_text(self, tmp_path):
        model_file = tmp_path / "model.gguf"
        model_file.touch()
        provider = LlamaCppProvider(model_path=str(model_file))
        # correct() on empty text should return it without needing the model
        result = provider.correct("   ")
        assert result == "   "

    def test_correct_without_load_raises(self, tmp_path):
        model_file = tmp_path / "model.gguf"
        model_file.touch()
        provider = LlamaCppProvider(model_path=str(model_file))
        with pytest.raises(RuntimeError, match="not loaded"):
            provider.correct("some text")


class TestOpenAIProvider:
    def test_init_no_key_env(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        from vibing.providers.llm.openai import OpenAIProvider

        provider = OpenAIProvider()
        assert not provider.is_loaded

    def test_load_model_no_key_raises(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        from vibing.providers.llm.openai import OpenAIProvider

        provider = OpenAIProvider(api_key="")
        with pytest.raises(ValueError, match="API key required"):
            provider.load_model()

    def test_correct_empty_text(self):
        from vibing.providers.llm.openai import OpenAIProvider

        provider = OpenAIProvider(api_key="test")
        result = provider.correct("  ")
        assert result == "  "


class TestAnthropicProvider:
    def test_load_model_no_key_raises(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        from vibing.providers.llm.anthropic import AnthropicProvider

        provider = AnthropicProvider(api_key="")
        with pytest.raises(ValueError, match="API key required"):
            provider.load_model()
