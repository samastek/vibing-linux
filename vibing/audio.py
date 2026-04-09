"""Audio recording using sounddevice."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import sounddevice as sd

logger = logging.getLogger("vibing.audio")


class AudioRecorder:
    """Records audio from the default input device.

    Supports context-manager usage for guaranteed resource cleanup::

        with AudioRecorder() as rec:
            rec.start()
            ...
            audio = rec.stop()
    """

    def __init__(self, sample_rate: int = 16000, channels: int = 1) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self._buffer: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None

    def _callback(
        self,
        indata: np.ndarray,
        frames: int,
        time: Any,
        status: sd.CallbackFlags,
    ) -> None:
        if status:
            logger.warning("Audio stream status: %s", status)
        self._buffer.append(indata.copy())

    def start(self) -> None:
        """Start recording audio."""
        self._buffer = []
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> np.ndarray:
        """Stop recording and return the captured audio.

        Returns:
            A 1-D float32 numpy array of audio samples, or an empty array
            if nothing was recorded.
        """
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        if self._buffer:
            return np.concatenate(self._buffer, axis=0).flatten()
        return np.array([], dtype="float32")

    @property
    def is_recording(self) -> bool:
        return self._stream is not None and self._stream.active

    def __enter__(self) -> AudioRecorder:
        return self

    def __exit__(self, *exc: object) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
