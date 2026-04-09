# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-04-09

### Added

- Initial release
- Local ASR via Faster Whisper (CTranslate2)
- Hosted ASR via OpenAI Whisper API
- Local LLM correction via llama.cpp (GGUF models)
- Hosted LLM correction via OpenAI and Anthropic APIs
- Global hotkey support via evdev
- System tray icon with status indicators
- Wayland and X11 clipboard support
- XDG-compliant configuration
- First-run setup with automatic model download
- Interactive configuration wizard (`vibing-linux configure`)
- `.deb` packaging with GPU auto-detection
- pipx installation script
