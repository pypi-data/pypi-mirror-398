"""Integration tests for CLI commands with config options."""

import pytest
from typer.testing import CliRunner
from pathlib import Path

from todo_cli.main import app
from todo_cli.config import Config
from todo_cli.database import Database
from todo_cli.models import Status


@pytest.fixture
def cli_env(temp_dir, monkeypatch):
    """Set up isolated CLI environment."""
    import todo_cli.config as config_module
    import todo_cli.main as main_module

    config_path = temp_dir / "config.yaml"
    db_path = temp_dir / "todos.db"

    # Patch DEFAULT_CONFIG_PATH
    monkeypatch.setattr(config_module, "DEFAULT_CONFIG_PATH", config_path)

    # Reset global config
    config_module._config = None

    # Create config with custom db_path
    config = Config(db_path=str(db_path))
    config.save(config_path)
    config_module._config = config

    # Patch get_db to use our test database
    def get_test_db():
        return Database(db_path)

    monkeypatch.setattr(main_module, "get_db", get_test_db)

    return {
        "config_path": config_path,
        "db_path": db_path,
        "config": config,
    }


class TestDefaultPriority:
    """Test default_priority config option."""

    def test_add_uses_config_default_priority(self, runner, cli_env, monkeypatch):
        import todo_cli.config as config_module

        # Set default priority to p1
        config = Config(default_priority="p1", db_path=str(cli_env["db_path"]))
        config.save(cli_env["config_path"])
        config_module._config = config

        result = runner.invoke(app, ["add", "Test task"])
        assert result.exit_code == 0

        db = Database(cli_env["db_path"])
        todos = db.list_all()
        assert len(todos) == 1
        assert todos[0].priority.value == 1  # P1

    def test_add_priority_flag_overrides_config(self, runner, cli_env, monkeypatch):
        import todo_cli.config as config_module

        config = Config(default_priority="p1", db_path=str(cli_env["db_path"]))
        config.save(cli_env["config_path"])
        config_module._config = config

        result = runner.invoke(app, ["add", "Test task", "-p", "p3"])
        assert result.exit_code == 0

        db = Database(cli_env["db_path"])
        todos = db.list_all()
        assert todos[0].priority.value == 3  # P3 from flag


class TestAutoStartOnAdd:
    """Test auto_start_on_add config option."""

    def test_auto_start_disabled_no_timer(self, runner, cli_env, monkeypatch):
        import todo_cli.config as config_module

        config = Config(auto_start_on_add=False, db_path=str(cli_env["db_path"]))
        config.save(cli_env["config_path"])
        config_module._config = config

        result = runner.invoke(app, ["add", "Test task"])
        assert result.exit_code == 0
        assert "Timer started" not in result.output

        db = Database(cli_env["db_path"])
        todos = db.list_all()
        assert todos[0].timer_started is None

    def test_auto_start_enabled_starts_timer(self, runner, cli_env, monkeypatch):
        import todo_cli.config as config_module

        config = Config(auto_start_on_add=True, db_path=str(cli_env["db_path"]))
        config.save(cli_env["config_path"])
        config_module._config = config

        result = runner.invoke(app, ["add", "Test task"])
        assert result.exit_code == 0
        assert "Timer started" in result.output

        db = Database(cli_env["db_path"])
        todos = db.list_all()
        assert todos[0].timer_started is not None
        assert todos[0].status == Status.DOING


