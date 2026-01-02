"""Tests for interactive menu interface."""

import pytest
from io import StringIO
from unittest.mock import patch, MagicMock

from rich.console import Console

from todo_cli.database import Database
from todo_cli.models import Priority, Status
from todo_cli.interactive import (
    parse_priority,
    interactive_add,
    interactive_list,
    interactive_show,
    interactive_done,
    interactive_delete,
    interactive_start,
    interactive_stop,
    interactive_edit,
    interactive_report,
    interactive_export,
    interactive_projects,
    run_interactive,
    MENU_OPTIONS,
)


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
    monkeypatch.setattr("todo_cli.interactive.console", console)
    monkeypatch.setattr("todo_cli.reports.console", console)
    monkeypatch.setattr("todo_cli.export.console", console)
    # Patch get_console to return our captured console
    monkeypatch.setattr("todo_cli.display.get_console", lambda: console)
    return output


class TestParsePriority:
    """Test parse_priority function."""

    def test_p0_variants(self):
        assert parse_priority("p0") == Priority.P0
        assert parse_priority("P0") == Priority.P0
        assert parse_priority("0") == Priority.P0

    def test_p1_variants(self):
        assert parse_priority("p1") == Priority.P1
        assert parse_priority("P1") == Priority.P1
        assert parse_priority("1") == Priority.P1

    def test_p2_variants(self):
        assert parse_priority("p2") == Priority.P2
        assert parse_priority("P2") == Priority.P2
        assert parse_priority("2") == Priority.P2

    def test_p3_variants(self):
        assert parse_priority("p3") == Priority.P3
        assert parse_priority("P3") == Priority.P3
        assert parse_priority("3") == Priority.P3

    def test_default_for_invalid(self):
        assert parse_priority("invalid") == Priority.P2
        assert parse_priority("") == Priority.P2
        assert parse_priority("p5") == Priority.P2


class TestInteractiveAdd:
    """Test interactive_add function."""

    @patch("todo_cli.interactive.Prompt.ask")
    def test_add_basic_todo(self, mock_prompt, db, capture_console):
        # Mock prompt responses in order
        mock_prompt.side_effect = [
            "Test task",  # Task description
            "p2",         # Priority
            "",           # Project
            "",           # Tags
            "",           # Due date
        ]

        interactive_add(db)
        output = capture_console.getvalue()

        assert "Added todo" in output
        assert "Test task" in output

        todo = db.get(1)
        assert todo is not None
        assert todo.task == "Test task"
        assert todo.priority == Priority.P2

    @patch("todo_cli.interactive.Prompt.ask")
    def test_add_todo_with_all_fields(self, mock_prompt, db, capture_console):
        mock_prompt.side_effect = [
            "Full todo",
            "p0",
            "work",
            "tag1, tag2",
            "2025-12-31",
        ]

        interactive_add(db)

        todo = db.get(1)
        assert todo.task == "Full todo"
        assert todo.priority == Priority.P0
        assert todo.project == "work"
        assert todo.tags == ["tag1", "tag2"]
        assert todo.due_date is not None

    @patch("todo_cli.interactive.Prompt.ask")
    def test_add_empty_task_rejected(self, mock_prompt, db, capture_console):
        mock_prompt.side_effect = ["", "p2", "", "", ""]

        interactive_add(db)
        output = capture_console.getvalue()

        assert "cannot be empty" in output
        assert db.get(1) is None

    @patch("todo_cli.interactive.Prompt.ask")
    def test_add_invalid_date(self, mock_prompt, db, capture_console):
        mock_prompt.side_effect = [
            "Task with bad date",
            "p2",
            "",
            "",
            "not-a-date",
        ]

        interactive_add(db)
        output = capture_console.getvalue()

        assert "Invalid date format" in output
        todo = db.get(1)
        assert todo is not None
        assert todo.due_date is None


