import numpy as np


class ASREngine:
    def __init__(self, model="large-v3-turbo", device="cuda", compute_type="float16"):
        from faster_whisper import WhisperModel

        print(f"Loading ASR model: {model} on {device} ({compute_type})...")
        self.model = WhisperModel(model, device=device, compute_type=compute_type)
        print("ASR model loaded.")

    def transcribe(self, audio, language=None, initial_prompt=None):
        if isinstance(audio, np.ndarray) and audio.size == 0:
            return ""
        segments, info = self.model.transcribe(
            audio,
            language=language,
            initial_prompt=initial_prompt or None,
            beam_size=5,
            vad_filter=True,
        )
        text = " ".join(seg.text for seg in segments).strip()
        return text