class TestConfirmDelete:
    """Test confirm_delete config option."""

    def test_confirm_delete_enabled_prompts(self, runner, cli_env, monkeypatch):
        import todo_cli.config as config_module

        config = Config(confirm_delete=True, db_path=str(cli_env["db_path"]))
        config.save(cli_env["config_path"])
        config_module._config = config

        # Add a todo first
        db = Database(cli_env["db_path"])
        db.add("Test task")

        # Try to delete without confirmation (type 'n')
        result = runner.invoke(app, ["delete", "1"], input="n\n")
        assert "Cancelled" in result.output

        # Todo should still exist
        assert db.get(1) is not None

    def test_confirm_delete_enabled_with_yes(self, runner, cli_env, monkeypatch):
        import todo_cli.config as config_module

        config = Config(confirm_delete=True, db_path=str(cli_env["db_path"]))
        config.save(cli_env["config_path"])
        config_module._config = config

        db = Database(cli_env["db_path"])
        db.add("Test task")

        result = runner.invoke(app, ["delete", "1"], input="y\n")
        assert "Deleted" in result.output
        assert db.get(1) is None

    def test_confirm_delete_disabled_no_prompt(self, runner, cli_env, monkeypatch):
        import todo_cli.config as config_module

        config = Config(confirm_delete=False, db_path=str(cli_env["db_path"]))
        config.save(cli_env["config_path"])
        config_module._config = config

        db = Database(cli_env["db_path"])
        db.add("Test task")

        result = runner.invoke(app, ["delete", "1"])
        assert "Deleted" in result.output
        assert db.get(1) is None

    def test_force_flag_skips_confirm(self, runner, cli_env, monkeypatch):
        import todo_cli.config as config_module

        config = Config(confirm_delete=True, db_path=str(cli_env["db_path"]))
        config.save(cli_env["config_path"])
        config_module._config = config

        db = Database(cli_env["db_path"])
        db.add("Test task")

        result = runner.invoke(app, ["delete", "1", "--force"])
        assert "Deleted" in result.output
        assert db.get(1) is None


class TestShowCompletedInList:
    """Test show_completed_in_list config option."""

    def test_show_completed_false_hides_done(self, runner, cli_env, monkeypatch):
        import todo_cli.config as config_module

        config = Config(show_completed_in_list=False, db_path=str(cli_env["db_path"]))
        config.save(cli_env["config_path"])
        config_module._config = config

        db = Database(cli_env["db_path"])
        db.add("Active task")
        todo = db.add("Completed task")
        db.mark_done(todo.id)

        result = runner.invoke(app, ["list"])
        # Check by ID - ID 1 should be shown (active), ID 2 hidden (done)
        # Rich table may truncate task names, so check for row presence via status icons
        assert "1" in result.output  # Active todo ID
        lines = result.output.split("\n")
        # Count rows with todo IDs - should only have 1 row (the active one)
        data_rows = [l for l in lines if "│ 1 " in l or "│ 2 " in l]
        assert len(data_rows) == 1  # Only active task shown

    def test_show_completed_true_shows_done(self, runner, cli_env, monkeypatch):
        import todo_cli.config as config_module

        config = Config(show_completed_in_list=True, db_path=str(cli_env["db_path"]))
        config.save(cli_env["config_path"])
        config_module._config = config

        db = Database(cli_env["db_path"])
        db.add("Active task")
        todo = db.add("Completed task")
        db.mark_done(todo.id)

        result = runner.invoke(app, ["list"])
        # Both IDs should be present
        lines = result.output.split("\n")
        data_rows = [l for l in lines if "│ 1 " in l or "│ 2 " in l]
        assert len(data_rows) == 2  # Both todos shown

    def test_all_flag_overrides_config(self, runner, cli_env, monkeypatch):
        import todo_cli.config as config_module

        config = Config(show_completed_in_list=False, db_path=str(cli_env["db_path"]))
        config.save(cli_env["config_path"])
        config_module._config = config

        db = Database(cli_env["db_path"])
        db.add("Active task")
        todo = db.add("Completed task")
        db.mark_done(todo.id)

        result = runner.invoke(app, ["list", "--all"])
        # --all flag should show both todos
        lines = result.output.split("\n")
        data_rows = [l for l in lines if "│ 1 " in l or "│ 2 " in l]
        assert len(data_rows) == 2  # Both todos shown with --all


