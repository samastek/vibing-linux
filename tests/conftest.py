"""Shared test fixtures for Vibing Linux."""

from __future__ import annotations

import copy
import sys
from typing import Any
from unittest.mock import MagicMock

import numpy as np
import pytest

# Mock heavy/native dependencies that may not be installed or cause segfaults
for _mod in ("faster_whisper", "llama_cpp", "sounddevice"):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

from vibing.config import DEFAULTS
from vibing.providers.asr.base import ASRProvider
from vibing.providers.llm.base import LLMProvider

# ── Mock providers ───────────────────────────────────────────────────────


class MockASRProvider(ASRProvider):
    """A no-op ASR provider for testing."""

    def __init__(self, transcribe_result: str = "hello world") -> None:
        self._transcribe_result = transcribe_result
        self._loaded = False

    def load_model(self) -> None:
        self._loaded = True

    def transcribe(
        self,
        audio: np.ndarray,
        language: str | None = None,
        initial_prompt: str | None = None,
    ) -> str:
        return self._transcribe_result

    @property
    def is_loaded(self) -> bool:
        return self._loaded


class MockLLMProvider(LLMProvider):
    """A no-op LLM provider for testing."""

    def __init__(self, correct_result: str = "corrected text") -> None:
        self._correct_result = correct_result
        self._loaded = False

    def load_model(self) -> None:
        self._loaded = True

    def correct(self, text: str, temperature: float = 0.3) -> str:
        return self._correct_result

    @property
    def is_loaded(self) -> bool:
        return self._loaded


# ── Config fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def default_config() -> dict[str, Any]:
    """Return a full default config dict (deep copy of DEFAULTS)."""
    return copy.deepcopy(DEFAULTS)


@pytest.fixture
def mock_asr() -> MockASRProvider:
    provider = MockASRProvider()
    provider.load_model()
    return provider


@pytest.fixture
def mock_llm() -> MockLLMProvider:
    provider = MockLLMProvider()
    provider.load_model()
    return provider


@pytest.fixture
def tmp_config_dir(tmp_path, monkeypatch):
    """Redirect config/data dirs to a temp directory."""
    config_dir = tmp_path / "config" / "vibing-linux"
    data_dir = tmp_path / "data" / "vibing-linux"
    config_dir.mkdir(parents=True)
    data_dir.mkdir(parents=True)

    monkeypatch.setattr("vibing.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("vibing.config.DATA_DIR", data_dir)
    monkeypatch.setattr("vibing.config.CONFIG_FILE", config_dir / "config.yaml")

    return {"config_dir": config_dir, "data_dir": data_dir}
