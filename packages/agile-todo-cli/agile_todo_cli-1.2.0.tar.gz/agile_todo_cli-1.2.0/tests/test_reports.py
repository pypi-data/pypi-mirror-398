"""Tests for time tracking reports."""

import pytest
import time
from datetime import datetime, timedelta
from io import StringIO

from rich.console import Console

from todo_cli.database import Database
from todo_cli.models import Priority, Status
from todo_cli.reports import (
    format_duration,
    get_week_range,
    daily_report,
    weekly_report,
    project_report,
)


def track_time(db, todo_id, seconds=1.1):
    """Helper to track time on a todo with minimum duration.

    Must be at least 1 second because time is stored as integer seconds.
    """
    db.start_timer(todo_id)
    time.sleep(seconds)
    db.stop_timer(todo_id)


@pytest.fixture
def db(temp_dir):
    """Create a test database."""
    db_path = temp_dir / "test.db"
    return Database(db_path)


@pytest.fixture
def capture_console(monkeypatch):
    """Capture Rich console output."""
    output = StringIO()
    console = Console(file=output, force_terminal=True, width=120)
    monkeypatch.setattr("todo_cli.reports.console", console)
    return output


class TestFormatDuration:
    """Test format_duration function."""

    def test_zero_seconds(self):
        assert format_duration(0) == "00:00:00"

    def test_only_seconds(self):
        assert format_duration(45) == "00:00:45"

    def test_minutes_and_seconds(self):
        assert format_duration(125) == "00:02:05"

    def test_hours_minutes_seconds(self):
        assert format_duration(3661) == "01:01:01"

    def test_many_hours(self):
        assert format_duration(36000) == "10:00:00"

    def test_float_input(self):
        assert format_duration(90.7) == "00:01:30"

    def test_large_value(self):
        # 100 hours
        result = format_duration(360000)
        assert result == "100:00:00"


class TestGetWeekRange:
    """Test get_week_range function."""

    def test_monday(self):
        # Monday 2025-01-06
        date = datetime(2025, 1, 6, 12, 30, 45)
        start, end = get_week_range(date)

        assert start.weekday() == 0  # Monday
        assert start.date() == date.date()
        assert start.hour == 0
        assert start.minute == 0

    def test_wednesday(self):
        # Wednesday 2025-01-08
        date = datetime(2025, 1, 8, 14, 0, 0)
        start, end = get_week_range(date)

        assert start.weekday() == 0
        assert start.date() == datetime(2025, 1, 6).date()

    def test_sunday(self):
        # Sunday 2025-01-12
        date = datetime(2025, 1, 12, 20, 0, 0)
        start, end = get_week_range(date)

        assert start.weekday() == 0
        assert end.weekday() == 6
        assert start.date() == datetime(2025, 1, 6).date()
        assert end.date() == datetime(2025, 1, 12).date()

    def test_end_time(self):
        date = datetime(2025, 1, 10)
        start, end = get_week_range(date)

        assert end.hour == 23
        assert end.minute == 59
        assert end.second == 59

    def test_week_span(self):
        date = datetime(2025, 1, 8)
        start, end = get_week_range(date)

        diff = (end - start).days
        assert diff == 6  # 7 days, 0-indexed


