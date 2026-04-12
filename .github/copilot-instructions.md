# Vibing Linux – Project Guidelines

Offline voice-to-text for Linux (and macOS) with optional LLM correction. Hold a hotkey → record → release → transcribe → correct → clipboard → optional auto-paste.

See [README.md](../README.md) for feature overview and [CONTRIBUTING.md](../CONTRIBUTING.md) for setup and PR workflow.

---

## Build & Test

```bash
pip install -e ".[dev]"   # dev install (editable)
pytest                    # all tests
pytest tests/unit/        # unit only
pytest tests/integration/ # integration only
pytest --cov=vibing       # with coverage
ruff check vibing/ tests/ # lint
ruff format vibing/       # format
python -m vibing         # run the app
vibing-linux configure    # interactive config wizard
```

---

## Architecture

```
main()
 ├── load_config()                    # YAML + deep-merge with DEFAULTS
 ├── create_asr_provider(config)      # FasterWhisperProvider | OpenAIWhisperProvider
 ├── create_llm_provider(config)      # LlamaCppProvider | OpenAIProvider | AnthropicProvider | None
 ├── get_platform_factory()           # LinuxPlatformFactory | MacOSPlatformFactory (via entry points)
 └── VibingApp(config, factory, asr, llm)
      ├── AudioRecorder              # sounddevice, 16 kHz mono
      ├── HotkeyProvider             # evdev (Linux) | pynput (macOS)
      ├── TrayProvider               # pystray-based
      └── ClipboardProvider          # xclip/xsel/wl-copy (Linux) | pbcopy (macOS)
```

**Pipeline** (in `VibingApp._process()`): hotkey release → duration check → `asr.transcribe()` → `llm.correct()` → `clipboard.copy()` → optional `clipboard.paste()`.

Processing runs in a **daemon thread**; the tray loop runs on the main thread and blocks for the app lifetime.

### Provider base classes

| Interface | Location | Key methods |
|-----------|----------|-------------|
| `ASRProvider` (ABC) | `vibing/providers/asr/base.py` | `load_model()`, `transcribe(audio, ...) → str` |
| `LLMProvider` (ABC) | `vibing/providers/llm/base.py` | `load_model()`, `correct(text, ...) → str` |
| `PlatformFactory` (Protocol) | `vibing/platform/base.py` | `clipboard`, `create_hotkey()`, `create_tray()`, `system` |

Platform factories are discovered at runtime via `importlib.metadata` entry points defined in `pyproject.toml` (`vibing.platforms` group) – no hardcoded `sys.platform` checks in core code.

### Adding providers

- **ASR:** subclass `ASRProvider` in `vibing/providers/asr/`, register in `create_asr_provider()` in `vibing/asr.py`.  
- **LLM:** subclass `LLMProvider` in `vibing/providers/llm/`, register in `create_llm_provider()` in `vibing/llm.py`.  
- **Platform:** implement `PlatformFactory` Protocol, add entry point in `pyproject.toml`.

---

## Conventions

- **Python 3.10+** – use modern type hints: `dict[str, Any]`, `X | None`, etc.
- **All imports at top level** – never inside functions, methods, `if` blocks, or `try` blocks. This is a hard rule.
- **Lazy model loading** – both ASR and LLM providers defer `load_model()` to first use, keeping startup instant. Do not eagerly load heavy resources.
- **Graceful degradation** – if the LLM model is missing or fails to load, the app falls back to raw transcription without crashing. Preserve this pattern.
- **Ruff** is the only linter/formatter – run before committing. No pylint, flake8, or black.

---

## Key Files

| File | Purpose |
|------|---------|
| `vibing/app.py` | `VibingApp` – main orchestrator, pipeline, state machine |
| `vibing/config.py` | `DEFAULTS` schema, `load_config()`, deep-merge + validation |
| `vibing/asr.py` | `create_asr_provider()` factory |
| `vibing/llm.py` | `create_llm_provider()` factory |
| `vibing/audio.py` | `AudioRecorder` – sounddevice-based 16 kHz mono recording |
| `vibing/platform/loader.py` | `get_platform_factory()` – entry-point discovery |
| `vibing/platform/base.py` | `PlatformFactory` Protocol, `AppState` enum, provider Protocols |
| `vibing/setup.py` | `run_first_time_setup()` – model download, permission checks |
| `tests/conftest.py` | Shared fixtures: `MockASRProvider`, `MockLLMProvider`, `default_config`, temp path isolation |

---

## Gotchas

- **Linux hotkey** requires the user to be in the `input` group.  
- **Clipboard tools** (`xclip`, `xsel`, or `wl-clipboard`) must be installed; paste additionally needs `xdotool`/`ydotool`/`wtype`.  
- **Audio sample rate is fixed at 16 kHz mono** – all ASR providers assume this.  
- **Config is read once at startup** – changes to `~/.config/vibing-linux/config.yaml` require a restart.  
- **Cancel (ESC) is checked only at discrete points** in the pipeline, not mid-API-call.  
- **macOS platform defaults differ** (`hotkey.key` is `Key.cmd_r`, `asr.device` is `auto`, `compute_type` is `int8`) – set in `config.py` via `sys.platform` check.
