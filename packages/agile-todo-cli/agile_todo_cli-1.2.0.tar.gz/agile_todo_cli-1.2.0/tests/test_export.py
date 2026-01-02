"""Tests for export functionality."""

import csv
import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path

from todo_cli.database import Database
from todo_cli.export import (
    todo_to_dict,
    export_json,
    export_csv,
    export_markdown,
    export_todos,
)
from todo_cli.models import Todo, Priority, Status


@pytest.fixture
def db(temp_dir):
    """Create a test database with sample data."""
    db_path = temp_dir / "test.db"
    database = Database(db_path)
    return database


@pytest.fixture
def db_with_todos(db):
    """Database with sample todos for testing."""
    # Add various todos
    db.add("Task one", priority=Priority.P0, project="work", tags=["urgent"])
    db.add("Task two", priority=Priority.P1, project="work")
    db.add("Task three", priority=Priority.P2, project="home", tags=["shopping", "weekend"])

    # Add a completed task
    todo = db.add("Completed task", priority=Priority.P3)
    db.mark_done(todo.id)

    # Add a task with time tracking
    timed = db.add("Timed task", project="work")
    db.start_timer(timed.id)
    db.stop_timer(timed.id)

    # Add a task with due date
    db.add("Due task", due_date=datetime(2025, 12, 31))

    return db


class TestTodoToDict:
    """Test todo_to_dict function."""

    def test_basic_conversion(self, db):
        todo = db.add("Test task")
        result = todo_to_dict(todo)

        assert result["id"] == todo.id
        assert result["task"] == "Test task"
        assert result["status"] == "todo"
        assert "priority" in result
        assert "created_at" in result

    def test_with_project_and_tags(self, db):
        todo = db.add("Tagged task", project="myproject", tags=["tag1", "tag2"])
        result = todo_to_dict(todo)

        assert result["project"] == "myproject"
        assert result["tags"] == ["tag1", "tag2"]

    def test_with_due_date(self, db):
        due = datetime(2025, 6, 15)
        todo = db.add("Due task", due_date=due)
        result = todo_to_dict(todo)

        assert result["due_date"] == due.isoformat()

    def test_completed_todo(self, db):
        todo = db.add("Task to complete")
        db.mark_done(todo.id)
        completed = db.get(todo.id)
        result = todo_to_dict(completed)

        assert result["status"] == "done"
        assert result["completed_at"] is not None

    def test_time_spent_fields(self, db):
        todo = db.add("Timed task")
        db.start_timer(todo.id)
        db.stop_timer(todo.id)
        tracked = db.get(todo.id)
        result = todo_to_dict(tracked)

        assert "time_spent_seconds" in result
        assert "time_spent_formatted" in result
        assert result["time_spent_seconds"] >= 0

    def test_tracking_status(self, db):
        todo = db.add("Active task")
        result_before = todo_to_dict(todo)
        assert result_before["is_tracking"] is False

        db.start_timer(todo.id)
        active = db.get(todo.id)
        result_after = todo_to_dict(active)
        assert result_after["is_tracking"] is True

    def test_overdue_status(self, db):
        # Past due date
        past_due = datetime.now() - timedelta(days=1)
        todo = db.add("Overdue task", due_date=past_due)
        result = todo_to_dict(todo)
        assert result["is_overdue"] is True

        # Future due date
        future_due = datetime.now() + timedelta(days=7)
        todo2 = db.add("Future task", due_date=future_due)
        result2 = todo_to_dict(todo2)
        assert result2["is_overdue"] is False


class TestExportJson:
    """Test JSON export functionality."""

    def test_export_creates_file(self, db_with_todos, temp_dir):
        output = temp_dir / "export.json"
        result = export_json(db_with_todos, output)

        assert result == output
        assert output.exists()

    def test_export_auto_filename(self, db_with_todos, temp_dir, monkeypatch):
        monkeypatch.chdir(temp_dir)
        result = export_json(db_with_todos)

        assert result.exists()
        assert result.suffix == ".json"
        assert "todos-" in result.name

    def test_export_valid_json(self, db_with_todos, temp_dir):
        output = temp_dir / "export.json"
        export_json(db_with_todos, output)

        with open(output) as f:
            data = json.load(f)

        assert "exported_at" in data
        assert "total_count" in data
        assert "todos" in data
        assert isinstance(data["todos"], list)

    def test_export_includes_all_todos(self, db_with_todos, temp_dir):
        output = temp_dir / "export.json"
        export_json(db_with_todos, output, include_done=True)

        with open(output) as f:
            data = json.load(f)

        assert data["total_count"] >= 6  # All todos including completed

    def test_export_excludes_done(self, db_with_todos, temp_dir):
        output = temp_dir / "export.json"
        export_json(db_with_todos, output, include_done=False)

        with open(output) as f:
            data = json.load(f)

        statuses = [t["status"] for t in data["todos"]]
        assert "done" not in statuses

    def test_export_filter_by_project(self, db_with_todos, temp_dir):
        output = temp_dir / "export.json"
        export_json(db_with_todos, output, project="work")

        with open(output) as f:
            data = json.load(f)

        projects = [t["project"] for t in data["todos"]]
        assert all(p == "work" for p in projects)

    def test_export_empty_database(self, db, temp_dir):
        output = temp_dir / "export.json"
        export_json(db, output)

        with open(output) as f:
            data = json.load(f)

        assert data["total_count"] == 0
        assert data["todos"] == []