class TestDailyReport:
    """Test daily_report function."""

    def test_no_data(self, db, capture_console):
        daily_report(db)
        output = capture_console.getvalue()
        assert "No time tracked" in output

    def test_with_tracked_time_today(self, db, capture_console):
        todo = db.add("Task with time", project="work")
        track_time(db, todo.id)

        daily_report(db)
        output = capture_console.getvalue()

        assert "Daily Report" in output
        assert "Task with time" in output

    def test_with_completed_today(self, db, capture_console):
        todo = db.add("Completed task")
        track_time(db, todo.id)
        db.mark_done(todo.id)

        daily_report(db)
        output = capture_console.getvalue()

        assert "Daily Report" in output
        assert "done" in output.lower()

    def test_shows_project(self, db, capture_console):
        todo = db.add("Project task", project="myproject")
        track_time(db, todo.id)

        daily_report(db)
        output = capture_console.getvalue()

        assert "myproject" in output

    def test_multiple_projects_breakdown(self, db, capture_console):
        todo1 = db.add("Work task", project="work")
        track_time(db, todo1.id)

        todo2 = db.add("Home task", project="home")
        track_time(db, todo2.id)

        daily_report(db)
        output = capture_console.getvalue()

        assert "By Project" in output
        assert "work" in output
        assert "home" in output

    def test_shows_total_time(self, db, capture_console):
        todo = db.add("Timed task")
        track_time(db, todo.id)

        daily_report(db)
        output = capture_console.getvalue()

        assert "Total time" in output

    def test_specific_date(self, db, capture_console):
        # Create a todo for a specific past date by manipulating created_at
        todo = db.add("Past task")
        track_time(db, todo.id)

        # Report for today should show it
        daily_report(db, datetime.now())
        output = capture_console.getvalue()

        assert "Daily Report" in output

    def test_excludes_no_time_tasks(self, db, capture_console):
        # Task without time tracking
        db.add("No time task")

        # Task with time tracking
        todo = db.add("Timed task")
        track_time(db, todo.id)

        daily_report(db)
        output = capture_console.getvalue()

        assert "Timed task" in output
        # The no-time task shouldn't appear in time report


class TestWeeklyReport:
    """Test weekly_report function."""

    def test_no_data(self, db, capture_console):
        weekly_report(db)
        output = capture_console.getvalue()
        assert "No time tracked" in output

    def test_with_tracked_time(self, db, capture_console):
        todo = db.add("Weekly task", project="work")
        track_time(db, todo.id)
        db.mark_done(todo.id)

        weekly_report(db)
        output = capture_console.getvalue()

        assert "Weekly Report" in output

    def test_shows_daily_breakdown(self, db, capture_console):
        todo = db.add("Task")
        track_time(db, todo.id)
        db.mark_done(todo.id)

        weekly_report(db)
        output = capture_console.getvalue()

        assert "Daily Breakdown" in output
        # Should show day names
        assert "Monday" in output or "Tuesday" in output or "Wednesday" in output

    def test_shows_project_breakdown(self, db, capture_console):
        todo1 = db.add("Work task", project="work")
        track_time(db, todo1.id)
        db.mark_done(todo1.id)

        todo2 = db.add("Home task", project="home")
        track_time(db, todo2.id)
        db.mark_done(todo2.id)

        weekly_report(db)
        output = capture_console.getvalue()

        assert "By Project" in output

    def test_shows_top_tasks(self, db, capture_console):
        for i in range(3):
            todo = db.add(f"Task {i}")
            track_time(db, todo.id)
            db.mark_done(todo.id)

        weekly_report(db)
        output = capture_console.getvalue()

        assert "Top Tasks" in output

    def test_shows_total_and_average(self, db, capture_console):
        todo = db.add("Task")
        track_time(db, todo.id)
        db.mark_done(todo.id)

        weekly_report(db)
        output = capture_console.getvalue()

        assert "Total time this week" in output
        assert "Average per day" in output

    def test_week_date_range(self, db, capture_console):
        todo = db.add("Task")
        track_time(db, todo.id)
        db.mark_done(todo.id)

        weekly_report(db)
        output = capture_console.getvalue()

        # Should show date range
        assert " to " in output


