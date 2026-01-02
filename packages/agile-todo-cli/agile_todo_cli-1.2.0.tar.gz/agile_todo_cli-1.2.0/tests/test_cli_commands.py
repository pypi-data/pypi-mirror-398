"""Tests for core CLI commands."""

import pytest
from typer.testing import CliRunner
from datetime import datetime, timedelta
import time

from todo_cli.main import app
from todo_cli.config import Config
from todo_cli.database import Database
from todo_cli.models import Status, Priority


@pytest.fixture
def cli_env(temp_dir, monkeypatch):
    """Set up isolated CLI environment."""
    import todo_cli.config as config_module
    import todo_cli.main as main_module

    config_path = temp_dir / "config.yaml"
    db_path = temp_dir / "todos.db"

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


class TestAddCommand:
    """Test the add command."""

    def test_add_basic(self, runner, cli_env):
        result = runner.invoke(app, ["add", "Buy groceries"])
        assert result.exit_code == 0
        assert "Added todo #1" in result.output
        assert "Buy groceries" in result.output

        db = cli_env["get_db"]()
        todos = db.list_all()
        assert len(todos) == 1
        assert todos[0].task == "Buy groceries"

    def test_add_with_priority(self, runner, cli_env):
        result = runner.invoke(app, ["add", "Urgent task", "-p", "p0"])
        assert result.exit_code == 0

        db = cli_env["get_db"]()
        todos = db.list_all()
        assert todos[0].priority == Priority.P0

    def test_add_with_project(self, runner, cli_env):
        # Create project first
        from todo_cli.projects import ProjectManager
        pm = ProjectManager(cli_env["get_db"]().db_path)
        pm.create_project("work")

        result = runner.invoke(app, ["add", "Project task", "-P", "work"])
        assert result.exit_code == 0

        db = cli_env["get_db"]()
        todos = db.list_all()
        # Check that task was assigned to project (project_id should be set)
        assert todos[0].project_id == 1

    def test_add_with_tags(self, runner, cli_env):
        result = runner.invoke(app, ["add", "Tagged task", "-t", "urgent,important"])
        assert result.exit_code == 0

        db = cli_env["get_db"]()
        todos = db.list_all()
        assert "urgent" in todos[0].tags
        assert "important" in todos[0].tags

    def test_add_with_due_date(self, runner, cli_env):
        result = runner.invoke(app, ["add", "Due task", "-d", "2025-12-31"])
        assert result.exit_code == 0

        db = cli_env["get_db"]()
        todos = db.list_all()
        assert todos[0].due_date is not None
        assert todos[0].due_date.year == 2025
        assert todos[0].due_date.month == 12
        assert todos[0].due_date.day == 31

    def test_add_with_all_options(self, runner, cli_env):
        # Create project first
        from todo_cli.projects import ProjectManager
        pm = ProjectManager(cli_env["get_db"]().db_path)
        pm.create_project("project-x")

        result = runner.invoke(app, [
            "add", "Complete task",
            "-p", "p1",
            "-P", "project-x",
            "-t", "review,code",
            "-d", "2025-06-15"
        ])
        assert result.exit_code == 0

        db = cli_env["get_db"]()
        todos = db.list_all()
        todo = todos[0]
        assert todo.task == "Complete task"
        assert todo.priority == Priority.P1
        # Check that task was assigned to project (project_id should be set)
        assert todo.project_id == 1
        assert set(todo.tags) == {"review", "code"}


class TestListCommand:
    """Test the list command."""

    def test_list_empty(self, runner, cli_env):
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0

    def test_list_with_todos(self, runner, cli_env):
        db = cli_env["get_db"]()
        db.add("Task one")
        db.add("Task two")
        db.add("Task three")

        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        # Check IDs are present
        assert "1" in result.output
        assert "2" in result.output
        assert "3" in result.output

    def test_list_filter_by_project(self, runner, cli_env):
        db = cli_env["get_db"]()
        db.add("Work task", project="work")
        db.add("Home task", project="home")
        db.add("Another work task", project="work")

        result = runner.invoke(app, ["list", "-P", "work"])
        assert result.exit_code == 0
        lines = result.output.split("\n")
        # Should show 2 tasks (IDs 1 and 3), not ID 2
        data_rows = [l for l in lines if "│" in l and any(f"│ {i} " in l for i in [1, 2, 3])]
        work_rows = [l for l in data_rows if "│ 1 " in l or "│ 3 " in l]
        assert len(work_rows) == 2

    def test_list_filter_by_status(self, runner, cli_env):
        db = cli_env["get_db"]()
        db.add("Todo task")
        todo2 = db.add("Doing task")
        db.start_timer(todo2.id)
        todo3 = db.add("Done task")
        db.mark_done(todo3.id)

        result = runner.invoke(app, ["list", "-s", "doing"])
        assert result.exit_code == 0
        lines = result.output.split("\n")
        data_rows = [l for l in lines if "│ 2 " in l]
        assert len(data_rows) >= 1


