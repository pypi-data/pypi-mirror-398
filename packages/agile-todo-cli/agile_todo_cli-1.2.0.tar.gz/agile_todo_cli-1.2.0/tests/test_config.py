"""Tests for config module."""

import pytest
import yaml
from pathlib import Path

from todo_cli.config import (
    Config, get_config, get_config_warnings, reload_config, save_config,
    VALID_PRIORITIES, VALID_DATE_FORMATS, VALID_TIME_FORMATS, VALID_COLOR_SCHEMES,
)


class TestConfigDefaults:
    """Test default config values."""

    def test_default_priority(self, config_with_defaults):
        assert config_with_defaults.default_priority == "p2"

    def test_default_date_format(self, config_with_defaults):
        assert config_with_defaults.date_format == "YYYY-MM-DD"

    def test_default_time_format(self, config_with_defaults):
        assert config_with_defaults.time_format == "24h"

    def test_default_color_scheme(self, config_with_defaults):
        assert config_with_defaults.color_scheme == "auto"

    def test_default_confirm_delete(self, config_with_defaults):
        assert config_with_defaults.confirm_delete is True

    def test_default_auto_start_on_add(self, config_with_defaults):
        assert config_with_defaults.auto_start_on_add is False

    def test_default_show_completed_in_list(self, config_with_defaults):
        assert config_with_defaults.show_completed_in_list is False

    def test_default_db_path(self, config_with_defaults):
        assert config_with_defaults.db_path is None


class TestConfigDateFormat:
    """Test date format conversion."""

    def test_yyyy_mm_dd(self):
        config = Config(date_format="YYYY-MM-DD")
        assert config.get_date_format_str() == "%Y-%m-%d"

    def test_mm_dd_yyyy(self):
        config = Config(date_format="MM/DD/YYYY")
        assert config.get_date_format_str() == "%m/%d/%Y"

    def test_dd_mm_yyyy(self):
        config = Config(date_format="DD/MM/YYYY")
        assert config.get_date_format_str() == "%d/%m/%Y"

    def test_dd_mm_yyyy_hyphen(self):
        config = Config(date_format="DD-MM-YYYY")
        assert config.get_date_format_str() == "%d-%m-%Y"

    def test_unknown_format_returns_default(self):
        config = Config(date_format="UNKNOWN")
        assert config.get_date_format_str() == "%Y-%m-%d"


class TestConfigTimeFormat:
    """Test time format conversion."""

    def test_24h_format(self):
        config = Config(time_format="24h")
        assert config.get_time_format_str() == "%H:%M"

    def test_12h_format(self):
        config = Config(time_format="12h")
        assert config.get_time_format_str() == "%I:%M %p"

    def test_unknown_format_defaults_to_24h(self):
        config = Config(time_format="unknown")
        assert config.get_time_format_str() == "%H:%M"


class TestConfigDbPath:
    """Test database path configuration."""

    def test_default_db_path(self, config_with_defaults):
        path = config_with_defaults.get_db_path()
        assert path == Path.home() / ".local" / "share" / "todo-cli" / "todos.db"

    def test_custom_db_path(self):
        config = Config(db_path="/tmp/custom.db")
        assert config.get_db_path() == Path("/tmp/custom.db")

    def test_tilde_expansion(self):
        config = Config(db_path="~/mydata/todos.db")
        path = config.get_db_path()
        assert path == Path.home() / "mydata" / "todos.db"


class TestConfigSaveLoad:
    """Test config save and load."""

    def test_save_creates_file(self, temp_config):
        config = Config()
        config.save(temp_config)
        assert temp_config.exists()

    def test_save_creates_parent_dirs(self, temp_dir):
        config_path = temp_dir / "nested" / "path" / "config.yaml"
        config = Config()
        config.save(config_path)
        assert config_path.exists()

    def test_load_nonexistent_returns_defaults(self, temp_dir):
        config, warnings = Config.load(temp_dir / "nonexistent.yaml")
        assert config.default_priority == "p2"
        assert config.confirm_delete is True
        assert warnings == []

    def test_save_and_load_roundtrip(self, temp_config):
        original = Config(
            default_priority="p0",
            date_format="MM/DD/YYYY",
            time_format="12h",
            color_scheme="dark",
            confirm_delete=False,
            auto_start_on_add=True,
            show_completed_in_list=True,
        )
        original.save(temp_config)

        loaded, warnings = Config.load(temp_config)
        assert loaded.default_priority == "p0"
        assert loaded.date_format == "MM/DD/YYYY"
        assert loaded.time_format == "12h"
        assert loaded.color_scheme == "dark"
        assert loaded.confirm_delete is False
        assert loaded.auto_start_on_add is True
        assert loaded.show_completed_in_list is True
        assert warnings == []

    def test_load_ignores_unknown_keys(self, temp_config):
        with open(temp_config, "w") as f:
            yaml.dump({"unknown_key": "value", "default_priority": "p1"}, f)

        config, warnings = Config.load(temp_config)
        assert config.default_priority == "p1"
        assert not hasattr(config, "unknown_key")

    def test_load_handles_invalid_yaml(self, temp_config):
        with open(temp_config, "w") as f:
            f.write("invalid: yaml: content: [")

        config, warnings = Config.load(temp_config)
        assert config.default_priority == "p2"  # Returns defaults
        assert len(warnings) == 1
        assert "Error loading config" in warnings[0]

    def test_save_omits_none_values(self, temp_config):
        config = Config(db_path=None)
        config.save(temp_config)

        with open(temp_config) as f:
            data = yaml.safe_load(f)

        assert "db_path" not in data