class TestInteractiveList:
    """Test interactive_list function."""

    @patch("todo_cli.interactive.Prompt.ask")
    @patch("todo_cli.interactive.Confirm.ask")
    def test_list_todos(self, mock_confirm, mock_prompt, db, capture_console):
        db.add("Task 1")
        db.add("Task 2")

        mock_confirm.return_value = False  # Don't include done
        mock_prompt.return_value = ""      # No project filter

        interactive_list(db)
        output = capture_console.getvalue()

        assert "Task 1" in output
        assert "Task 2" in output

    @patch("todo_cli.interactive.Prompt.ask")
    @patch("todo_cli.interactive.Confirm.ask")
    def test_list_with_project_filter(self, mock_confirm, mock_prompt, db, capture_console):
        db.add("Work task", project="work")
        db.add("Home task", project="home")

        mock_confirm.return_value = False
        mock_prompt.return_value = "work"

        interactive_list(db)
        output = capture_console.getvalue()

        assert "Work task" in output
        # Home task should not appear
        assert "Home task" not in output


class TestInteractiveShow:
    """Test interactive_show function."""

    @patch("todo_cli.interactive.IntPrompt.ask")
    def test_show_existing_todo(self, mock_int, db, capture_console):
        db.add("Show me", project="test", priority=Priority.P0)
        mock_int.return_value = 1

        interactive_show(db)
        output = capture_console.getvalue()

        assert "Show me" in output
        assert "test" in output

    @patch("todo_cli.interactive.IntPrompt.ask")
    def test_show_nonexistent_todo(self, mock_int, db, capture_console):
        mock_int.return_value = 999

        interactive_show(db)
        output = capture_console.getvalue()

        assert "not found" in output


class TestInteractiveDone:
    """Test interactive_done function."""

    @patch("todo_cli.interactive.IntPrompt.ask")
    def test_mark_todo_done(self, mock_int, db, capture_console):
        db.add("Complete me")
        mock_int.return_value = 1

        interactive_done(db)
        output = capture_console.getvalue()

        assert "Completed" in output
        todo = db.get(1)
        assert todo.status == Status.DONE

    @patch("todo_cli.interactive.IntPrompt.ask")
    def test_done_nonexistent_todo(self, mock_int, db, capture_console):
        mock_int.return_value = 999

        interactive_done(db)
        output = capture_console.getvalue()

        assert "not found" in output

    @patch("todo_cli.interactive.IntPrompt.ask")
    def test_done_shows_time_spent(self, mock_int, db, capture_console):
        import time
        todo = db.add("Timed task")
        db.start_timer(todo.id)
        time.sleep(1.1)
        db.stop_timer(todo.id)

        mock_int.return_value = 1

        interactive_done(db)
        output = capture_console.getvalue()

        assert "Time spent" in output or "time" in output.lower()


class TestInteractiveDelete:
    """Test interactive_delete function."""

    @patch("todo_cli.interactive.Confirm.ask")
    @patch("todo_cli.interactive.IntPrompt.ask")
    def test_delete_confirmed(self, mock_int, mock_confirm, db, capture_console):
        db.add("Delete me")
        mock_int.return_value = 1
        mock_confirm.return_value = True

        interactive_delete(db)
        output = capture_console.getvalue()

        assert "Deleted" in output
        assert db.get(1) is None

    @patch("todo_cli.interactive.Confirm.ask")
    @patch("todo_cli.interactive.IntPrompt.ask")
    def test_delete_cancelled(self, mock_int, mock_confirm, db, capture_console):
        db.add("Keep me")
        mock_int.return_value = 1
        mock_confirm.return_value = False

        interactive_delete(db)
        output = capture_console.getvalue()

        assert "Cancelled" in output
        assert db.get(1) is not None

    @patch("todo_cli.interactive.IntPrompt.ask")
    def test_delete_nonexistent(self, mock_int, db, capture_console):
        mock_int.return_value = 999

        interactive_delete(db)
        output = capture_console.getvalue()

        assert "not found" in output


