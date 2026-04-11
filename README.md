# Vibing Linux

**Offline voice-to-text for Linux with LLM correction.**

Hold a hotkey to record your voice, release to transcribe. Optionally corrects grammar and punctuation using a local or hosted LLM. The result is copied to your clipboard and (optionally) pasted into the focused window.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Features

- **Local-first** — runs entirely offline with Faster Whisper + llama.cpp (no API keys needed)
- **Hosted providers** — optionally use OpenAI Whisper API, OpenAI chat, or Anthropic for transcription/correction
- **Global hotkey** — hold Right Alt (configurable) to record from any application
- **LLM correction** — fixes grammar, punctuation, and filler words automatically
- **System tray** — status indicator with idle/recording/processing/done states
- **Wayland & X11** — clipboard and paste support for both display servers
- **XDG-compliant** — config in `~/.config/vibing-linux/`, data in `~/.local/share/vibing-linux/`
- **Zero-config first run** — downloads models and creates config automatically

## Installation

### Option A: `.deb` package (recommended for Ubuntu/Debian)

Download the latest `.deb` from [GitHub Releases](https://github.com/VibeVoice/vibing-linux/releases), then:

```bash
sudo apt install ./vibing-linux_*.deb
```

This creates a virtual environment at `/opt/vibing-linux/`, installs dependencies, and auto-detects your GPU.

### Option B: pipx (any distro)

```bash

# Install
git clone https://github.com/VibeVoice/vibing-linux.git
cd vibing-linux
./install.sh            # auto-detects GPU
# or
./install.sh --cpu      # force CPU-only
./install.sh --cuda 12.8  # override CUDA version
```

### System requirements

- Linux (X11 or Wayland)
- Python 3.10+
- `libportaudio2` (audio recording)
- `wl-clipboard` or `xclip` or `xsel` (clipboard)
- User must be in the `input` group for global hotkeys:
  ```bash
  sudo usermod -aG input $USER
  # Log out and back in
  ```

## Usage

```bash
vibing-linux              # start (first run downloads models automatically)
vibing-linux configure    # interactive setup wizard
```

1. **Hold Right Alt** (or your configured hotkey) to start recording
2. **Release** to stop — transcription and correction happen automatically
3. The corrected text is **copied to clipboard** and optionally **pasted** into the focused window

## Configuration

Config file: `~/.config/vibing-linux/config.yaml`

Run `vibing-linux configure` for an interactive wizard, or edit the file directly:

```yaml
hotkey:
  key: KEY_RIGHTALT       # any evdev key name
  device: auto            # or a specific /dev/input/event* path

asr:
  provider: faster_whisper  # or: openai_whisper
  model: large-v3-turbo
  device: cuda              # or: cpu
  language: en

llm:
  provider: llama_cpp       # or: openai, anthropic, none
  model_path: ~/.local/share/vibing-linux/models/gemma-4-E2B-it-Q4_K_M.gguf

auto_paste: true
```

### Providers

| Component | Provider | Type | Notes |
|-----------|----------|------|-------|
| ASR | `faster_whisper` | Local | Default. Uses CTranslate2, supports GPU |
| ASR | `openai_whisper` | Hosted | Requires `OPENAI_API_KEY` or `asr.api_key` |
| LLM | `llama_cpp` | Local | Default. Runs GGUF models via llama.cpp |
| LLM | `openai` | Hosted | Any OpenAI-compatible API (Ollama, vLLM, etc.) |
| LLM | `anthropic` | Hosted | Anthropic Messages API |
| LLM | `none` | — | Disable LLM correction entirely |

### API keys

For hosted providers, set keys via environment variables or config:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

Or in `config.yaml`:

```yaml
asr:
  api_key: "sk-..."
llm:
  api_key: "sk-..."
```

> **Note:** The config file is stored with restricted permissions (owner-read/write only). Never commit it to version control.

## Development

```bash
# Clone and install in development mode
git clone https://github.com/VibeVoice/vibing-linux.git
cd vibing-linux
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check vibing/ tests/

# Run
python -m vibing
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Architecture

```
vibing/
├── app.py              Main orchestrator (VibingApp)
├── audio.py            Recording via sounddevice
├── clipboard.py        X11/Wayland clipboard operations
├── config.py           XDG-compliant configuration
├── configure.py        Interactive setup wizard
├── hotkey.py           Global hotkey via evdev
├── logging.py          Logger setup with file rotation
├── setup.py            First-run model download
├── tray.py             System tray icon (pystray)
└── providers/
    ├── asr/
    │   ├── base.py             ASR interface
    │   ├── faster_whisper.py   Local (CTranslate2)
    │   └── openai_whisper.py   Hosted (OpenAI API)
    └── llm/
        ├── base.py         LLM interface
        ├── llama_cpp.py    Local (GGUF)
        ├── openai.py       Hosted (OpenAI-compatible)
        └── anthropic.py    Hosted (Anthropic)
```

## License

[MIT](LICENSE) — Copyright (c) 2026 Sami Alzein