class TestExportCsv:
    """Test CSV export functionality."""

    def test_export_creates_file(self, db_with_todos, temp_dir):
        output = temp_dir / "export.csv"
        result = export_csv(db_with_todos, output)

        assert result == output
        assert output.exists()

    def test_export_auto_filename(self, db_with_todos, temp_dir, monkeypatch):
        monkeypatch.chdir(temp_dir)
        result = export_csv(db_with_todos)

        assert result.exists()
        assert result.suffix == ".csv"

    def test_export_valid_csv(self, db_with_todos, temp_dir):
        output = temp_dir / "export.csv"
        export_csv(db_with_todos, output)

        with open(output, newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Check header
        assert rows[0][0] == "ID"
        assert rows[0][1] == "Task"
        assert len(rows) > 1  # Has data rows

    def test_export_csv_headers(self, db_with_todos, temp_dir):
        output = temp_dir / "export.csv"
        export_csv(db_with_todos, output)

        with open(output, newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames

        expected = ["ID", "Task", "Priority", "Status", "Project", "Tags",
                   "Due Date", "Created At", "Completed At", "Time Spent"]
        assert fieldnames == expected

    def test_export_csv_data_integrity(self, db, temp_dir):
        db.add("Test task", project="myproject", tags=["tag1", "tag2"])
        output = temp_dir / "export.csv"
        export_csv(db, output)

        with open(output, newline="") as f:
            reader = csv.DictReader(f)
            row = next(reader)

        assert row["Task"] == "Test task"
        assert row["Project"] == "myproject"
        assert "tag1" in row["Tags"]
        assert "tag2" in row["Tags"]

    def test_export_excludes_done(self, db_with_todos, temp_dir):
        output = temp_dir / "export.csv"
        export_csv(db_with_todos, output, include_done=False)

        with open(output, newline="") as f:
            reader = csv.DictReader(f)
            statuses = [row["Status"] for row in reader]

        assert "done" not in statuses

    def test_export_filter_by_project(self, db_with_todos, temp_dir):
        output = temp_dir / "export.csv"
        export_csv(db_with_todos, output, project="home")

        with open(output, newline="") as f:
            reader = csv.DictReader(f)
            projects = [row["Project"] for row in reader]

        assert all(p == "home" for p in projects)

    def test_export_empty_database(self, db, temp_dir):
        output = temp_dir / "export.csv"
        export_csv(db, output)

        with open(output, newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)

        assert len(rows) == 1  # Only header


class TestExportMarkdown:
    """Test Markdown export functionality."""

    def test_export_creates_file(self, db_with_todos, temp_dir):
        output = temp_dir / "export.md"
        result = export_markdown(db_with_todos, output)

        assert result == output
        assert output.exists()

    def test_export_auto_filename(self, db_with_todos, temp_dir, monkeypatch):
        monkeypatch.chdir(temp_dir)
        result = export_markdown(db_with_todos)

        assert result.exists()
        assert result.suffix == ".md"

    def test_export_has_title(self, db_with_todos, temp_dir):
        output = temp_dir / "export.md"
        export_markdown(db_with_todos, output)

        content = output.read_text()
        assert "# Todo Export" in content

    def test_export_has_summary(self, db_with_todos, temp_dir):
        output = temp_dir / "export.md"
        export_markdown(db_with_todos, output)

        content = output.read_text()
        assert "## Summary" in content
        assert "**Total:**" in content
        assert "**Todo:**" in content
        assert "**In Progress:**" in content
        assert "**Done:**" in content

    def test_export_groups_by_project(self, db_with_todos, temp_dir):
        output = temp_dir / "export.md"
        export_markdown(db_with_todos, output)

        content = output.read_text()
        assert "### work" in content
        assert "### home" in content
        assert "### (No Project)" in content

    def test_export_checkbox_format(self, db_with_todos, temp_dir):
        output = temp_dir / "export.md"
        export_markdown(db_with_todos, output)

        content = output.read_text()
        assert "- [ ]" in content  # Incomplete tasks
        assert "- [x]" in content  # Completed tasks

    def test_export_shows_tags(self, db, temp_dir):
        db.add("Tagged task", tags=["important", "review"])
        output = temp_dir / "export.md"
        export_markdown(db, output)

        content = output.read_text()
        assert "`important, review`" in content

    def test_export_shows_due_date(self, db, temp_dir):
        db.add("Due task", due_date=datetime(2025, 12, 31))
        output = temp_dir / "export.md"
        export_markdown(db, output)

        content = output.read_text()
        assert "2025-12-31" in content

    def test_export_shows_overdue(self, db, temp_dir):
        past = datetime.now() - timedelta(days=1)
        db.add("Overdue task", due_date=past)
        output = temp_dir / "export.md"
        export_markdown(db, output)

        content = output.read_text()
        assert "⚠️" in content or "DUE:" in content

    def test_export_time_tracking_summary(self, db, temp_dir):
        todo = db.add("Timed task")
        db.start_timer(todo.id)
        db.stop_timer(todo.id)

        output = temp_dir / "export.md"
        export_markdown(db, output)

        content = output.read_text()
        assert "## Time Tracking" in content or "Time" in content

    def test_export_excludes_done(self, db_with_todos, temp_dir):
        output = temp_dir / "export.md"
        export_markdown(db_with_todos, output, include_done=False)

        content = output.read_text()
        # Should not have completed checkbox
        lines = [l for l in content.split("\n") if l.startswith("- [x]")]
        assert len(lines) == 0

    def test_export_filter_by_project(self, db_with_todos, temp_dir):
        output = temp_dir / "export.md"
        export_markdown(db_with_todos, output, project="work")

        content = output.read_text()
        assert "### work" in content
        assert "### home" not in content


class TestExportTodos:
    """Test main export_todos dispatcher."""

    def test_export_json_format(self, db_with_todos, temp_dir):
        output = temp_dir / "export.json"
        result = export_todos(db_with_todos, "json", output)

        assert result.suffix == ".json"
        assert result.exists()

    def test_export_csv_format(self, db_with_todos, temp_dir):
        output = temp_dir / "export.csv"
        result = export_todos(db_with_todos, "csv", output)

        assert result.suffix == ".csv"
        assert result.exists()

    def test_export_md_format(self, db_with_todos, temp_dir):
        output = temp_dir / "export.md"
        result = export_todos(db_with_todos, "md", output)

        assert result.suffix == ".md"
        assert result.exists()

    def test_export_markdown_format(self, db_with_todos, temp_dir):
        output = temp_dir / "export.md"
        result = export_todos(db_with_todos, "markdown", output)

        assert result.exists()

    def test_export_case_insensitive(self, db_with_todos, temp_dir):
        output = temp_dir / "export.json"
        result = export_todos(db_with_todos, "JSON", output)

        assert result.exists()

    def test_export_invalid_format(self, db_with_todos, temp_dir):
        output = temp_dir / "export.txt"

        with pytest.raises(ValueError) as exc_info:
            export_todos(db_with_todos, "txt", output)

        assert "Unsupported format" in str(exc_info.value)
        assert "txt" in str(exc_info.value)

    def test_export_passes_include_done(self, db_with_todos, temp_dir):
        output = temp_dir / "export.json"
        export_todos(db_with_todos, "json", output, include_done=False)

        with open(output) as f:
            data = json.load(f)

        statuses = [t["status"] for t in data["todos"]]
        assert "done" not in statuses

    def test_export_passes_project_filter(self, db_with_todos, temp_dir):
        output = temp_dir / "export.json"
        export_todos(db_with_todos, "json", output, project="work")

        with open(output) as f:
            data = json.load(f)

        projects = [t["project"] for t in data["todos"]]
        assert all(p == "work" for p in projects)


class TestExportCli:
    """Test export via CLI command."""

    def test_export_command_json(self, runner, cli_env):
        from todo_cli.main import app

        db = cli_env["get_db"]()
        db.add("Test task")

        output = cli_env["db_path"].parent / "export.json"
        result = runner.invoke(app, ["export", "json", "-o", str(output)])

        assert result.exit_code == 0
        assert output.exists()

    def test_export_command_csv(self, runner, cli_env):
        from todo_cli.main import app

        db = cli_env["get_db"]()
        db.add("Test task")

        output = cli_env["db_path"].parent / "export.csv"
        result = runner.invoke(app, ["export", "csv", "-o", str(output)])

        assert result.exit_code == 0
        assert output.exists()

    def test_export_command_md(self, runner, cli_env):
        from todo_cli.main import app

        db = cli_env["get_db"]()
        db.add("Test task")

        output = cli_env["db_path"].parent / "export.md"
        result = runner.invoke(app, ["export", "md", "-o", str(output)])

        assert result.exit_code == 0
        assert output.exists()

    def test_export_command_invalid_format(self, runner, cli_env):
        from todo_cli.main import app

        result = runner.invoke(app, ["export", "invalid"])
        assert result.exit_code == 1
        assert "Unsupported" in result.output or "error" in result.output.lower()


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