class TestInteractiveStart:
    """Test interactive_start function."""

    @patch("todo_cli.interactive.IntPrompt.ask")
    def test_start_timer(self, mock_int, db, capture_console):
        db.add("Track me")
        mock_int.return_value = 1

        interactive_start(db)
        output = capture_console.getvalue()

        assert "Started tracking" in output
        todo = db.get(1)
        assert todo.timer_started is not None

    @patch("todo_cli.interactive.IntPrompt.ask")
    def test_start_nonexistent(self, mock_int, db, capture_console):
        mock_int.return_value = 999

        interactive_start(db)
        output = capture_console.getvalue()

        assert "not found" in output

    @patch("todo_cli.interactive.Confirm.ask")
    @patch("todo_cli.interactive.IntPrompt.ask")
    def test_start_stops_active_timer(self, mock_int, mock_confirm, db, capture_console):
        db.add("First task")
        db.add("Second task")
        db.start_timer(1)

        mock_int.return_value = 2
        mock_confirm.return_value = True  # Confirm stopping first timer

        interactive_start(db)

        # First timer should be stopped
        first = db.get(1)
        assert first.timer_started is None

        # Second timer should be active
        second = db.get(2)
        assert second.timer_started is not None

    @patch("todo_cli.interactive.Confirm.ask")
    @patch("todo_cli.interactive.IntPrompt.ask")
    def test_start_cancel_when_active(self, mock_int, mock_confirm, db, capture_console):
        db.add("First task")
        db.start_timer(1)

        mock_confirm.return_value = False  # Don't stop current timer

        interactive_start(db)

        # First timer should still be active
        first = db.get(1)
        assert first.timer_started is not None


class TestInteractiveStop:
    """Test interactive_stop function."""

    @patch("todo_cli.interactive.Confirm.ask")
    def test_stop_active_timer(self, mock_confirm, db, capture_console):
        import time
        db.add("Stop me")
        db.start_timer(1)
        time.sleep(1.1)

        mock_confirm.return_value = True

        interactive_stop(db)
        output = capture_console.getvalue()

        assert "Stopped" in output
        todo = db.get(1)
        assert todo.timer_started is None

    def test_stop_no_active_timer(self, db, capture_console):
        db.add("Not tracking")

        interactive_stop(db)
        output = capture_console.getvalue()

        assert "No active timer" in output


class TestInteractiveEdit:
    """Test interactive_edit function."""

    @patch("todo_cli.interactive.Prompt.ask")
    @patch("todo_cli.interactive.IntPrompt.ask")
    def test_edit_todo(self, mock_int, mock_prompt, db, capture_console):
        db.add("Original task", project="old", priority=Priority.P2)
        mock_int.return_value = 1

        mock_prompt.side_effect = [
            "Updated task",  # New task
            "p0",            # New priority
            "new",           # New project
            "new-tag",       # New tags
            "doing",         # New status
        ]

        interactive_edit(db)
        output = capture_console.getvalue()

        assert "Updated" in output

        todo = db.get(1)
        assert todo.task == "Updated task"
        assert todo.priority == Priority.P0
        assert todo.project == "new"
        assert todo.tags == ["new-tag"]
        assert todo.status == Status.DOING

    @patch("todo_cli.interactive.IntPrompt.ask")
    def test_edit_nonexistent(self, mock_int, db, capture_console):
        mock_int.return_value = 999

        interactive_edit(db)
        output = capture_console.getvalue()

        assert "not found" in output


class TestInteractiveReport:
    """Test interactive_report function."""

    @patch("todo_cli.interactive.Prompt.ask")
    def test_daily_report(self, mock_prompt, db, capture_console):
        mock_prompt.return_value = "daily"

        interactive_report(db)
        output = capture_console.getvalue()

        assert "Report" in output or "No time tracked" in output

    @patch("todo_cli.interactive.Prompt.ask")
    def test_weekly_report(self, mock_prompt, db, capture_console):
        mock_prompt.return_value = "weekly"

        interactive_report(db)
        output = capture_console.getvalue()

        assert "No time tracked" in output or "Week" in output

    @patch("todo_cli.interactive.Prompt.ask")
    def test_project_report(self, mock_prompt, db, capture_console):
        db.add("Task", project="myproj")
        mock_prompt.side_effect = ["project", "myproj"]

        interactive_report(db)
        output = capture_console.getvalue()

        assert "myproj" in output


class TestInteractiveExport:
    """Test interactive_export function."""

    @patch("todo_cli.interactive.Confirm.ask")
    @patch("todo_cli.interactive.Prompt.ask")
    def test_export_json(self, mock_prompt, mock_confirm, db, capture_console, temp_dir, monkeypatch):
        db.add("Export me")
        mock_prompt.return_value = "json"
        mock_confirm.return_value = True

        # Change cwd to temp_dir so export saves there
        monkeypatch.chdir(temp_dir)
        interactive_export(db)

        output = capture_console.getvalue()
        assert "Exported" in output

    @patch("todo_cli.interactive.Confirm.ask")
    @patch("todo_cli.interactive.Prompt.ask")
    def test_export_csv(self, mock_prompt, mock_confirm, db, capture_console, temp_dir, monkeypatch):
        db.add("Export me")
        mock_prompt.return_value = "csv"
        mock_confirm.return_value = True

        monkeypatch.chdir(temp_dir)
        interactive_export(db)

        output = capture_console.getvalue()
        assert "Exported" in output


