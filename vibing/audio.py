import numpy as np
import sounddevice as sd


class AudioRecorder:
    def __init__(self, sample_rate=16000, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
        self._buffer = []
        self._stream = None

    def _callback(self, indata, frames, time, status):
        if status:
            print(f"Audio: {status}")
        self._buffer.append(indata.copy())

    def start(self):
        self._buffer = []
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()

    def stop(self):
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        if self._buffer:
            return np.concatenate(self._buffer, axis=0).flatten()
        return np.array([], dtype="float32")

    @property
    def is_recording(self):
        return self._stream is not None and self._stream.active
