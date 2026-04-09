import sys
import threading
import time

from vibing.audio import AudioRecorder
from vibing.asr import ASREngine
from vibing.clipboard import copy_to_clipboard, paste
from vibing.config import CONFIG_FILE, load_config, save_default_config
from vibing.hotkey import HotkeyListener
from vibing.llm import LLMCorrector
from vibing.tray import SystemTray


class VibingApp:
    def __init__(self, config):
        self.config = config
        self._recording = False
        self._lock = threading.Lock()

        audio_cfg = config["audio"]
        self.recorder = AudioRecorder(
            sample_rate=audio_cfg["sample_rate"],
            channels=audio_cfg["channels"],
        )

        asr_cfg = config["asr"]
        self.asr = ASREngine(
            model=asr_cfg["model"],
            device=asr_cfg["device"],
            compute_type=asr_cfg["compute_type"],
        )

        llm_cfg = config["llm"]
        try:
            self.llm = LLMCorrector(
                model_path=llm_cfg["model_path"],
                n_gpu_layers=llm_cfg["n_gpu_layers"],
                n_ctx=llm_cfg["n_ctx"],
            )
        except FileNotFoundError as e:
            print(f"Warning: {e}")
            print("Running without LLM correction.")
            self.llm = None

        self.tray = SystemTray(on_quit=self.shutdown)

        hotkey_cfg = config["hotkey"]
        self.hotkey = HotkeyListener(
            key_name=hotkey_cfg["key"],
            device_path=hotkey_cfg["device"],
            on_press=self._on_press,
            on_release=self._on_release,
        )

    def _on_press(self):
        with self._lock:
            if self._recording:
                return
            self._recording = True
        self.tray.set_state("recording")
        self.recorder.start()
        print("Recording...")

    def _on_release(self):
        with self._lock:
            if not self._recording:
                return
            self._recording = False
        audio = self.recorder.stop()
        duration = len(audio) / self.config["audio"]["sample_rate"]
        print(f"Recorded {duration:.1f}s of audio.")
        if duration < 0.3:
            print("Too short, ignoring.")
            self.tray.set_state("idle")
            return
        threading.Thread(target=self._process, args=(audio,), daemon=True).start()

    def _process(self, audio):
        self.tray.set_state("processing")
        try:
            asr_cfg = self.config["asr"]
            raw_text = self.asr.transcribe(
                audio,
                language=asr_cfg["language"],
                initial_prompt=asr_cfg["initial_prompt"],
            )
            if not raw_text:
                print("No speech detected.")
                self.tray.set_state("idle")
                return

            print(f"Transcription: {raw_text}")

            if self.llm:
                corrected = self.llm.correct(
                    raw_text,
                    temperature=self.config["llm"]["temperature"],
                )
                print(f"Corrected: {corrected}")
                result = corrected
            else:
                result = raw_text

            copy_to_clipboard(result)
            print("Copied to clipboard.")

            if self.config["auto_paste"]:
                time.sleep(0.05)
                paste()

            self.tray.set_state("done")
            time.sleep(1.5)
        except Exception as e:
            print(f"Error: {e}")
            self.tray.set_state("error")
            time.sleep(2)

        self.tray.set_state("idle")

    def shutdown(self):
        print("Shutting down...")
        self.hotkey.stop()

    def run(self):
        print("Starting hotkey listener...")
        self.hotkey.start()
        print("Vibing Linux ready! Hold the hotkey to record.")
        self.tray.run()


def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Vibing Linux - Offline voice-to-text with LLM correction")
        print(f"Config: {CONFIG_FILE}")
        print("Usage: vibing-linux")
        sys.exit(0)

    save_default_config()
    config = load_config()
    app = VibingApp(config)
    app.run()


if __name__ == "__main__":
    main()
