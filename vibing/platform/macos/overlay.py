"""macOS floating overlay using AppKit via pyobjc.

Dispatches all NSWindow/NSTextField operations to the main thread, which is
required by AppKit. The main thread runs NSApplication's event loop (via
pystray). Communication uses performSelectorOnMainThread:withObject:waitUntilDone:.

All public methods of MacOSOverlay are safe to call from any thread.
"""

from __future__ import annotations

import logging
from typing import Any

import objc
from AppKit import (
    NSBackingStoreBuffered,
    NSColor,
    NSFloatingWindowLevel,
    NSFont,
    NSPanel,
    NSScreen,
    NSTextField,
    NSTextAlignmentCenter,
)
from Foundation import NSMakeRect, NSObject

logger = logging.getLogger("vibing.overlay.macos")

# Window style mask integer constants — avoids version-specific AppKit symbol names.
_BORDERLESS: int = 0          # NSWindowStyleMaskBorderless
_NON_ACTIVATING: int = 1 << 7  # NSWindowStyleMaskNonactivatingPanel = 128

_PADDING: float = 16.0
_PHASE_H: float = 20.0
_PHASE_GAP: float = 8.0


class _Controller(NSObject):
    """NSObject subclass that owns the overlay NSPanel.

    All methods that touch AppKit state are intended to be called on the main
    thread only, via ``performSelectorOnMainThread:withObject:waitUntilDone:``.
    """

    def init(self) -> "_Controller":
        self = objc.super(_Controller, self).init()
        if self is None:
            return None  # type: ignore[return-value]
        self._config: dict = {}
        self._panel = None
        self._phase_field = None
        self._text_field = None
        return self

    def dispatchBlock_(self, block: Any) -> None:
        """Execute *block* (a Python callable) on the main thread."""
        block()

    def doHide_(self, _: Any) -> None:
        """Hide the panel. Used as a delayed-perform selector target."""
        if self._panel is not None:
            self._panel.orderOut_(None)

    def setupPanel_(self, _: Any) -> None:
        """Create and configure the overlay NSPanel. Must run on the main thread."""
        config = self._config
        font_size = float(config.get("font_size", 16))
        max_width = float(config.get("max_width", 620))
        opacity = float(config.get("opacity", 0.92))

        text_h = font_size * 3.5
        panel_h = _PADDING + _PHASE_H + _PHASE_GAP + text_h + _PADDING

        screen = NSScreen.mainScreen()
        if screen is None:
            logger.warning("No main screen found; overlay cannot be created.")
            return

        sf = screen.visibleFrame()
        x = sf.origin.x + (sf.size.width - max_width) / 2.0
        y = sf.origin.y + 72.0

        bg = NSColor.colorWithRed_green_blue_alpha_(0.07, 0.094, 0.153, opacity)
        panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, max_width, panel_h),
            _BORDERLESS | _NON_ACTIVATING,
            NSBackingStoreBuffered,
            False,
        )
        panel.setLevel_(NSFloatingWindowLevel)
        panel.setBackgroundColor_(bg)
        panel.setOpaque_(False)
        panel.setHasShadow_(True)
        panel.setIgnoresMouseEvents_(True)
        panel.setFloatingPanel_(True)
        panel.setBecomesKeyOnlyIfNeeded_(True)

        # Rounded corners via CALayer
        content = panel.contentView()
        content.setWantsLayer_(True)
        content.layer().setCornerRadius_(12.0)
        content.layer().setMasksToBounds_(True)

        # ── Phase label (top row, muted colour) ──────────────────────────────
        phase_y = _PADDING + text_h + _PHASE_GAP
        phase = NSTextField.alloc().initWithFrame_(
            NSMakeRect(_PADDING, phase_y, max_width - 2.0 * _PADDING, _PHASE_H)
        )
        phase.setEditable_(False)
        phase.setBordered_(False)
        phase.setDrawsBackground_(False)
        phase.setTextColor_(NSColor.colorWithRed_green_blue_alpha_(0.42, 0.447, 0.502, 1.0))
        phase.setFont_(NSFont.systemFontOfSize_(12.0))
        phase.setAlignment_(NSTextAlignmentCenter)
        content.addSubview_(phase)

        # ── Body text (bottom section, wrapping) ─────────────────────────────
        body = NSTextField.alloc().initWithFrame_(
            NSMakeRect(_PADDING, _PADDING, max_width - 2.0 * _PADDING, text_h)
        )
        body.setEditable_(False)
        body.setBordered_(False)
        body.setDrawsBackground_(False)
        body.setTextColor_(NSColor.whiteColor())
        body.setFont_(NSFont.systemFontOfSize_(font_size))
        body.setAlignment_(NSTextAlignmentCenter)
        body.setMaximumNumberOfLines_(4)
        body.cell().setWraps_(True)
        body.cell().setScrollable_(False)
        content.addSubview_(body)

        panel.orderOut_(None)  # hidden until first show
        self._panel = panel
        self._phase_field = phase
        self._text_field = body