class TestInteractiveProjects:
    """Test interactive_projects function."""

    def test_list_projects(self, db, capture_console):
        db.add("Task 1", project="project-a")
        db.add("Task 2", project="project-b")

        interactive_projects(db)
        output = capture_console.getvalue()

        assert "project-a" in output
        assert "project-b" in output

    def test_no_projects(self, db, capture_console):
        db.add("No project task")

        interactive_projects(db)
        output = capture_console.getvalue()

        assert "No projects found" in output


class TestRunInteractive:
    """Test run_interactive main loop."""

    @patch("todo_cli.interactive.Database")
    @patch("todo_cli.interactive.Prompt.ask")
    def test_quit_command(self, mock_prompt, mock_db_class, capture_console):
        mock_db = MagicMock()
        mock_db.list_all.return_value = []
        mock_db.get_active_timer.return_value = None
        mock_db_class.return_value = mock_db

        mock_prompt.side_effect = ["q"]

        run_interactive()
        output = capture_console.getvalue()

        assert "Goodbye" in output

    @patch("todo_cli.interactive.Database")
    @patch("todo_cli.interactive.Prompt.ask")
    def test_help_command(self, mock_prompt, mock_db_class, capture_console):
        mock_db = MagicMock()
        mock_db.list_all.return_value = []
        mock_db.get_active_timer.return_value = None
        mock_db_class.return_value = mock_db

        mock_prompt.side_effect = ["?", "q"]

        run_interactive()
        output = capture_console.getvalue()

        assert "add" in output.lower()
        assert "list" in output.lower()

    @patch("todo_cli.interactive.Database")
    @patch("todo_cli.interactive.Prompt.ask")
    def test_unknown_command(self, mock_prompt, mock_db_class, capture_console):
        mock_db = MagicMock()
        mock_db.list_all.return_value = []
        mock_db.get_active_timer.return_value = None
        mock_db_class.return_value = mock_db

        mock_prompt.side_effect = ["unknowncmd", "q"]

        run_interactive()
        output = capture_console.getvalue()

        assert "Unknown command" in output

    @patch("todo_cli.interactive.Database")
    @patch("todo_cli.interactive.Prompt.ask")
    def test_empty_command_ignored(self, mock_prompt, mock_db_class, capture_console):
        mock_db = MagicMock()
        mock_db.list_all.return_value = []
        mock_db.get_active_timer.return_value = None
        mock_db_class.return_value = mock_db

        mock_prompt.side_effect = ["", "", "q"]

        run_interactive()
        # Should not crash, just continue

    @patch("todo_cli.interactive.Confirm.ask")
    @patch("todo_cli.interactive.Database")
    @patch("todo_cli.interactive.Prompt.ask")
    def test_quit_with_active_timer(self, mock_prompt, mock_db_class, mock_confirm, capture_console):
        mock_db = MagicMock()
        mock_db.list_all.return_value = []

        # Create a mock todo with active timer
        mock_todo = MagicMock()
        mock_todo.id = 1
        mock_todo.task = "Active task"
        mock_todo.format_time.return_value = "00:05:00"
        mock_db.get_active_timer.return_value = mock_todo
        mock_db_class.return_value = mock_db

        mock_prompt.side_effect = ["q"]
        mock_confirm.return_value = True  # Confirm stop timer

        run_interactive()
        output = capture_console.getvalue()

        mock_db.stop_timer.assert_called_once()

    @patch("todo_cli.interactive.display_stats")
    @patch("todo_cli.interactive.Database")
    @patch("todo_cli.interactive.Prompt.ask")
    def test_stats_command(self, mock_prompt, mock_db_class, mock_display_stats, capture_console):
        mock_db = MagicMock()
        mock_db.list_all.return_value = []
        mock_db.get_active_timer.return_value = None
        mock_db.get_stats.return_value = {"total": 5, "done": 2}
        mock_db_class.return_value = mock_db

        mock_prompt.side_effect = ["stats", "q"]

        run_interactive()

        mock_display_stats.assert_called_once()

    @patch("todo_cli.interactive.Database")
    @patch("todo_cli.interactive.Prompt.ask")
    def test_active_command_no_timer(self, mock_prompt, mock_db_class, capture_console):
        mock_db = MagicMock()
        mock_db.list_all.return_value = []
        mock_db.get_active_timer.return_value = None
        mock_db_class.return_value = mock_db

        mock_prompt.side_effect = ["active", "q"]

        run_interactive()
        output = capture_console.getvalue()

        assert "No active timer" in output

    @patch("todo_cli.interactive.display_todo_detail")
    @patch("todo_cli.interactive.Database")
    @patch("todo_cli.interactive.Prompt.ask")
    def test_active_command_with_timer(self, mock_prompt, mock_db_class, mock_display, capture_console):
        mock_db = MagicMock()
        mock_db.list_all.return_value = []

        mock_todo = MagicMock()
        mock_db.get_active_timer.return_value = mock_todo
        mock_db_class.return_value = mock_db

        mock_prompt.side_effect = ["active", "q"]

        # Need to handle the second get_active_timer call for quit
        mock_db.get_active_timer.side_effect = [mock_todo, None]

        run_interactive()

        mock_display.assert_called_once_with(mock_todo)


