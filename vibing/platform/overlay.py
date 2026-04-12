"""Floating transcript + correction overlay window.

Shows a borderless, always-on-top HUD at the bottom-centre of the screen.
The overlay is driven by a thread-safe queue so that the processing pipeline
(a daemon thread) can update the UI safely.

Lifecycle
---------
1. ``overlay.start()``  — spawns the tkinter thread and shows the window.
2. ``overlay.show_transcript(text)`` — called right after ASR; shows raw text.
3. ``overlay.show_result(corrected)`` — called after LLM; transitions to the
   corrected text and schedules an auto-hide after *result_duration* seconds.
4. ``overlay.hide()``   — immediately withdraws the window (e.g. on cancel).
5. ``overlay.stop()``   — quits the tkinter mainloop and joins the thread.

All public methods are safe to call from any thread.
If the underlying tkinter window fails to initialise (e.g. no display
available), all subsequent calls become silent no-ops so the app continues.
"""

from __future__ import annotations

import logging
import queue
import threading
import tkinter as tk
from typing import Any

logger = logging.getLogger("vibing.overlay")

# ── Constants ────────────────────────────────────────────────────────────────

_BG = "#111827"
_TRANSCRIPT_FG = "#e5e7eb"
_RESULT_FG = "#86efac"
_PHASE_FG = "#6b7280"
_TRANSCRIPT_LABEL = "🎤  Transcript"
_RESULT_LABEL = "✓  Corrected"

# Minimum milliseconds between queue polls.
_POLL_MS = 50


# ── TkOverlay ────────────────────────────────────────────────────────────────