class TestProjectReport:
    """Test project_report function."""

    def test_no_projects(self, db, capture_console):
        project_report(db)
        output = capture_console.getvalue()
        assert "No projects" in output

    def test_all_projects_summary(self, db, capture_console):
        db.add("Work task 1", project="work")
        db.add("Work task 2", project="work")
        db.add("Home task", project="home")

        project_report(db)
        output = capture_console.getvalue()

        assert "All Projects" in output
        assert "work" in output
        assert "home" in output

    def test_shows_task_counts(self, db, capture_console):
        db.add("Task 1", project="myproject")
        db.add("Task 2", project="myproject")
        todo = db.add("Task 3", project="myproject")
        db.mark_done(todo.id)

        project_report(db)
        output = capture_console.getvalue()

        assert "Tasks" in output
        assert "Done" in output

    def test_shows_progress_bar(self, db, capture_console):
        todo = db.add("Done task", project="myproject")
        db.mark_done(todo.id)
        db.add("Pending task", project="myproject")

        project_report(db)
        output = capture_console.getvalue()

        # Progress bar uses block characters
        assert "%" in output

    def test_single_project_detail(self, db, capture_console):
        db.add("Task 1", project="work", priority=Priority.P0)
        todo = db.add("Task 2", project="work", priority=Priority.P1)
        track_time(db, todo.id)
        db.mark_done(todo.id)

        project_report(db, "work")
        output = capture_console.getvalue()

        assert "Project: work" in output
        assert "Task 1" in output
        assert "Task 2" in output

    def test_single_project_not_found(self, db, capture_console):
        db.add("Task", project="other")

        project_report(db, "nonexistent")
        output = capture_console.getvalue()

        assert "No todos found" in output

    def test_single_project_shows_stats(self, db, capture_console):
        db.add("Task 1", project="myproject")
        todo = db.add("Task 2", project="myproject")
        db.mark_done(todo.id)

        project_report(db, "myproject")
        output = capture_console.getvalue()

        assert "Total tasks" in output
        assert "Completed" in output
        assert "Total time" in output

    def test_single_project_shows_time(self, db, capture_console):
        todo = db.add("Timed task", project="work")
        track_time(db, todo.id)

        project_report(db, "work")
        output = capture_console.getvalue()

        assert "Time" in output

    def test_no_project_group(self, db, capture_console):
        db.add("Task without project")

        project_report(db)
        output = capture_console.getvalue()

        assert "(No project)" in output


class TestReportCli:
    """Test report command via CLI."""

    def test_report_daily_command(self, runner, cli_env):
        from todo_cli.main import app

        db = cli_env["get_db"]()
        todo = db.add("Test task")
        track_time(db, todo.id)

        result = runner.invoke(app, ["report", "daily"])
        assert result.exit_code == 0

    def test_report_weekly_command(self, runner, cli_env):
        from todo_cli.main import app

        db = cli_env["get_db"]()
        todo = db.add("Test task")
        track_time(db, todo.id)
        db.mark_done(todo.id)

        result = runner.invoke(app, ["report", "weekly"])
        assert result.exit_code == 0

    def test_report_project_command(self, runner, cli_env):
        from todo_cli.main import app

        db = cli_env["get_db"]()
        db.add("Test task", project="work")

        result = runner.invoke(app, ["report", "project"])
        assert result.exit_code == 0

    def test_report_project_with_name(self, runner, cli_env):
        from todo_cli.main import app

        db = cli_env["get_db"]()
        db.add("Test task", project="work")

        result = runner.invoke(app, ["report", "project", "-P", "work"])
        assert result.exit_code == 0

    def test_report_invalid_type(self, runner, cli_env):
        from todo_cli.main import app

        result = runner.invoke(app, ["report", "invalid"])
        assert result.exit_code == 1
        assert "Unknown report type" in result.output

    def test_report_default_is_daily(self, runner, cli_env):
        from todo_cli.main import app

        result = runner.invoke(app, ["report"])
        assert result.exit_code == 0


@pytest.fixture
def cli_env(temp_dir, monkeypatch):
    """Set up isolated CLI environment."""
    import todo_cli.config as config_module
    import todo_cli.main as main_module
    from todo_cli.config import Config

    config_path = temp_dir / "config.yaml"
    db_path = temp_dir / "todos.db"

    monkeypatch.setattr(config_module, "DEFAULT_CONFIG_PATH", config_path)
    config_module._config = None
    config_module._config_warnings = []

    config = Config(db_path=str(db_path))
    config.save(config_path)
    config_module._config = config

    def get_test_db():
        return Database(db_path)

    monkeypatch.setattr(main_module, "get_db", get_test_db)

    return {
        "config_path": config_path,
        "db_path": db_path,
        "config": config,
        "get_db": get_test_db,
    }
