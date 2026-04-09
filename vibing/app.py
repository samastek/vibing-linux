"""Vibing Linux — application orchestrator.

Ties together audio recording, ASR transcription, LLM correction,
clipboard output, hotkey listening, and the system-tray icon.
"""

from __future__ import annotations

import logging
import sys
import threading
import time
from typing import Any

from vibing.audio import AudioRecorder
from vibing.clipboard import copy_to_clipboard, paste_from_clipboard
from vibing.config import CONFIG_FILE, load_config, save_default_config
from vibing.configure import run_configure
from vibing.hotkey import HotkeyListener
from vibing.logging import setup_logging
from vibing.providers import create_asr_provider, create_llm_provider
from vibing.providers.asr.base import ASRProvider
from vibing.providers.llm.base import LLMProvider
from vibing.setup import run_first_time_setup
from vibing.tray import AppState, SystemTray

logger = logging.getLogger("vibing.app")


class VibingApp:
    """Main application class.

    All heavy dependencies (ASR model, LLM model) are injected via
    provider instances rather than being created internally, making
    the class easier to test and extend.
    """

    def __init__(
        self,
        config: dict[str, Any],
        asr: ASRProvider,
        llm: LLMProvider | None,
    ) -> None:
        self.config = config
        self._recording = False
        self._lock = threading.Lock()

        audio_cfg = config["audio"]
        self.recorder = AudioRecorder(
            sample_rate=audio_cfg["sample_rate"],
            channels=audio_cfg["channels"],
        )

        self.asr = asr
        self.llm = llm

        self.tray = SystemTray(
            on_quit=self.shutdown,
            tray_config=config.get("tray"),
        )

        hotkey_cfg = config["hotkey"]
        self.hotkey = HotkeyListener(
            key_name=hotkey_cfg["key"],
            device_path=hotkey_cfg["device"],
            on_press=self._on_press,
            on_release=self._on_release,
        )

    # ── Hotkey callbacks ─────────────────────────────────────────────

    def _on_press(self) -> None:
        with self._lock:
            if self._recording:
                return
            self._recording = True
        self.tray.set_state(AppState.RECORDING)
        self.recorder.start()
        logger.info("Recording...")

    def _on_release(self) -> None:
        with self._lock:
            if not self._recording:
                return
            self._recording = False
        audio = self.recorder.stop()

        sample_rate = self.config["audio"]["sample_rate"]
        min_duration = self.config["audio"].get("min_duration", 0.3)
        duration = len(audio) / sample_rate
        logger.info("Recorded %.1fs of audio.", duration)

        if duration < min_duration:
            logger.info("Too short, ignoring.")
            self.tray.set_state(AppState.IDLE)
            return

        threading.Thread(target=self._process, args=(audio,), daemon=True).start()

    # ── Processing pipeline ──────────────────────────────────────────

    def _process(self, audio) -> None:
        self.tray.set_state(AppState.PROCESSING)
        clip_cfg = self.config.get("clipboard", {})
        try:
            asr_cfg = self.config["asr"]
            raw_text = self.asr.transcribe(
                audio,
                language=asr_cfg["language"],
                initial_prompt=asr_cfg["initial_prompt"],
            )
            if not raw_text:
                logger.info("No speech detected.")
                self.tray.set_state(AppState.IDLE)
                return

            logger.info("Transcription: %s", raw_text)

            if self.llm:
                corrected = self.llm.correct(
                    raw_text,
                    temperature=self.config["llm"]["temperature"],
                )
                logger.info("Corrected: %s", corrected)
                result = corrected
            else:
                result = raw_text

            copy_to_clipboard(result, timeout=clip_cfg.get("copy_timeout", 5))
            logger.info("Copied to clipboard.")

            if self.config.get("auto_paste", False):
                if paste_from_clipboard(
                    paste_delay=clip_cfg.get("paste_delay", 0.1),
                    paste_timeout=clip_cfg.get("paste_timeout", 3),
                ):
                    logger.info("Auto-pasted to focused window.")
                else:
                    logger.info("Auto-paste unavailable. Text is in clipboard.")

            self.tray.set_state(AppState.DONE)
            time.sleep(1.5)
        except Exception:
            logger.exception("Error during processing")
            self.tray.set_state(AppState.ERROR)
            time.sleep(2)

        self.tray.set_state(AppState.IDLE)

    # ── Lifecycle ────────────────────────────────────────────────────

    def shutdown(self) -> None:
        """Stop all background services."""
        logger.info("Shutting down...")
        self.hotkey.stop()

    def run(self) -> None:
        """Start the application (blocks on the tray icon loop)."""
        logger.info("Starting hotkey listener...")
        self.hotkey.start()
        logger.info("Vibing Linux ready! Hold the hotkey to record.")
        self.tray.run()


# ── Entry point ──────────────────────────────────────────────────────

def main() -> None:
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Vibing Linux - Offline voice-to-text with LLM correction")
        print(f"Config: {CONFIG_FILE}")
        print()
        print("Usage: vibing-linux [command]")
        print()
        print("Commands:")
        print("  (none)       Start the application")
        print("  configure    Interactive configuration wizard")
        print("  --help, -h   Show this help message")
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] == "configure":
        run_configure()
        sys.exit(0)

    save_default_config()
    run_first_time_setup()
    config = load_config()

    setup_logging(config.get("logging", {}).get("level"))

    # Create providers via factory (uses config to pick the right backend)
    asr = create_asr_provider(config)
    asr.load_model()

    llm: LLMProvider | None = None
    try:
        llm = create_llm_provider(config)
        if llm is not None:
            llm.load_model()
    except (FileNotFoundError, ValueError) as e:
        logger.warning("%s", e)
        logger.warning("Running without LLM correction.")

    app = VibingApp(config, asr=asr, llm=llm)
    app.run()


if __name__ == "__main__":
    main()
