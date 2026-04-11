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
from vibing.config import CONFIG_FILE, load_config, save_default_config
from vibing.configure import run_configure
from vibing.logging import setup_logging
from vibing.providers import create_asr_provider, create_llm_provider
from vibing.providers.asr.base import ASRProvider
from vibing.providers.llm.base import LLMProvider
from vibing.setup import run_first_time_setup
from vibing.platform.loader import get_platform_factory
from vibing.platform.base import PlatformFactory, AppState

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
        factory: PlatformFactory,
        asr: ASRProvider,
        llm: LLMProvider | None,
    ) -> None:
        self.config = config
        self.factory = factory
        self._recording = False
        self._lock = threading.Lock()

        audio_cfg = config["audio"]
        self.recorder = AudioRecorder(
            sample_rate=audio_cfg["sample_rate"],
            channels=audio_cfg["channels"],
        )

        self.asr = asr
        self.llm = llm

        self.tray = self.factory.create_tray(
            on_quit=self.shutdown,
            tray_config=config.get("tray", {}),
        )

        hotkey_cfg = config["hotkey"]
        self.hotkey = self.factory.create_hotkey(
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
            # Lazily load ASR model on first transcription
            if not self.asr.is_loaded:
                self.asr.load_model()
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
                # Lazily load LLM model on first correction
                if not self.llm.is_loaded:
                    try:
                        self.llm.load_model()
                    except FileNotFoundError as e:
                        logger.warning("LLM model not found: %s. Running without LLM correction.", e)
                        self.llm = None
                        result = raw_text
                    except Exception as e:
                        logger.warning("LLM failed to load: %s. Running without LLM correction.", e)
                        self.llm = None
                        result = raw_text
                    else:
                        corrected = self.llm.correct(
                            raw_text,
                            temperature=self.config["llm"]["temperature"],
                        )
                        logger.info("Corrected: %s", corrected)
                        result = corrected
                else:
                    corrected = self.llm.correct(
                        raw_text,
                        temperature=self.config["llm"]["temperature"],
                    )
                    logger.info("Corrected: %s", corrected)
                    result = corrected
            else:
                result = raw_text

            copy_timeout = clip_cfg.get("copy_timeout", 5)
            self.factory.clipboard.copy(result, timeout=copy_timeout)
            logger.info("Copied to clipboard.")

            if self.config.get("auto_paste", False):
                paste_delay = clip_cfg.get("paste_delay", 0.1)
                paste_timeout = clip_cfg.get("paste_timeout", 3)
                if self.factory.clipboard.paste(
                    paste_delay=paste_delay,
                    paste_timeout=paste_timeout,
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
    # Don't load ASR model here — load lazily on first transcription to save RAM

    llm: LLMProvider | None = None
    try:
        llm = create_llm_provider(config)
        # Don't load LLM model here — load lazily on first correction to save RAM
    except (FileNotFoundError, ValueError) as e:
        logger.warning("%s", e)
        logger.warning("Running without LLM correction.")

    factory = get_platform_factory()
    app = VibingApp(config, factory=factory, asr=asr, llm=llm)
    app.run()


if __name__ == "__main__":
    main()