class TestGlobalConfig:
    """Test global config singleton."""

    def test_get_config_returns_config(self):
        config = get_config()
        assert isinstance(config, Config)

    def test_get_config_is_cached(self):
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_reload_config_creates_new_instance(self):
        config1 = get_config()
        config2 = reload_config()
        assert config1 is not config2

    def test_save_config_updates_global(self, temp_config, monkeypatch):
        import todo_cli.config as config_module
        monkeypatch.setattr(config_module, "DEFAULT_CONFIG_PATH", temp_config)

        new_config = Config(default_priority="p0")
        save_config(new_config)

        assert get_config().default_priority == "p0"


class TestConfigValidation:
    """Test config validation."""

    def test_valid_config_no_warnings(self):
        config = Config()
        warnings = config.validate()
        assert warnings == []

    def test_invalid_priority_warning(self):
        config = Config(default_priority="invalid")
        warnings = config.validate()
        assert len(warnings) == 1
        assert "Invalid default_priority" in warnings[0]
        assert "invalid" in warnings[0]

    def test_invalid_date_format_warning(self):
        config = Config(date_format="INVALID")
        warnings = config.validate()
        assert len(warnings) == 1
        assert "Invalid date_format" in warnings[0]

    def test_invalid_time_format_warning(self):
        config = Config(time_format="invalid")
        warnings = config.validate()
        assert len(warnings) == 1
        assert "Invalid time_format" in warnings[0]

    def test_invalid_color_scheme_warning(self):
        config = Config(color_scheme="rainbow")
        warnings = config.validate()
        assert len(warnings) == 1
        assert "Invalid color_scheme" in warnings[0]

    def test_multiple_invalid_values(self):
        config = Config(
            default_priority="bad",
            date_format="bad",
            time_format="bad",
            color_scheme="bad",
        )
        warnings = config.validate()
        assert len(warnings) == 4

    def test_load_with_invalid_values_returns_warnings(self, temp_config):
        with open(temp_config, "w") as f:
            yaml.dump({
                "default_priority": "invalid",
                "date_format": "BADFORMAT",
            }, f)

        config, warnings = Config.load(temp_config)
        assert len(warnings) == 2
        assert any("default_priority" in w for w in warnings)
        assert any("date_format" in w for w in warnings)

    def test_load_without_validation(self, temp_config):
        with open(temp_config, "w") as f:
            yaml.dump({"default_priority": "invalid"}, f)

        config, warnings = Config.load(temp_config, validate=False)
        assert config.default_priority == "invalid"
        assert warnings == []

    def test_valid_priority_values(self):
        for priority in VALID_PRIORITIES:
            config = Config(default_priority=priority)
            warnings = config.validate()
            assert not any("priority" in w.lower() for w in warnings)

    def test_valid_date_format_values(self):
        for fmt in VALID_DATE_FORMATS:
            config = Config(date_format=fmt)
            warnings = config.validate()
            assert not any("date_format" in w for w in warnings)

    def test_valid_time_format_values(self):
        for fmt in VALID_TIME_FORMATS:
            config = Config(time_format=fmt)
            warnings = config.validate()
            assert not any("time_format" in w for w in warnings)

    def test_valid_color_scheme_values(self):
        for scheme in VALID_COLOR_SCHEMES:
            config = Config(color_scheme=scheme)
            warnings = config.validate()
            assert not any("color_scheme" in w for w in warnings)


class TestConfigWarningsGlobal:
    """Test global config warnings."""

    def test_get_config_warnings_empty_for_valid(self, temp_config, monkeypatch):
        import todo_cli.config as config_module
        monkeypatch.setattr(config_module, "DEFAULT_CONFIG_PATH", temp_config)

        Config().save(temp_config)
        config_module._config = None
        config_module._config_warnings = []

        get_config()
        assert get_config_warnings() == []

    def test_get_config_warnings_populated_for_invalid(self, temp_config, monkeypatch):
        import todo_cli.config as config_module
        monkeypatch.setattr(config_module, "DEFAULT_CONFIG_PATH", temp_config)

        with open(temp_config, "w") as f:
            yaml.dump({"default_priority": "bad"}, f)

        config_module._config = None
        config_module._config_warnings = []

        get_config()
        warnings = get_config_warnings()
        assert len(warnings) == 1
        assert "default_priority" in warnings[0]
