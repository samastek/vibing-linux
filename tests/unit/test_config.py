"""Tests for vibing.config."""

from __future__ import annotations

import copy

import pytest
import yaml

from vibing.config import DEFAULTS, _deep_merge, _validate, load_config, save_default_config


class TestDeepMerge:
    def test_flat_merge(self):
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_merge(self):
        base = {"x": {"a": 1, "b": 2}}
        override = {"x": {"b": 3}}
        result = _deep_merge(base, override)
        assert result == {"x": {"a": 1, "b": 3}}

    def test_no_mutation_of_base(self):
        base = {"x": {"a": 1}}
        override = {"x": {"b": 2}}
        original = copy.deepcopy(base)
        _deep_merge(base, override)
        assert base == original

    def test_override_replaces_non_dict_with_dict(self):
        base = {"x": 1}
        override = {"x": {"nested": True}}
        result = _deep_merge(base, override)
        assert result == {"x": {"nested": True}}


class TestValidate:
    def test_valid_defaults(self):
        _validate(DEFAULTS)  # should not raise

    def test_invalid_asr_provider(self):
        config = copy.deepcopy(DEFAULTS)
        config["asr"]["provider"] = "invalid_provider"
        with pytest.raises(ValueError, match="Invalid asr.provider"):
            _validate(config)

    def test_invalid_llm_provider(self):
        config = copy.deepcopy(DEFAULTS)
        config["llm"]["provider"] = "invalid_provider"
        with pytest.raises(ValueError, match="Invalid llm.provider"):
            _validate(config)

    def test_invalid_sample_rate(self):
        config = copy.deepcopy(DEFAULTS)
        config["audio"]["sample_rate"] = -1
        with pytest.raises(ValueError, match="sample_rate"):
            _validate(config)

    def test_none_provider_is_valid(self):
        config = copy.deepcopy(DEFAULTS)
        config["llm"]["provider"] = "none"
        _validate(config)  # should not raise


class TestLoadConfig:
    def test_load_defaults_when_no_file(self, tmp_config_dir):
        config = load_config()
        assert config["asr"]["provider"] == "faster_whisper"
        assert config["llm"]["provider"] == "llama_cpp"

    def test_load_merges_user_overrides(self, tmp_config_dir):
        config_file = tmp_config_dir["config_dir"] / "config.yaml"
        user_config = {"asr": {"model": "tiny"}, "auto_paste": False}
        config_file.write_text(yaml.dump(user_config))

        # Patch CONFIG_FILE to point to the written file
        import vibing.config

        vibing.config.CONFIG_FILE = config_file

        config = load_config()
        assert config["asr"]["model"] == "tiny"
        assert config["asr"]["provider"] == "faster_whisper"  # default preserved
        assert config["auto_paste"] is False


class TestSaveDefaultConfig:
    def test_creates_file(self, tmp_config_dir):
        import vibing.config

        config_file = vibing.config.CONFIG_FILE
        assert not config_file.exists()

        save_default_config()
        assert config_file.exists()

        with open(config_file) as f:
            saved = yaml.safe_load(f)
        assert saved["asr"]["provider"] == "faster_whisper"

    def test_does_not_overwrite(self, tmp_config_dir):
        import vibing.config

        config_file = vibing.config.CONFIG_FILE
        config_file.write_text("custom: true\n")

        save_default_config()

        with open(config_file) as f:
            content = f.read()
        assert "custom: true" in content