class TestDoneCommand:
    """Test the done command."""

    def test_done_marks_complete(self, runner, cli_env):
        db = cli_env["get_db"]()
        db.add("Task to complete")

        result = runner.invoke(app, ["done", "1"])
        assert result.exit_code == 0
        assert "Completed" in result.output

        todo = db.get(1)
        assert todo.status == Status.DONE
        assert todo.completed_at is not None

    def test_done_not_found(self, runner, cli_env):
        result = runner.invoke(app, ["done", "999"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_done_shows_time_spent(self, runner, cli_env):
        db = cli_env["get_db"]()
        todo = db.add("Timed task")
        db.start_timer(todo.id)
        time.sleep(0.1)  # Brief delay to accumulate some time
        db.stop_timer(todo.id)

        result = runner.invoke(app, ["done", "1"])
        assert result.exit_code == 0
        assert "Completed" in result.output


class TestDeleteCommand:
    """Test the delete command."""

    def test_delete_removes_todo(self, runner, cli_env):
        db = cli_env["get_db"]()
        db.add("Task to delete")

        result = runner.invoke(app, ["delete", "1"])
        assert result.exit_code == 0
        assert "Deleted" in result.output
        assert db.get(1) is None

    def test_delete_not_found(self, runner, cli_env):
        result = runner.invoke(app, ["delete", "999"])
        assert result.exit_code == 1
        assert "not found" in result.output


class TestStartCommand:
    """Test the start command."""

    def test_start_begins_timer(self, runner, cli_env):
        db = cli_env["get_db"]()
        db.add("Task to track")

        result = runner.invoke(app, ["start", "1"])
        assert result.exit_code == 0
        assert "Started tracking" in result.output

        todo = db.get(1)
        assert todo.timer_started is not None
        assert todo.status == Status.DOING

    def test_start_not_found(self, runner, cli_env):
        result = runner.invoke(app, ["start", "999"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_start_stops_previous_timer(self, runner, cli_env):
        db = cli_env["get_db"]()
        db.add("First task")
        db.add("Second task")

        runner.invoke(app, ["start", "1"])
        result = runner.invoke(app, ["start", "2"])

        assert result.exit_code == 0
        assert "Stopping timer" in result.output

        todo1 = db.get(1)
        todo2 = db.get(2)
        assert todo1.timer_started is None
        assert todo2.timer_started is not None


class TestStopCommand:
    """Test the stop command."""

    def test_stop_ends_timer(self, runner, cli_env):
        db = cli_env["get_db"]()
        todo = db.add("Task to stop")
        db.start_timer(todo.id)

        result = runner.invoke(app, ["stop", "1"])
        assert result.exit_code == 0
        assert "Stopped tracking" in result.output

        todo = db.get(1)
        assert todo.timer_started is None

    def test_stop_no_active_timer(self, runner, cli_env):
        db = cli_env["get_db"]()
        db.add("Task without timer")

        result = runner.invoke(app, ["stop", "1"])
        assert "No active timer" in result.output

    def test_stop_without_id_stops_any(self, runner, cli_env):
        db = cli_env["get_db"]()
        todo = db.add("Active task")
        db.start_timer(todo.id)

        result = runner.invoke(app, ["stop"])
        assert result.exit_code == 0
        assert "Stopped tracking" in result.output

    def test_stop_no_active_timer_global(self, runner, cli_env):
        result = runner.invoke(app, ["stop"])
        assert "No active timer" in result.output


class TestShowCommand:
    """Test the show command."""

    def test_show_displays_todo(self, runner, cli_env):
        db = cli_env["get_db"]()
        db.add("Detailed task", project="test-project")

        result = runner.invoke(app, ["show", "1"])
        assert result.exit_code == 0
        assert "Detailed task" in result.output

    def test_show_not_found(self, runner, cli_env):
        result = runner.invoke(app, ["show", "999"])
        assert result.exit_code == 1
        assert "not found" in result.output


class TestStatusCommand:
    """Test the status command."""

    def test_status_change_to_doing(self, runner, cli_env):
        db = cli_env["get_db"]()
        db.add("Task to start")

        result = runner.invoke(app, ["status", "1", "doing"])
        assert result.exit_code == 0
        assert "doing" in result.output.lower()

        todo = db.get(1)
        assert todo.status == Status.DOING

    def test_status_change_to_done(self, runner, cli_env):
        db = cli_env["get_db"]()
        db.add("Task to finish")

        result = runner.invoke(app, ["status", "1", "done"])
        assert result.exit_code == 0

        todo = db.get(1)
        assert todo.status == Status.DONE
        assert todo.completed_at is not None

    def test_status_invalid(self, runner, cli_env):
        db = cli_env["get_db"]()
        db.add("Task")

        result = runner.invoke(app, ["status", "1", "invalid"])
        assert result.exit_code == 1
        assert "Invalid status" in result.output

    def test_status_not_found(self, runner, cli_env):
        result = runner.invoke(app, ["status", "999", "done"])
        assert result.exit_code == 1
        assert "not found" in result.output


class TestEditCommand:
    """Test the edit command."""

    def test_edit_task_description(self, runner, cli_env):
        db = cli_env["get_db"]()
        db.add("Original task")

        result = runner.invoke(app, ["edit", "1", "-t", "Updated task"])
        assert result.exit_code == 0
        assert "Updated" in result.output

        todo = db.get(1)
        assert todo.task == "Updated task"

    def test_edit_priority(self, runner, cli_env):
        db = cli_env["get_db"]()
        db.add("Task", priority=Priority.P2)

        result = runner.invoke(app, ["edit", "1", "-p", "p0"])
        assert result.exit_code == 0

        todo = db.get(1)
        assert todo.priority == Priority.P0

    def test_edit_project(self, runner, cli_env):
        db = cli_env["get_db"]()
        db.add("Task")

        result = runner.invoke(app, ["edit", "1", "-P", "new-project"])
        assert result.exit_code == 0

        todo = db.get(1)
        assert todo.project == "new-project"

    def test_edit_tags(self, runner, cli_env):
        db = cli_env["get_db"]()
        db.add("Task", tags=["old"])

        result = runner.invoke(app, ["edit", "1", "--tags", "new,updated"])
        assert result.exit_code == 0

        todo = db.get(1)
        assert set(todo.tags) == {"new", "updated"}

    def test_edit_not_found(self, runner, cli_env):
        result = runner.invoke(app, ["edit", "999", "-t", "New text"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_edit_clear_project(self, runner, cli_env):
        db = cli_env["get_db"]()
        db.add("Task", project="old-project")

        result = runner.invoke(app, ["edit", "1", "-P", ""])
        assert result.exit_code == 0

        todo = db.get(1)
        assert todo.project is None


class TestProjectsCommand:
    """Test the project commands."""

    def test_projects_empty(self, runner, cli_env):
        result = runner.invoke(app, ["project", "list"])
        assert result.exit_code == 0
        assert "No projects" in result.output

    def test_projects_lists_all(self, runner, cli_env):
        # Use ProjectManager to create projects
        from todo_cli.projects import ProjectManager
        pm = ProjectManager(cli_env["get_db"]().db_path)
        pm.create_project("Alpha")
        pm.create_project("Beta")

        result = runner.invoke(app, ["project", "list"])
        assert result.exit_code == 0
        assert "Alpha" in result.output
        assert "Beta" in result.output


class TestStatsCommand:
    """Test the stats command."""

    def test_stats_empty(self, runner, cli_env):
        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 0

    def test_stats_with_data(self, runner, cli_env):
        db = cli_env["get_db"]()
        db.add("Task 1")
        todo2 = db.add("Task 2")
        db.mark_done(todo2.id)

        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 0


class TestActiveCommand:
    """Test the active command."""

    def test_active_no_timer(self, runner, cli_env):
        result = runner.invoke(app, ["active"])
        assert result.exit_code == 0
        assert "No active timer" in result.output

    def test_active_shows_current(self, runner, cli_env):
        db = cli_env["get_db"]()
        todo = db.add("Active task")
        db.start_timer(todo.id)

        result = runner.invoke(app, ["active"])
        assert result.exit_code == 0
        assert "Active task" in result.output


class TestVersionCommand:
    """Test the version command."""

    def test_version_displays(self, runner, cli_env):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "Todo CLI" in result.output
        assert "v" in result.output


class TestParsePriority:
    """Test priority parsing edge cases."""

    def test_numeric_priority_1(self, runner, cli_env):
        result = runner.invoke(app, ["add", "Task", "-p", "1"])
        assert result.exit_code == 0

        db = cli_env["get_db"]()
        assert db.list_all()[0].priority == Priority.P1

    def test_numeric_priority_0(self, runner, cli_env):
        result = runner.invoke(app, ["add", "Task", "-p", "0"])
        assert result.exit_code == 0

        db = cli_env["get_db"]()
        assert db.list_all()[0].priority == Priority.P0


class TestParseDate:
    """Test date parsing formats."""

    def test_date_yyyy_mm_dd(self, runner, cli_env):
        result = runner.invoke(app, ["add", "Task", "-d", "2025-06-15"])
        assert result.exit_code == 0

        db = cli_env["get_db"]()
        todo = db.list_all()[0]
        assert todo.due_date.month == 6
        assert todo.due_date.day == 15

    def test_date_mm_dd_yyyy(self, runner, cli_env):
        result = runner.invoke(app, ["add", "Task", "-d", "06/15/2025"])
        assert result.exit_code == 0

        db = cli_env["get_db"]()
        todo = db.list_all()[0]
        assert todo.due_date.month == 6

    def test_date_mm_dd_only(self, runner, cli_env):
        result = runner.invoke(app, ["add", "Task", "-d", "06/15"])
        assert result.exit_code == 0

        db = cli_env["get_db"]()
        todo = db.list_all()[0]
        assert todo.due_date.month == 6
        assert todo.due_date.year == datetime.now().year

    def test_date_invalid_no_crash(self, runner, cli_env):
        result = runner.invoke(app, ["add", "Task", "-d", "not-a-date"])
        assert result.exit_code == 0  # Should not crash, just skip invalid date

        db = cli_env["get_db"]()
        todo = db.list_all()[0]
        assert todo.due_date is None


class TestProjectFiltering:
    """Test project filtering across commands (Story 1.3)."""

    def test_list_with_project_filter(self, runner, cli_env):
        """Test filtering todos by project name."""
        from todo_cli.projects import ProjectManager

        # Create projects
        pm = ProjectManager(cli_env["get_db"]().db_path)
        project_a = pm.create_project("Project A")
        project_b = pm.create_project("Project B")

        # Add todos to different projects
        runner.invoke(app, ["add", "Task in A", "-P", "Project A"])
        runner.invoke(app, ["add", "Task in B", "-P", "Project B"])
        runner.invoke(app, ["add", "Task without project"])

        # List all todos (should show all 3) - verify by checking project names in output
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        # Verify all 3 rows exist (IDs 1, 2, 3) and project names display correctly
        assert "│ 1" in result.output
        assert "│ 2" in result.output
        assert "│ 3" in result.output
        assert "Project A" in result.output
        assert "Project B" in result.output

        # Filter by Project A (should show only 1)
        result = runner.invoke(app, ["list", "-P", "Project A"])
        assert result.exit_code == 0
        assert "│ 1" in result.output  # Only task 1
        assert "│ 2" not in result.output  # Not task 2
        assert "│ 3" not in result.output  # Not task 3
        assert "Project A" in result.output
        assert "Project B" not in result.output

        # Filter by Project B (should show only 1)
        result = runner.invoke(app, ["list", "-P", "Project B"])
        assert result.exit_code == 0
        assert "│ 1" not in result.output  # Not task 1
        assert "│ 2" in result.output  # Only task 2
        assert "│ 3" not in result.output  # Not task 3
        assert "Project A" not in result.output
        assert "Project B" in result.output

    def test_add_task_to_project(self, runner, cli_env):
        """Test adding a task to a project."""
        from todo_cli.projects import ProjectManager

        # Create project
        pm = ProjectManager(cli_env["get_db"]().db_path)
        project = pm.create_project("Test Project")

        # Add task to project
        result = runner.invoke(app, ["add", "Task in project", "-P", "Test Project"])
        assert result.exit_code == 0
        assert "Added todo #1" in result.output

        # Verify task is assigned to project
        db = cli_env["get_db"]()
        with db._get_conn() as conn:
            row = conn.execute("SELECT project_id FROM todos WHERE id = 1").fetchone()
            assert row["project_id"] == project.id

    def test_invalid_project_name_error(self, runner, cli_env):
        """Test that invalid project name shows helpful error."""
        # Try to add task to non-existent project
        result = runner.invoke(app, ["add", "Task", "-P", "NonExistent"])
        assert result.exit_code == 1
        assert "Project 'NonExistent' not found" in result.output

        # Try to list with non-existent project
        result = runner.invoke(app, ["list", "-P", "NonExistent"])
        assert result.exit_code == 1
        assert "Project 'NonExistent' not found" in result.output

    def test_empty_results_clear_message(self, runner, cli_env):
        """Test that empty results show clear message."""
        from todo_cli.projects import ProjectManager

        # Create project but don't add any tasks
        pm = ProjectManager(cli_env["get_db"]().db_path)
        pm.create_project("Empty Project")

        # List tasks for empty project
        result = runner.invoke(app, ["list", "-P", "Empty Project"])
        assert result.exit_code == 0
        assert "No todos found" in result.output

    def test_combined_filters_project_and_status(self, runner, cli_env):
        """Test combining --project with --status filter."""
        from todo_cli.projects import ProjectManager

        # Create project
        pm = ProjectManager(cli_env["get_db"]().db_path)
        pm.create_project("Test Project")

        # Add tasks with different statuses
        runner.invoke(app, ["add", "Todo task", "-P", "Test Project"])
        runner.invoke(app, ["add", "Doing task", "-P", "Test Project"])
        runner.invoke(app, ["add", "Other project task"])

        # Mark one as doing, one as done
        db = cli_env["get_db"]()
        task2 = db.get(2)
        task2.status = Status.DOING
        db.update(task2)
        db.mark_done(1)

        # List only todo status in Test Project
        result = runner.invoke(app, ["list", "-P", "Test Project", "-s", "todo"])
        assert result.exit_code == 0
        # Should not show completed or doing tasks (no tasks with 'todo' status)
        assert "│ 1" not in result.output  # Task 1 is done
        assert "│ 2" not in result.output  # Task 2 is doing
        assert "No todos found" in result.output

        # List all in Test Project (including done)
        result = runner.invoke(app, ["list", "-P", "Test Project", "-a"])
        assert result.exit_code == 0
        assert "│ 1" in result.output  # Task 1 (done)
        assert "│ 2" in result.output  # Task 2 (doing)
        assert "│ 3" not in result.output  # Task 3 is different project
        assert "Test Project" in result.output

    def test_project_name_case_insensitive(self, runner, cli_env):
        """Test that project name lookup is case-insensitive."""
        from todo_cli.projects import ProjectManager

        # Create project
        pm = ProjectManager(cli_env["get_db"]().db_path)
        pm.create_project("MyProject")

        # Add task with different case
        result = runner.invoke(app, ["add", "Task 1", "-P", "myproject"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["add", "Task 2", "-P", "MYPROJECT"])
        assert result.exit_code == 0

        # List with different case
        result = runner.invoke(app, ["list", "-P", "MyPrOjEcT"])
        assert result.exit_code == 0
        assert "│ 1" in result.output
        assert "│ 2" in result.output
        # Both tasks should have MyProject shown (verifying case-insensitive project assignment worked)
        assert result.output.count("MyProject") >= 2

    def test_backwards_compatibility_legacy_project_string(self, runner, cli_env):
        """Test backwards compatibility with legacy project strings."""
        db = cli_env["get_db"]()

        # Add task with legacy project string (no project_id, just project string)
        with db._get_conn() as conn:
            conn.execute("""
                INSERT INTO todos (task, priority, project, created_at)
                VALUES (?, ?, ?, ?)
            """, ("Legacy task", 2, "Legacy Project", datetime.now().isoformat()))
            conn.commit()

        # List should still work with legacy project filter
        result = runner.invoke(app, ["list", "-P", "Legacy Project"])
        assert result.exit_code == 0
        # Note: This test verifies the backwards compatibility path works
        # The task won't show up since project name doesn't match a real project,
        # but the command shouldn't crash


class TestAddRecurrence:
    """Test the add command with recurrence options."""

    def test_add_with_daily_recurrence(self, runner, cli_env):
        """Test adding a task with daily recurrence."""
        result = runner.invoke(app, ["add", "Daily standup", "--recur", "daily"])
        assert result.exit_code == 0
        assert "Added recurring todo #1" in result.output
        assert "Daily standup" in result.output
        assert "(daily)" in result.output

        # Verify recurrence rule was created in database
        db = cli_env["get_db"]()
        rule = db.get_recurrence_rule_by_task(1)
        assert rule is not None
        assert rule.pattern.value == "daily"
        assert rule.interval == 1

    def test_add_with_weekly_recurrence(self, runner, cli_env):
        """Test adding a task with weekly recurrence."""
        result = runner.invoke(app, ["add", "Weekly review", "-r", "weekly"])
        assert result.exit_code == 0
        assert "(weekly)" in result.output

        db = cli_env["get_db"]()
        rule = db.get_recurrence_rule_by_task(1)
        assert rule is not None
        assert rule.pattern.value == "weekly"

    def test_add_with_monthly_recurrence(self, runner, cli_env):
        """Test adding a task with monthly recurrence."""
        result = runner.invoke(app, ["add", "Monthly report", "--recur", "monthly"])
        assert result.exit_code == 0
        assert "(monthly)" in result.output

        db = cli_env["get_db"]()
        rule = db.get_recurrence_rule_by_task(1)
        assert rule is not None
        assert rule.pattern.value == "monthly"

    def test_add_with_yearly_recurrence(self, runner, cli_env):
        """Test adding a task with yearly recurrence."""
        result = runner.invoke(app, ["add", "Annual review", "--recur", "yearly"])
        assert result.exit_code == 0
        assert "(yearly)" in result.output

        db = cli_env["get_db"]()
        rule = db.get_recurrence_rule_by_task(1)
        assert rule is not None
        assert rule.pattern.value == "yearly"

    def test_add_with_interval_recurrence(self, runner, cli_env):
        """Test adding a task with interval-based recurrence."""
        result = runner.invoke(app, ["add", "Bi-weekly check", "--recur", "every 2 weeks"])
        assert result.exit_code == 0
        assert "(every 2 weeks)" in result.output

        db = cli_env["get_db"]()
        rule = db.get_recurrence_rule_by_task(1)
        assert rule is not None
        assert rule.pattern.value == "weekly"
        assert rule.interval == 2

    def test_add_with_custom_days_recurrence(self, runner, cli_env):
        """Test adding a task with custom days of week recurrence."""
        result = runner.invoke(app, ["add", "Workout", "--recur", "every mon,wed,fri"])
        assert result.exit_code == 0
        assert "(every" in result.output  # Pattern may reorder days

        db = cli_env["get_db"]()
        rule = db.get_recurrence_rule_by_task(1)
        assert rule is not None
        assert rule.pattern.value == "custom"
        assert set(rule.days_of_week) == {"mon", "wed", "fri"}

    def test_add_with_monthly_on_day_recurrence(self, runner, cli_env):
        """Test adding a task with monthly on specific day recurrence."""
        result = runner.invoke(app, ["add", "Rent payment", "--recur", "monthly on 1"])
        assert result.exit_code == 0
        assert "(monthly on 1)" in result.output

        db = cli_env["get_db"]()
        rule = db.get_recurrence_rule_by_task(1)
        assert rule is not None
        assert rule.pattern.value == "monthly"
        assert rule.day_of_month == 1

    def test_add_with_recurrence_and_until(self, runner, cli_env):
        """Test adding a task with recurrence and end date."""
        result = runner.invoke(app, ["add", "Limited series", "--recur", "daily", "--until", "2025-12-31"])
        assert result.exit_code == 0
        assert "(daily)" in result.output

        db = cli_env["get_db"]()
        rule = db.get_recurrence_rule_by_task(1)
        assert rule is not None
        assert rule.end_date is not None
        assert rule.end_date.year == 2025
        assert rule.end_date.month == 12
        assert rule.end_date.day == 31

    def test_add_with_invalid_recurrence_pattern(self, runner, cli_env):
        """Test adding a task with invalid recurrence pattern."""
        result = runner.invoke(app, ["add", "Invalid task", "--recur", "biweekly"])
        assert result.exit_code == 1
        assert "Invalid recurrence pattern" in result.output

    def test_add_with_invalid_until_date(self, runner, cli_env):
        """Test adding a task with invalid until date format.

        Note: Invalid date formats are parsed as None, so the task
        is created with recurrence but no end date.
        """
        result = runner.invoke(app, ["add", "Bad date", "--recur", "daily", "--until", "not-a-date"])
        assert result.exit_code == 0  # Task is created, date is just None
        db = cli_env["get_db"]()
        rule = db.get_recurrence_rule_by_task(1)
        assert rule is not None
        assert rule.end_date is None  # Invalid date becomes None

    def test_add_until_without_recur(self, runner, cli_env):
        """Test that --until without --recur is ignored."""
        result = runner.invoke(app, ["add", "Normal task", "--until", "2025-12-31"])
        assert result.exit_code == 0
        # Task is added but until is ignored without recur
        db = cli_env["get_db"]()
        todos = db.list_all()
        assert len(todos) == 1
        assert todos[0].task == "Normal task"
        # No recurrence rule should exist
        rule = db.get_recurrence_rule_by_task(1)
        assert rule is None

    def test_recurrence_indicator_in_list(self, runner, cli_env):
        """Test that recurring tasks show 🔄 indicator in list."""
        # Add regular task
        runner.invoke(app, ["add", "Regular task"])
        # Add recurring task
        runner.invoke(app, ["add", "Daily standup", "--recur", "daily"])

        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        # The recurring task should have the 🔄 indicator
        assert "🔄" in result.output

    def test_recurrence_info_in_show(self, runner, cli_env):
        """Test that show command displays recurrence information."""
        runner.invoke(app, ["add", "Daily standup", "--recur", "daily", "--until", "2025-12-31"])

        result = runner.invoke(app, ["show", "1"])
        assert result.exit_code == 0
        assert "Recurrence" in result.output
        assert "daily" in result.output
        assert "2025-12-31" in result.output

    def test_add_recurrence_with_all_options(self, runner, cli_env):
        """Test adding recurring task with all options."""
        from todo_cli.projects import ProjectManager
        pm = ProjectManager(cli_env["get_db"]().db_path)
        pm.create_project("work")

        result = runner.invoke(app, [
            "add", "Sprint planning",
            "-p", "p1",
            "-P", "work",
            "-t", "meeting,agile",
            "-d", "2025-01-15",
            "--recur", "every 2 weeks",
            "--until", "2025-12-31"
        ])
        assert result.exit_code == 0
        assert "Added recurring todo #1" in result.output
        assert "(every 2 weeks)" in result.output

        db = cli_env["get_db"]()
        todo = db.get(1)
        assert todo.task == "Sprint planning"
        assert todo.priority == Priority.P1
        assert todo.project_id == 1
        assert set(todo.tags) == {"meeting", "agile"}
        assert todo.due_date is not None

        rule = db.get_recurrence_rule_by_task(1)
        assert rule is not None
        assert rule.pattern.value == "weekly"
        assert rule.interval == 2
        assert rule.end_date is not None


class TestDueDateFiltering:
    """Test due date filtering options - Story 5.6."""

    def test_list_due_today(self, runner, cli_env):
        """Test --due today filter shows only tasks due today."""
        from datetime import date, timedelta

        today = date.today()
        tomorrow = today + timedelta(days=1)
        yesterday = today - timedelta(days=1)

        # Add tasks with different due dates
        runner.invoke(app, ["add", "Due today", "-d", today.isoformat()])
        runner.invoke(app, ["add", "Due tomorrow", "-d", tomorrow.isoformat()])
        runner.invoke(app, ["add", "Due yesterday", "-d", yesterday.isoformat()])
        runner.invoke(app, ["add", "No due date"])

        result = runner.invoke(app, ["list", "--due", "today"])
        assert result.exit_code == 0
        assert "Due today" in result.output
        assert "Due tomorrow" not in result.output
        assert "Due yesterday" not in result.output
        assert "No due date" not in result.output

    def test_list_due_tomorrow(self, runner, cli_env):
        """Test --due tomorrow filter shows only tasks due tomorrow."""
        from datetime import date, timedelta

        today = date.today()
        tomorrow = today + timedelta(days=1)

        runner.invoke(app, ["add", "Due today", "-d", today.isoformat()])
        runner.invoke(app, ["add", "Due tomorrow", "-d", tomorrow.isoformat()])

        result = runner.invoke(app, ["list", "--due", "tomorrow"])
        assert result.exit_code == 0
        assert "Due tomorrow" in result.output
        assert "Due today" not in result.output

    def test_list_due_week(self, runner, cli_env):
        """Test --due week filter shows tasks due in next 7 days."""
        from datetime import date, timedelta

        today = date.today()
        in_3_days = today + timedelta(days=3)
        in_10_days = today + timedelta(days=10)
        yesterday = today - timedelta(days=1)

        runner.invoke(app, ["add", "Due in 3 days", "-d", in_3_days.isoformat()])
        runner.invoke(app, ["add", "Due in 10 days", "-d", in_10_days.isoformat()])
        runner.invoke(app, ["add", "Due yesterday", "-d", yesterday.isoformat()])

        result = runner.invoke(app, ["list", "--due", "week"])
        assert result.exit_code == 0
        assert "Due in 3 days" in result.output
        assert "Due in 10 days" not in result.output
        assert "Due yesterday" not in result.output

    def test_list_due_specific_date(self, runner, cli_env):
        """Test --due with specific YYYY-MM-DD date."""
        runner.invoke(app, ["add", "Target task", "-d", "2025-06-15"])
        runner.invoke(app, ["add", "Other task", "-d", "2025-06-16"])

        result = runner.invoke(app, ["list", "--due", "2025-06-15", "-a"])
        assert result.exit_code == 0
        assert "Target task" in result.output
        assert "Other task" not in result.output

    def test_list_due_invalid_format(self, runner, cli_env):
        """Test --due with invalid format shows error."""
        runner.invoke(app, ["add", "Some task"])

        result = runner.invoke(app, ["list", "--due", "invalid-date"])
        assert result.exit_code == 1
        assert "Invalid due date format" in result.output

    def test_list_overdue(self, runner, cli_env):
        """Test --overdue filter shows only overdue tasks."""
        from datetime import date, timedelta

        today = date.today()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)
        tomorrow = today + timedelta(days=1)

        runner.invoke(app, ["add", "Overdue 1 day", "-d", yesterday.isoformat()])
        runner.invoke(app, ["add", "Overdue 2 days", "-d", two_days_ago.isoformat()])
        runner.invoke(app, ["add", "Due tomorrow", "-d", tomorrow.isoformat()])
        runner.invoke(app, ["add", "Due today", "-d", today.isoformat()])

        result = runner.invoke(app, ["list", "--overdue"])
        assert result.exit_code == 0
        assert "Overdue 1 day" in result.output
        assert "Overdue 2 days" in result.output
        assert "Due tomorrow" not in result.output
        assert "Due today" not in result.output

    def test_list_overdue_excludes_done(self, runner, cli_env):
        """Test --overdue filter excludes completed tasks."""
        from datetime import date, timedelta

        yesterday = (date.today() - timedelta(days=1)).isoformat()

        runner.invoke(app, ["add", "Overdue incomplete", "-d", yesterday])
        runner.invoke(app, ["add", "Overdue complete", "-d", yesterday])
        runner.invoke(app, ["done", "2"])

        result = runner.invoke(app, ["list", "--overdue"])
        assert result.exit_code == 0
        assert "Overdue incomplete" in result.output
        assert "Overdue complete" not in result.output

    def test_list_due_before(self, runner, cli_env):
        """Test --due-before filter shows tasks due before date."""
        runner.invoke(app, ["add", "Due Jan 10", "-d", "2025-01-10"])
        runner.invoke(app, ["add", "Due Jan 15", "-d", "2025-01-15"])
        runner.invoke(app, ["add", "Due Jan 20", "-d", "2025-01-20"])

        result = runner.invoke(app, ["list", "--due-before", "2025-01-15", "-a"])
        assert result.exit_code == 0
        assert "Due Jan 10" in result.output
        assert "Due Jan 15" not in result.output  # Not before, exactly on
        assert "Due Jan 20" not in result.output

    def test_list_due_after(self, runner, cli_env):
        """Test --due-after filter shows tasks due after date."""
        runner.invoke(app, ["add", "Due Jan 10", "-d", "2025-01-10"])
        runner.invoke(app, ["add", "Due Jan 15", "-d", "2025-01-15"])
        runner.invoke(app, ["add", "Due Jan 20", "-d", "2025-01-20"])

        result = runner.invoke(app, ["list", "--due-after", "2025-01-15", "-a"])
        assert result.exit_code == 0
        assert "Due Jan 10" not in result.output
        assert "Due Jan 15" not in result.output  # Not after, exactly on
        assert "Due Jan 20" in result.output

    def test_list_due_before_invalid_format(self, runner, cli_env):
        """Test --due-before with invalid format shows error."""
        result = runner.invoke(app, ["list", "--due-before", "bad-date"])
        assert result.exit_code == 1
        assert "Invalid date format for --due-before" in result.output

    def test_list_due_after_invalid_format(self, runner, cli_env):
        """Test --due-after with invalid format shows error."""
        result = runner.invoke(app, ["list", "--due-after", "bad-date"])
        assert result.exit_code == 1
        assert "Invalid date format for --due-after" in result.output

    def test_list_due_range_combined(self, runner, cli_env):
        """Test combining --due-after and --due-before for date range."""
        runner.invoke(app, ["add", "Due Jan 10", "-d", "2025-01-10"])
        runner.invoke(app, ["add", "Due Jan 15", "-d", "2025-01-15"])
        runner.invoke(app, ["add", "Due Jan 20", "-d", "2025-01-20"])
        runner.invoke(app, ["add", "Due Jan 25", "-d", "2025-01-25"])

        result = runner.invoke(app, ["list", "--due-after", "2025-01-10", "--due-before", "2025-01-25", "-a"])
        assert result.exit_code == 0
        assert "Due Jan 10" not in result.output  # On boundary
        assert "Due Jan 15" in result.output
        assert "Due Jan 20" in result.output
        assert "Due Jan 25" not in result.output  # On boundary

    def test_list_due_with_other_filters(self, runner, cli_env):
        """Test --due works with other filters like --status."""
        from datetime import date

        today = date.today().isoformat()

        runner.invoke(app, ["add", "Today todo", "-d", today])
        runner.invoke(app, ["add", "Today doing", "-d", today])
        runner.invoke(app, ["start", "2"])

        result = runner.invoke(app, ["list", "--due", "today", "--status", "doing"])
        assert result.exit_code == 0
        assert "Today doing" in result.output
        assert "Today todo" not in result.output

    def test_list_no_tasks_with_due_filter(self, runner, cli_env):
        """Test --due shows empty when no matching tasks."""
        runner.invoke(app, ["add", "No due date task"])

        result = runner.invoke(app, ["list", "--due", "today"])
        assert result.exit_code == 0
        assert "No todos found" in result.output
