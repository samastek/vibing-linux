"""Tests for provider factory functions."""

from __future__ import annotations

import copy

import pytest

from vibing.config import DEFAULTS
from vibing.providers import create_asr_provider, create_llm_provider
from vibing.providers.asr.base import ASRProvider
from vibing.providers.llm.base import LLMProvider


class TestCreateASRProvider:
    def test_faster_whisper(self):
        config = copy.deepcopy(DEFAULTS)
        config["asr"]["provider"] = "faster_whisper"
        provider = create_asr_provider(config)
        assert isinstance(provider, ASRProvider)

    def test_openai_whisper(self):
        config = copy.deepcopy(DEFAULTS)
        config["asr"]["provider"] = "openai_whisper"
        config["asr"]["api_key"] = "test-key"
        provider = create_asr_provider(config)
        assert isinstance(provider, ASRProvider)

    def test_invalid_provider(self):
        config = copy.deepcopy(DEFAULTS)
        config["asr"]["provider"] = "nonexistent"
        with pytest.raises(ValueError, match="Unknown ASR provider"):
            create_asr_provider(config)


class TestCreateLLMProvider:
    def test_llama_cpp(self):
        config = copy.deepcopy(DEFAULTS)
        config["llm"]["provider"] = "llama_cpp"
        provider = create_llm_provider(config)
        assert isinstance(provider, LLMProvider)

    def test_openai(self):
        config = copy.deepcopy(DEFAULTS)
        config["llm"]["provider"] = "openai"
        config["llm"]["api_key"] = "test-key"
        provider = create_llm_provider(config)
        assert isinstance(provider, LLMProvider)

    def test_anthropic(self):
        config = copy.deepcopy(DEFAULTS)
        config["llm"]["provider"] = "anthropic"
        config["llm"]["api_key"] = "test-key"
        provider = create_llm_provider(config)
        assert isinstance(provider, LLMProvider)

    def test_none_provider(self):
        config = copy.deepcopy(DEFAULTS)
        config["llm"]["provider"] = "none"
        provider = create_llm_provider(config)
        assert provider is None

    def test_invalid_provider(self):
        config = copy.deepcopy(DEFAULTS)
        config["llm"]["provider"] = "nonexistent"
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            create_llm_provider(config)