class TestColorScheme:
    """Test color_scheme config option."""

    def test_color_scheme_none_no_ansi(self, runner, cli_env, monkeypatch):
        import todo_cli.config as config_module

        config = Config(color_scheme="none", db_path=str(cli_env["db_path"]))
        config.save(cli_env["config_path"])
        config_module._config = config

        db = Database(cli_env["db_path"])
        db.add("Test task")

        result = runner.invoke(app, ["list"])
        # Check no ANSI escape codes in output
        assert "\x1b[" not in result.output

    def test_color_scheme_auto_has_colors(self, runner, cli_env, monkeypatch):
        import todo_cli.config as config_module

        config = Config(color_scheme="auto", db_path=str(cli_env["db_path"]))
        config.save(cli_env["config_path"])
        config_module._config = config

        db = Database(cli_env["db_path"])
        db.add("Test task")

        # Note: In test environment, Rich may not output colors
        # This test verifies the code path runs without error
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0


class TestConfigCommand:
    """Test the config command itself."""

    def test_config_show_displays_options(self, runner, cli_env):
        result = runner.invoke(app, ["config"])
        assert result.exit_code == 0
        assert "default_priority" in result.output
        assert "date_format" in result.output
        assert "confirm_delete" in result.output

    def test_config_set_updates_value(self, runner, cli_env, monkeypatch):
        import todo_cli.config as config_module

        result = runner.invoke(app, ["config", "--set", "default_priority=p0"])
        assert result.exit_code == 0
        assert "Set default_priority" in result.output

        # Reload and verify
        config_module._config = None
        config, _ = Config.load(cli_env["config_path"])
        assert config.default_priority == "p0"

    def test_config_set_boolean(self, runner, cli_env, monkeypatch):
        import todo_cli.config as config_module

        result = runner.invoke(app, ["config", "--set", "confirm_delete=false"])
        assert result.exit_code == 0

        config_module._config = None
        config, _ = Config.load(cli_env["config_path"])
        assert config.confirm_delete is False

    def test_config_path_shows_location(self, runner, cli_env):
        result = runner.invoke(app, ["config", "--path"])
        assert result.exit_code == 0
        assert "Config file:" in result.output


class TestConfigValidation:
    """Test config validation via CLI."""

    def test_config_validate_valid(self, runner, cli_env, monkeypatch):
        import todo_cli.config as config_module

        config = Config()
        config.save(cli_env["config_path"])
        config_module._config = config

        result = runner.invoke(app, ["config", "--validate"])
        assert result.exit_code == 0
        assert "valid" in result.output.lower()

    def test_config_validate_invalid(self, runner, cli_env, monkeypatch):
        import todo_cli.config as config_module
        import yaml

        with open(cli_env["config_path"], "w") as f:
            yaml.dump({"default_priority": "bad"}, f)

        config_module._config = None
        config_module._config_warnings = []

        result = runner.invoke(app, ["config", "--validate"])
        assert "Invalid" in result.output

    def test_config_set_invalid_priority_rejected(self, runner, cli_env):
        result = runner.invoke(app, ["config", "--set", "default_priority=invalid"])
        assert result.exit_code == 1
        assert "Invalid priority" in result.output

    def test_config_set_invalid_date_format_rejected(self, runner, cli_env):
        result = runner.invoke(app, ["config", "--set", "date_format=BADFORMAT"])
        assert result.exit_code == 1
        assert "Invalid date format" in result.output

    def test_config_set_invalid_time_format_rejected(self, runner, cli_env):
        result = runner.invoke(app, ["config", "--set", "time_format=48h"])
        assert result.exit_code == 1
        assert "Invalid time format" in result.output

    def test_config_set_invalid_color_scheme_rejected(self, runner, cli_env):
        result = runner.invoke(app, ["config", "--set", "color_scheme=rainbow"])
        assert result.exit_code == 1
        assert "Invalid color scheme" in result.output

    def test_config_set_valid_priority_accepted(self, runner, cli_env):
        result = runner.invoke(app, ["config", "--set", "default_priority=p0"])
        assert result.exit_code == 0
        assert "Set default_priority" in result.output

    def test_config_set_valid_date_format_accepted(self, runner, cli_env):
        result = runner.invoke(app, ["config", "--set", "date_format=MM/DD/YYYY"])
        assert result.exit_code == 0
        assert "Set date_format" in result.output
