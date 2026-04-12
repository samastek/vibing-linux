"""Vibing Linux — application orchestrator.

Ties together audio recording, ASR transcription, LLM correction,
clipboard output, hotkey listening, and the system-tray icon.
"""

from __future__ import annotations

import logging
import signal
import sys
import threading
import time
from typing import Any

from vibing.audio import AudioRecorder
from vibing.config import CONFIG_FILE, load_config, save_default_config
from vibing.configure import run_configure
from vibing.logging import setup_logging
from vibing.platform.base import AppState, OverlayProvider, PlatformFactory
from vibing.platform.loader import get_platform_factory
from vibing.providers import create_asr_provider, create_llm_provider
from vibing.providers.asr.base import ASRProvider
from vibing.providers.llm.base import LLMProvider
from vibing.setup import run_first_time_setup

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
        overlay: OverlayProvider | None = None,
    ) -> None:
        self.config = config
        self.factory = factory
        self.overlay = overlay
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

        self._cancel_event = threading.Event()
        self._process_lock = threading.Lock()
        cancel_key = "Key.esc" if sys.platform == "darwin" else "KEY_ESC"

        self.hotkey = self.factory.create_hotkey(
            key_name=hotkey_cfg["key"],
            device_path=hotkey_cfg["device"],
            on_press=self._on_press,
            on_release=self._on_release,
            cancel_key_name=cancel_key,
            on_cancel=self._on_cancel,
        )

    # ── Hotkey callbacks ─────────────────────────────────────────────

    def _on_cancel(self) -> None:
        logger.info("Cancellation requested via hotkey.")
        self._cancel_event.set()
        if self.overlay:
            self.overlay.hide()
        with self._lock:
            if self._recording:
                self._recording = False
                self.recorder.stop()
                self.tray.set_state(AppState.IDLE)
                logger.info("Recording canceled.")

    def _on_press(self) -> None:
        with self._lock:
            if self._recording:
                return
            self._recording = True
        self._cancel_event.clear()
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
        if not self._process_lock.acquire(blocking=False):
            logger.info("Processing already in progress, skipping.")
            return
        self.tray.set_state(AppState.PROCESSING)
        clip_cfg = self.config.get("clipboard", {})
        try:
            asr_cfg = self.config["asr"]
            # Lazily load ASR model on first transcription
            if not self.asr.is_loaded:
                self.asr.load_model()

            if self._cancel_event.is_set():
                logger.info("Processing canceled before transcription.")
                self.tray.set_state(AppState.IDLE)
                return

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
            if self.overlay:
                self.overlay.show_transcript(raw_text)

            if self._cancel_event.is_set():
                logger.info("Processing canceled after transcription.")
                if self.overlay:
                    self.overlay.hide()
                self.tray.set_state(AppState.IDLE)
                return

            if self.llm:
                # Lazily load LLM model on first correction
                if not self.llm.is_loaded:
                    try:
                        self.llm.load_model()
                    except FileNotFoundError as e:
                        logger.warning(
                            "LLM model not found: %s. Running without LLM correction.", e
                        )
                        self.factory.system.notify(
                            "LLM Model Missing",
                            "Model not found. Running without correction. "
                            "Check config or download the model.",
                        )
                        self.llm = None
                        result = raw_text
                    except Exception as e:
                        logger.warning("LLM failed to load: %s. Running without LLM correction.", e)
                        self.factory.system.notify(
                            "LLM Failed to Load",
                            "Failed to load the LLM. Running without correction.",
                        )
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

            if self._cancel_event.is_set():
                logger.info("Processing canceled before clipboard copy.")
                if self.overlay:
                    self.overlay.hide()
                self.tray.set_state(AppState.IDLE)
                return

            if self.overlay:
                self.overlay.show_result(result)

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
        finally:
            self.tray.set_state(AppState.IDLE)
            self._process_lock.release()

    # ── Lifecycle ────────────────────────────────────────────────────

    def _handle_signal(self, signum: int, frame: object) -> None:
        """Handle SIGINT/SIGTERM for a clean shutdown without Metal teardown crash."""
        logger.info("Signal received, shutting down cleanly...")
        with self._process_lock:
            if self.llm is not None:
                self.llm.unload()
            self.shutdown()
        self.tray.stop()

    def shutdown(self) -> None:
        """Stop all background services."""
        logger.info("Shutting down...")
        self.hotkey.stop()
        if self.overlay:
            self.overlay.stop()

    def run(self) -> None:
        """Start the application (blocks on the tray icon loop)."""
        logger.info("Starting hotkey listener...")
        self.hotkey.start()
        # Reinstall after pynput starts — pynput's machsignals overwrites SIGINT
        # on macOS and routes it through NSApplication.terminate(), which causes
        # a Metal GPU resource teardown crash in llama.cpp. Our handler unloads
        # the LLM first, then stops the tray cleanly.
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
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

    factory = get_platform_factory()

    llm: LLMProvider | None = None
    try:
        llm = create_llm_provider(config)
        # Don't load LLM model here — load lazily on first correction to save RAM
    except (FileNotFoundError, ValueError) as e:
        logger.warning("%s", e)
        logger.warning("Running without LLM correction.")
        factory.system.notify("LLM Provider Configuration Error", str(e))

    overlay: OverlayProvider | None = None
    overlay_cfg = config.get("overlay", {})
    if overlay_cfg.get("enabled", True):
        overlay = factory.create_overlay(overlay_cfg)
        if overlay is not None:
            overlay.start()

    app = VibingApp(config, factory=factory, asr=asr, llm=llm, overlay=overlay)
    app.run()


if __name__ == "__main__":
    main()