class TestMenuOptions:
    """Test menu options constant."""

    def test_menu_contains_all_commands(self):
        # Check the parts inside [green] tags for each command
        assert "[green]a[/green]dd" in MENU_OPTIONS
        assert "[green]l[/green]ist" in MENU_OPTIONS
        assert "[green]s[/green]how" in MENU_OPTIONS
        assert "[green]d[/green]one" in MENU_OPTIONS
        assert "[green]del[/green]ete" in MENU_OPTIONS
        assert "[green]st[/green]art" in MENU_OPTIONS
        assert "[green]sto[/green]p" in MENU_OPTIONS
        assert "[green]e[/green]dit" in MENU_OPTIONS
        assert "[green]r[/green]eport" in MENU_OPTIONS
        assert "[green]ex[/green]port" in MENU_OPTIONS
        assert "[green]stat[/green]s" in MENU_OPTIONS
        assert "[green]p[/green]rojects" in MENU_OPTIONS
        assert "[green]q[/green]uit" in MENU_OPTIONS


class TestCommandAliases:
    """Test that command aliases work correctly."""

    @patch("todo_cli.interactive.interactive_list")
    @patch("todo_cli.interactive.Database")
    @patch("todo_cli.interactive.Prompt.ask")
    def test_list_aliases(self, mock_prompt, mock_db_class, mock_list, capture_console):
        mock_db = MagicMock()
        mock_db.list_all.return_value = []
        mock_db.get_active_timer.return_value = None
        mock_db_class.return_value = mock_db

        # Test all list aliases
        mock_prompt.side_effect = ["l", "list", "ls", "q"]

        run_interactive()

        assert mock_list.call_count == 3

    @patch("todo_cli.interactive.interactive_done")
    @patch("todo_cli.interactive.Database")
    @patch("todo_cli.interactive.Prompt.ask")
    def test_done_aliases(self, mock_prompt, mock_db_class, mock_done, capture_console):
        mock_db = MagicMock()
        mock_db.list_all.return_value = []
        mock_db.get_active_timer.return_value = None
        mock_db_class.return_value = mock_db

        mock_prompt.side_effect = ["d", "done", "complete", "q"]

        run_interactive()

        assert mock_done.call_count == 3

    @patch("todo_cli.interactive.interactive_delete")
    @patch("todo_cli.interactive.Database")
    @patch("todo_cli.interactive.Prompt.ask")
    def test_delete_aliases(self, mock_prompt, mock_db_class, mock_delete, capture_console):
        mock_db = MagicMock()
        mock_db.list_all.return_value = []
        mock_db.get_active_timer.return_value = None
        mock_db_class.return_value = mock_db

        mock_prompt.side_effect = ["del", "delete", "rm", "q"]

        run_interactive()

        assert mock_delete.call_count == 3
