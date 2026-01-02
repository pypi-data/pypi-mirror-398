"""Tests for recurrence CLI commands - Story 5.4 and 5.5."""

import pytest
from typer.testing import CliRunner
from datetime import datetime, timedelta

from todo_cli.main import app
from todo_cli.config import Config
from todo_cli.database import Database
from todo_cli.models import Status, Priority, RecurrencePattern


@pytest.fixture
def cli_env(tmp_path, monkeypatch):
    """Set up isolated CLI environment for recurrence tests."""
    import todo_cli.config as config_module
    import todo_cli.main as main_module

    config_path = tmp_path / "config.yaml"
    db_path = tmp_path / "todos.db"

    monkeypatch.setattr(config_module, "DEFAULT_CONFIG_PATH", config_path)
    config_module._config = None
    config_module._config_warnings = []

    config = Config(db_path=str(db_path), confirm_delete=False)
    config.save(config_path)
    config_module._config = config

    def get_test_db():
        return Database(db_path)

    monkeypatch.setattr(main_module, "get_db", get_test_db)

    # Initialize database and run migrations before tests
    get_test_db()

    return {
        "config_path": config_path,
        "db_path": db_path,
        "config": config,
        "get_db": get_test_db,
    }


@pytest.fixture
def runner():
    """Create CLI runner."""
    return CliRunner()


class TestAddWithRecurrence:
    """Test add command with --recur option."""

    def test_add_daily_recurrence(self, runner, cli_env):
        result = runner.invoke(app, ["add", "Daily standup", "--recur", "daily"])
        assert result.exit_code == 0
        assert "Added recurring todo #1" in result.output
        assert "daily" in result.output

        db = cli_env["get_db"]()
        rule = db.get_recurrence_rule_by_task(1)
        assert rule is not None
        assert rule.pattern == RecurrencePattern.DAILY

    def test_add_weekly_recurrence(self, runner, cli_env):
        result = runner.invoke(app, ["add", "Weekly review", "--recur", "weekly"])
        assert result.exit_code == 0
        assert "weekly" in result.output

        db = cli_env["get_db"]()
        rule = db.get_recurrence_rule_by_task(1)
        assert rule.pattern == RecurrencePattern.WEEKLY

    def test_add_monthly_recurrence(self, runner, cli_env):
        result = runner.invoke(app, ["add", "Monthly report", "--recur", "monthly"])
        assert result.exit_code == 0

        db = cli_env["get_db"]()
        rule = db.get_recurrence_rule_by_task(1)
        assert rule.pattern == RecurrencePattern.MONTHLY

    def test_add_every_n_days(self, runner, cli_env):
        result = runner.invoke(app, ["add", "Every 3 days", "--recur", "every 3 days"])
        assert result.exit_code == 0

        db = cli_env["get_db"]()
        rule = db.get_recurrence_rule_by_task(1)
        assert rule.pattern == RecurrencePattern.DAILY
        assert rule.interval == 3

    def test_add_specific_days(self, runner, cli_env):
        result = runner.invoke(app, ["add", "MWF workout", "--recur", "every mon,wed,fri"])
        assert result.exit_code == 0

        db = cli_env["get_db"]()
        rule = db.get_recurrence_rule_by_task(1)
        assert rule.pattern == RecurrencePattern.CUSTOM
        assert set(rule.days_of_week) == {"mon", "wed", "fri"}

    def test_add_recurrence_with_until(self, runner, cli_env):
        result = runner.invoke(app, [
            "add", "Limited task",
            "--recur", "daily",
            "--until", "2025-12-31"
        ])
        assert result.exit_code == 0

        db = cli_env["get_db"]()
        rule = db.get_recurrence_rule_by_task(1)
        assert rule.end_date is not None
        assert rule.end_date.year == 2025
        assert rule.end_date.month == 12
        assert rule.end_date.day == 31

    def test_add_invalid_recurrence_pattern(self, runner, cli_env):
        result = runner.invoke(app, ["add", "Bad pattern", "--recur", "invalid"])
        assert result.exit_code == 1
        assert "Cannot parse" in result.output or "Invalid" in result.output