class MacOSOverlay:
    """Floating transcript/correction overlay for macOS.

    All public methods are thread-safe; they dispatch AppKit calls to the main
    thread where NSApplication's run loop is running.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self._config = config or {}
        self._controller: _Controller | None = None
        self._transcript_dur = float(self._config.get("transcript_duration", 10.0))
        self._result_dur = float(self._config.get("result_duration", 4.0))

    def start(self) -> None:
        """Create the NSPanel. Safe to call from the main thread before the run loop."""
        try:
            ctrl = _Controller.alloc().init()
            ctrl._config = self._config
            # performSelectorOnMainThread:withObject:waitUntilDone: runs inline
            # (synchronously) when we are already on the main thread.
            ctrl.performSelectorOnMainThread_withObject_waitUntilDone_(
                "setupPanel:", None, True
            )
            if ctrl._panel is not None:
                self._controller = ctrl
            else:
                logger.warning("macOS overlay panel creation failed; running without overlay.")
        except Exception:
            logger.exception("macOS overlay failed to start; running without overlay.")

    def stop(self) -> None:
        ctrl = self._controller
        if ctrl is None:
            return
        self._controller = None

        def _stop() -> None:
            NSObject.cancelPreviousPerformRequestsWithTarget_selector_object_(
                ctrl, "doHide:", None
            )
            if ctrl._panel is not None:
                ctrl._panel.orderOut_(None)

        ctrl.performSelectorOnMainThread_withObject_waitUntilDone_("dispatchBlock:", _stop, False)

    def show_transcript(self, text: str) -> None:
        ctrl = self._controller
        if ctrl is None:
            return
        dur = self._transcript_dur

        def _show() -> None:
            if ctrl._panel is None:
                return
            NSObject.cancelPreviousPerformRequestsWithTarget_selector_object_(
                ctrl, "doHide:", None
            )
            ctrl._phase_field.setStringValue_("🎤  Transcript")
            ctrl._phase_field.setTextColor_(
                NSColor.colorWithRed_green_blue_alpha_(0.42, 0.447, 0.502, 1.0)
            )
            ctrl._text_field.setStringValue_(text)
            ctrl._text_field.setTextColor_(
                NSColor.colorWithRed_green_blue_alpha_(0.898, 0.906, 0.918, 1.0)
            )
            ctrl._panel.orderFront_(None)
            ctrl.performSelector_withObject_afterDelay_("doHide:", None, dur)

        ctrl.performSelectorOnMainThread_withObject_waitUntilDone_("dispatchBlock:", _show, False)

    def show_result(self, corrected: str) -> None:
        ctrl = self._controller
        if ctrl is None:
            return
        dur = self._result_dur

        def _show() -> None:
            if ctrl._panel is None:
                return
            NSObject.cancelPreviousPerformRequestsWithTarget_selector_object_(
                ctrl, "doHide:", None
            )
            result_green = NSColor.colorWithRed_green_blue_alpha_(0.525, 0.937, 0.671, 1.0)
            ctrl._phase_field.setStringValue_("✓  Corrected")
            ctrl._phase_field.setTextColor_(result_green)
            ctrl._text_field.setStringValue_(corrected)
            ctrl._text_field.setTextColor_(result_green)
            ctrl._panel.orderFront_(None)
            ctrl.performSelector_withObject_afterDelay_("doHide:", None, dur)

        ctrl.performSelectorOnMainThread_withObject_waitUntilDone_("dispatchBlock:", _show, False)

    def hide(self) -> None:
        ctrl = self._controller
        if ctrl is None:
            return

        def _hide() -> None:
            NSObject.cancelPreviousPerformRequestsWithTarget_selector_object_(
                ctrl, "doHide:", None
            )
            if ctrl._panel is not None:
                ctrl._panel.orderOut_(None)

        ctrl.performSelectorOnMainThread_withObject_waitUntilDone_("dispatchBlock:", _hide, False)