class TkOverlay:
    """Floating transcript + correction overlay driven by a dedicated thread."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        cfg = config or {}
        self._enabled: bool = cfg.get("enabled", True)
        self._transcript_duration_ms: int = int(cfg.get("transcript_duration", 10.0) * 1000)
        self._result_duration_ms: int = int(cfg.get("result_duration", 4.0) * 1000)
        self._font_size: int = int(cfg.get("font_size", 16))
        self._max_width: int = int(cfg.get("max_width", 620))
        self._opacity: float = float(cfg.get("opacity", 0.92))

        self._queue: queue.Queue[tuple[str, ...]] = queue.Queue()
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        # Set to True when the tkinter window has been initialised successfully.
        self._available = False

    # ── Public API ────────────────────────────────────────────────────────

    def start(self) -> None:
        """Spawn the overlay thread. Returns immediately."""
        if not self._enabled:
            return
        self._thread = threading.Thread(target=self._run, daemon=True, name="vibing-overlay")
        self._thread.start()
        # Wait briefly for tkinter to init so the first show_transcript call
        # doesn't race with window creation.
        self._ready.wait(timeout=3.0)

    def stop(self) -> None:
        """Ask the overlay thread to quit and wait for it to finish."""
        if self._available:
            self._queue.put(("quit",))
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def show_transcript(self, text: str) -> None:
        """Display *text* as the raw transcript phase."""
        if self._available:
            self._queue.put(("transcript", text))

    def show_result(self, corrected: str) -> None:
        """Transition the overlay to show the LLM-corrected *corrected* text."""
        if self._available:
            self._queue.put(("result", corrected))

    def hide(self) -> None:
        """Immediately hide the overlay (e.g. on cancel)."""
        if self._available:
            self._queue.put(("hide",))

    # ── Thread target ─────────────────────────────────────────────────────

    def _run(self) -> None:
        """Build and run the tkinter window. Runs entirely in the overlay thread."""
        try:
            root = tk.Tk()
        except Exception:
            logger.warning("Overlay: failed to create tkinter root; overlay disabled.", exc_info=True)
            self._ready.set()
            return

        try:
            self._setup_window(root)
            self._available = True
            self._ready.set()
            root.after(_POLL_MS, lambda: self._check_queue(root))
            root.mainloop()
        except Exception:
            logger.warning("Overlay: unexpected error in mainloop; overlay disabled.", exc_info=True)
            self._ready.set()
        finally:
            self._available = False
            try:
                root.destroy()
            except Exception:
                pass

    def _setup_window(self, root: tk.Tk) -> None:
        """Configure the root window and build the label widgets."""
        root.wm_overrideredirect(True)
        root.wm_attributes("-topmost", True)
        root.configure(bg=_BG)

        # Transparency — works on most X11 compositors and macOS.
        try:
            root.wm_attributes("-alpha", self._opacity)
        except tk.TclError:
            pass

        # ── Outer frame adds padding / gives a pill-like feel ─────────────
        frame = tk.Frame(root, bg=_BG, padx=20, pady=14)
        frame.pack(fill=tk.BOTH, expand=True)

        phase_font = ("Helvetica", self._font_size - 3)
        text_font = ("Helvetica", self._font_size)

        self._phase_label = tk.Label(
            frame,
            text="",
            font=phase_font,
            fg=_PHASE_FG,
            bg=_BG,
            anchor="w",
        )
        self._phase_label.pack(fill=tk.X)

        self._text_label = tk.Label(
            frame,
            text="",
            font=text_font,
            fg=_TRANSCRIPT_FG,
            bg=_BG,
            wraplength=self._max_width - 40,
            justify=tk.LEFT,
            anchor="w",
        )
        self._text_label.pack(fill=tk.X, pady=(4, 0))

        # Start hidden; shown only when content arrives.
        root.withdraw()

        # Bind click-to-dismiss for power users.
        root.bind("<Button-1>", lambda _e: root.withdraw())

        self._root = root
        self._auto_hide_id: str | None = None

    def _check_queue(self, root: tk.Tk) -> None:
        """Poll the command queue and dispatch, then reschedule itself."""
        try:
            while True:
                msg = self._queue.get_nowait()
                cmd = msg[0]
                if cmd == "transcript":
                    self._show_transcript_ui(root, msg[1])
                elif cmd == "result":
                    self._show_result_ui(root, msg[1])
                elif cmd == "hide":
                    self._cancel_auto_hide()
                    root.withdraw()
                elif cmd == "quit":
                    root.quit()
                    return
        except queue.Empty:
            pass

        root.after(_POLL_MS, lambda: self._check_queue(root))

    # ── UI update helpers (called from tkinter thread only) ───────────────

    def _show_transcript_ui(self, root: tk.Tk, text: str) -> None:
        self._cancel_auto_hide()
        self._phase_label.config(text=_TRANSCRIPT_LABEL, fg=_PHASE_FG)
        self._text_label.config(text=text, fg=_TRANSCRIPT_FG)
        self._position_window(root)
        root.deiconify()
        root.lift()
        # Auto-hide if no result arrives within transcript_duration.
        self._auto_hide_id = root.after(
            self._transcript_duration_ms, lambda: root.withdraw()
        )

    def _show_result_ui(self, root: tk.Tk, corrected: str) -> None:
        self._cancel_auto_hide()
        self._phase_label.config(text=_RESULT_LABEL, fg=_RESULT_FG)
        self._text_label.config(text=corrected, fg=_RESULT_FG)
        self._position_window(root)
        root.deiconify()
        root.lift()
        # Auto-hide after result_duration.
        self._auto_hide_id = root.after(
            self._result_duration_ms, lambda: root.withdraw()
        )

    def _cancel_auto_hide(self) -> None:
        if self._auto_hide_id is not None and hasattr(self, "_root"):
            try:
                self._root.after_cancel(self._auto_hide_id)
            except Exception:
                pass
            self._auto_hide_id = None

    def _position_window(self, root: tk.Tk) -> None:
        """Centre the window horizontally, near the bottom of the screen."""
        root.update_idletasks()
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        win_w = root.winfo_reqwidth()
        win_h = root.winfo_reqheight()
        # Clamp width to max_width
        win_w = min(win_w, self._max_width)
        x = (screen_w - win_w) // 2
        y = screen_h - win_h - 72
        root.geometry(f"{win_w}x{win_h}+{x}+{y}")
