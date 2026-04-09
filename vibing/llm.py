"""Backward-compatibility shim — use vibing.providers.llm instead."""

from vibing.providers.llm.llama_cpp import LlamaCppProvider as LLMCorrector

__all__ = ["LLMCorrector"]
