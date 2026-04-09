"""Backward-compatibility shim — use vibing.providers.asr instead."""

from vibing.providers.asr.faster_whisper import FasterWhisperProvider as ASREngine

__all__ = ["ASREngine"]
