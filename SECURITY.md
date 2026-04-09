# Security Policy

## Reporting a vulnerability

If you discover a security vulnerability, please report it responsibly:

**Email:** sami.alzein@hotmail.com

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact

Do **not** open a public GitHub issue for security vulnerabilities.

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Security considerations

### API keys

Vibing Linux can store API keys for hosted providers (OpenAI, Anthropic) in `~/.config/vibing-linux/config.yaml`. This file is created with restricted permissions (`0600`, owner-read/write only).

**Best practices:**
- Prefer environment variables (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) over config file storage
- Never commit your config file to version control
- Rotate API keys if you suspect they have been exposed

### Local models

When using local providers (Faster Whisper, llama.cpp), no data leaves your machine. Audio and text are processed entirely on-device.

### Hosted providers

When using hosted providers, audio data (for ASR) or transcribed text (for LLM) is sent to third-party APIs. Review the respective provider's privacy policy:
- [OpenAI Privacy Policy](https://openai.com/privacy/)
- [Anthropic Privacy Policy](https://www.anthropic.com/privacy)
