"""Integration tests for config file round-trip."""

from __future__ import annotations

import yaml

from vibing.config import load_config, save_default_config


class TestConfigRoundTrip:
    def test_save_then_load(self, tmp_config_dir):
        save_default_config()

        config = load_config()

        assert config["asr"]["provider"] == "faster_whisper"
        assert config["llm"]["provider"] == "llama_cpp"
        assert config["audio"]["sample_rate"] == 16000
        assert config["auto_paste"] is True

    def test_user_override_preserved(self, tmp_config_dir):
        save_default_config()

        import vibing.config

        config_file = vibing.config.CONFIG_FILE

        with open(config_file) as f:
            cfg = yaml.safe_load(f)

        cfg["llm"]["provider"] = "openai"
        cfg["llm"]["api_key"] = "sk-test"

        with open(config_file, "w") as f:
            yaml.dump(cfg, f)

        loaded = load_config()
        assert loaded["llm"]["provider"] == "openai"
        assert loaded["llm"]["api_key"] == "sk-test"
        # Defaults for other fields preserved
        assert loaded["asr"]["model"] == "large-v3-turbo"