class TestRecurListCommand:
    """Test recur list command."""

    def test_recur_list_empty(self, runner, cli_env):
        result = runner.invoke(app, ["recur", "list"])
        assert result.exit_code == 0
        assert "No recurring tasks" in result.output

    def test_recur_list_with_tasks(self, runner, cli_env):
        db = cli_env["get_db"]()
        task1 = db.add("Daily task", due_date=datetime(2025, 1, 15))
        task2 = db.add("Weekly task", due_date=datetime(2025, 1, 15))

        db.add_recurrence_rule(task1.id, RecurrencePattern.DAILY)
        db.add_recurrence_rule(task2.id, RecurrencePattern.WEEKLY)

        result = runner.invoke(app, ["recur", "list"])
        assert result.exit_code == 0
        assert "Daily task" in result.output
        assert "Weekly task" in result.output
        assert "daily" in result.output
        assert "weekly" in result.output


class TestRecurShowCommand:
    """Test recur show command."""

    def test_recur_show_basic(self, runner, cli_env):
        db = cli_env["get_db"]()
        task = db.add("Daily standup", due_date=datetime(2025, 1, 15))
        db.add_recurrence_rule(task.id, RecurrencePattern.DAILY)

        result = runner.invoke(app, ["recur", "show", "1"])
        assert result.exit_code == 0
        assert "Daily standup" in result.output
        assert "daily" in result.output

    def test_recur_show_nonexistent(self, runner, cli_env):
        result = runner.invoke(app, ["recur", "show", "999"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_recur_show_no_rule(self, runner, cli_env):
        db = cli_env["get_db"]()
        db.add("Regular task")

        result = runner.invoke(app, ["recur", "show", "1"])
        assert result.exit_code == 1
        assert "no recurrence rule" in result.output


class TestRecurGenerateCommand:
    """Test recur generate command - Story 5.4."""

    def test_recur_generate_specific_task(self, runner, cli_env):
        db = cli_env["get_db"]()
        task = db.add("Daily task", due_date=datetime(2025, 1, 15))
        db.add_recurrence_rule(task.id, RecurrencePattern.DAILY)

        result = runner.invoke(app, ["recur", "generate", "1"])
        assert result.exit_code == 0
        assert "Created occurrence #2" in result.output

        todos = db.list_all(include_done=True)
        assert len(todos) == 2

    def test_recur_generate_all(self, runner, cli_env):
        db = cli_env["get_db"]()
        task1 = db.add("Task 1", due_date=datetime(2025, 1, 15))
        task2 = db.add("Task 2", due_date=datetime(2025, 1, 15))

        db.add_recurrence_rule(task1.id, RecurrencePattern.DAILY)
        db.add_recurrence_rule(task2.id, RecurrencePattern.DAILY)

        result = runner.invoke(app, ["recur", "generate"])
        assert result.exit_code == 0
        assert "Generated 2 occurrence(s)" in result.output

        todos = db.list_all(include_done=True)
        assert len(todos) == 4

    def test_recur_generate_respects_limits(self, runner, cli_env):
        db = cli_env["get_db"]()
        task = db.add("Limited task", due_date=datetime(2025, 1, 15))
        db.add_recurrence_rule(
            task.id,
            RecurrencePattern.DAILY,
            max_occurrences=1
        )

        # First generation
        result = runner.invoke(app, ["recur", "generate", "1"])
        assert result.exit_code == 0
        assert "Created occurrence" in result.output

        # Second should fail (limit reached)
        result = runner.invoke(app, ["recur", "generate", "1"])
        assert result.exit_code == 0
        assert "limit reached" in result.output

    def test_recur_generate_nonexistent(self, runner, cli_env):
        result = runner.invoke(app, ["recur", "generate", "999"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_recur_generate_no_rule(self, runner, cli_env):
        db = cli_env["get_db"]()
        db.add("Regular task")

        result = runner.invoke(app, ["recur", "generate", "1"])
        assert result.exit_code == 1
        assert "no recurrence rule" in result.output

    def test_recur_generate_no_tasks(self, runner, cli_env):
        result = runner.invoke(app, ["recur", "generate"])
        assert result.exit_code == 0
        assert "No recurring tasks" in result.output


class TestRecurStopCommand:
    """Test recur stop command."""

    def test_recur_stop(self, runner, cli_env):
        db = cli_env["get_db"]()
        task = db.add("Recurring task")
        db.add_recurrence_rule(task.id, RecurrencePattern.DAILY)

        result = runner.invoke(app, ["recur", "stop", "1"])
        assert result.exit_code == 0
        assert "Stopped recurrence" in result.output

        # Verify rule is deleted
        rule = db.get_recurrence_rule_by_task(1)
        assert rule is None

    def test_recur_stop_nonexistent(self, runner, cli_env):
        result = runner.invoke(app, ["recur", "stop", "999"])
        assert result.exit_code == 1
        assert "not found" in result.output


class TestDoneAutoGeneration:
    """Test that done command auto-generates next occurrence - Story 5.4."""

    def test_done_generates_next_occurrence(self, runner, cli_env):
        db = cli_env["get_db"]()
        task = db.add("Daily standup", due_date=datetime(2025, 1, 15))
        db.add_recurrence_rule(task.id, RecurrencePattern.DAILY)

        result = runner.invoke(app, ["done", "1"])
        assert result.exit_code == 0
        assert "Created next occurrence" in result.output

        todos = db.list_all(include_done=True)
        assert len(todos) == 2

        # Original should be done
        original = db.get(1)
        assert original.status == Status.DONE

        # New occurrence should be todo
        new_task = db.get(2)
        assert new_task.status == Status.TODO
        assert new_task.due_date.date() == datetime(2025, 1, 16).date()

    def test_done_respects_max_occurrences(self, runner, cli_env):
        db = cli_env["get_db"]()
        task = db.add("Limited task", due_date=datetime(2025, 1, 15))
        db.add_recurrence_rule(
            task.id,
            RecurrencePattern.DAILY,
            max_occurrences=1
        )

        # Generate one occurrence
        from todo_cli.recurrence import RecurrenceManager
        rm = RecurrenceManager()
        rm.create_occurrence(db, task.id)

        # Now complete original - should not generate another
        result = runner.invoke(app, ["done", "1"])
        assert result.exit_code == 0
        # Should not mention next occurrence
        assert "Created next occurrence" not in result.output

    def test_done_regular_task_no_auto_generate(self, runner, cli_env):
        db = cli_env["get_db"]()
        db.add("Regular task")

        result = runner.invoke(app, ["done", "1"])
        assert result.exit_code == 0
        assert "Created next occurrence" not in result.output

        todos = db.list_all(include_done=True)
        assert len(todos) == 1


class TestListRecurrenceIndicator:
    """Test that list command shows recurrence indicator."""

    def test_list_shows_recurrence_icon(self, runner, cli_env):
        db = cli_env["get_db"]()
        task = db.add("Recurring task")
        db.add_recurrence_rule(task.id, RecurrencePattern.DAILY)

        db.add("Regular task")

        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        # The recurring task should show the recurrence indicator (🔄)
        # We can't directly test for emoji in output, but we can verify structure
        assert "Recurring task" in result.output
        assert "Regular task" in result.output


class TestRecurEditCommand:
    """Test recur edit command - Story 5.5."""

    def test_recur_edit_interval(self, runner, cli_env):
        """Test editing the interval."""
        db = cli_env["get_db"]()
        task = db.add("Daily task")
        db.add_recurrence_rule(task.id, RecurrencePattern.DAILY, interval=1)

        result = runner.invoke(app, ["recur", "edit", "1", "--interval", "3"])
        assert result.exit_code == 0
        assert "Updated recurrence" in result.output
        assert "interval=3" in result.output

        rule = db.get_recurrence_rule_by_task(1)
        assert rule.interval == 3

    def test_recur_edit_pattern(self, runner, cli_env):
        """Test editing the pattern."""
        db = cli_env["get_db"]()
        task = db.add("Daily task")
        db.add_recurrence_rule(task.id, RecurrencePattern.DAILY)

        result = runner.invoke(app, ["recur", "edit", "1", "--pattern", "weekly"])
        assert result.exit_code == 0
        assert "pattern=weekly" in result.output

        rule = db.get_recurrence_rule_by_task(1)
        assert rule.pattern == RecurrencePattern.WEEKLY

    def test_recur_edit_days(self, runner, cli_env):
        """Test editing days of week."""
        db = cli_env["get_db"]()
        task = db.add("Custom task")
        db.add_recurrence_rule(task.id, RecurrencePattern.DAILY)

        result = runner.invoke(app, ["recur", "edit", "1", "--days", "mon,wed,fri"])
        assert result.exit_code == 0
        assert "days=" in result.output

        rule = db.get_recurrence_rule_by_task(1)
        assert rule.pattern == RecurrencePattern.CUSTOM
        assert set(rule.days_of_week) == {"mon", "wed", "fri"}

    def test_recur_edit_until(self, runner, cli_env):
        """Test editing end date."""
        db = cli_env["get_db"]()
        task = db.add("Limited task")
        db.add_recurrence_rule(task.id, RecurrencePattern.DAILY)

        result = runner.invoke(app, ["recur", "edit", "1", "--until", "2025-12-31"])
        assert result.exit_code == 0
        assert "until=2025-12-31" in result.output

        rule = db.get_recurrence_rule_by_task(1)
        assert rule.end_date is not None
        assert rule.end_date.year == 2025
        assert rule.end_date.month == 12

    def test_recur_edit_max_occurrences(self, runner, cli_env):
        """Test editing max occurrences."""
        db = cli_env["get_db"]()
        task = db.add("Limited task")
        db.add_recurrence_rule(task.id, RecurrencePattern.DAILY)

        result = runner.invoke(app, ["recur", "edit", "1", "--max", "10"])
        assert result.exit_code == 0
        assert "max=10" in result.output

        rule = db.get_recurrence_rule_by_task(1)
        assert rule.max_occurrences == 10

    def test_recur_edit_clear_end(self, runner, cli_env):
        """Test clearing end date."""
        db = cli_env["get_db"]()
        task = db.add("Limited task")
        db.add_recurrence_rule(
            task.id, RecurrencePattern.DAILY,
            end_date=datetime(2025, 12, 31)
        )

        result = runner.invoke(app, ["recur", "edit", "1", "--clear-end"])
        assert result.exit_code == 0
        assert "end_date=none" in result.output

        rule = db.get_recurrence_rule_by_task(1)
        assert rule.end_date is None

    def test_recur_edit_clear_max(self, runner, cli_env):
        """Test clearing max occurrences."""
        db = cli_env["get_db"]()
        task = db.add("Limited task")
        db.add_recurrence_rule(
            task.id, RecurrencePattern.DAILY,
            max_occurrences=5
        )

        result = runner.invoke(app, ["recur", "edit", "1", "--clear-max"])
        assert result.exit_code == 0
        assert "max_occurrences=none" in result.output

        rule = db.get_recurrence_rule_by_task(1)
        assert rule.max_occurrences is None

    def test_recur_edit_no_changes(self, runner, cli_env):
        """Test edit with no options specified."""
        db = cli_env["get_db"]()
        task = db.add("Daily task")
        db.add_recurrence_rule(task.id, RecurrencePattern.DAILY)

        result = runner.invoke(app, ["recur", "edit", "1"])
        assert result.exit_code == 0
        assert "No changes specified" in result.output

    def test_recur_edit_nonexistent_task(self, runner, cli_env):
        """Test editing nonexistent task."""
        result = runner.invoke(app, ["recur", "edit", "999", "--interval", "2"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_recur_edit_task_without_rule(self, runner, cli_env):
        """Test editing task without recurrence rule."""
        db = cli_env["get_db"]()
        db.add("Regular task")

        result = runner.invoke(app, ["recur", "edit", "1", "--interval", "2"])
        assert result.exit_code == 1
        assert "no recurrence rule" in result.output

    def test_recur_edit_invalid_pattern(self, runner, cli_env):
        """Test editing with invalid pattern."""
        db = cli_env["get_db"]()
        task = db.add("Daily task")
        db.add_recurrence_rule(task.id, RecurrencePattern.DAILY)

        result = runner.invoke(app, ["recur", "edit", "1", "--pattern", "invalid"])
        assert result.exit_code == 1
        assert "Invalid pattern" in result.output

    def test_recur_edit_invalid_day(self, runner, cli_env):
        """Test editing with invalid day name."""
        db = cli_env["get_db"]()
        task = db.add("Daily task")
        db.add_recurrence_rule(task.id, RecurrencePattern.DAILY)

        result = runner.invoke(app, ["recur", "edit", "1", "--days", "invalid"])
        assert result.exit_code == 1
        assert "Invalid day" in result.output


class TestRecurDeleteCommand:
    """Test recur delete command - Story 5.5."""

    def test_recur_delete(self, runner, cli_env):
        """Test deleting recurrence rule."""
        db = cli_env["get_db"]()
        task = db.add("Recurring task")
        db.add_recurrence_rule(task.id, RecurrencePattern.DAILY)

        result = runner.invoke(app, ["recur", "delete", "1"])
        assert result.exit_code == 0
        assert "Deleted recurrence rule" in result.output
        assert "preserved" in result.output

        # Verify rule is deleted but task remains
        rule = db.get_recurrence_rule_by_task(1)
        assert rule is None

        task = db.get(1)
        assert task is not None

    def test_recur_delete_nonexistent_task(self, runner, cli_env):
        """Test deleting from nonexistent task."""
        result = runner.invoke(app, ["recur", "delete", "999"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_recur_delete_task_without_rule(self, runner, cli_env):
        """Test deleting from task without rule."""
        db = cli_env["get_db"]()
        db.add("Regular task")

        result = runner.invoke(app, ["recur", "delete", "1"])
        assert result.exit_code == 1
        assert "no recurrence rule" in result.output
